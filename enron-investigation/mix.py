"""Visual Investigation score (VSCO 2 CE + VCSL) & procedural forensic foley (45s)."""
import os, sys, json
import numpy as np
import soundfile as sf
import soxr

LIB = os.environ.get('LIB', '/home/devuser/lemo-opuscar')
sys.path.insert(0, LIB)
from core.audio import sampler as S
from core.audio.sfx import SR, add, bp, lp, noise, env_exp, norm, t_

HERE = os.path.dirname(os.path.abspath(__file__))
DUR = 45.0
N = int(round(DUR * SR))

def shutter(dur=0.07):
    return norm(bp(noise(dur), 1800, 6200) * env_exp(dur, 0.012)) * 0.48

def sub_impact(dur=0.9):
    tt = t_(dur)
    f = np.linspace(88, 34, len(tt))
    return norm(np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(dur, 0.32)) * 0.72

def tick_snd(accent=False):
    d = 0.045
    return norm(bp(noise(d), 2200 if accent else 1600, 5800) * env_exp(d, 0.008)) * (0.45 if accent else 0.25)

def duck_env(vo_spans, fade=0.18, floor=0.22):
    env = np.ones(N, dtype=np.float32)
    f = int(fade * SR)
    for t0, t1 in vo_spans:
        i0, i1 = max(0, int(t0 * SR) - f), min(N, int(t1 * SR) + f)
        a0, a1 = max(0, int(t0 * SR)), min(N, int(t1 * SR))
        if a0 > i0: env[i0:a0] = np.minimum(env[i0:a0], np.linspace(1.0, floor, a0 - i0))
        env[a0:a1] = np.minimum(env[a0:a1], floor)
        if i1 > a1: env[a1:i1] = np.minimum(env[a1:i1], np.linspace(floor, 1.0, i1 - a1))
    return env

def main():
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    with open(os.path.join(HERE, 'lines.json'), encoding='utf-8') as f:
        lines = json.load(f)
    vo_buf = np.zeros((N, 2), dtype=np.float32)
    vo_spans = []
    for L in lines:
        w, sr = sf.read(os.path.join(HERE, 'voices', f"{L['id']}.wav"), dtype='float32')
        if w.ndim > 1: w = w.mean(axis=1)
        if sr != SR: w = soxr.resample(w, sr, SR)
        w = norm(np.tanh(w * 1.35) / 1.35) * 0.75
        add(vo_buf, w, L['t'], gain=1.0, pan=0.0)
        vo_spans.append((L['t'], L['t'] + len(w) / SR))

    # Restraint investigation bed: low D cello pedal + sparse pizzicato + vibraphone resolve
    ev = [
        (0.0, 'cellos', 'D2', 12.0, 0.45, -0.15),
        (13.5, 'cellos', 'D2', 11.0, 0.50, -0.15),
        (25.5, 'timpani', 'D2', 1.8, 0.75, 0.0),
        (38.5, 'vibraphone_bowed', 'A4', 5.5, 0.42, 0.2),
        (38.5, 'cellos', 'D2', 6.0, 0.45, -0.2),
    ]
    for b in np.arange(0.5, 38.0, 0.5):
        if int(b * 2) % 2 == 0:
            ev.append((float(b), 'cellos_pizz', 'D3' if int(b) % 2 == 0 else 'F3', 0.35, 0.42, 0.15))

    S.seed(2001)
    score = S.room(S.render(ev, dur=DUR, master=False), size=0.4, mix=0.18)

    fol = np.zeros((N, 2), dtype=np.float32)
    with open(os.path.join(HERE, 'events.json'), encoding='utf-8') as f:
        events = json.load(f)['ev']
    for e in events:
        et, ty = e['t'], e['type']
        if ty in ('sub', 'impact', 'resolve'): add(fol, sub_impact(), et, gain=0.8, pan=0.0)
        elif ty in ('shutter', 'loupe', 'scan'): add(fol, shutter(), et, gain=0.75, pan=0.1)
    for k in range(12):
        add(fol, tick_snd(k % 4 == 0), 32.0 + k * 0.5, gain=0.55, pan=-0.1)

    duck = duck_env(vo_spans)
    mix = score * duck[:, None] * 0.42 + fol * 0.65 + vo_buf
    peak = np.abs(mix).max()
    if peak > 0.92: mix *= 0.92 / peak
    out = os.path.join(HERE, 'out', 'mix.wav')
    sf.write(out, mix, SR, subtype='PCM_16')
    print(f'wrote {out} ({DUR}s)')

if __name__ == '__main__':
    main()
