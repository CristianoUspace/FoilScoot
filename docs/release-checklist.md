# Release checklist

- [x] Import the initial v1.5 package, then the owner-updated sketch and required dependency.
- [x] Preserve supplied Italian documentation and record file hashes.
- [x] Add English setup/wiring/data documentation and a synthetic CSV inspection example.
- [x] Restore the original required MPU6050/I2Cdev dependency from the owner archive and preserve its notices.
- [ ] Identify its exact upstream revision (archive hashes are recorded).
- [ ] Record carrier board, selected Arduino board, Arduino-ESP32 core version and tested IDE/toolchain.
- [ ] Confirm SDA/SCL, breakout supply, converter model/output, LED resistor and full power wiring.
- [ ] Compile and upload the restored baseline with the recorded toolchain.
- [ ] Bench-test calibration, preview, START/MARK/STOP, LED events, disconnection and reboot behavior.
- [ ] Validate battery divider voltage and displayed voltage against a multimeter, then check IMU timing with ADC enabled.
- [ ] Add an explicitly shareable real recording with mounting and test conditions.
- [x] Create the public GitHub repository and publish source files. Create a release/tag only after validation.

Earlier documentation reports simulator tests, but the original tests were not bundled. Repository checks added here do not imply firmware or hardware validation.

## Publish from this local repository

The public repository is `CristianoUspace/FoilScoot`; the project name remains FoilMotion. For a new checkout:

```sh
git clone https://github.com/CristianoUspace/FoilScoot.git
cd FoilScoot
```

If an origin already exists, inspect it before changing anything. Do not publish private recordings. Suggested description: “ESP32 and MPU6050 motion recording for foilscoot and pumping, with Wi-Fi CSV capture and optional 2S LiPo monitoring.”
