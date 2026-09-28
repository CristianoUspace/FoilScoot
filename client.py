"""FoilScoot recorder. Python 3.10+, standard library only; all assets offline."""
import argparse
import csv
import datetime as dt
import json
import logging
import math
import os
from pathlib import Path
import queue
import secrets
import socket
import threading
import time
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import webbrowser
from board_zero import Capture, relative

ROOT = Path(__file__).resolve().parent
LOG = logging.getLogger('FoilScoot')
BATTERY_LOW_V = 7.2
BATTERY_CRITICAL_V = 7.0
BATTERY_HYSTERESIS_V = 0.1
FIELDS = ['row_type', 'session_id', 'boot_id', 'device_us', 'session_s',
          'received_utc', 'received_local', 'received_monotonic_ns', 'sequence',
          'missed_slots_total', 'acc_x_g', 'acc_y_g', 'acc_z_g',
          'gyro_x_dps', 'gyro_y_dps', 'gyro_z_dps', 'event', 'led', 'battery_v', 'battery_state']
REL_FIELDS = ['acc_ref_x_g', 'acc_ref_y_g', 'acc_ref_z_g',
              'gyro_ref_x_dps', 'gyro_ref_y_dps', 'gyro_ref_z_dps',
              'pitch_ref_deg', 'roll_ref_deg']
FIELDS += REL_FIELDS + ['zero_id', 'zero_reference_json', 'client_version']


class Recorder:
    def __init__(self, host='192.168.4.1', port=8765, output=None):
        self.host, self.port = host, port
        self.output = Path(output or ROOT / 'registrazioni')
        self.output.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.commands = queue.Queue(maxsize=10)
        self.quit = threading.Event()
        self.points = deque(maxlen=1000)
        self.log = deque(maxlen=12)
        self.sock = None
        self.file = self.writer = None
        self.session = self.boot = ''
        self.origin = None
        self.closing = False
        self.pending = ''
        self.deadline = 0
        self.last_flush = 0
        self.last_seq = None
        self.rx_samples = 0
        self.report_samples = 0
        self.report_time = time.monotonic()
        self.last_data_time = None
        self.battery_time = None
        self.battery_level = 'unknown'
        self.last_status = None
        self.reference = None
        self.capture = None
        self.state = dict(connected=False, ready=False, recording=False,
                          pending='', message='In attesa della rete FoilScoot-IMU',
                          file='', samples=0, gaps=0, missed=0, duration=0,
                          output=str(self.output), boot='', battery_v=None, battery_state='unknown')
        self.state.update(version='1.6', zero_status='missing', zero_progress=0,
                          zero_message='Ricalibra IMU per acquisire lo zero della tavola',
                          zero_id='', reference=None, angles=None)

    def clear_zero(self, message):
        self.reference = self.capture = None
        self.points.clear()
        self.state.update(zero_status='missing', zero_progress=0, zero_id='',
                          reference=None, angles=None, zero_message=message)

    def zero_sample(self, m):
        if self.capture is None:
            return
        try:
            ref = self.capture.add(m['t_us'], m['v'])
            self.state['zero_progress'] = min(100, int(
                (m['t_us'] - self.capture.samples[0][0]) / 20000))
            if ref is not None:
                ref.update(zero_id=secrets.token_hex(8), boot_id=self.boot,
                           acquired_utc=dt.datetime.now(dt.timezone.utc).isoformat())
                self.reference = ref
                self.capture = None
                self.pending = ''
                self.points.clear()
                self.state.update(zero_status='ready', zero_progress=100,
                                  zero_id=ref['zero_id'], reference=ref,
                                  zero_message='Zero acquisito: riferimento valido per questa connessione')
                LOG.info('BOARD_ZERO_SET: %s', ref['zero_id'])
                self.note('Zero della tavola acquisito; puoi avviare la registrazione')
        except ValueError as exc:
            self.clear_zero(str(exc))
            self.state['zero_status'] = 'failed'
            self.pending = ''
            self.note(str(exc))

    def note(self, message):
        LOG.info('%s', message)
        self.state['message'] = message
        self.log.append(dt.datetime.now().strftime('%H:%M:%S') + '  ' + message)

    def snapshot(self):
        with self.lock:
            battery = {}
            if self.battery_time is None or time.monotonic() - self.battery_time > 4 or not self.state['connected']:
                battery = dict(battery_v=None, battery_state='unknown')
            return {**self.state, **battery, 'pending': self.pending,
                    'points': list(self.points), 'log': list(self.log)}

    def request(self, action):
        if action not in ('start', 'stop', 'mark', 'calibrate'):
            raise ValueError('Comando non valido')
        with self.lock:
            if self.closing:
                raise ValueError('Chiusura in corso')
            if not self.state['connected']:
                raise ValueError('Client non collegato alla scheda')
            if self.pending:
                raise ValueError('Attendere la conferma del comando precedente')
            if action == 'start' and (not self.state['ready'] or self.file):
                raise ValueError('IMU non pronta o sessione gia aperta')
            if action == 'start' and self.reference is None:
                raise ValueError('Acquisire prima lo zero con Ricalibra IMU')
            if action in ('stop', 'mark') and not self.state['recording']:
                raise ValueError('Nessuna registrazione attiva')
            if action == 'calibrate' and self.file:
                raise ValueError('Terminare prima la registrazione')
            self.pending = action
            self.deadline = time.monotonic() + 15
            self.commands.put_nowait(action)
            if action == 'calibrate':
                self.clear_zero('Calibrazione gyro; poi tenere la tavola ferma per 2 secondi')
                self.state['zero_status'] = 'calibrating'
            LOG.info('COMANDO accettato dalla pagina: %s', action)

    def send(self, line):
        self.sock.sendall((line + '\n').encode('ascii'))
        if line == 'PING':
            LOG.debug('TX ESP: PING')
        else:
            LOG.info('TX ESP: %s', line)

    def open_session(self):
        self.session = dt.datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '_' + secrets.token_hex(3)
        path = self.output / ('FoilScoot_' + self.session + '.csv')
        self.file = path.open('x', newline='', encoding='utf-8')
        self.writer = csv.DictWriter(self.file, fieldnames=FIELDS)
        self.writer.writeheader()
        self.file.flush()
        LOG.info('CSV aperto: %s', path.resolve())
        self.origin = None
        self.state.update(file=path.name, samples=0, gaps=0, missed=0, duration=0)
        self.note('Richiesta avvio: ' + path.name)

    def row(self, message, stamp=None, mono=None):
        if not self.writer:
            return
        stamp = stamp or dt.datetime.now(dt.timezone.utc)
        t = message.get('t_us', '')
        elapsed = (t - self.origin) / 1e6 if t != '' and self.origin is not None else ''
        row = dict(row_type=message['type'], session_id=self.session, boot_id=self.boot,
                   device_us=t, session_s=elapsed, received_utc=stamp.isoformat(timespec='microseconds'),
                   received_local=stamp.astimezone().isoformat(timespec='microseconds'),
                   received_monotonic_ns=mono if mono is not None else time.monotonic_ns(),
                   sequence=message.get('seq', ''), missed_slots_total=message.get('missed', ''),
                   event=message.get('name', ''), led=message.get('led', ''))
        row['client_version'] = '1.6'
        if self.reference:
            row['zero_id'] = self.reference['zero_id']
        if message.get('name') == 'BOARD_ZERO_REFERENCE':
            row['zero_reference_json'] = json.dumps(self.reference, ensure_ascii=False)
        if message['type'] == 'data':
            row.update(zip(FIELDS[10:16], message['v']))
            if self.reference:
                row.update(zip(REL_FIELDS, relative(message['v'], self.reference)))
        if message['type'] == 'battery':
            row.update(battery_v=message.get('volts', '') if message.get('valid') else '',
                       battery_state=self.state['battery_state'])
        self.writer.writerow(row)
        if message['type'] != 'data' or time.monotonic() - self.last_flush >= 1:
            self.file.flush()
            self.last_flush = time.monotonic()

    def close_session(self, reason):
        if self.file:
            try:
                self.row({'type': 'event', 'name': reason})
                self.file.flush()
                os.fsync(self.file.fileno())
                LOG.info('CSV salvato: %s | campioni=%d | durata=%.2fs | esito=%s',
                         self.file.name, self.state['samples'], self.state['duration'], reason)
            finally:
                self.file.close()
                self.file = self.writer = None
        self.state['recording'] = False
        self.origin = None
        self.session = ''
        self.note(reason)

    def process(self, m, stamp=None, mono=None):
        kind = m.get('type')
        if kind == 'status':
            if m.get('protocol') != 1 or not isinstance(m.get('boot'), str):
                raise ValueError('Protocollo firmware non compatibile')
            if self.boot and m['boot'] != self.boot and self.file:
                self.close_session('INTERRUPTED_BOARD_REBOOT')
            if self.boot and m['boot'] != self.boot:
                self.clear_zero('Scheda riavviata: acquisire nuovamente lo zero')
                self.last_seq = None
                self.pending = ''
            self.boot = m['boot']
            status_key = (self.boot, bool(m['ready']), bool(m.get('recording')), m['error'])
            if status_key != self.last_status:
                LOG.info('STATO ESP: boot=%s | IMU pronta=%s | registrazione=%s | errore=%s',
                         *status_key[:-1], status_key[-1] or 'nessuno')
                self.last_status = status_key
            first = not self.state['connected']
            self.state.update(connected=True, ready=bool(m['ready']), boot=self.boot)
            if first:
                self.note('Client collegato; IMU pronta' if m['ready'] else 'IMU non pronta: ' + m['error'])
            if not m['ready']:
                self.clear_zero('IMU non pronta: ripetere Ricalibra IMU')
                self.state['message'] = 'IMU: ' + m['error']
                if self.file:
                    self.close_session('INTERRUPTED_IMU_ERROR')
                    self.pending = ''
        elif kind == 'battery':
            old_level = self.battery_level
            self.battery_time = time.monotonic()
            voltage = m.get('volts')
            level = 'disabled'
            if m.get('enabled'):
                if not m.get('valid') or type(voltage) not in (int, float) or not math.isfinite(voltage) or not 4.0 <= voltage <= 8.6:
                    level, voltage = 'invalid', None
                elif voltage <= BATTERY_CRITICAL_V or (old_level == 'critical' and voltage < BATTERY_CRITICAL_V + BATTERY_HYSTERESIS_V):
                    level = 'critical'
                elif voltage <= BATTERY_LOW_V or (old_level in ('low', 'critical') and voltage < BATTERY_LOW_V + BATTERY_HYSTERESIS_V):
                    level = 'low'
                else:
                    level = 'ok'
            else:
                voltage = None
            self.battery_level = level
            self.state.update(battery_v=voltage, battery_state=level)
            if level != old_level:
                log = LOG.warning if level in ('low', 'critical', 'invalid') else LOG.info
                log('BATTERIA: %s | tensione=%s V', level, voltage if voltage is not None else 'n/d')
            if self.file and self.state['recording'] and m.get('session') == self.session:
                self.row({**m, 'valid': voltage is not None, 'volts': voltage}, stamp, mono)
        elif kind == 'data':
            v = m['v']
            if len(v) != 6 or not all(isinstance(x, (int, float)) and math.isfinite(x) for x in v):
                raise ValueError('Campione IMU non valido')
            for field in ('seq', 't_us', 'missed'):
                if type(m[field]) is not int or m[field] < 0:
                    raise ValueError('Timestamp o contatore non valido')
            if self.last_seq is not None and m['seq'] <= self.last_seq:
                raise ValueError('Sequenza IMU non crescente')
            gap = max(0, m['seq'] - self.last_seq - 1) if self.last_seq is not None else 0
            self.last_seq = m['seq']
            self.rx_samples += 1
            self.last_data_time = time.monotonic()
            if self.rx_samples == 1:
                LOG.info('Primo campione IMU ricevuto: seq=%d', m['seq'])
            self.zero_sample(m)
            if self.reference:
                rv = relative(v, self.reference)
                self.state['angles'] = rv[-2:]
                self.points.append([m['t_us'] / 1e6, *rv])
            if self.file and self.state['recording'] and m.get('session') == self.session:
                self.row(m, stamp, mono)
                self.state['samples'] += 1
                self.state['gaps'] += gap
                self.state['missed'] = m['missed']
                self.state['duration'] = (m['t_us'] - self.origin) / 1e6
        elif kind == 'event':
            LOG.info('EVENTO ESP: %s | device_us=%s | LED=%s',
                     m.get('name'), m.get('t_us', '-'), m.get('led', '-'))
            if m['name'] == 'CALIBRATION_DONE':
                if self.pending == 'calibrate':
                    if self.state['ready']:
                        self.capture = Capture()
                        self.pending = 'zero'
                        self.deadline = time.monotonic() + 6
                        self.state.update(zero_status='capturing', zero_progress=0,
                                          zero_message='Tenere ferma la tavola: acquisizione zero per 2 secondi')
                        self.note('Giroscopio calibrato; acquisizione zero tavola')
                    else:
                        self.pending = ''
                        self.clear_zero('Calibrazione fallita: ripetere Ricalibra IMU')
                return
            if not self.file or m.get('session') != self.session:
                return
            name = m['name']
            if name == 'START':
                self.origin = m['t_us']
                self.state['recording'] = True
                self.note('Registrazione attiva; sincronizzazione LED iniziale')
                # Attendere il termine del pattern prima di accettare STOP o MARK.
                self.deadline = time.monotonic() + 15
            self.row(m, stamp, mono)
            if name == 'START':
                self.row({'type': 'event', 'name': 'BOARD_ZERO_REFERENCE'}, stamp, mono)
            if name in ('START_SYNC_DONE', 'MARK_SYNC_DONE'):
                self.pending = ''
            elif name == 'MARK':
                self.note('Marcatore video inviato')
            elif name == 'STOP':
                self.close_session('COMPLETED')
                self.pending = ''
            elif name == 'IMU_ERROR':
                self.close_session('INTERRUPTED_IMU_ERROR')
                self.pending = ''
        elif kind == 'error':
            if self.pending in ('calibrate', 'zero'):
                self.clear_zero('Calibrazione rifiutata: ' + m['error'])
            self.note('Scheda: ' + m['error'])
            if self.pending == 'start' and not self.state['recording']:
                self.close_session('START_REJECTED')
            self.pending = ''
        else:
            raise ValueError('Messaggio di rete non valido')

    def report(self):
        now = time.monotonic()
        elapsed = now - self.report_time
        if elapsed < 5:
            return
        rate = (self.rx_samples - self.report_samples) / elapsed
        age = 'mai' if self.last_data_time is None else f'{now - self.last_data_time:.1f}s fa'
        LOG.info('VIVO | %s | ricezione=%.1f campioni/s | ultimo dato=%s | CSV=%d campioni | durata=%.1fs | salti=%d | slot saltati=%d',
                 'REGISTRAZIONE' if self.state['recording'] else 'ANTEPRIMA',
                 rate, age, self.state['samples'], self.state['duration'],
                 self.state['gaps'], self.state['missed'])
        self.report_time, self.report_samples = now, self.rx_samples

    def run(self):
        while not self.quit.is_set():
            try:
                LOG.info('Connessione ESP: %s:%d ...', self.host, self.port)
                self.sock = socket.create_connection((self.host, self.port), timeout=2)
                LOG.info('TCP collegato; attendo conferma ESP')
                self.sock.settimeout(0.15)
                self.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                self.send('HELLO')
                buf = b''
                last_receive = last_ping = time.monotonic()
                with self.lock:
                    self.last_seq = None
                    self.last_status = None
                    self.battery_time = None
                    self.battery_level = 'unknown'
                    self.rx_samples = self.report_samples = 0
                    self.report_time = time.monotonic()
                    self.last_data_time = None
                    self.points.clear()
                while not self.quit.is_set():
                    with self.lock:
                        try:
                            action = self.commands.get_nowait()
                        except queue.Empty:
                            action = None
                        if action == 'start':
                            self.open_session()
                            self.send('START ' + self.session)
                        elif action:
                            self.send({'stop': 'STOP', 'mark': 'MARK', 'calibrate': 'CAL'}[action])
                        if self.pending and time.monotonic() > self.deadline:
                            raise TimeoutError('Conferma comando non ricevuta')
                    if time.monotonic() - last_ping > 2:
                        self.send('PING')
                        last_ping = time.monotonic()
                    try:
                        chunk = self.sock.recv(16384)
                    except socket.timeout:
                        chunk = None
                    if chunk == b'':
                        raise ConnectionError('Collegamento chiuso dalla scheda')
                    if chunk:
                        last_receive = time.monotonic()
                        buf += chunk
                        if len(buf) > 65536:
                            raise ValueError('Messaggio troppo lungo')
                        while b'\n' in buf:
                            line, buf = buf.split(b'\n', 1)
                            stamp, mono = dt.datetime.now(dt.timezone.utc), time.monotonic_ns()
                            with self.lock:
                                self.process(json.loads(line), stamp, mono)
                    with self.lock:
                        self.report()
                    timeout = 15 if self.pending == 'calibrate' else 6
                    if time.monotonic() - last_receive > timeout:
                        raise TimeoutError(f'Nessun messaggio dalla scheda da {timeout} secondi')
            except (OSError, ValueError, KeyError, TypeError) as exc:
                LOG.warning('Errore collegamento/file: %s; nuovo tentativo tra 2s', exc)
                LOG.debug('Dettaglio errore', exc_info=True)
                with self.lock:
                    try:
                        if self.file:
                            self.close_session('INTERRUPTED_CONNECTION_OR_IO')
                    except OSError:
                        LOG.exception('Errore durante la chiusura del CSV')
                    self.note('Collegamento o file: ' + str(exc))
            finally:
                with self.lock:
                    self.state.update(connected=False, ready=False, recording=False)
                    self.clear_zero('Collegamento interrotto: acquisire nuovamente lo zero')
                    self.pending = ''
                    while not self.commands.empty():
                        self.commands.get_nowait()
                if self.sock:
                    self.sock.close()
                    self.sock = None
            self.quit.wait(2)
        with self.lock:
            self.close_session('INTERRUPTED_CLIENT_CLOSED')


def make_handler(recorder, web_port, token):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, code, content, mime='application/json; charset=utf-8'):
            data = content.encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path == '/':
                LOG.info('Pagina web aperta/ricaricata')
                page = (ROOT / 'index.html').read_text(encoding='utf-8').replace('__TOKEN__', token)
                self.reply(200, page, 'text/html; charset=utf-8')
            elif self.path == '/api/state':
                self.reply(200, json.dumps(recorder.snapshot()))
            else:
                self.reply(404, '{}')

        def do_POST(self):
            if self.headers.get('X-FoilScoot-Token') != token:
                LOG.warning('Comando web rifiutato: token mancante o non valido; ricaricare la pagina')
                self.reply(403, json.dumps({'error': 'Richiesta non autorizzata'}))
                return
            if self.path == '/api/shutdown':
                with recorder.lock:
                    if recorder.file or recorder.pending:
                        self.reply(409, json.dumps({'error': 'Attendere la fine della registrazione o del comando in corso'}))
                        return
                    recorder.closing = True
                LOG.info('Chiusura richiesta dal pulsante web')
                self.reply(200, '{"ok":true}')
                recorder.quit.set()
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            if not self.path.startswith('/api/'):
                self.reply(404, '{}')
                return
            try:
                recorder.request(self.path[5:])
                self.reply(202, '{"ok":true}')
            except (ValueError, queue.Full) as exc:
                LOG.warning('Comando web %s rifiutato: %s', self.path, exc)
                self.reply(409, json.dumps({'error': str(exc)}))
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', default='192.168.4.1')
    parser.add_argument('--port', type=int, default=8765)
    parser.add_argument('--web-port', type=int, default=8080)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--no-browser', action='store_true')
    parser.add_argument('--debug', action='store_true', help='Mostra anche PING e dettagli degli errori')
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO,
                        format='%(asctime)s [%(levelname)s] %(message)s', datefmt='%H:%M:%S')
    LOG.info('FoilScoot client v1.6 - zero tavola e console diagnostica attivi')
    rec = Recorder(args.host, args.port, args.output)
    http = ThreadingHTTPServer(('127.0.0.1', args.web_port),
                               make_handler(rec, args.web_port, secrets.token_urlsafe(32)))
    worker = threading.Thread(target=rec.run, daemon=True)
    worker.start()
    url = f'http://127.0.0.1:{args.web_port}'
    print(f'FoilScoot: {url}\nCSV: {rec.output}\nCtrl+C per chiudere. Usare Stop nella pagina per completare la sessione.')
    if not args.no_browser:
        webbrowser.open(url)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        LOG.info('Chiusura richiesta dalla console')
    finally:
        rec.quit.set()
        worker.join(timeout=5)
        http.server_close()
        LOG.info('Client terminato')


if __name__ == '__main__':
    main()
