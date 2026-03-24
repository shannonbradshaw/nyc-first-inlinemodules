# Distance Display Module: Line by Line

This tutorial walks through every line of the distance display inline module.
By the end, you'll understand every piece well enough to write your own.

## The full code

```python
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


class MyGenericService(GenericService, EasyResource):
    MODEL: ClassVar[Model] = Model(ModelFamily("REPLACE", "distance-display"), "generic-service")

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

        display_name = attrs.get("display")
        if not isinstance(display_name, str) or not display_name:
            raise ValueError("attribute 'display' (non-empty string) is required")
        required_deps.append(display_name)

        unit = attrs.get("unit")
        if unit is not None and unit not in ["cm", "in", "m"]:
            raise ValueError("attribute 'unit' must be 'cm', 'in', or 'm'")

        return required_deps, []

    @classmethod
    def new(
        cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
    ) -> Self:
        self = super().new(config, dependencies)
        attrs = struct_to_dict(config.attributes)

        self.unit = attrs.get("unit", "cm")

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
            raise ValueError("No sensor readings available")

        distance_m = readings.get("distance")
        if distance_m is None:
            raise ValueError(
                f"Sensor returned no 'distance' key. Got: {list(readings.keys())}"
            )

        distance_m = float(distance_m)

        if self.unit == "cm":
            display_value = distance_m * 100
        elif self.unit == "in":
            display_value = distance_m * 39.3701
        else:
            display_value = distance_m

        if display_value < 10:
            text = f"{display_value:.2f}"
        elif display_value < 100:
            text = f"{display_value:.1f}"
        else:
            text = f"{int(display_value):4d}"

        await self.display.do_command({"print": {"value": text}})

        return {
            "distance_m": distance_m,
            "displayed": text,
            "unit": self.unit,
        }
```

Now let's break it down.

---

## Part 1: Imports

### Python type hints

```python
from typing import ClassVar, List, Mapping, Optional, Sequence, Tuple
```

Python is a dynamically typed language, which means you don't *have* to declare what type a variable is. But **type hints** let you annotate your code so that other people (and tools) can understand what types you expect. They don't change how the code runs. Think of them as labels.

Here's what each one means:

- **`ClassVar`** — marks a variable as belonging to the class itself, not to individual instances. Like a shared constant.
- **`List`** — a list of things, like `List[str]` means "a list of strings."
- **`Mapping`** — a read-only dictionary. `Mapping[str, int]` means "keys are strings, values are integers."
- **`Optional`** — means "this value could be `None`." `Optional[float]` is the same as `float | None`.
- **`Sequence`** — anything you can loop over in order (a list, a tuple, etc.).
- **`Tuple`** — a fixed-size collection. `Tuple[str, int]` means "first item is a string, second is an integer."

```python
from typing_extensions import Self
```

**`Self`** refers to "the current class." When a method returns `Self`, it means "I return an instance of whatever class I belong to." This comes from `typing_extensions` because it was added to Python relatively recently.

### Viam SDK imports

```python
from viam.components.sensor import Sensor
```

This gives us the `Sensor` class, which represents any sensor component on a Viam machine. We'll use it to read distance values from the ultrasonic sensor.

```python
from viam.components.generic import Generic as GenericComponent
```

The `Generic` component type is used for hardware that doesn't fit into a standard category like "motor" or "sensor." Our LED display is a generic component. We rename it to `GenericComponent` with `as` to avoid a name collision (there's also a generic *service*, which we import next).

```python
from viam.proto.app.robot import ComponentConfig
```

`ComponentConfig` is the configuration object that Viam passes to your module. It contains the JSON attributes you set in the Viam app (like `"sensor": "distance-sensor"`).

```python
from viam.proto.common import ResourceName
```

Every component and service on a Viam machine has a unique `ResourceName`. It's like an address that identifies a specific piece of hardware or software on the machine.

```python
from viam.resource.base import ResourceBase
```

`ResourceBase` is the base class for all Viam resources (components and services). It appears in type hints for the `dependencies` parameter.

```python
from viam.resource.easy_resource import EasyResource
```

`EasyResource` is a helper mixin that handles boilerplate for you. It simplifies creating a module by providing default implementations for common patterns.

```python
from viam.resource.types import Model, ModelFamily
```

Every Viam module has a **model** — a three-part identifier like `"myorg:myproject:mymodel"`. `Model` and `ModelFamily` are used to construct this identifier.

```python
from viam.utils import struct_to_dict, ValueTypes
```

- **`struct_to_dict`** converts the protobuf configuration structure into a regular Python dictionary. Without this, you'd have to navigate a complex protobuf object.
- **`ValueTypes`** is a type alias for the kinds of values that `do_command` can accept and return (strings, numbers, booleans, lists, dicts).

```python
from viam.services.generic import Generic as GenericService
```

This is the base class for a generic *service*. A service is different from a component: components represent hardware (sensors, motors), while services represent software logic. Our module is a service that reads from components. We rename it to `GenericService` to avoid confusion with `GenericComponent`.

---

## Part 2: The class definition

```python
class MyGenericService(GenericService, EasyResource):
    MODEL: ClassVar[Model] = Model(ModelFamily("REPLACE", "distance-display"), "generic-service")
```

This creates a new class called `MyGenericService`. Let's unpack the syntax:

### Inheritance

```python
class MyGenericService(GenericService, EasyResource):
```

The parentheses after the class name mean "this class inherits from these other classes." This is called **inheritance** — our class gets all the behavior of `GenericService` and `EasyResource` automatically, and we only need to write the parts that are specific to our module.

Think of it like a template: `GenericService` provides the structure that Viam expects, and `EasyResource` fills in common boilerplate. We just fill in the custom parts.

### The MODEL identifier

```python
MODEL: ClassVar[Model] = Model(ModelFamily("REPLACE", "distance-display"), "generic-service")
```

- `ClassVar[Model]` means this variable belongs to the class, not to individual instances. Every instance of `MyGenericService` shares the same MODEL.
- The `Model(...)` creates the three-part identifier that Viam uses to find your module. When you create an inline module in the Viam app, the platform generates this for you. The `"REPLACE"` placeholder gets filled in with your organization's ID.

---

## Part 3: validate_config

```python
@classmethod
def validate_config(
    cls, config: ComponentConfig
) -> Tuple[Sequence[str], Sequence[str]]:
```

### What is `@classmethod`?

The `@classmethod` decorator means this method belongs to the *class itself*, not to an instance. Notice the first parameter is `cls` (the class) instead of `self` (an instance). This matters because `validate_config` runs *before* any instance of your service exists — Viam calls it to check your configuration before creating anything.

### What does this method do?

This method has two jobs:
1. **Validate** that the configuration JSON makes sense (required fields exist, types are correct).
2. **Return** a list of dependencies your module needs (other components on the machine).

### The return type

```python
-> Tuple[Sequence[str], Sequence[str]]:
```

This means the method returns a tuple with two lists of strings:
- First list: **required** dependencies (names of components this module *must* have)
- Second list: **optional** dependencies (names of components this module *can* use but doesn't require)

### Inside the method

```python
attrs = struct_to_dict(config.attributes)
```

Converts the protobuf config into a plain Python dictionary. After this line, `attrs` is something like:
```python
{"sensor": "distance-sensor", "display": "led-display", "unit": "cm"}
```

```python
required_deps: List[str] = []
```

Creates an empty list that we'll fill with dependency names.

```python
sensor_name = attrs.get("sensor")
if not isinstance(sensor_name, str) or not sensor_name:
    raise ValueError("attribute 'sensor' (non-empty string) is required")
required_deps.append(sensor_name)
```

This block:
1. Tries to get `"sensor"` from the config. `attrs.get("sensor")` returns `None` if the key doesn't exist (instead of crashing like `attrs["sensor"]` would).
2. Checks that it's a non-empty string. `isinstance(sensor_name, str)` checks the type. `not sensor_name` catches empty strings.
3. If the check fails, raises a `ValueError` — this tells Viam the configuration is invalid, and the user sees the error message in the app.
4. If it passes, adds the name to our required dependencies list.

The same pattern repeats for the display dependency.

```python
unit = attrs.get("unit")
if unit is not None and unit not in ["cm", "in", "m"]:
    raise ValueError("attribute 'unit' must be 'cm', 'in', or 'm'")
```

The `unit` attribute is optional. We only validate it *if it's present* (`is not None`). The `not in` check ensures it's one of the three allowed values.

```python
return required_deps, []
```

Returns our required dependencies and an empty list for optional dependencies. This tells Viam: "before you create my service, make sure these components exist and are ready."

---

## Part 4: new

```python
@classmethod
def new(
    cls, config: ComponentConfig, dependencies: Mapping[ResourceName, ResourceBase]
) -> Self:
```

This is the **constructor** — it creates a new instance of your service. Viam calls this after `validate_config` passes. The `dependencies` parameter is a dictionary containing the actual component objects that you requested in `validate_config`.

### Inside the method

```python
self = super().new(config, dependencies)
```

`super()` refers to the parent class (`EasyResource`). This calls the parent's `new` method first, which handles basic setup. The result is a new instance of our service, stored in `self`.

```python
attrs = struct_to_dict(config.attributes)
```

Same conversion as in `validate_config`. We need to read the config again because `new` is a separate method call.

```python
self.unit = attrs.get("unit", "cm")
```

The second argument to `.get()` is a **default value**. If `"unit"` isn't in the config, use `"cm"`. This is how we handle optional attributes.

### Resolving dependencies

```python
sensor_name = attrs.get("sensor")
display_name = attrs.get("display")
self.sensor = dependencies[Sensor.get_resource_name(sensor_name)]
self.display = dependencies[GenericComponent.get_resource_name(display_name)]
```

This is where the magic happens. `dependencies` is a dictionary where:
- The **keys** are `ResourceName` objects (unique identifiers)
- The **values** are actual component objects you can call methods on

`Sensor.get_resource_name("distance-sensor")` creates the `ResourceName` key for looking up that specific sensor in the dependencies dictionary. After this, `self.sensor` is a real `Sensor` object that we can call `get_readings()` on.

We store these on `self` so that `do_command` can use them later.

```python
return self
```

Returns the fully constructed service instance back to Viam.

---

## Part 5: do_command

```python
async def do_command(
    self,
    command: Mapping[str, ValueTypes],
    *,
    timeout: Optional[float] = None,
    **kwargs
) -> Mapping[str, ValueTypes]:
```

This is where your actual logic lives. Viam calls this method when the service is triggered (manually from the app, or automatically via a scheduled job).

### What is `async`?

`async def` makes this an **asynchronous** method. Reading from a sensor or writing to a display takes time — the signal has to travel to the hardware and back. `async` lets Python do other work while waiting, instead of freezing up.

Every time you see `await` before a call, it means "wait for this to finish before continuing." You can only use `await` inside an `async` method.

### The `*` in the parameters

```python
    *,
    timeout: Optional[float] = None,
    **kwargs
```

The bare `*` means everything after it is a **keyword-only argument** — you must use the name when passing it (like `timeout=5.0`), you can't just pass it by position. `**kwargs` captures any additional keyword arguments. These are part of the Viam interface and you don't need to worry about them for this module.

### Reading the sensor

```python
readings = await self.sensor.get_readings()
```

Calls the ultrasonic sensor and waits for a response. `readings` is a dictionary like `{"distance": 0.453}` where the value is in meters.

```python
if not readings:
    raise ValueError("No sensor readings available")
```

Safety check: if the sensor returned nothing, stop and report an error.

```python
distance_m = readings.get("distance")
if distance_m is None:
    raise ValueError(
        f"Sensor returned no 'distance' key. Got: {list(readings.keys())}"
    )
```

Gets the `"distance"` value from the readings. If it's not there, the error message tells you what keys *were* returned — helpful for debugging. The `f"..."` syntax is an **f-string**: anything inside `{...}` is evaluated as Python code and inserted into the string.

```python
distance_m = float(distance_m)
```

Ensures the value is a floating-point number. Sensor readings sometimes come back as other numeric types.

### Unit conversion

```python
if self.unit == "cm":
    display_value = distance_m * 100
elif self.unit == "in":
    display_value = distance_m * 39.3701
else:
    display_value = distance_m
```

The sensor always reports meters. This converts to whatever unit the user configured. Multiplying by 100 converts meters to centimeters. Multiplying by 39.3701 converts meters to inches. If the unit is `"m"`, no conversion needed.

### Formatting for the display

```python
if display_value < 10:
    text = f"{display_value:.2f}"
elif display_value < 100:
    text = f"{display_value:.1f}"
else:
    text = f"{int(display_value):4d}"
```

The LED display has 4 characters. We need to format the number to fit:

- **Less than 10:** show 2 decimal places (e.g. `"3.45"`) — 4 characters including the decimal point
- **Less than 100:** show 1 decimal place (e.g. `"45.2"`) — 4 characters
- **100 or more:** show a whole number, right-aligned in 4 spaces (e.g. `" 145"`)

The `:.2f` inside the f-string means "format as a floating-point number with 2 decimal places." The `:4d` means "format as an integer, padded to 4 characters wide."

### Writing to the display

```python
await self.display.do_command({"print": {"value": text}})
```

Sends a command to the LED display component. The `{"print": {"value": text}}` format is specific to the HT16K33 display module — it accepts a `print` command with a `value` to show on screen.

### Returning results

```python
return {
    "distance_m": distance_m,
    "displayed": text,
    "unit": self.unit,
}
```

`do_command` must return a dictionary. This return value shows up in the Viam app when you run the command manually, and is useful for debugging. It tells you:
- The raw distance in meters
- What text was sent to the display
- What unit was used

---

## How it all fits together

1. You configure the module in the Viam app with a JSON block specifying which sensor and display to use.
2. Viam calls `validate_config` to check that the config makes sense.
3. Viam calls `new` to create the service, connecting it to the sensor and display.
4. A scheduled job calls `do_command` continuously.
5. Each call reads the sensor, converts the distance, formats it, and writes it to the LED.

The sensor reading, the math, and the display command all happen in `do_command`, every time it's called. Change the `"unit"` in your config, and the display switches between centimeters, inches, and meters — no code changes needed.
