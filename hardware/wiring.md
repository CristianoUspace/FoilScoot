# Hardware and wiring

Current divider: owner-supplied updated sketch, 22 kΩ / 10 kΩ. Historical 27 kΩ design: `docs/original/LEGGIMI_BATTERIA.md`. This document describes that baseline; the exact ESP32 carrier board and MPU6050 breakout are not identified.

## Bill of materials

| Part | Baseline detail |
|---|---|
| ESP32 board | ESP-WROOM-32 module; carrier model and power input pending |
| IMU | MPU6050, I2C address 0x68; breakout supply requirements pending |
| Warning LED | GPIO23, active high; original resistor/circuit must be confirmed |
| Board LED | GPIO2 in firmware; depends on carrier board |
| Battery | LiPo 2S, 7.4 V nominal, 8.4 V fully charged |
| Divider top resistor | 22 kΩ, 1%, 1/4 W |
| Divider bottom resistor | 10 kΩ, 1%, 1/4 W |
| Suggested capacitor | 100 nF ceramic, GPIO34 to GND, near ESP32 |
| Converter | Non-isolated supply converter; model/output and carrier input pending |

The sketch calls `Wire.begin()` without explicit pins, at 400 kHz. Confirm the actual SDA/SCL pins against the selected board and working wiring. Do not infer the full pinout from the module name. The supplied package does not specify the breakout supply pin, LED resistor or converter wiring sufficiently for a complete assembly diagram.

## Battery divider from the supplied v1.5 design

```text
2S LiPo + -- main switch --+-- converter input (verify model/input wiring)
                          |
                        22 kΩ
                          |
                          +-- GPIO34
                          |      |
                        10 kΩ  100 nF
                          |      |
LiPo - / common GND ------+------+-- ESP32 GND
```

The divider measures upstream of the converter. At 8.4 V, the divider node is approximately 2.625 V (`Vpack × 10/32`). Never connect LiPo positive directly to GPIO34. This dimensioning applies to the supplied 2S design only.

Build with the battery disconnected; measure the divider node before connecting it to ESP32. The main switch must remove power from both converter and divider to avoid driving an unpowered GPIO. Disconnect the battery measurement branch during USB tests unless the power sequence is managed. Verify the carrier board's power circuit before combining USB and external power.

The supplied updated sketch already sets `BATTERY_MONITOR_ENABLED = true`. Verify the circuit before using it, or disable this setting for a setup without the divider. Compare the displayed voltage with a multimeter under Wi-Fi operation. Adjust `BATTERY_CAL_FACTOR` by multiplying its current value by `Vmultimeter / Vdisplay`; verify at another voltage too.

The recorder warns at 7.2 V and 7.0 V with 0.1 V hysteresis. These are baseline operational thresholds, not universal battery limits. Pack voltage does not detect individual cell imbalance, provide protection or disconnect the battery. The supplied design requires appropriate per-cell monitoring/protection. Waterproof enclosure, mounting and strain relief are not specified or validated in this package.
