# CSV inspection

Run `python analysis/inspect_csv.py path/to/recording.csv` from the repository root. Output is JSON with timing, sequence gaps, missed-slot delta, event names and channel ranges. Python 3.10+; no packages required.

Timing uses board acquisition timestamps for IMU rows only. The reported mean received sample rate is based on retained samples over their device time span, not Wi-Fi arrival speed. The missed-slot delta excludes slots before the first sample. A clean timing report does not establish measurement accuracy or session completeness; inspect terminal events too.

This tool is new repository tooling, not part of the original v1.5 ZIP. It does not estimate pumping frequency, orientation or technique quality.
