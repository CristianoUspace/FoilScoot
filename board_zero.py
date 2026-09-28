"""Pose reference only, not accelerometer bias calibration. Standard library."""
import math
import statistics


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def unit(v):
    n = math.sqrt(dot(v, v))
    if n < 1e-9:
        raise ValueError('Posa non valida')
    return [x / n for x in v]


def basis(acc):
    z = unit(acc)
    if z[2] < 0.5:
        raise ValueError('Posare il deck con IMU verso l’alto, vicino all’orizzontale')
    # Project sensor X onto the reference plane; preserve its heading.
    x = unit([1 - z[0] * z[0], -z[0] * z[1], -z[0] * z[2]])
    y = [z[1]*x[2]-z[2]*x[1], z[2]*x[0]-z[0]*x[2], z[0]*x[1]-z[1]*x[0]]
    return [x, y, z]


def transform(v, axes):
    return [dot(axis, v) for axis in axes]


def relative(v, reference):
    acc = transform(v[:3], reference['axes'])
    gyro = transform(v[3:], reference['axes'])
    pitch = math.degrees(math.atan2(acc[0], math.hypot(acc[1], acc[2])))
    roll = math.degrees(math.atan2(acc[1], acc[2]))
    return acc + gyro + [pitch, roll]


class Capture:
    def __init__(self):
        self.samples = []

    def add(self, t, v):
        if self.samples and (t <= self.samples[-1][0] or t - self.samples[-1][0] > 50000):
            raise ValueError('Dati discontinui durante lo zero: ripetere la calibrazione')
        self.samples.append((t, list(v)))
        span = (t - self.samples[0][0]) / 1e6
        if span < 2:
            return None
        if len(self.samples) < 180:
            raise ValueError('Campioni insufficienti per lo zero')
        cols = list(zip(*(v for _, v in self.samples)))
        avg = [statistics.mean(c) for c in cols]
        sd = [statistics.stdev(c) for c in cols]
        if any(s > .025 for s in sd[:3]) or any(s > .8 for s in sd[3:]):
            raise ValueError('Tavola non stabile: tenere ferma e ripetere Ricalibra IMU')
        if any(abs(x) > .8 for x in avg[3:]) or any(abs(x) > 3 for c in cols[3:] for x in c):
            raise ValueError('Rotazione durante lo zero: ripetere a tavola ferma')
        if any(max(c)-min(c) > .12 for c in cols[:3]):
            raise ValueError('Urto durante lo zero: ripetere a tavola ferma')
        n = max(1, len(self.samples) // 4)
        drift = [statistics.mean(c[-n:])-statistics.mean(c[:n]) for c in cols[:3]]
        if math.sqrt(dot(drift, drift)) > .012:
            raise ValueError('La posa sta cambiando: tenere ferma la tavola e ripetere')
        norm = math.sqrt(dot(avg[:3], avg[:3]))
        if not .75 <= norm <= 1.25:
            raise ValueError('Accelerazione non plausibile per una tavola ferma')
        return dict(axes=basis(avg[:3]), mean_acc_g=avg[:3], mean_gyro_dps=avg[3:],
                    std=sd, norm_g=norm, samples=len(self.samples),
                    first_device_us=self.samples[0][0], last_device_us=t,
                    method='reference_frame_v1_project_sensor_x',
                    note='Zero di posa; gravita conservata; angoli accelerometrici apparenti')
