from typing import ClassVar, List, Mapping, Optional, Sequence, Tuple

from typing_extensions import Self
from viam.components.motor import Motor
from viam.components.sensor import Sensor
from viam.proto.app.robot import ComponentConfig
from viam.proto.common import ResourceName
from viam.resource.base import ResourceBase
from viam.resource.easy_resource import EasyResource
from viam.resource.types import Model, ModelFamily
from viam.utils import struct_to_dict, ValueTypes
from viam.services.generic import Generic as GenericService
from viam.logging import getLogger

LOGGER = getLogger(__name__)


class MyGenericService(GenericService, EasyResource):
    MODEL: ClassVar[Model] = Model(ModelFamily("3448343a-37bc-489d-bd46-2b3bc0c4b5ac", "motor-speed"), "generic-service")

    @classmethod
    def validate_config(
        cls, config: ComponentConfig
    ) -> Tuple[Sequence[str], Sequence[str]]:
        attrs = struct_to_dict(config.attributes)

        required_deps: List[str] = []

        sensor_name = attrs.get("sensor")
        if not isinstance(sensor_name, str) or not sensor_name:
            raise ValueError("attribute 'sensor' (non-empty string) is required")
        required_deps.append(sensor_name)

        motor_name = attrs.get("motor")
        if not isinstance(motor_name, str) or not motor_name:
            raise ValueError("attribute 'motor' (non-empty string) is required")
        required_deps.append(motor_name)

        max_distance_m = attrs.get("max_distance_m")
        if max_distance_m is None or not isinstance(max_distance_m, (int, float)):
            raise ValueError("attribute 'max_distance_m' is required and must be a number")

        return required_deps, []

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        self = super().new(config, dependencies)
        attrs = struct_to_dict(config.attributes)

        self.max_distance_m = float(attrs.get("max_distance_m"))

        sensor_name = attrs.get("sensor")
        motor_name = attrs.get("motor")
        self.sensor = dependencies[Sensor.get_resource_name(sensor_name)]
        self.motor = dependencies[Motor.get_resource_name(motor_name)]

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

        # Closer = faster. At 0m, full speed. At max_distance_m or beyond, stopped.
        speed = 1.0 - min(distance_m / self.max_distance_m, 1.0)
        await self.motor.set_power(speed)

        return {
            "distance_m": distance_m,
            "speed": speed,
        }
