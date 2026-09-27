# Baseline provenance

The first table below records the INITIAL import, preserved in commit fafc569. The current firmware is superseded by the owner update documented below.

Imported from `FoilScoot_WiFi_v1_5_Batteria.zip` supplied by the project owner. Files below were compared byte for byte against the archive. No original application behavior was changed.

Archive SHA-256: `db7a8dbd9f11288e4b6fd971015cdc100fb70e2ac5e948c70289115cad5a4341`

| Repository path | SHA-256 |
|---|---|
| `docs/original/LEGGIMI_BATTERIA.md` | `ed43f989ef811d2980d34332ac136a921c2f5b50d1a87cb0be383b9ac122df88` |
| `desktop/Avvia_FoilScoot.cmd` | `988a1f55ee9f88d038c22ddbc0feb39f2da7e02b6389934e5a45a5d214f21e76` |
| `desktop/client.py` | `8e589dfb7865b28285ce9e998829c9627900c0ccddd669b2388d8628c496527e` |
| `desktop/index.html` | `5327c78fda2f184546ec321e63ec55b5af46267a1c303d4aa3b434d01c1c5c06` |
| `firmware/FoilScoot_WiFi/FoilScoot_WiFi.ino` | `7ddd9c7a219c8803df85bce0d56bb75914da69f111a0cf26d70224dd02a560bf` |

The separately supplied `LEGGIMI_FoilScoot_WiFi.md` describes v1.3 and earlier changes; the battery document and v1.5 code govern battery behavior. The original dependency folder and original test suite were not supplied.

New additions: English documentation, MIT license, ignore rules, CSV inspector, synthetic example and repository tests. The desktop interface remains in Italian. No release tag is created because firmware dependencies and hardware validation are incomplete.

## Owner update

Source: `FoilScoot_WiFi.zip`. Archive SHA-256: `c3a7c78c6700f305ecf054a72d8cd96f5179dc4c8c881234c3ea0c55fbeacd2b`.

The supplied sketch changes only battery enable false → true and top resistor 27000 → 22000. Repository comments were updated to match 22 kΩ and the bundled dependency; executable code matches the owner sketch. The complete MPU6050 folder is copied byte for byte. Unused MPU9250 and SBUS folders are excluded; no firmware references them. Original documentation remains historical and unchanged. Exact toolchain and upstream library revision remain unconfirmed.

| Bundled file | SHA-256 |
|---|---|
| `FoilScoot_WiFi/src/MPU6050/helper_3dmath.h` | `7831b6e5d2226707d8c8d6736585e970ec141283c6c976b7ee210ecf5ec2ec2c` |
| `FoilScoot_WiFi/src/MPU6050/I2Cdev.cpp` | `0a1288ef9ed45a8ca4c10714e7f553840127d0f8e2c66c7fe933eee0cd50fe44` |
| `FoilScoot_WiFi/src/MPU6050/I2Cdev.h` | `7264c75fcbe2107d8778a9e2bd0e8d24caf131de30b51ffbe5a718f9e578a9b2` |
| `FoilScoot_WiFi/src/MPU6050/MPU6050.cpp` | `b4fdfca4e6fee7ed4a53159df39e7ae13e4ccc1a0fa88dd02ce73f37bf05d67e` |
| `FoilScoot_WiFi/src/MPU6050/MPU6050.h` | `ec3ae81efd1f943e728ca2982d84ee4bf3994dc91281ae5dd443e9767d757984` |
| `FoilScoot_WiFi/src/MPU6050/MPU6050_6Axis_MotionApps20.h` | `36e7af28abaefb073784e75de3ff55cc1b8da852e94f72137585061475d9d178` |
| `FoilScoot_WiFi/src/MPU6050/MPU6050_6Axis_MotionApps_V6_12.h` | `6745c1092143c8908bf8db10194b426c33f11bc5e32919b17985690b2b12e53b` |
| `FoilScoot_WiFi/src/MPU6050/MPU6050_9Axis_MotionApps41.h` | `86ac568e629bb8980360c420f15efb5159761bfbd243906f535a4a821b12476e` |
