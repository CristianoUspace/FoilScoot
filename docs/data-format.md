# CSV format

The authoritative column list is `FIELDS` in `desktop/client.py`. UTF-8, comma-separated, decimal point. Import explicitly as comma-delimited in locales that default to semicolons.

| Fields | Meaning |
|---|---|
| row_type | `data`, `event` or `battery` |
| session_id, boot_id | Recording identifier and board boot identifier |
| device_us | Monotonic board microseconds; IMU time is start of I2C read |
| session_s | Seconds relative to accepted START |
| received_utc, received_local | Laptop receipt date/time with timezone |
| received_monotonic_ns | Laptop monotonic clock at decoding |
| sequence | IMU sample sequence since boot, including preview |
| missed_slots_total | Cumulative missed acquisition slots since boot |
| acc_x_g, acc_y_g, acc_z_g | Filtered acceleration including gravity, in g |
| gyro_x_dps, gyro_y_dps, gyro_z_dps | Bias-corrected, filtered gyro in degrees/s |
| event, led | Event name and reported LED state |
| battery_v, battery_state | Pack voltage and recorder classification |

Battery values are not copied into IMU rows. Empty means absent, not zero. Laptop-generated completion/interruption events have no board timestamp. The two clocks are not synchronized. Compare acquisition intervals using `device_us`, not reception timestamps.

The transport is newline-delimited JSON over TCP, protocol 1. Client commands are `HELLO`, `PING`, `CAL`, `START <id>`, `MARK`, `STOP`. The exact message implementation remains in the unchanged source. Do not concatenate sessions or boot IDs before timing analysis.
