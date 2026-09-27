"""Inspect one FoilScoot v1.5 CSV session; no external dependencies."""
import argparse
import csv
import json
import math
import statistics
from collections import Counter

CHANNELS = ('acc_x_g', 'acc_y_g', 'acc_z_g', 'gyro_x_dps', 'gyro_y_dps', 'gyro_z_dps')


def inspect(path):
    with open(path, newline='', encoding='utf-8-sig') as stream:
        reader = csv.DictReader(stream)
        required = {'row_type', 'session_id', 'boot_id', 'device_us', 'sequence',
                    'missed_slots_total', 'event', 'battery_v', *CHANNELS}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('Missing v1.5 CSV columns')
        rows = list(reader)
    identities = {(r['session_id'], r['boot_id']) for r in rows}
    if len(identities) > 1:
        raise ValueError('Expected one session and one boot; split the file first')
    if any(r['row_type'] not in ('data', 'event', 'battery') for r in rows):
        raise ValueError('Unknown row type')
    samples = [r for r in rows if r['row_type'] == 'data']
    if len(samples) < 2:
        raise ValueError('At least two IMU samples are required')
    times = [int(r['device_us']) for r in samples]
    seq = [int(r['sequence']) for r in samples]
    missed = [int(r['missed_slots_total']) for r in samples]
    if any(v < 0 for v in times + seq + missed):
        raise ValueError('Negative timestamp or counter')
    intervals = [b - a for a, b in zip(times, times[1:])]
    gaps = [b - a for a, b in zip(seq, seq[1:])]
    if min(intervals) <= 0 or min(gaps) <= 0 or any(b < a for a, b in zip(missed, missed[1:])):
        raise ValueError('Non-monotonic timestamps or counters')
    ranges = {}
    for name in CHANNELS:
        values = [float(r[name]) for r in samples]
        if not all(math.isfinite(v) for v in values):
            raise ValueError('Non-finite IMU value')
        ranges[name] = {'min': min(values), 'max': max(values)}
    return {
        'samples': len(samples), 'sample_span_s': (times[-1] - times[0]) / 1e6,
        'mean_received_sample_rate_hz': (len(samples) - 1) * 1e6 / (times[-1] - times[0]),
        'interval_us': {'min': min(intervals), 'median': statistics.median(intervals), 'max': max(intervals)},
        'sequence_gaps': sum(g - 1 for g in gaps),
        'missed_slots_delta_between_first_and_last_sample': missed[-1] - missed[0],
        'row_counts': dict(Counter(r['row_type'] for r in rows)),
        'events': [r['event'] for r in rows if r['row_type'] == 'event'],
        'channel_ranges': ranges,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv_path')
    args = parser.parse_args()
    try:
        print(json.dumps(inspect(args.csv_path), indent=2))
    except (OSError, ValueError, TypeError, KeyError, csv.Error) as exc:
        parser.exit(2, f'Cannot inspect CSV: {exc}\n')


if __name__ == '__main__':
    main()
