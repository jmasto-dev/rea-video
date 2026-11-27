import os
import sys
import numpy as np
import soundfile as sf
from scipy.signal import fftconvolve

sys.path.insert(0, '/home/devuser/lemo-opuscar')
from core.audio.sfx import SR, bp, lp, hp, click, ding

D = os.path.dirname(os.path.abspath(__file__))
VO_DIR = os.path.join(D, 'voices')
DUR = 48.0
N = int(DUR * SR)

rng = np.random.default_rng(2026)
amb = np.zeros((N, 2), dtype=np.float64)
fol = np.zeros((N, 2), dtype=np.float64)
vox = np.zeros((N, 2), dtype=np.float64)


def put(buf, s, t_sec, gain=1.0, pan=0.0):
    s = np.asarray(s, dtype=np.float64)
    if s.ndim == 1:
        gl = gain * np.cos((pan + 1.0) * np.pi / 4.0)
        gr = gain * np.sin((pan + 1.0) * np.pi / 4.0)
        st = np.column_stack([s * gl, s * gr])
    else:
        st = s * gain
    i = int(round(t_sec * SR))
    if i >= N or i + len(st) <= 0:
        return
    src_a = max(0, -i)
    dst_a = max(0, i)
    length = min(len(st) - src_a, N - dst_a)
    if length > 0:
        buf[dst_a:dst_a + length] += st[src_a:src_a + length]


def norm(x, p=1.0):
    m = np.abs(x).max()
    return x * p / m if m > 0 else x


def sub_drone(d, f0=38.0):
    t = np.arange(int(d * SR)) / SR
    y = 0.7 * np.sin(2 * np.pi * f0 * t) + 0.3 * np.sin(2 * np.pi * (f0 * 1.5) * t)
    y *= np.minimum(1.0, t / 0.8) * np.minimum(1.0, (d - t) / 0.6)
    return norm(y, 0.55)


# 1. Opening 0.4s PURE SILENCE, then quiet computer hum (0.4 - 7.5s) + accelerating clicks (3.5 - 7.5s)
hum = lp(rng.standard_normal(int(7.1 * SR)), 140) * 0.14
hum *= np.minimum(1.0, np.arange(len(hum)) / (0.5 * SR))
put(amb, hum, 0.4, 0.55, 0.0)

t_c = 3.5
dt = 0.28
while t_c < 7.45:
    put(fol, norm(click(), 0.45), t_c, 0.42, 0.0)
    t_c += dt
    dt = max(0.08, dt * 0.90)

# 2. Sub-45Hz Sicario/Chernobyl drone under Data Center (7.5 - 13.5s)
put(amb, sub_drone(6.0, 39.0), 7.5, 0.58, 0.0)

# 3. L-cut room tone + distant city (13.5 - 19.0s) + dry fingernail double-tap (17.0, 17.7s)
room = lp(rng.standard_normal(int(5.5 * SR)), 180) * 0.09
put(amb, room, 13.5, 0.45, 0.0)
put(fol, norm(click(), 0.6), 17.0, 0.58, 0.1)
put(fol, norm(click(), 0.6), 17.7, 0.58, 0.1)

# 4. Paper rack-focus air/rustle (19.0 - 27.0s)
for t_p in [22.2, 23.0]:
    n_p = int(0.35 * SR)
    rustle = bp(rng.standard_normal(n_p), 900, 3400) * np.sin(np.pi * np.arange(n_p) / n_p)
    put(fol, norm(rustle, 0.35), t_p, 0.35, -0.1)

# 5. Terminal: 3 polite electronic validation beeps (28.6, 30.2, 31.8s) + oppressive sub (27.0 - 34.0s)
put(amb, sub_drone(7.0, 36.0), 27.0, 0.62, 0.0)
for t_b in [28.6, 30.2, 31.8]:
    put(fol, norm(ding(1320), 0.4), t_b, 0.32, 0.0)

# 6. Nocturnal office air (34.0 - 44.1s) -> crisp daylight mouse click (44.1s) -> 0.4s SILENCE -> pure low note (44.5 - 48.0s)
office_air = lp(rng.standard_normal(int(10.1 * SR)), 220) * 0.10
put(amb, office_air, 34.0, 0.45, 0.0)
put(fol, norm(click(), 0.75), 44.1, 0.72, 0.0)
put(amb, sub_drone(3.5, 41.2), 44.5, 0.68, 0.0)

# 7. Calm LEMMiNO-style voiceover
VO_CUES = [
    ('c1', 0.4),
    ('c2', 7.8),
    ('c3', 13.8),
    ('c4', 19.3),
    ('c5', 27.5),
    ('c6', 34.2),
    ('c7', 39.5),
]
for vid, vt in VO_CUES:
    x, sr = sf.read(os.path.join(VO_DIR, f'{vid}.wav'))
    if x.ndim > 1:
        x = x.mean(1)
    put(vox, norm(x, 0.85), vt, 1.0, 0.0)

mix = amb * 0.85 + fol * 0.85 + vox * 1.25

# Hard digital silences: 0.0-0.4s opening + 44.14-44.50s before JUNE.
mix[:int(0.4 * SR)] = 0.0
mix[int(44.14 * SR):int(44.50 * SR)] = 0.0

end_fade = int(1.0 * SR)
mix[-end_fade:] *= np.linspace(1.0, 0.0, end_fade)[:, None]

pk = float(np.abs(mix).max())
if pk > 0:
    mix = mix / pk * 0.89

out_wav = os.path.join(D, 'mix.wav')
sf.write(out_wav, mix.astype(np.float32), SR)
print(f"Wrote {out_wav} shape={mix.shape} peak={pk:.4f}")
