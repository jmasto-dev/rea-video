"""Archive Light Table score (VSCO2/VCSL), 100Hz ballast hum, glass loupe clacks, and US voice (42s)."""
import os, sys, json
import numpy as np
import soundfile as sf
import soxr

LIB = os.environ.get('LIB', '/home/devuser/lemo-opuscar')
sys.path.insert(0, LIB)
from core.audio import sampler as S
from core.audio.sfx import SR, add, bp, lp, noise, env_exp, norm, t_

HERE = os.path.dirname(os.path.abspath(__file__))
DUR = 42.0
N = int(round(DUR * SR))

def glass_clack(dur=0.14):
    """Loupe landing on backlit glass."""
    tt = t_(dur)
    ring = np.sin(2 * np.pi * 1680 * tt) * env_exp(dur, 0.035) * 0.45
    thud = np.sin(2 * np.pi * 190 * tt) * env_exp(dur, 0.018) * 0.65
    click = bp(noise(dur), 2400, 6500) * env_exp(dur, 0.006) * 0.5
    return norm(ring + thud + click) * 0.65

def develop_wash(dur=1.4):
    """Soft chemical/paper sweep during negative->positive develop."""
    tt = t_(dur)
    return norm(bp(noise(dur), 500, 2400) * np.sin(np.pi * tt / dur)) * 0.25

def duck_env(vo_spans, fade=0.22, floor=0.22):
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
        w = norm(np.tanh(w * 1.35) / 1.35) * 0.74
        add(vo_buf, w, L['t'], gain=1.0, pan=0.0)
        vo_spans.append((L['t'], L['t'] + len(w) / SR))

    # Restrained Archive Light Table score (cellos + bowed vibraphone + pizzicato)
    ev = [
        (0.0, 'vibraphone_bowed', 'D4', 5.0, 0.42, -0.2),
        (0.0, 'cellos', 'D2', 11.0, 0.45, 0.15),
        (12.0, 'cellos', 'C2', 11.0, 0.48, 0.15),
        (16.5, 'vibraphone_bowed', 'F4', 4.5, 0.40, -0.2),
        (24.0, 'cellos', 'Bb1', 10.0, 0.50, 0.15),
        (35.0, 'vibraphone_bowed', 'A4', 6.5, 0.44, 0.0),
        (35.0, 'cellos', 'D2', 6.5, 0.48, 0.0),
    ]
    for t_p in [2.0, 4.0, 6.0, 8.0, 14.0, 18.0, 20.0, 26.0, 30.0, 32.0]:
        ev.append((t_p, 'cellos_pizz', 'D3', 0.45, 0.42, -0.15))

    S.seed(1903)
    score = S.room(S.render(ev, dur=DUR, master=False), size=0.42, mix=0.2)

    fol = np.zeros((N, 2), dtype=np.float32)
    # 100 Hz light table ballast hum
    tt = t_(DUR)
    hum = (np.sin(2 * np.pi * 100 * tt) * 0.6 + np.sin(2 * np.pi * 200 * tt) * 0.25) * 0.028
    add(fol, hum, 0.0, gain=1.0, pan=0.0)

    with open(os.path.join(HERE, 'events.json'), encoding='utf-8') as f:
        events = json.load(f)['ev']
    for e in events:
        et, ty = e['t'], e['type']
        if ty in ('loupe_drop', 'loupe_lift'): add(fol, glass_clack(), et, gain=0.75, pan=0.05)
        elif ty == 'develop': add(fol, develop_wash(), et, gain=0.65, pan=-0.1)

    duck = duck_env(vo_spans)
    mix = score * duck[:, None] * 0.45 + fol * 0.75 + vo_buf
    peak = np.abs(mix).max()
    if peak > 0.92: mix *= 0.92 / peak
    out = os.path.join(HERE, 'out', 'mix.wav')
    sf.write(out, mix, SR, subtype='PCM_16')
    print(f'wrote {out} ({DUR}s)')

if __name__ == '__main__':
    main()
