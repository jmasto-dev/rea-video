"""Build Act 1 (0.00s - 42.84s) studio-grade audio mix for binance-cinema."""
import os
import sys
import subprocess
import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly, butter, sosfilt

sys.path.insert(0, '/home/devuser/lemo-opuscar')
from core.audio.sfx import SR, bp, lp, hp, norm, brown, click, clack, creak, thump, ding, compress, limit

ACT1_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(ACT1_DIR)
SRC_WAV = os.path.join(ROOT_DIR, 'binance-hacking.wav')
OUT_WAV = os.path.join(ACT1_DIR, 'act1_mix.wav')

DUR = 42.84
N = int(round(DUR * SR))
rng = np.random.default_rng(20261029)

amb = np.zeros((N, 2), dtype=np.float64)
fol = np.zeros((N, 2), dtype=np.float64)


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


def fade_env(length, fi=0.25, fo=0.25):
    e = np.ones(length, dtype=np.float64)
    ni = min(length // 2, int(fi * SR))
    no = min(length // 2, int(fo * SR))
    if ni > 0:
        e[:ni] *= np.linspace(0.0, 1.0, ni)
    if no > 0:
        e[-no:] *= np.linspace(1.0, 0.0, no)
    return e


def sine_tone(d, f, f_end=None):
    t = np.arange(int(round(d * SR))) / SR
    if f_end is None:
        return np.sin(2 * np.pi * f * t)
    freq = np.linspace(f, f_end, len(t))
    return np.sin(2 * np.pi * np.cumsum(freq) / SR)


# ==============================================================================
# 1. EXTRACT & RESAMPLE VOICEOVER (0.00 - 42.84s, 24kHz -> 48kHz via ffmpeg)
# ==============================================================================
vo_proc = subprocess.run(
    ['ffmpeg', '-v', 'error', '-ss', '0', '-t', f'{DUR:.3f}', '-i', SRC_WAV,
     '-ar', str(SR), '-ac', '1', '-f', 'f32le', 'pipe:1'],
    capture_output=True, check=True
)
vo_48 = np.frombuffer(vo_proc.stdout, dtype=np.float32).astype(np.float64)[:N]
if len(vo_48) < N:
    vo_48 = np.pad(vo_48, (0, N - len(vo_48)))
# Clean sub-75Hz rumble from VO so it never muddies 40Hz sub-bass, gentle vocal compression
vo_48 = hp(vo_48, 75.0, o=2)
vo_48 = compress(vo_48, thr=0.22, ratio=2.8, att=0.004, rel=0.09)
vo_48 = norm(vo_48, 0.78)
vox = np.column_stack([vo_48, vo_48])


# ==============================================================================
# 2. FOLEY & ATMOSPHERE DESIGN (11 BEATS)
# ==============================================================================

# Beat 1 (0.00-4.20s): 40Hz sub-bass swell + silent hydraulic hiss (zero alarm)
d1 = 4.50
t1 = np.arange(int(round(d1 * SR))) / SR
sub1 = 0.75 * np.sin(2 * np.pi * 40.0 * t1) + 0.25 * np.sin(2 * np.pi * 80.0 * t1)
sub1 *= np.sin(np.pi * np.minimum(1.0, t1 / d1)) ** 1.4
put(amb, norm(sub1, 0.42), 0.0, 0.55, 0.0)

hiss1 = bp(rng.standard_normal(int(round(2.8 * SR))), 1800, 6200)
hiss1 *= fade_env(len(hiss1), 0.6, 0.9)
put(fol, norm(hiss1, 0.20), 1.35, 0.22, 0.05)

# Beat 2 (4.20-8.52s): Rushing current + 10 staggered crystalline chimes (4.8s-7.8s)
d2 = 4.60
cur_l = bp(brown(d2), 140, 1400) * fade_env(int(round(d2 * SR)), 0.5, 0.7)
cur_r = bp(brown(d2), 160, 1550) * fade_env(int(round(d2 * SR)), 0.5, 0.7)
put(amb, np.column_stack([norm(cur_l, 0.28), norm(cur_r, 0.28)]), 4.10, 0.36)

chime_times = np.linspace(4.8, 7.8, 10)
chime_freqs = [1760, 2093, 2349, 2637, 2960, 3136, 3520, 3951, 4186, 4698]
for idx, (tc, fc) in enumerate(zip(chime_times, chime_freqs)):
    dc = 0.9
    tt = np.arange(int(round(dc * SR))) / SR
    chime = (
        0.65 * np.sin(2 * np.pi * fc * tt) * np.exp(-tt / 0.26)
        + 0.30 * np.sin(2 * np.pi * (fc * 1.5) * tt) * np.exp(-tt / 0.16)
        + 0.15 * np.sin(2 * np.pi * (fc * 2.0) * tt) * np.exp(-tt / 0.10)
    )
    pan = -0.65 + 1.30 * (idx / 9.0)
    put(fol, norm(chime, 0.35), tc, 0.22, pan)

# Beat 3 (8.52-12.00s): Mechanical odometer whirr + heavy stone thud at 10.5s ($6.3B)
d3 = 3.50
whirr_n = int(round(2.1 * SR))
whirr = bp(rng.standard_normal(whirr_n), 420, 1800)
tt_w = np.arange(whirr_n) / SR
whirr *= (0.45 + 0.55 * np.abs(np.sin(2 * np.pi * 14.0 * tt_w))) * fade_env(whirr_n, 0.2, 0.25)
put(fol, norm(whirr, 0.25), 8.52, 0.30, -0.15)
# Accelerating odometer clicks
for k in range(14):
    put(fol, norm(click(1.15), 0.32), 8.65 + k * 0.125, 0.20, -0.1)

# Heavy stone thud at 10.5s
d_thud = 1.1
tt_t = np.arange(int(round(d_thud * SR))) / SR
stone_thud = (
    0.80 * np.sin(2 * np.pi * 48.0 * tt_t * np.exp(-tt_t * 1.2)) * np.exp(-tt_t / 0.22)
    + 0.45 * lp(rng.standard_normal(len(tt_t)), 220) * np.exp(-tt_t / 0.06)
    + 0.25 * thump(1.0, 62)
) if False else (
    0.80 * np.sin(2 * np.pi * 46.0 * tt_t * np.exp(-tt_t * 0.9)) * np.exp(-tt_t / 0.24)
    + 0.50 * lp(rng.standard_normal(len(tt_t)), 240) * np.exp(-tt_t / 0.05)
)
put(fol, norm(stone_thud, 0.80), 10.50, 0.72, 0.0)

# Beat 4 (12.00-15.80s): Soft sheet rustle + phone unlock click (14.2s) + low room tone
d4 = 3.90
room4 = lp(rng.standard_normal(int(round(d4 * SR))), 160) * fade_env(int(round(d4 * SR)), 0.3, 0.4)
put(amb, norm(room4, 0.18), 11.95, 0.24, 0.0)

n_rust = int(round(0.65 * SR))
rustle4 = bp(rng.standard_normal(n_rust), 700, 2900) * np.sin(np.pi * np.arange(n_rust) / n_rust) ** 1.5
put(fol, norm(rustle4, 0.28), 12.45, 0.26, -0.25)

# Phone unlock click at 14.2s (crisp micro-switch + subtle screen wake chirp)
unlock_c = click(1.35, 0.8)
put(fol, norm(unlock_c, 0.55), 14.20, 0.44, 0.12)

# Beat 5 (15.80-19.04s): 3 dry glass taps (16.3s, 17.0s, 17.7s) + deadened muted thud
for tp in [16.30, 17.00, 17.70]:
    d_gt = 0.07
    tt_g = np.arange(int(round(d_gt * SR))) / SR
    tap = (
        0.55 * hp(rng.standard_normal(len(tt_g)), 2200) * np.exp(-tt_g / 0.002)
        + 0.65 * np.sin(2 * np.pi * 2450 * tt_g) * np.exp(-tt_g / 0.008)
        + 0.35 * np.sin(2 * np.pi * 4100 * tt_g) * np.exp(-tt_g / 0.005)
    )
    put(fol, norm(tap, 0.55), tp, 0.46, 0.10)

# Deadened muted thud at 18.25s (zero haptic response)
d_m = 0.22
tt_m = np.arange(int(round(d_m * SR))) / SR
muted_thud = 0.7 * np.sin(2 * np.pi * 78.0 * tt_m) * np.exp(-tt_m / 0.04) + 0.3 * lp(rng.standard_normal(len(tt_m)), 180) * np.exp(-tt_m / 0.02)
put(fol, norm(muted_thud, 0.45), 18.25, 0.36, 0.05)

# Beat 6 (19.04-22.08s): Soft CRT hum + rapid teletype scroll ticks
d6 = 3.15
tt6 = np.arange(int(round(d6 * SR))) / SR
crt_hum = (0.55 * np.sin(2 * np.pi * 60.0 * tt6) + 0.30 * np.sin(2 * np.pi * 120.0 * tt6) + 0.15 * np.sin(2 * np.pi * 180.0 * tt6))
crt_hum *= fade_env(len(tt6), 0.25, 0.30)
put(amb, norm(crt_hum, 0.20), 19.00, 0.24, 0.0)

t_tick = 19.25
while t_tick < 21.85:
    tt_tk = np.arange(int(round(0.025 * SR))) / SR
    tk = hp(rng.standard_normal(len(tt_tk)), 3000) * np.exp(-tt_tk / 0.0018) + 0.4 * np.sin(2 * np.pi * 3400 * tt_tk) * np.exp(-tt_tk / 0.003)
    put(fol, norm(tk, 0.24), t_tick, 0.20, rng.uniform(-0.2, 0.2))
    t_tick += 0.085

# Beat 7 (22.08-26.32s): Glass harmonic resonance + near-silence (strategic silence!)
d7 = 3.80
tt7 = np.arange(int(round(d7 * SR))) / SR
glass_harm = (
    0.55 * np.sin(2 * np.pi * 1046.5 * tt7)
    + 0.30 * np.sin(2 * np.pi * 1568.0 * tt7)
    + 0.15 * np.sin(2 * np.pi * 2093.0 * tt7)
) * fade_env(len(tt7), 0.8, 1.2)
put(amb, norm(glass_harm, 0.18), 22.25, 0.18, 0.0)

# Beat 8 (26.32-29.60s): Crisp pneumatic stamp clack x2 (27.2s, 28.4s)
for ts in [27.20, 28.40]:
    # Pneumatic hiss pre-stroke + heavy mechanical stamp clack
    n_pre = int(round(0.09 * SR))
    pre = bp(rng.standard_normal(n_pre), 2000, 5500) * np.linspace(0.2, 1.0, n_pre)
    put(fol, norm(pre, 0.28), ts - 0.08, 0.28, -0.08)
    stamp = 0.65 * clack(0.85, 0.9) + 0.55 * np.pad(thump(0.8, 95), (0, 0))[:len(clack(0.85, 0.9))]
    put(fol, norm(stamp, 0.72), ts, 0.58, 0.0)

# Beat 9 (29.60-33.00s): Relay clicks + clean digital chime
for tr in [29.85, 30.35, 30.85, 31.35]:
    put(fol, norm(click(1.25, 0.7), 0.42), tr, 0.34, rng.uniform(-0.25, 0.25))
d_ch9 = 1.2
tt9 = np.arange(int(round(d_ch9 * SR))) / SR
chime9 = (0.7 * np.sin(2 * np.pi * 1318.5 * tt9) * np.exp(-tt9 / 0.35) + 0.35 * np.sin(2 * np.pi * 1975.5 * tt9) * np.exp(-tt9 / 0.22))
put(fol, norm(chime9, 0.38), 31.65, 0.32, 0.0)

# Beat 10 (33.00-37.28s): Deep server fan drone + distant metal creak
d10 = 4.40
tt10 = np.arange(int(round(d10 * SR))) / SR
fan_drone = (
    0.55 * lp(brown(d10), 190)
    + 0.35 * np.sin(2 * np.pi * 54.0 * tt10)
    + 0.20 * np.sin(2 * np.pi * 108.0 * tt10)
) * fade_env(len(tt10), 0.45, 0.55)
put(amb, norm(fan_drone, 0.32), 32.90, 0.36, 0.0)

crk = creak(0.8)
put(fol, norm(crk, 0.30), 35.40, 0.26, 0.35)

# Beat 11 (37.28-42.84s): Parchment scrape + soft lock pin click (39.2s)
n_sc = int(round(0.75 * SR))
scrape = bp(rng.standard_normal(n_sc), 1100, 3800) * np.sin(np.pi * np.arange(n_sc) / n_sc) ** 1.3
put(fol, norm(scrape, 0.34), 37.85, 0.30, -0.15)

# Soft lock pin click at 39.2s
d_pk = 0.045
tt_pk = np.arange(int(round(d_pk * SR))) / SR
pin_click = 0.6 * hp(rng.standard_normal(len(tt_pk)), 2800) * np.exp(-tt_pk / 0.0015) + 0.5 * np.sin(2 * np.pi * 3100 * tt_pk) * np.exp(-tt_pk / 0.006)
put(fol, norm(pin_click, 0.50), 39.20, 0.44, 0.08)


# ==============================================================================
# 3. SUM, DUCK BED SLIGHTLY UNDER VO, LIMIT & NORMALIZE TO -14 LUFS / <=0.89 PEAK
# ==============================================================================
# Subtle sidechain envelope from VO so VO stays crystal clear
vo_env = np.abs(vo_48)
win = int(0.08 * SR)
kernel = np.ones(win) / win
vo_smooth = np.convolve(vo_env, kernel, mode='same')
duck = 1.0 - 0.28 * np.clip(vo_smooth / 0.18, 0.0, 1.0)

mix = (amb * duck[:, None]) * 0.72 + fol * 0.78 + vox * 1.10

# Smooth tail fade (last 0.15s) to avoid any end-of-file click
end_f = int(0.15 * SR)
mix[-end_f:] *= np.linspace(1.0, 0.0, end_f)[:, None]

# Peak-protect before LUFS pass
mix[:, 0] = limit(mix[:, 0], ceil=0.89)
mix[:, 1] = limit(mix[:, 1], ceil=0.89)

tmp_wav = os.path.join(ACT1_DIR, '_act1_tmp.wav')
wavfile.write(tmp_wav, SR, np.clip(mix, -1.0, 1.0).astype(np.float32))

# Measure integrated LUFS with ffmpeg ebur128
res = subprocess.run(
    ['ffmpeg', '-y', '-i', tmp_wav, '-af', 'ebur128=framelog=quiet', '-f', 'null', '-'],
    capture_output=True, text=True, check=True
)
lufs_val = -14.0
for line in res.stderr.splitlines():
    if 'I:' in line and 'LUFS' in line:
        lufs_val = float(line.split('I:')[1].split('LUFS')[0].strip())

gain_db = -14.0 - lufs_val
gain_lin = 10.0 ** (gain_db / 20.0)
mix_norm = mix * gain_lin
mix_norm[:, 0] = limit(mix_norm[:, 0], ceil=0.89)
mix_norm[:, 1] = limit(mix_norm[:, 1], ceil=0.89)

wavfile.write(OUT_WAV, SR, np.clip(mix_norm, -1.0, 1.0).astype(np.float32))
os.remove(tmp_wav)

pk = float(np.abs(mix_norm).max())
print(f"Pre-norm LUFS: {lufs_val:.2f} | Applied gain: {gain_db:+.2f} dB | Final peak: {pk:.4f} | Output: {OUT_WAV}")
