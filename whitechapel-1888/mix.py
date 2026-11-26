"""Whitechapel, 1888 — foley (wood gouge, cobble footsteps, paper peel, block thump),
dark Victorian score (cellos, cellos_pizz, timpani, vibraphone_bowed),
US English narration (en-US-AndrewNeural), ducking, and 28.0-30.0s digital silence -> mix.wav
"""
import os
import sys
import json
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly, fftconvolve

D = os.path.dirname(os.path.abspath(__file__))
ROOT = '/home/devuser/lemo-opuscar'
sys.path.insert(0, ROOT)

from core.audio.sfx import SR, bp, lp, hp
from core.audio import sampler as S

rng = np.random.default_rng(1888)
ev_data = json.load(open(os.path.join(D, 'events.json')))
EV = ev_data['ev']
DUR = float(ev_data.get('dur', 45.0))
N = int(DUR * SR)

amb = np.zeros((N, 2), dtype=np.float64)
fol = np.zeros((N, 2), dtype=np.float64)
vox = np.zeros((N, 2), dtype=np.float64)


def t_(d):
    return np.arange(int(d * SR)) / SR


def nz(d):
    return rng.standard_normal(int(d * SR))


def env(d, a=0.005, tau=0.1):
    t = t_(d)
    return np.minimum(1.0, t / max(a, 1e-4)) * np.exp(-t / tau)


def norm(x, p=1.0):
    m = np.abs(x).max()
    return x * p / m if m > 0 else x


def modal(parts, d, click=0.0):
    t = t_(d)
    y = np.zeros_like(t)
    for f, a, tau in parts:
        y += a * np.sin(2 * np.pi * f * t + rng.random() * 6.283) * np.exp(-t / tau)
    y *= np.minimum(1.0, t / 0.0015)
    if click:
        c_len = min(len(y), int(0.006 * SR))
        y[:c_len] += click * hp(nz(c_len / SR), 2400)[:c_len] * np.linspace(1.0, 0.0, c_len)
    return y


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


def reverb(x, rt60=1.2, wet=0.18):
    n_ir = int(rt60 * SR)
    t = np.arange(n_ir) / SR
    ir = rng.standard_normal(n_ir) * np.exp(-6.9 * t / max(rt60, 0.05))
    ir = lp(ir, 3200)
    ir /= np.sqrt(np.sum(ir ** 2) + 1e-12)
    y = fftconvolve(x, ir, mode='full')[:len(x)]
    return (1.0 - wet) * x + wet * y


# --- Foley generators ---
def sfx_gouge(d=0.18):
    d = max(0.08, min(0.45, d))
    scrape = bp(nz(d), 900, 3800) * env(d, 0.008, d * 0.45)
    bite = modal([(190, 1.0, 0.035), (780, 0.45, 0.02)], d, click=1.1)
    return norm(0.65 * scrape + 0.55 * bite, 0.72)


def sfx_footstep():
    d = 0.22
    thud = lp(nz(d), 220) * env(d, 0.004, 0.045)
    grit = bp(nz(d), 1400, 4800) * env(d, 0.003, 0.025) * 0.35
    return norm(thud + grit, 0.78)


def sfx_peel(d=0.8):
    d = max(0.3, min(1.8, d))
    t = t_(d)
    sweep = bp(nz(d), 500, 3200) * (0.25 + 0.75 * np.sin(np.pi * t / d))
    sweep *= np.minimum(1.0, t / 0.06) * np.minimum(1.0, (d - t) / 0.08)
    return norm(sweep, 0.58)


def sfx_thump():
    d = 0.32
    sub = np.sin(2 * np.pi * 62 * t_(d)) * env(d, 0.003, 0.11)
    wood = modal([(128, 0.8, 0.05), (310, 0.3, 0.025)], d, click=0.9)
    return norm(0.9 * sub + 0.5 * wood, 0.92)


for e in EV:
    ty = e.get('type', '')
    t = float(e.get('t', 0.0))
    d = float(e.get('d', 0.2))
    g = float(e.get('g', 1.0))
    pan = float(e.get('pan', rng.uniform(-0.35, 0.35)))
    if ty == 'gouge':
        put(fol, sfx_gouge(d), t, 0.60 * g, pan)
    elif ty == 'tally':
        put(fol, sfx_gouge(0.16), t, 0.72 * g, rng.uniform(-0.4, 0.4))
    elif ty == 'lantern':
        bloom = bp(nz(1.2), 280, 1400) * env(1.2, 0.25, 0.55)
        put(fol, norm(bloom, 0.45), t, 0.55, 0.25)
    elif ty in ('step', 'footstep'):
        for k in range(4):
            put(fol, reverb(sfx_footstep(), 0.7, 0.22), t + k * 0.72, (0.72 - k * 0.08) * g, -0.15 + k * 0.1)
    elif ty == 'peel':
        put(fol, sfx_peel(0.8), t, 0.75 * g, 0.15)
    elif ty == 'thump':
        put(fol, reverb(sfx_thump(), 0.9, 0.2), t, 0.85 * g, 0.0)

# --- Ambience: London night fog & distant wind ---
fog1 = lp(nz(28.0), 260) * 0.08 + bp(nz(28.0), 180, 520) * 0.025
fog1 *= np.minimum(1.0, t_(28.0) / 0.6)
put(amb, fog1, 0.0, 1.0, 0.0)

fog2 = lp(nz(15.0), 240) * 0.075 + bp(nz(15.0), 160, 480) * 0.02
fog2 *= np.minimum(1.0, (15.0 - t_(15.0)) / 1.5)
put(amb, fog2, 30.0, 1.0, 0.0)

# --- Score (D minor / Phrygian gothic woodcut) ---
S.seed(1888)
score_events = [
    # Plate 1 (0 - 9.0s): brooding low D cello drone + bowed vibraphone
    (0.0, 'cellos', 'D2', 9.0, 0.55, -0.15),
    (0.4, 'vibraphone_bowed', 'A4', 5.0, 0.32, 0.25),
    (4.5, 'cellos', 'F2', 4.5, 0.50, 0.15),
    (5.2, 'vibraphone_bowed', 'Bb4', 4.0, 0.28, -0.25),

    # Plate 2 (9.0 - 18.5s): pizzicato pulse + stalking cello
    (9.2, 'cellos', 'D2', 9.2, 0.60, -0.1),
    (10.0, 'cellos_pizz', 'D3', 0.6, 0.65, -0.2),
    (11.4, 'cellos_pizz', 'F3', 0.6, 0.60, 0.2),
    (12.8, 'cellos_pizz', 'Eb3', 0.6, 0.68, -0.15),
    (14.2, 'cellos_pizz', 'D3', 0.6, 0.65, 0.15),
    (15.6, 'cellos_pizz', 'C#3', 0.6, 0.72, 0.0),
    (16.8, 'timpani', 'D2', 2.0, 0.45, 0.0),

    # Plate 3 (18.5 - 28.0s): five tallies — rising tension
    (18.6, 'cellos', 'D2', 9.0, 0.68, -0.15),
    (19.0, 'cellos', 'A2', 8.5, 0.52, 0.15),
    (19.8, 'vibraphone_bowed', 'E5', 4.0, 0.30, 0.3),
    (23.5, 'timpani', 'D2', 3.5, 0.55, 0.0),
    (24.5, 'vibraphone_bowed', 'F5', 3.2, 0.35, -0.3),

    # 28.0 - 30.0s: DIGITAL SILENCE (no notes)

    # Plate 4 & 5 (30.0 - 45.0s): "FROM HELL" reveal + unsolved finale
    (30.0, 'timpani', 'D2', 4.5, 0.78, 0.0),
    (30.0, 'cellos', 'D2', 14.5, 0.72, -0.15),
    (30.5, 'cellos', 'A2', 13.5, 0.55, 0.15),
    (31.2, 'vibraphone_bowed', 'D5', 6.0, 0.36, 0.2),
    (36.8, 'vibraphone_bowed', 'Bb4', 5.5, 0.32, -0.25),
    (38.0, 'cellos', 'F2', 6.5, 0.58, 0.1),
    (41.5, 'timpani', 'D2', 3.2, 0.42, 0.0),
]
mus = S.render(score_events, DUR)
if len(mus) < N:
    mus = np.pad(mus, ((0, N - len(mus)), (0, 0)))
else:
    mus = mus[:N]

# --- Voiceover ---
VO_CUES = [
    ('w1', 1.0),
    ('w2', 9.8),
    ('w3', 19.2),
    ('w4', 31.0),
    ('w5', 38.0),
]
vo_win = []
for vid, vt in VO_CUES:
    wav_path = os.path.join(D, 'voices', f'{vid}.wav')
    if not os.path.exists(wav_path):
        continue
    x, sr = sf.read(wav_path)
    if x.ndim > 1:
        x = x.mean(1)
    if sr != SR:
        x = resample_poly(x, SR, sr)
    x = norm(x, 0.85)
    put(vox, reverb(x, 0.45, 0.08), vt, 1.0, 0.0)
    vo_win.append((vt, vt + len(x) / SR))

# --- Ducking & Mix ---
tt = np.arange(N) / SR
duck = np.ones(N)
for a, b in vo_win:
    w_ = np.clip(np.minimum((tt - (a - 0.25)) / 0.25, ((b + 0.35) - tt) / 0.35), 0.0, 1.0)
    duck = np.minimum(duck, 1.0 - 0.58 * w_)

fduck = np.ones(N)
for a, b in vo_win:
    w_ = np.clip(np.minimum((tt - (a - 0.12)) / 0.12, ((b + 0.15) - tt) / 0.2), 0.0, 1.0)
    fduck = np.minimum(fduck, 1.0 - 0.38 * w_)

mix = mus * 0.85 * duck[:, None] + amb * fduck[:, None] + fol * fduck[:, None] + vox * 1.32

# --- Digital silence at 28.0 - 30.0s ---
s_a = int(28.0 * SR)
s_b = int(30.0 * SR)
fade = int(0.025 * SR)
mix[s_a - fade:s_a] *= np.linspace(1.0, 0.0, fade)[:, None]
mix[s_a:s_b] = 0.0
mix[s_b:s_b + fade] *= np.linspace(0.0, 1.0, fade)[:, None]

# Final tail fade-out (44.0 - 45.0s)
end_fade = int(1.0 * SR)
mix[-end_fade:] *= np.linspace(1.0, 0.0, end_fade)[:, None]

pk = float(np.abs(mix).max())
if pk > 0:
    mix = mix / pk * 0.89

out_path = os.path.join(D, 'mix.wav')
sf.write(out_path, mix.astype(np.float32), SR)
print(f'mix.wav {mix.shape} peak={pk:.4f} vo={vo_win}')
