import os
import sys
import numpy as np
import soundfile as sf

sys.path.insert(0, '/home/devuser/lemo-opuscar')
from core.audio.sfx import SR, bp, lp, thump, clack, click, whoosh
from core.audio import sampler as S

D = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(D, 'assets', 'audio')
DUR = 42.0
N = int(DUR * SR)

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


S.seed(1991)
score_events = [
    (0.0, 'cellos', 'D2', 13.0, 0.45, -0.1),
    (5.0, 'cellos_pizz', 'D3', 0.4, 0.55, 0.2),
    (6.6, 'cellos_pizz', 'F3', 0.4, 0.55, -0.2),
    (8.2, 'cellos_pizz', 'E3', 0.4, 0.60, 0.15),
    (10.0, 'timpani', 'D2', 2.8, 0.65, 0.0),
    (13.5, 'vibraphone_bowed', 'A4', 5.0, 0.30, 0.2),
    (18.2, 'cellos', 'D2', 12.0, 0.48, -0.1),
    (25.3, 'vibraphone_bowed', 'Bb4', 4.5, 0.32, -0.25),
    (30.6, 'cellos', 'D2', 11.0, 0.55, 0.0),
    (37.2, 'timpani', 'D2', 4.0, 0.72, 0.0),
]
mus = S.render(score_events, DUR)
if len(mus) < N:
    mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
else:
    mus = mus[:N]

for t_slam in [5.0, 5.8, 6.6, 7.4, 8.2, 14.2, 37.2]:
    put(fol, norm(thump(0.22), 0.7), t_slam, 0.72, 0.0)
    put(fol, norm(clack(), 0.7), t_slam, 0.45, 0.1)

for t_w in [9.8, 13.4, 18.0, 30.4]:
    put(fol, norm(whoosh(0.35), 0.55), t_w, 0.55, -0.15)

for t_c in [25.2, 27.2, 33.0, 34.8]:
    put(fol, norm(click(), 0.6), t_c, 0.50, 0.1)

VO_CUES = [
    ('vo1', 0.5),
    ('vo2', 5.0),
    ('vo3', 13.5),
    ('vo4', 18.2),
    ('vo5', 25.3),
    ('vo6', 30.6),
]
vo_win = []
for vid, vt in VO_CUES:
    x, sr = sf.read(os.path.join(AUDIO_DIR, f'{vid}.wav'))
    if x.ndim > 1:
        x = x.mean(1)
    x = norm(x, 0.85)
    put(vox, x, vt, 1.0, 0.0)
    vo_win.append((vt, vt + len(x) / SR))

tt = np.arange(N) / SR
duck = np.ones(N)
for a, b in vo_win:
    w_ = np.clip(np.minimum((tt - (a - 0.2)) / 0.2, ((b + 0.3) - tt) / 0.3), 0.0, 1.0)
    duck = np.minimum(duck, 1.0 - 0.72 * w_)

mix = mus * 0.45 * duck[:, None] + fol * 0.75 + vox * 1.25
end_fade = int(1.2 * SR)
mix[-end_fade:] *= np.linspace(1.0, 0.0, end_fade)[:, None]

pk = float(np.abs(mix).max())
if pk > 0:
    mix = mix / pk * 0.89

out_wav = os.path.join(AUDIO_DIR, 'mix.wav')
sf.write(out_wav, mix.astype(np.float32), SR)
print(f"Wrote {out_wav} shape={mix.shape} peak={pk:.4f} vo={vo_win}")
