from typing import ClassVar, List, Mapping, Optional, Sequence, Tuple

from typing_extensions import Self
from viam.components.sensor import Sensor
from viam.components.generic import Generic as GenericComponent
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import struct_to_dict, ValueTypes
from viam.services.generic import Generic as GenericService
from viam.logging import getLogger

LOGGER = getLogger(__name__)


# IMPORTANT: Do not change the class name or the MODEL triplet below.
# The platform uses these auto-generated values to identify your module.
# Changing them will break your inline module.
class MyGenericService(GenericService, EasyResource):
    MODEL: ClassVar[Model] = Model(ModelFamily("3448343a-37bc-489d-bd46-2b3bc0c4b5ac", "distance-display0"), "generic-service")

    @classmethod
    def validate_config(
        cls, config: ComponentConfig
    ) -> Tuple[Sequence[str], Sequence[str]]:
        attrs = struct_to_dict(config.attributes)

        required_deps: List[str] = []

        # sensor dependency
        sensor_name = attrs.get("sensor")
        if not isinstance(sensor_name, str) or not sensor_name:
            raise ValueError("attribute 'sensor' (non-empty string) is required")
        required_deps.append(sensor_name)

        # led display dependency
        display_name = attrs.get("display")
        if not isinstance(display_name, str) or not display_name:
            raise ValueError("attribute 'display' (non-empty string) is required")
        required_deps.append(display_name)

        return required_deps, []

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        self = super().new(config, dependencies)
        attrs = struct_to_dict(config.attributes)

        # Resolve dependencies
        sensor_name = attrs.get("sensor")
        display_name = attrs.get("display")
        self.sensor = dependencies[Sensor.get_resource_name(sensor_name)]
        self.display = dependencies[GenericComponent.get_resource_name(display_name)]

        return self

    async def do_command(
        self,
        command: Mapping[str, ValueTypes],
        *,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Mapping[str, ValueTypes]:
        readings = await self.sensor.get_readings()
        if not readings:
            LOGGER.warning("No sensor readings available")
            return {"error": "no readings"}

        distance_m = readings.get("distance")
        if distance_m is None:
            LOGGER.warning("Sensor returned no 'distance' key. Got: %s", list(readings.keys()))
            return {"error": "no distance key"}

        distance_m = float(distance_m)

        # Format for 4-character display
        if distance_m < 10:
            text = f"{distance_m:.2f}"
        else:
            text = f"{distance_m:.1f}"

        # Clear the display, then show the new value
        await self.display.do_command({"print": {"value": "    "}})
        await self.display.do_command({"print": {"value": text}})

        return {
            "distance_m": distance_m,
            "displayed": text,
        }
