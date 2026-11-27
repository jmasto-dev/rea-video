import os
import sys
import numpy as np
import soundfile as sf

sys.path.insert(0, '/home/devuser/lemo-opuscar')
from core.audio.sfx import SR, bp, lp, thump, clack, click, whoosh, pop, ding

D = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(D, 'assets', 'audio')
DUR = 42.0
N = int(DUR * SR)

rng = np.random.default_rng(2026)
fol = np.zeros((N, 2), dtype=np.float64)
vox = np.zeros((N, 2), dtype=np.float64)
pulse = np.zeros((N, 2), dtype=np.float64)


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


put(fol, norm(click(), 0.7), 0.02, 0.75, 0.0)
put(fol, norm(pop(0.08), 0.7), 1.20, 0.70, -0.15)
put(fol, norm(pop(0.08), 0.75), 2.50, 0.75, 0.15)

for k in range(5):
    t_c = 3.5 + k * 0.30
    f_step = 750 + k * 140
    tt = np.arange(int(0.05 * SR)) / SR
    toc = np.sin(2 * np.pi * f_step * tt) * np.exp(-tt / 0.012)
    put(fol, norm(toc, 0.65), t_c, 0.65, -0.3 + k * 0.15)

n_riser = int(1.2 * SR)
t_r = np.arange(n_riser) / SR
riser = bp(rng.standard_normal(n_riser), 300, 3200) * (t_r / 1.2) ** 2.2
put(fol, norm(riser, 0.55), 6.0, 0.60, 0.0)
put(fol, norm(thump(0.35), 0.95), 8.3, 0.95, 0.0)
put(fol, norm(clack(), 0.7), 8.3, 0.55, 0.0)

put(fol, norm(click(), 0.7), 11.8, 0.65, 0.0)
put(fol, norm(click(), 0.7), 12.7, 0.75, 0.0)
for idx, t_p in enumerate([14.1, 14.7, 15.3]):
    put(fol, norm(ding(1400 + idx * 120), 0.5), t_p, 0.45, -0.25 + idx * 0.25)

beat = 60.0 / 115.0
t_cur = 16.0
while t_cur < 33.9:
    sub_thump = thump(0.14) if t_cur < 24.0 else lp(thump(0.22), 160)
    put(pulse, norm(sub_thump, 0.45), t_cur, 0.35 if t_cur < 24.0 else 0.45, 0.0)
    t_cur += beat

put(fol, norm(whoosh(0.28), 0.7), 16.0, 0.75, 0.25)
put(fol, norm(thump(0.22), 0.8), 18.8, 0.75, -0.2)
put(fol, norm(thump(0.22), 0.8), 21.4, 0.75, 0.2)

n_mk = int(0.42 * SR)
t_mk = np.arange(n_mk) / SR
marker = bp(rng.standard_normal(n_mk), 1200, 4200) * np.sin(np.pi * t_mk / 0.42)
put(fol, norm(marker, 0.55), 26.5, 0.65, 0.0)

for k in range(5):
    t_f = 30.2 + k * 0.70
    put(fol, norm(clack(), 0.65), t_f, 0.60, 0.3 - k * 0.15)

n_rw = int(1.6 * SR)
t_rw = np.arange(n_rw) / SR
rewind = bp(rng.standard_normal(n_rw), 800, 5200) * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 12 * t_rw)))
put(fol, norm(rewind, 0.55), 39.2, 0.60, 0.0)
put(fol, norm(thump(0.28), 0.9), 40.9, 0.90, 0.0)
put(fol, norm(clack(), 0.75), 40.9, 0.65, 0.0)

VO_CUES = [
    ('v1', 0.15),
    ('v2', 6.35),
    ('v3', 11.2),
    ('v4', 16.0),
    ('v5', 24.0),
    ('v6', 30.0),
    ('v7', 39.0),
]
vo_win = []
for vid, vt in VO_CUES:
    x, sr = sf.read(os.path.join(AUDIO_DIR, f'{vid}.wav'))
    if x.ndim > 1:
        x = x.mean(1)
    x = norm(x, 0.88)
    put(vox, x, vt, 1.0, 0.0)
    vo_win.append((vt, vt + len(x) / SR))

mix = pulse * 0.75 + fol * 0.85 + vox * 1.25

for a, b in [(34.1, 35.4), (41.7, 42.0)]:
    ia, ib = int(a * SR), int(b * SR)
    mix[ia:ib] = 0.0

pk = float(np.abs(mix).max())
if pk > 0:
    mix = mix / pk * 0.90

out_wav = os.path.join(AUDIO_DIR, 'mix.wav')
sf.write(out_wav, mix.astype(np.float32), SR)
print(f"Wrote {out_wav} shape={mix.shape} peak={pk:.4f} vo={vo_win}")
