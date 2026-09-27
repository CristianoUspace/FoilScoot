# FoilMotion

ESP32 motion recording for foilscoot and pumping, based on the supplied **FoilScoot Wi-Fi v1.5 battery release** by Cristiano Baldoni.

Record six MPU6050 motion channels on a laptop over a standalone Wi-Fi network, mark video synchronization events with an LED, and optionally log a 2S LiPo pack voltage. No internet connection or Python packages are required for recording.

**Packaging status:** the original firmware and desktop application are included unchanged. The original `src/MPU6050` dependency is missing from the supplied release. Firmware compilation and hardware validation remain pending. This repository is not yet a reproducible firmware release; see [release checklist](docs/release-checklist.md).

## Contents

| Directory | Contents |
|---|---|
| `firmware/FoilScoot_WiFi/` | Original v1.5 Arduino sketch |
| `desktop/` | Original Python recorder, offline Italian interface and Windows launcher |
| `hardware/` | Wiring and bill of materials based on supplied sources |
| `docs/` | Setup, CSV format, provenance and release checklist |
| `docs/original/` | Supplied Italian documentation, preserved unchanged |
| `data/examples/` | Clearly labeled synthetic CSV, not an actual ride |
| `analysis/` | New, standalone CSV inspection tool |

## Quick start

1. The required original MPU6050/I2Cdev sources are bundled beside `firmware/FoilScoot_WiFi/FoilScoot_WiFi.ino` in `src/MPU6050`.
2. Open that sketch in Arduino IDE. Use the board configuration and ESP32 core from the working setup (exact versions still to be recorded). Review [hardware wiring](hardware/wiring.md) before powering the board. Battery monitoring is already enabled in this owner-supplied configuration: verify the 22 kΩ / 10 kΩ divider before use, or set `BATTERY_MONITOR_ENABLED = false` for a setup without it.
3. Upload, then keep the IMU stationary through startup calibration. The sketch waits three seconds, then performs settling and calibration.
4. Connect the laptop to **FoilScoot-IMU**, password **FoilScoot32**. No internet access is expected. These are public defaults, not private credentials. Only one station is allowed.
5. Install Python 3.10 or newer, then run from the repository root:

   ```sh
   python desktop/client.py
   ```

   On Windows, `desktop/Avvia_FoilScoot.cmd` also launches the client. The browser opens at http://127.0.0.1:8080. Device TCP: `192.168.4.1:8765`.
6. Use **Avvia registrazione** (start), **Segna evento / LED** (mark) and **Stop e salva** (stop and save). Wait for `COMPLETED` before closing. Files are stored in `desktop/registrazioni/` by default. See [recording guide](docs/recording.md).
7. Inspect a recording:

   ```sh
   python analysis/inspect_csv.py data/examples/synthetic.csv
   ```

## What is measured

Nominal 100 Hz filtered acceleration (g, including gravity) and gyro (degrees/s, startup bias corrected). Battery messages are separate, approximately once per second when enabled. Acquisition timestamps come from the ESP32; laptop reception timestamps include network delays.

The baseline does not compute pitch/roll/yaw angles, pumping frequency, efficiency or automatic video alignment. The new inspection tool reports timing and basic ranges only. There is no onboard recording or recovery of disconnected samples.

## Contributing and license

## First session: recordings and hardware

The owner-supplied first session is available in [results](results/README.md): the recorded CSV, Italian analysis, summary plot and shortened footage. [Hardware photographs and a live-client screen recording](images/README.md) show the setup on the board.

Both MP4 files are stored with Git LFS. To download them in a local clone, install Git LFS and run `git lfs install` followed by `git lfs pull`. The analysis refers to the original full-length video; its time references must not be assumed to match the shortened clip.

## Contributing and license

See [CONTRIBUTING.md](CONTRIBUTING.md). Project code and documentation are provided under the [MIT license](LICENSE). Bundled third-party sources retain their original MIT notices; see [third-party notices](THIRD_PARTY_NOTICES.md). Preserve original FoilScoot names in the baseline code to keep its provenance clear.

Run the offline checks with `python -m unittest discover -s tests -v`.
