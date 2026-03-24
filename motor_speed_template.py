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

        # TODO: Validate the "max_distance_m" attribute.
        # It is required and must be a number (int or float).
        # Hint: look at how sensor_name is validated above,
        # but check for a number instead of a string.

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

        # TODO: Resolve the sensor and motor dependencies.
        # Store them as self.sensor and self.motor.
        #
        # Hint: In the display module, we resolved the sensor like this:
        #   self.sensor = dependencies[Sensor.get_resource_name(sensor_name)]
        #
        # Do the same for the sensor here, and then do the equivalent
        # for the motor using the Motor class.

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

        # TODO: Calculate the motor speed based on distance.
        # The motor should spin FASTER when objects are CLOSER.
        # Speed should be a number between 0.0 (stopped) and 1.0 (full speed).
        #
        # At distance 0, speed should be 1.0 (full speed).
        # At max_distance_m or beyond, speed should be 0.0 (stopped).
        #
        # Hint: think about what distance_m / self.max_distance_m gives you,
        # and how to flip it so that closer = faster.
        speed = 0.0  # Replace this line with your calculation

        await self.motor.set_power(speed)

        return {
            "distance_m": distance_m,
            "speed": speed,
        }
