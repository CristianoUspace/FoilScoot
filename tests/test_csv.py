import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


analysis = load('analysis_tool', ROOT / 'analysis/inspect_csv.py')
client = load('recorder', ROOT / 'desktop/client.py')


class CSVTests(unittest.TestCase):
    def test_synthetic_timing_and_schema(self):
        path = ROOT / 'data/examples/synthetic.csv'
        with path.open(newline='', encoding='utf-8') as stream:
            self.assertEqual(next(csv.reader(stream)), client.FIELDS)
        report = analysis.inspect(path)
        self.assertEqual(report['samples'], 3)
        self.assertEqual(report['mean_received_sample_rate_hz'], 100)
        self.assertEqual(report['sequence_gaps'], 0)

    def test_rejects_clock_reset(self):
        with (ROOT / 'data/examples/synthetic.csv').open(newline='', encoding='utf-8') as stream:
            rows = list(csv.DictReader(stream))
        samples = [r for r in rows if r['row_type'] == 'data']
        samples[-1]['device_us'] = samples[0]['device_us']
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'bad.csv'
            with path.open('w', newline='', encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=client.FIELDS)
                writer.writeheader()
                writer.writerows(rows)
            with self.assertRaises(ValueError):
                analysis.inspect(path)

    def test_recorder_session_and_battery(self):
        with tempfile.TemporaryDirectory() as tmp:
            rec = client.Recorder(output=tmp)
            rec.process(dict(type='status', protocol=1, boot='test', ready=True, error=''))
            rec.open_session()
            session = rec.session
            rec.process(dict(type='event', name='START', session=session, t_us=1000, led=0))
            rec.process(dict(type='data', session=session, seq=1, t_us=11000, missed=0, v=[0, 0, 1, 0, 0, 0]))
            rec.process(dict(type='battery', session=session, enabled=True, valid=True, volts=7.1, t_us=12000))
            rec.process(dict(type='event', name='STOP', session=session, t_us=21000, led=0))
            with next(Path(tmp).glob('*.csv')).open(newline='', encoding='utf-8') as stream:
                rows = list(csv.DictReader(stream))
            battery = next(r for r in rows if r['row_type'] == 'battery')
            self.assertEqual(battery['battery_state'], 'low')
            self.assertEqual(rows[-1]['event'], 'COMPLETED')
            self.assertEqual(rows[-1]['device_us'], '')


if __name__ == '__main__':
    unittest.main()
