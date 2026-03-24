# Wiring Instructions

These instructions work for both Raspberry Pi 4 and Raspberry Pi 5.

## Components

- HC-SR04 ultrasonic distance sensor
- 28BYJ-48 stepper motor with ULN2003 driver board
- HT16K33 14-segment LED display (0.54" quad alphanumeric backpack)

## HC-SR04 ultrasonic sensor

| HC-SR04 Pin | Pi physical pin |
|---|---|
| VCC | Pin 1 (3.3V) |
| Trig | Pin 38 |
| Echo | Pin 40 |
| GND | Pin 6 |

The HC-SR04 is spec'd for 5V but works at 3.3V with reduced range. Running it at 3.3V means the Echo output is also 3.3V, so no voltage divider is needed on either Pi 4 or Pi 5.

## 28BYJ-48 stepper motor (ULN2003 driver)

| ULN2003 Pin | Pi physical pin |
|---|---|
| IN1 | Pin 11 |
| IN2 | Pin 13 |
| IN3 | Pin 15 |
| IN4 | Pin 16 |
| + | Pin 4 (5V) |
| - | Pin 9 (GND) |

The motor plugs into the ULN2003 driver board via its white JST connector.

Note: for extended use, the stepper motor can draw enough current to brownout the Pi. If you experience instability, use an external 5V power supply for the motor driver's + and - pins instead of the Pi's 5V.

## HT16K33 14-segment LED display

| LED Pin | Pi physical pin |
|---|---|
| VCC | Pin 2 (5V) |
| Vi2c | Pin 17 (3.3V) |
| SDA | Pin 3 |
| SCL | Pin 5 |
| GND | Pin 14 |

VCC is 5V for brighter LEDs. Vi2c is 3.3V to match the Pi's I2C logic level. The HT16K33 accepts 3V-5V on VCC.

After wiring, enable I2C and verify the display is detected:

```bash
sudo raspi-config nonint do_i2c 0
i2cdetect -y 1
```

The default I2C address is 0x70. If address jumpers on the back of the board are bridged, the address will be different. Use whatever address shows up in the i2cdetect output.

## Pin summary

| Pin | Used by |
|---|---|
| 1 | Sensor VCC (3.3V) |
| 2 | LED VCC (5V) |
| 3 | LED SDA |
| 4 | Motor + (5V) |
| 5 | LED SCL |
| 6 | Sensor GND |
| 9 | Motor GND |
| 11 | Motor IN1 |
| 13 | Motor IN2 |
| 14 | LED GND |
| 15 | Motor IN3 |
| 16 | Motor IN4 |
| 17 | LED Vi2c (3.3V) |
| 38 | Sensor Trig |
| 40 | Sensor Echo |

## Viam board config

For Pi 5:
```json
"model": "viam:raspberry-pi:rpi5"
```

For Pi 4:
```json
"model": "viam:raspberry-pi:rpi4"
```

All pin numbers in the component configs are physical pin numbers, which are the same on both boards.
