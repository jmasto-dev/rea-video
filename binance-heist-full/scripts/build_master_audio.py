#!/usr/bin/env python3
"""Build the 483.5000s (11,604 frames @ 24fps) Master Audio Mix for The $6.3B Binance Heist.

Outputs:
  /home/devuser/projects/rea-video/binance-heist-full/audio/master_mix.wav
  (48,000 Hz, 16-bit PCM stereo, exact 23,208,000 samples = 483.5000s, ~-15.5 LUFS, peak <= 0.85)
"""
import json
import math
import subprocess
import wave
from pathlib import Path

import numpy as np
from scipy.ndimage import maximum_filter1d, uniform_filter1d
from scipy.signal import butter, resample_poly, sosfilt

SR = 48000
TOTAL_DUR = 483.5000
N_SAMPLES = int(round(TOTAL_DUR * SR))  # 23,208,000 samples
VO_OFFSET_SEC = 1.500

ROOT = Path('/home/devuser/projects/rea-video/binance-heist-full')
VO_SRC = Path('/home/devuser/projects/rea-video/binance-cinema/binance-hacking.wav')
MUSIC_DIR = ROOT / 'audio' / 'lib' / 'music' / 'audio' / 'music'
SFX_LIB_DIR = ROOT / 'audio' / 'lib' / 'sfx'
SFX_MANIFEST = SFX_LIB_DIR / 'audio-selection.json'
OUT_WAV = ROOT / 'audio' / 'master_mix.wav'

RNG = np.random.default_rng(20261029)


# ---------------------------------------------------------------------------
# DSP & IO Utilities
# ---------------------------------------------------------------------------
def biquad_peaking(fc: float, gain_db: float, q: float, sr: int = SR) -> np.ndarray:
    """Return second-order section [b0, b1, b2, 1, a1, a2] for peaking EQ."""
    A = 10.0 ** (gain_db / 40.0)
    w0 = 2.0 * math.pi * fc / sr
    alpha = math.sin(w0) / (2.0 * q)
    cosw = math.cos(w0)
    b0 = 1.0 + alpha * A
    b1 = -2.0 * cosw
    b2 = 1.0 - alpha * A
    a0 = 1.0 + alpha / A
    a1 = -2.0 * cosw
    a2 = 1.0 - alpha / A
    return np.array([[b0 / a0, b1 / a0, b2 / a0, 1.0, a1 / a0, a2 / a0]], dtype=np.float64)


def hp(x: np.ndarray, freq: float, order: int = 3) -> np.ndarray:
    sos = butter(order, freq, btype='high', fs=SR, output='sos')
    return sosfilt(sos, x, axis=0)


def lp(x: np.ndarray, freq: float, order: int = 2) -> np.ndarray:
    sos = butter(order, freq, btype='low', fs=SR, output='sos')
    return sosfilt(sos, x, axis=0)


def bp(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    sos = butter(order, [lo, hi], btype='band', fs=SR, output='sos')
    return sosfilt(sos, x, axis=0)


def norm_peak(x: np.ndarray, peak: float = 0.9) -> np.ndarray:
    m = float(np.max(np.abs(x)))
    return x * (peak / m) if m > 1e-12 else x


def decode_audio_48k_stereo(path: Path) -> np.ndarray:
    """Decode any MP3/OGG/WAV/FLAC file via ffmpeg to float64 stereo @ 48kHz."""
    raw = subprocess.run(
        ['ffmpeg', '-v', 'error', '-i', str(path), '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'],
        capture_output=True,
        check=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64).reshape(-1, 2)


def trim_leading_silence(x: np.ndarray, thresh_db: float = -55.0, pad_ms: float = 4.0) -> np.ndarray:
    """Trim dead leading silence from library SFX so transients align with storyboard beats."""
    thr = 10.0 ** (thresh_db / 20.0)
    env = np.max(np.abs(x), axis=1) if x.ndim == 2 else np.abs(x)
    idx = np.where(env > thr)[0]
    if len(idx) == 0:
        return x
    start = max(0, int(idx[0]) - int(pad_ms * 0.001 * SR))
    return x[start:]


def place(buf: np.ndarray, sig: np.ndarray, t_sec: float, gain: float = 1.0, pan: float = 0.0) -> None:
    """Add mono or stereo signal into stereo master buffer at t_sec with constant-power pan."""
    s = np.asarray(sig, dtype=np.float64)
    if s.ndim == 1:
        ang = (np.clip(pan, -1.0, 1.0) + 1.0) * math.pi / 4.0
        st = np.column_stack([s * (gain * math.cos(ang)), s * (gain * math.sin(ang))])
    else:
        if abs(pan) > 1e-3:
            ang = (np.clip(pan, -1.0, 1.0) + 1.0) * math.pi / 4.0
            mono = 0.5 * (s[:, 0] + s[:, 1])
            st = np.column_stack([
                (0.5 * s[:, 0] + 0.5 * mono) * gain * math.cos(ang) * 1.414,
                (0.5 * s[:, 1] + 0.5 * mono) * gain * math.sin(ang) * 1.414,
            ])
        else:
            st = s * gain

    i0 = int(round(t_sec * SR))
    if i0 >= len(buf) or i0 + len(st) <= 0:
        return
    src_a = max(0, -i0)
    dst_a = max(0, i0)
    length = min(len(st) - src_a, len(buf) - dst_a)
    if length > 0:
        buf[dst_a:dst_a + length] += st[src_a:src_a + length]


def lookahead_limit_stereo(x: np.ndarray, ceil: float = 0.85, look_sec: float = 0.005) -> np.ndarray:
    """Smooth stereo-linked look-ahead peak limiter to avoid clipping or pumping."""
    n_win = max(3, int(round(look_sec * SR)))
    pk = np.max(np.abs(x), axis=1)
    held = maximum_filter1d(pk, size=2 * n_win + 1)
    gain = np.minimum(1.0, ceil / np.maximum(held, 1e-9))
    gain = uniform_filter1d(gain, size=n_win)
    return x * gain[:, None]


# ---------------------------------------------------------------------------
# Voiceover Conditioning & Sidechain Envelope Follower
# ---------------------------------------------------------------------------
def load_and_condition_vo() -> tuple[np.ndarray, float]:
    """Load binance-hacking.wav (24k mono), resample to 48k, HPF 75Hz, presence EQ, soft control."""
    with wave.open(str(VO_SRC), 'rb') as w:
        sr_in = w.getframerate()
        assert sr_in == 24000, f'Expected 24kHz VO, got {sr_in}'
        raw = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float64) / 32768.0

    # Clean 2x polyphase resampling 24k -> 48k
    vo = resample_poly(raw, up=2, down=1)
    # 75 Hz high-pass to strip plosive rumble + gentle +2.2 dB presence boost @ 3.1 kHz
    vo = hp(vo, 75.0, order=3)
    vo = sosfilt(biquad_peaking(3100.0, +2.2, q=0.9), vo)

    # Gentle soft-knee vocal compressor / peak control (ratio 2.2:1 above -14 dBFS)
    env_ms = int(0.012 * SR)
    abs_vo = np.abs(vo)
    fast_env = np.sqrt(uniform_filter1d(vo ** 2, size=env_ms) + 1e-12)
    thr = 0.22
    comp_gain = np.where(fast_env > thr, (thr + (fast_env - thr) / 2.2) / np.maximum(fast_env, 1e-9), 1.0)
    comp_gain = uniform_filter1d(comp_gain, size=int(0.008 * SR))
    vo = vo * comp_gain
    vo = lookahead_limit_stereo(np.column_stack([vo, vo]), ceil=0.78, look_sec=0.004)[:, 0]

    # Measure active speech RMS (frames above -34 dBFS)
    active = abs_vo > 0.02
    active_rms = float(np.sqrt(np.mean(vo[active] ** 2))) if np.any(active) else 0.14
    return vo, active_rms


def compute_sidechain_duck_envelope(vo_track_mono: np.ndarray, vo_active_rms: float) -> np.ndarray:
    """Compute smooth music ducking envelope from VO RMS (attack 80ms, release 350ms).

    Targets ~ -20 dB under narration, lifting smoothly to ~ -12.5 dB during pauses,
    cold open (0-1.5s), and closing outro (478.55-483.50s).
    """
    # 25ms sliding RMS energy
    win = int(0.025 * SR)
    rms = np.sqrt(uniform_filter1d(vo_track_mono ** 2, size=win) + 1e-12)

    # Downsample control envelope to 1000 Hz (1 ms step) for exact attack/release smoothing
    step = SR // 1000  # 48 samples
    rms_1k = rms[::step]
    n_1k = len(rms_1k)

    # Normalize speech detector: anything > ~16% of active RMS pushes ducking toward full -20 dB
    noise_floor = 0.05 * vo_active_rms
    speech_ceil = 0.28 * vo_active_rms
    speech_prob = np.clip((rms_1k - noise_floor) / max(speech_ceil - noise_floor, 1e-6), 0.0, 1.0)

    gain_under_vo = 10.0 ** (-20.0 / 20.0)   # 0.1000 (-20.0 dB)
    gain_pause = 10.0 ** (-12.5 / 20.0)      # 0.2371 (-12.5 dB)
    target_1k = gain_pause - speech_prob * (gain_pause - gain_under_vo)

    # Smooth attack (80ms when ducking down) and release (350ms when lifting back up)
    a_att = math.exp(-1.0 / (0.080 * 1000.0))
    a_rel = math.exp(-1.0 / (0.350 * 1000.0))
    env_1k = np.empty(n_1k, dtype=np.float64)
    cur = gain_pause
    for i in range(n_1k):
        tgt = float(target_1k[i])
        c = a_att if tgt < cur else a_rel
        cur = c * cur + (1.0 - c) * tgt
        env_1k[i] = cur

    # Upsample smoothly back to 48kHz
    t_1k = np.arange(n_1k, dtype=np.float64) * step
    t_48k = np.arange(len(vo_track_mono), dtype=np.float64)
    return np.interp(t_48k, t_1k, env_1k)


# ---------------------------------------------------------------------------
# Music Arrangement (7 CC-BY-4.0 Stems Normalized + Crossfaded)
# ---------------------------------------------------------------------------
def slice_music(track: np.ndarray, src_start_sec: float, dur_sec: float) -> np.ndarray:
    """Extract dur_sec stereo slice starting at src_start_sec (looping cleanly if ever needed)."""
    i0 = int(round(src_start_sec * SR))
    n_out = int(round(dur_sec * SR))
    if i0 + n_out <= len(track):
        return track[i0:i0 + n_out].copy()
    # Clean wrap with 1.5s equal-power crossfade if source shorter than cue
    out = np.zeros((n_out, 2), dtype=np.float64)
    rem = len(track) - i0
    out[:rem] = track[i0:]
    pos = rem
    while pos < n_out:
        take = min(len(track), n_out - pos)
        out[pos:pos + take] = track[:take]
        pos += take
    return out


def build_music_bed(vo_active_rms: float) -> np.ndarray:
    """Assemble all 7 music cues aligned to MASTER_STORYBOARD.md act/scene beats."""
    cues = [
        # (filename, t_master_start, t_master_end, src_start_sec, fade_in, fade_out, level_mul)
        ('bgm-decisions.mp3',          0.00,   44.33,  1.50, 0.08, 1.90, 1.02),  # Act 1: drops into rewind 42.4-44.33
        ('bgm-cipher.mp3',            44.33,   91.50, 12.00, 0.45, 1.40, 0.98),  # Act 2A-E -> DEAD SILENCE 91.50-96.46
        ('bgm-marty-gots-a-plan.mp3', 96.46,  128.80,  0.00, 0.35, 0.35, 1.00),  # Act 3A-C sneaky job-bait groove
        ('bgm-darkest-child.mp3',    128.80,  170.17,  0.00, 0.25, 0.80, 1.00),  # Act 3C-F Potemkin reveal -> end Act 3
        ('bgm-getting-it-done.mp3',  170.17,  272.08,  0.00, 0.65, 0.55, 0.96),  # Act 4 stealth heist
        ('bgm-volatile-reaction.mp3',272.08,  317.20,  0.00, 0.12, 0.45, 0.96),  # Act 5A-C explosive drain
        ('bgm-hitman.mp3',           317.20,  378.00, 51.00, 0.20, 0.85, 1.00),  # Act 5D-F urgent freeze race
        ('bgm-decisions.mp3',        378.00,  416.80,  1.50, 0.55, 0.45, 0.98),  # Act 6A-B bailout + DOJ -> DEAD SILENCE 416.8-418.2
        ('bgm-darkest-child.mp3',    418.20,  483.50,167.65, 0.25, 1.60, 1.02),  # Act 6C-F: final cadence @ 478.55, fade out by 483.3
    ]

    cache: dict[str, np.ndarray] = {}
    bed = np.zeros((N_SAMPLES, 2), dtype=np.float64)

    for fn, t0, t1, src_t0, fi, fo, mul in cues:
        if fn not in cache:
            cache[fn] = decode_audio_48k_stereo(MUSIC_DIR / fn)
        dur = t1 - t0
        seg = slice_music(cache[fn], src_t0, dur)

        # Loudness-match each stem segment to vo_active_rms so all 7 tracks share a uniform 0 dB reference
        seg_rms = float(np.sqrt(np.mean(seg ** 2)))
        if seg_rms > 1e-8:
            seg = seg * ((vo_active_rms * mul) / seg_rms)

        # Smooth cosine fade-in & fade-out
        n_fi = min(len(seg), int(round(fi * SR)))
        n_fo = min(len(seg), int(round(fo * SR)))
        if n_fi > 0:
            u = np.linspace(0.0, math.pi, n_fi)
            w = 0.5 * (1.0 - np.cos(u))
            seg[:n_fi] *= w[:, None]
        if n_fo > 0:
            u = np.linspace(0.0, math.pi, n_fo)
            w = 0.5 * (1.0 + np.cos(u))
            seg[-n_fo:] *= w[:, None]

        # For final outro cue, guarantee absolute zero over last 200ms (483.30-483.50s)
        if t1 >= 483.4:
            tail_zero = int(0.20 * SR)
            fade_tail = int(1.60 * SR)
            if fade_tail + tail_zero < len(seg):
                u = np.linspace(0.0, math.pi, fade_tail)
                seg[-(fade_tail + tail_zero):-tail_zero] *= (0.5 * (1.0 + np.cos(u)))[:, None]
                seg[-tail_zero:] = 0.0

        place(bed, seg, t0, gain=1.0, pan=0.0)

    # Extra-clean silence pocket guards: 91.50-96.46s and 416.80-418.20s
    for sa, sb in [(91.50, 96.46), (416.80, 418.20)]:
        ia, ib = int(round(sa * SR)), int(round(sb * SR))
        bed[ia:ib] = 0.0

    return bed


# ---------------------------------------------------------------------------
# Synthesized Documentary Foley Generators
# ---------------------------------------------------------------------------
def t_arr(dur: float) -> np.ndarray:
    return np.arange(int(round(dur * SR)), dtype=np.float64) / SR


def synth_stamp_thud(heavy: bool = True) -> np.ndarray:
    dur = 0.28 if heavy else 0.20
    t = t_arr(dur)
    f0, f1 = (118.0, 42.0) if heavy else (145.0, 56.0)
    ph = 2.0 * math.pi * (f1 * t + (f0 - f1) * (1.0 - np.exp(-24.0 * t)) / 24.0)
    body = np.sin(ph) * np.exp(-t * 17.0)
    slap = bp(RNG.standard_normal(len(t)), 450.0, 2600.0) * np.exp(-t * 48.0) * 0.75
    click_hi = bp(RNG.standard_normal(len(t)), 2400.0, 5500.0) * np.exp(-t * 95.0) * 0.45
    return norm_peak(body * 0.9 + slap + click_hi, 0.92)


def synth_sub_drop(dur: float = 1.45, f0: float = 82.0, f1: float = 31.0) -> np.ndarray:
    t = t_arr(dur)
    ph = 2.0 * math.pi * (f1 * t + (f0 - f1) * (1.0 - np.exp(-4.5 * t)) / 4.5)
    sig = (np.sin(ph) + 0.25 * np.sin(2.0 * ph)) * np.minimum(1.0, t / 0.015) * np.exp(-t * 2.5)
    return norm_peak(sig, 0.90)


def synth_sub_swell(dur: float = 1.15, f0: float = 36.0, f1: float = 72.0) -> np.ndarray:
    t = t_arr(dur)
    u = t / dur
    inst_f = f0 + (f1 - f0) * (u ** 1.6)
    ph = 2.0 * math.pi * np.cumsum(inst_f) / SR
    env = (u ** 1.8) * np.minimum(1.0, (dur - t) / 0.04)
    air = bp(RNG.standard_normal(len(t)), 180.0, 900.0) * (u ** 2.2) * 0.22
    return norm_peak(np.sin(ph) * env + air, 0.85)


def synth_clock_tick(pitch: float = 1.0) -> np.ndarray:
    t = t_arr(0.055)
    c1 = np.sin(2.0 * math.pi * 1750.0 * pitch * t) * np.exp(-t * 140.0)
    c2 = np.sin(2.0 * math.pi * 380.0 * pitch * t) * np.exp(-t * 90.0) * 0.55
    tr = bp(RNG.standard_normal(len(t)), 2200.0, 6200.0) * np.exp(-t * 240.0) * 0.5
    return norm_peak(c1 + c2 + tr, 0.85)


def synth_pendulum_tick(tock: bool = False) -> np.ndarray:
    t = t_arr(0.32)
    f_body = 112.0 if tock else 138.0
    f_click = 1380.0 if tock else 1680.0
    esc = np.sin(2.0 * math.pi * f_click * t) * np.exp(-t * 120.0) * 0.55
    brass = (np.sin(2.0 * math.pi * f_body * t) + 0.4 * np.sin(2.0 * math.pi * f_body * 2.3 * t)) * np.exp(-t * 18.0)
    tail = bp(RNG.standard_normal(len(t)), 600.0, 2200.0) * np.exp(-t * 15.0) * 0.14
    return norm_peak(esc + brass * 0.75 + tail, 0.88)


def synth_tape_rewind(dur: float = 1.90) -> np.ndarray:
    t = t_arr(dur)
    u = t / dur
    n = RNG.standard_normal(len(t))
    # Swept bandpass + high-speed reverse tape chirp texture
    f_sweep = 480.0 + 2800.0 * np.sin(math.pi * u) ** 1.3
    out = np.zeros_like(t)
    blk = 480
    for i in range(0, len(t), blk):
        hi = min(len(t), i + blk)
        fc = float(f_sweep[i])
        out[i:hi] = bp(n[max(0, i - 1600):hi], fc * 0.6, min(fc * 1.45, 9500.0))[-(hi - i):]
    # Fast spool flutter + modulated tape squeal
    flutter = np.sin(2.0 * math.pi * (920.0 + 420.0 * np.sin(2.0 * math.pi * 11.0 * t)) * t) * 0.18
    env = np.sin(math.pi * u) ** 0.9
    clack = np.zeros_like(t)
    c = synth_stamp_thud(heavy=False) * 0.55
    clack[-min(len(c), len(t)):] = c[:min(len(c), len(t))]
    return norm_peak(out * env + flutter * (env ** 1.5) + clack, 0.88)


def synth_rotary_phone_ring() -> np.ndarray:
    """Classic twin-bell rotary telephone double-ring (0.42s ring, 0.22s pause, 0.42s ring)."""
    dur = 1.15
    t = t_arr(dur)
    bell = (
        np.sin(2.0 * math.pi * 1640.0 * t)
        + 0.85 * np.sin(2.0 * math.pi * 2140.0 * t)
        + 0.45 * np.sin(2.0 * math.pi * 3290.0 * t)
    )
    striker = 0.5 * (1.0 + np.sin(2.0 * math.pi * 22.0 * t))
    w1 = ((t >= 0.0) & (t <= 0.42)).astype(np.float64)
    w2 = ((t >= 0.64) & (t <= 1.06)).astype(np.float64)
    gate = uniform_filter1d(w1 + w2, size=int(0.012 * SR))
    return norm_peak(bell * (0.45 + 0.55 * striker) * gate, 0.85)


def synth_gavel_bang() -> np.ndarray:
    t = t_arr(0.45)
    ph = 2.0 * math.pi * (88.0 * t + 95.0 * (1.0 - np.exp(-22.0 * t)) / 22.0)
    wood = np.sin(ph) * np.exp(-t * 12.0)
    crack = bp(RNG.standard_normal(len(t)), 700.0, 3200.0) * np.exp(-t * 55.0) * 0.85
    room = lp(RNG.standard_normal(len(t)), 1400.0) * np.exp(-t * 9.0) * 0.18
    return norm_peak(wood * 0.9 + crack + room, 0.92)


def synth_breaker_clank() -> np.ndarray:
    t = t_arr(0.75)
    clang = (
        np.sin(2.0 * math.pi * 310.0 * t) * np.exp(-t * 16.0)
        + 0.7 * np.sin(2.0 * math.pi * 645.0 * t) * np.exp(-t * 22.0)
        + 0.4 * np.sin(2.0 * math.pi * 1420.0 * t) * np.exp(-t * 34.0)
    )
    thump = synth_sub_drop(0.75, 78.0, 32.0)
    arc = bp(RNG.standard_normal(len(t)), 2200.0, 7500.0) * np.exp(-t * 11.0) * 0.55
    return norm_peak(clang * 0.7 + thump * 0.85 + arc, 0.92)


def synth_keyboard_burst(n_keys: int = 12, dur: float = 2.0) -> np.ndarray:
    n = int(round(dur * SR))
    out = np.zeros(n, dtype=np.float64)
    times = np.sort(RNG.uniform(0.02, max(0.08, dur - 0.08), size=n_keys))
    for kt in times:
        tk = t_arr(0.045)
        f = RNG.uniform(1400.0, 2600.0)
        key = (
            bp(RNG.standard_normal(len(tk)), 1200.0, 4800.0) * np.exp(-tk * 160.0)
            + 0.4 * np.sin(2.0 * math.pi * f * tk) * np.exp(-tk * 110.0)
            + 0.3 * np.sin(2.0 * math.pi * 240.0 * tk) * np.exp(-tk * 85.0)
        )
        i = int(kt * SR)
        ln = min(len(key), n - i)
        if ln > 0:
            out[i:i + ln] += norm_peak(key, RNG.uniform(0.55, 0.95))[:ln]
    return norm_peak(out, 0.85)


def synth_sonar_ping(freq: float = 1046.5, dur: float = 0.55) -> np.ndarray:
    t = t_arr(dur)
    env = np.minimum(1.0, t / 0.008) * np.exp(-t * 8.0)
    return norm_peak((np.sin(2.0 * math.pi * freq * t) + 0.25 * np.sin(2.0 * math.pi * freq * 2.0 * t)) * env, 0.82)


def synth_heartbeat(double: bool = True) -> np.ndarray:
    def beat(f: float, d: float = 0.24) -> np.ndarray:
        t = t_arr(d)
        ph = 2.0 * math.pi * (34.0 * t + (f - 34.0) * (1.0 - np.exp(-16.0 * t)) / 16.0)
        return np.sin(ph) * np.minimum(1.0, t / 0.012) * np.exp(-t * 14.0)

    b1 = beat(58.0, 0.30)
    if not double:
        return norm_peak(b1, 0.88)
    out = np.zeros(int(0.65 * SR), dtype=np.float64)
    out[:len(b1)] += b1
    b2 = beat(50.0, 0.30) * 0.75
    off = int(0.24 * SR)
    out[off:off + len(b2)] += b2
    return norm_peak(out, 0.88)


def synth_hourglass_whisper(dur: float = 2.6) -> np.ndarray:
    t = t_arr(dur)
    sand = bp(RNG.standard_normal(len(t)), 2600.0, 6800.0)
    shimmer = 0.7 + 0.3 * np.sin(2.0 * math.pi * 6.5 * t)
    env = np.sin(math.pi * t / dur) ** 0.8
    return norm_peak(sand * shimmer * env, 0.72)


def synth_shield_clang(pitch: float = 1.0) -> np.ndarray:
    t = t_arr(0.18)
    sig = (
        np.sin(2.0 * math.pi * 1120.0 * pitch * t) * np.exp(-t * 32.0)
        + 0.7 * np.sin(2.0 * math.pi * 1890.0 * pitch * t) * np.exp(-t * 42.0)
        + 0.45 * np.sin(2.0 * math.pi * 3150.0 * pitch * t) * np.exp(-t * 58.0)
        + bp(RNG.standard_normal(len(t)), 2400.0, 7200.0) * np.exp(-t * 110.0) * 0.6
    )
    return norm_peak(sig, 0.86)


def synth_whisper_blip() -> np.ndarray:
    """Needle-quiet whisper slide + tiny crystalline 70-byte slip blip."""
    dur = 1.65
    t = t_arr(dur)
    air = bp(RNG.standard_normal(len(t)), 1800.0, 4600.0) * np.sin(math.pi * t / dur) ** 1.4 * 0.25
    blip_t = np.maximum(0.0, t - 1.15)
    blip_gate = (t >= 1.15).astype(np.float64)
    blip = np.sin(2.0 * math.pi * 2093.0 * blip_t) * np.exp(-blip_t * 18.0) * blip_gate * 0.55
    return norm_peak(air + blip, 0.75)


def synth_elephant_stomp_trumpet() -> np.ndarray:
    """Deep comical noir boardroom thud + subtle muted brass tuba/trumpet groan."""
    dur = 1.45
    t = t_arr(dur)
    stomp = synth_sub_drop(0.7, 68.0, 28.0)
    out = np.zeros_like(t)
    out[:len(stomp)] += stomp
    # Muted brass groan starting at 0.18s
    bt = np.maximum(0.0, t - 0.18)
    bgate = ((t >= 0.18) & (t <= 1.35)).astype(np.float64)
    f = 225.0 - 55.0 * (bt / 1.15)
    brass = (
        np.sin(2.0 * math.pi * np.cumsum(f) / SR)
        + 0.55 * np.sin(2.0 * math.pi * np.cumsum(2.0 * f) / SR)
        + 0.25 * np.sin(2.0 * math.pi * np.cumsum(3.0 * f) / SR)
    )
    brass = lp(brass, 750.0) * np.sin(math.pi * np.clip(bt / 1.15, 0.0, 1.0)) ** 0.7 * bgate
    return norm_peak(out * 0.8 + brass * 0.52, 0.88)


def synth_pipe_rush(dur: float = 2.4) -> np.ndarray:
    t = t_arr(dur)
    u = t / dur
    w = RNG.standard_normal(len(t))
    rush = bp(w, 320.0, 2600.0) * (np.sin(math.pi * u) ** 0.75)
    low = lp(w, 280.0) * (np.sin(math.pi * u) ** 0.85) * 0.45
    return norm_peak(rush + low, 0.78)


def synth_split_flap(n_flaps: int = 12, dur: float = 2.0) -> np.ndarray:
    n = int(round(dur * SR))
    out = np.zeros(n, dtype=np.float64)
    for k in range(n_flaps):
        kt = (k / max(1, n_flaps - 1)) * (dur - 0.12)
        tk = t_arr(0.04)
        flap = (
            bp(RNG.standard_normal(len(tk)), 700.0, 3200.0) * np.exp(-tk * 130.0)
            + 0.45 * np.sin(2.0 * math.pi * 490.0 * tk) * np.exp(-tk * 85.0)
        )
        i = int(kt * SR)
        ln = min(len(flap), n - i)
        if ln > 0:
            out[i:i + ln] += norm_peak(flap, 0.82)[:ln]
    return norm_peak(out, 0.85)


def synth_telemetry_ticks(n_ticks: int = 16, dur: float = 3.2) -> np.ndarray:
    n = int(round(dur * SR))
    out = np.zeros(n, dtype=np.float64)
    for k in range(n_ticks):
        kt = (k / max(1, n_ticks)) * (dur - 0.05)
        tk = t_arr(0.03)
        f = 1950.0 + (k % 4) * 140.0
        blip = np.sin(2.0 * math.pi * f * tk) * np.exp(-tk * 140.0)
        i = int(kt * SR)
        ln = min(len(blip), n - i)
        if ln > 0:
            out[i:i + ln] += blip[:ln]
    return norm_peak(out, 0.78)


def synth_pneumatic_stamp_arm() -> np.ndarray:
    t = t_arr(0.24)
    hiss = bp(RNG.standard_normal(len(t)), 1800.0, 6200.0) * np.exp(-t * 38.0) * 0.45
    clack = synth_stamp_thud(heavy=True)
    out = np.zeros_like(t)
    out += hiss
    out[:min(len(t), len(clack))] += clack[:min(len(t), len(clack))]
    return norm_peak(out, 0.90)


def synth_klaxon_pulse() -> np.ndarray:
    t = t_arr(0.28)
    env = np.sin(math.pi * t / 0.28) ** 0.7
    sig = np.sin(2.0 * math.pi * 620.0 * t) + 0.45 * np.sin(2.0 * math.pi * 930.0 * t)
    return norm_peak(lp(sig, 1800.0) * env, 0.72)


# ---------------------------------------------------------------------------
# SFX Library Loader & Choreographed Cue Sheet (95+ Moments Across 6 Acts)
# ---------------------------------------------------------------------------
class SfxBank:
    """Lazy-cached decoder for audio/lib/sfx/ assets."""

    def __init__(self):
        manifest = json.loads(SFX_MANIFEST.read_text(encoding='utf-8'))
        self.paths = {a['id']: SFX_LIB_DIR / a['path'] for a in manifest['assets']}
        self.cache: dict[str, np.ndarray] = {}

    def get(self, asset_id: str, trim: bool = True) -> np.ndarray:
        if asset_id not in self.cache:
            x = decode_audio_48k_stereo(self.paths[asset_id])
            if trim:
                x = trim_leading_silence(x)
            self.cache[asset_id] = norm_peak(x, 0.88)
        return self.cache[asset_id]


def build_sfx_track(vo_active_rms: float) -> tuple[np.ndarray, int]:
    """Place 100+ tactile SFX/Foley hits synced to MASTER_STORYBOARD.md and act1/index.html."""
    bank = SfxBank()
    sfx = np.zeros((N_SAMPLES, 2), dtype=np.float64)
    g0 = vo_active_rms  # anchor gain scale to VO active RMS so hits never overpower narration
    hits = 0

    def hit(sig: np.ndarray, t: float, rel_gain: float, pan: float = 0.0) -> None:
        nonlocal hits
        place(sfx, sig, t, gain=g0 * rel_gain, pan=pan)
        hits += 1

    def lib(asset_id: str, t: float, rel_gain: float, pan: float = 0.0, trim: bool = True) -> None:
        hit(bank.get(asset_id, trim=trim), t, rel_gain, pan=pan)

    # ---- ACT 1 (0.00 - 44.33s) ----------------------------------------------
    # 1A Cold Open
    lib('owlish-home-202-paper-stationery-stationery-01', 0.06, 0.65, pan=-0.10)
    lib('kenney-rpg-book-open', 0.12, 0.55, pan=0.05)
    hit(synth_stamp_thud(heavy=True), 0.55, 1.35, pan=0.0)
    lib('kenney-impact-impact-soft-heavy-000', 0.55, 0.80, pan=0.0)

    # 1B Vault Atrium + 10 Pipes (1.50 - 10.02s)
    lib('artisticdude-swishes-swish-4', 1.50, 0.45, pan=-0.15)
    hit(synth_sub_swell(1.05, 36.0, 68.0), 1.50, 0.85, pan=0.0)
    lib('kenney-rpg-door-open-1', 1.85, 0.62, pan=-0.35)
    lib('owlish-home-202-money-money-02', 2.40, 0.42, pan=-0.20)
    lib('owlish-home-202-money-money-07', 3.15, 0.40, pan=0.10)
    lib('kenney-rpg-handle-coins2', 4.30, 0.38, pan=0.25)
    for i in range(10):
        # act1/index.html line 196: pipes open at 6.7 + i * 0.13
        lib('kenney-interface-drop-001' if i % 2 == 0 else 'kenney-interface-select-007',
            6.70 + i * 0.13, 0.32, pan=-0.35 + 0.08 * i)
    hit(synth_pipe_rush(2.2), 7.05, 0.48, pan=0.15)

    # 1C Empty Vault + 20-Min Spin + -$6.3B (10.02 - 15.30s)
    lib('artisticdude-swishes-swish-1', 10.02, 0.42, pan=0.0)
    for k in range(8):
        hit(synth_clock_tick(1.0 + 0.04 * k), 10.22 + k * 0.22, 0.36, pan=0.30)
    lib('kenney-rpg-metal-click', 12.05, 0.45, pan=0.25)
    hit(synth_stamp_thud(heavy=True), 13.20, 1.15, pan=0.10)
    hit(synth_sub_drop(1.25, 78.0, 30.0), 13.20, 1.05, pan=0.0)
    lib('kenney-impact-impact-plate-heavy-000', 13.20, 0.65, pan=0.0)

    # 1D Bedroom + Disabled Withdraw Button (15.30 - 20.54s)
    lib('owlish-home-202-paper-stationery-stationery-19', 15.32, 0.40, pan=-0.25)
    lib('kenney-interface-click-001', 15.72, 0.42, pan=-0.20)
    for tap_t in (17.85, 18.60, 19.35):
        lib('kenney-interface-glass-001', tap_t, 0.48, pan=0.30)
        lib('kenney-interface-error-001', tap_t + 0.02, 0.34, pan=0.30)
    hit(synth_stamp_thud(heavy=False), 18.92, 0.72, pan=0.25)

    # 1E Forensic Audit Office (20.54 - 27.82s)
    lib('artisticdude-swishes-swish-2', 20.54, 0.40, pan=0.0)
    lib('kenney-interface-glass-002', 21.45, 0.32, pan=-0.25)
    lib('owlish-home-202-paper-stationery-stationery-16', 22.10, 0.42, pan=0.0)
    lib('kenney-interface-confirmation-001', 23.60, 0.38, pan=0.30)
    hit(synth_stamp_thud(heavy=False), 26.10, 0.90, pan=0.25)

    # 1F Automated Signing Factory (27.82 - 34.10s)
    lib('artisticdude-swishes-swish-7', 27.82, 0.40, pan=-0.10)
    for k in range(5):
        lib('kenney-interface-tick-004', 28.20 + k * 0.95, 0.24, pan=-0.20 + 0.10 * k)
    hit(synth_pneumatic_stamp_arm(), 29.90, 0.92, pan=0.0)
    hit(synth_pneumatic_stamp_arm(), 31.40, 0.92, pan=0.0)
    lib('kenney-interface-confirmation-002', 31.65, 0.38, pan=0.35)

    # 1G 2-Floor Cutaway + Calendar + Rewind (34.10 - 44.33s)
    lib('kenney-interface-minimize-001', 34.10, 0.38, pan=0.0)
    for m in range(4):
        lib('kenney-rpg-book-flip3' if m % 2 == 0 else 'kenney-rpg-book-flip2',
            34.40 + m * 0.80, 0.48, pan=0.35)
    lib('owlish-home-202-paper-stationery-stationery-23', 38.95, 0.46, pan=0.30)
    lib('kenney-rpg-metal-click', 39.25, 0.38, pan=0.30)
    hit(synth_stamp_thud(heavy=True), 40.10, 0.95, pan=0.25)
    hit(synth_tape_rewind(1.88), 42.40, 1.05, pan=0.0)

    # ---- ACT 2 (44.33 - 96.46s) ----------------------------------------------
    # 2A June Dev Desk
    lib('artisticdude-swishes-swish-4', 44.34, 0.38, pan=0.0)
    hit(synth_keyboard_burst(14, 2.6), 44.75, 0.44, pan=-0.25)
    lib('kenney-interface-select-007', 47.20, 0.34, pan=0.25)
    lib('kenney-interface-click-001', 48.20, 0.48, pan=0.25)

    # 2B Trojan Installer
    lib('kenney-interface-confirmation-003', 53.60, 0.42, pan=0.0)
    lib('kenney-interface-error-003', 55.66, 0.65, pan=0.0)
    lib('kenney-digital-low-down', 55.85, 0.55, pan=0.10)
    hit(synth_stamp_thud(heavy=True), 56.25, 0.90, pan=0.0)

    # 2C Toast -> SOC Catch -> Cable Yank
    lib('bf-cartoon-bounce-bounceyofrankie', 58.72, 0.44, pan=-0.30)
    lib('kenney-impact-impact-bell-heavy-004', 59.10, 0.34, pan=-0.30)
    hit(synth_klaxon_pulse(), 61.55, 0.36, pan=0.0)
    hit(synth_klaxon_pulse(), 62.05, 0.32, pan=0.0)
    lib('kenney-digital-zap1', 66.20, 0.55, pan=0.10)
    lib('kenney-impact-impact-wood-heavy-000', 66.55, 0.72, pan=0.0)

    # 2D Access Wiped / Keys Rotated / Ticket Closed
    for st_t in (68.75, 70.00, 71.25):
        hit(synth_stamp_thud(heavy=True), st_t, 0.92, pan=0.0)
    lib('kenney-rpg-book-close', 72.55, 0.68, pan=0.0)
    lib('kenney-interface-confirmation-004', 72.90, 0.44, pan=0.0)

    # 2E Already Grabbed Map
    lib('owlish-home-202-paper-stationery-stationery-04', 75.55, 0.60, pan=0.0)
    lib('artisticdude-swishes-swish-9', 76.20, 0.44, pan=0.15)
    for b in range(3):
        lib('kenney-rpg-metal-click', 78.60 + b * 0.42, 0.40, pan=-0.25 + b * 0.25)
    for p_i, p_t in enumerate([82.10, 83.10, 84.10, 85.10]):
        lib('owlish-home-202-camera-camera-01' if p_i % 2 == 0 else 'kenney-interface-tick-004',
            p_t, 0.40, pan=-0.30 + p_i * 0.20)

    # 2F Evidence Locker -> Dead Silence Pendulum
    lib('kenney-impact-impact-metal-heavy-000', 88.35, 0.68, pan=-0.20)
    lib('owlish-home-202-keys-locks-door-key-lock-door-06', 89.20, 0.52, pan=-0.15)
    for k in range(5):
        hit(synth_pendulum_tick(tock=(k % 2 == 1)), 91.85 + k * 0.98, 0.78, pan=-0.12 if k % 2 == 0 else 0.12)

    # ---- ACT 3 (96.46 - 170.17s) --------------------------------------------
    # 3A LinkedIn Bait
    lib('kenney-digital-two-tone1', 96.70, 0.42, pan=-0.25)
    lib('kenney-interface-scratch-001', 101.60, 0.48, pan=0.20)
    lib('owlish-home-202-paper-stationery-stationery-10', 105.70, 0.50, pan=-0.20)
    lib('owlish-home-202-paper-stationery-stationery-23', 106.50, 0.46, pan=0.15)

    # 3B HR Video Call + Polaroids
    lib('owlish-home-202-phone-phone2', 110.10, 0.36, pan=0.15)
    lib('kenney-digital-three-tone1', 110.35, 0.32, pan=0.15)
    for c_i in range(4):
        lib('owlish-home-202-camera-camera-01' if c_i % 2 == 0 else 'owlish-home-202-camera-camera-02',
            117.30 + c_i * 0.65, 0.38, pan=-0.30 + 0.20 * c_i)
    lib('kenney-interface-confirmation-002', 124.00, 0.42, pan=0.30)

    # 3C CEO -> Potemkin Warehouse Reveal
    lib('rubberduck-general-100-2-sfx100v2-wood-hit-01', 127.80, 0.48, pan=0.0)
    lib('kenney-impact-impact-wood-heavy-000', 128.80, 0.90, pan=-0.15)
    hit(synth_sub_drop(1.20, 74.0, 29.0), 128.85, 0.95, pan=0.0)
    hit(synth_stamp_thud(heavy=True), 129.65, 0.92, pan=0.0)

    # 3D Take-Home Setup Script
    lib('kenney-interface-click-001', 136.50, 0.56, pan=-0.15)
    lib('kenney-digital-low-down', 139.85, 0.58, pan=0.0)
    lib('artisticdude-swishes-swish-7', 140.10, 0.46, pan=0.0)

    # 3E 3,344 -> 3,414 Bytes (+70 Bytes)
    lib('kenney-rpg-metal-click', 145.20, 0.45, pan=-0.25)
    lib('kenney-digital-phaser-up1', 150.60, 0.34, pan=0.0)
    lib('kenney-impact-impact-metal-medium-000', 153.20, 0.68, pan=0.0)
    lib('kenney-interface-glass-001', 155.40, 0.52, pan=0.25)
    hit(synth_sonar_ping(1318.5, 0.45), 155.55, 0.38, pan=0.25)

    # 3F Endpoint Scan Clear -> Lights Off + Heartbeat
    hit(synth_sonar_ping(987.7, 0.50), 160.20, 0.34, pan=-0.20)
    hit(synth_sonar_ping(987.7, 0.50), 162.10, 0.32, pan=-0.20)
    hit(synth_stamp_thud(heavy=False), 163.40, 0.70, pan=0.0)
    lib('kenney-rpg-book-close', 165.40, 0.52, pan=0.20)
    lib('owlish-home-202-paper-stationery-stationery-30', 166.20, 0.40, pan=0.25)
    lib('rubberduck-general-100-2-sfx100v2-switch-01', 168.00, 0.68, pan=0.0)
    hit(synth_heartbeat(double=True), 168.55, 1.02, pan=0.0)

    # ---- ACT 4 (170.17 - 272.08s) --------------------------------------------
    # 4A Outside Guards -> Already Inside
    lib('kenney-interface-error-001', 171.80, 0.48, pan=-0.30)
    for f_i in range(3):
        lib('kenney-impact-impact-generic-light-000', 176.20 + f_i * 0.48, 0.32, pan=-0.35 + f_i * 0.15)
    lib('owlish-home-202-keys-locks-door-key-lock-door-30', 178.50, 0.55, pan=0.25)

    # 4B Internal AI Tool Bridge
    lib('kenney-interface-tick-002', 180.60, 0.42, pan=-0.25)
    hit(synth_sonar_ping(880.0, 0.45), 186.50, 0.34, pan=0.0)
    lib('kenney-digital-power-up4', 191.50, 0.46, pan=0.15)

    # 4C Jump to Eng #3 & June Eng #1
    lib('ez-boings-bing-01-0', 196.40, 0.34, pan=0.0)
    lib('kenney-digital-phase-jump1', 197.80, 0.36, pan=-0.25)
    lib('kenney-interface-select-001', 199.60, 0.42, pan=0.25)
    lib('owlish-home-202-paper-stationery-stationery-04', 203.40, 0.62, pan=0.20)

    # 4D Deploy Token & 8-Day Patience
    lib('kenney-interface-confirmation-001', 211.30, 0.42, pan=-0.15)
    lib('owlish-home-202-keys-locks-door-key-lock-door-39', 217.50, 0.54, pan=0.20)
    for d in range(8):
        lib('kenney-interface-tick-004', 218.55 + d * 0.55, 0.25, pan=-0.35 + 0.10 * d)

    # 4E Mixer 0.1 ETH Drops & +36H Split-Flap
    for d_i, d_t in enumerate([227.60, 228.85, 230.10]):
        lib('kenney-interface-drop-003', d_t, 0.44, pan=-0.20 + d_i * 0.15)
    hit(synth_split_flap(12, 2.2), 233.10, 0.55, pan=0.25)

    # 4F Container Launch into Withdrawal Core
    hit(synth_keyboard_burst(10, 1.5), 238.80, 0.38, pan=-0.30)
    lib('kenney-impact-impact-metal-heavy-001', 244.40, 0.72, pan=0.0)
    lib('kenney-rpg-metal-latch', 244.75, 0.55, pan=0.0)
    lib('kenney-rpg-door-open-1', 247.20, 0.58, pan=0.25)

    # 4G 50 Pre-Signed Blanks + Nonce Queue Tension
    for b_k in range(18):
        hit(synth_stamp_thud(heavy=False), 255.20 + b_k * 0.32, 0.40, pan=-0.20 + 0.02 * b_k)
    lib('artisticdude-swishes-swish-10', 261.80, 0.52, pan=0.15)
    for g_k in range(12):
        lib('kenney-interface-tick-001', 263.40 + g_k * 0.55, 0.26, pan=0.25)
    hit(synth_sub_swell(1.80, 38.0, 82.0), 270.10, 0.90, pan=0.0)

    # ---- ACT 5 (272.08 - 378.00s) --------------------------------------------
    # 5A Flip the Switch -> 10-Chain Torrent
    hit(synth_breaker_clank(), 272.10, 1.15, pan=0.0)
    lib('kenney-impact-impact-metal-heavy-000', 272.12, 0.80, pan=0.0)
    for c_i in range(5):
        lib('kenney-rpg-handle-coins' if c_i % 2 == 0 else 'kenney-rpg-handle-coins2',
            275.30 + c_i * 1.15, 0.44, pan=-0.35 + 0.17 * c_i)
    hit(synth_pipe_rush(2.6), 276.00, 0.46, pan=0.0)

    # 5B Slip #37 Lock + Self-Emptying ATM + 03:24 Sweep
    lib('kenney-rpg-metal-latch', 283.10, 0.65, pan=-0.10)
    lib('kenney-interface-confirmation-003', 283.25, 0.48, pan=-0.10)
    hit(synth_pipe_rush(2.5), 287.10, 0.45, pan=0.0)
    hit(synth_telemetry_ticks(16, 3.0), 291.20, 0.42, pan=0.25)
    hit(synth_stamp_thud(heavy=True), 298.60, 0.95, pan=0.20)
    hit(synth_sub_drop(1.10, 72.0, 30.0), 298.60, 0.85, pan=0.0)

    # 5C $5,000 Bank Call vs Empty Guard Booth
    hit(synth_rotary_phone_ring(), 304.50, 0.66, pan=-0.40)
    lib('owlish-home-202-phone-phone1', 306.40, 0.36, pan=-0.35)
    lib('kenney-rpg-creak1', 311.20, 0.30, pan=0.35)

    # 5D Freeze Race: Tether / Circle / Ripple / Arbitrum
    hit(synth_klaxon_pulse(), 317.30, 0.40, pan=0.0)
    lib('owlish-home-202-phone-phone2', 319.10, 0.42, pan=-0.20)
    for br_i, br_t in enumerate([323.00, 324.60, 326.20, 327.80]):
        lib('kenney-impact-impact-metal-heavy-001', br_t, 0.72, pan=-0.35 + 0.23 * br_i)
        lib('rubberduck-general-100-2-sfx100v2-switch-02', br_t + 0.02, 0.55, pan=-0.35 + 0.23 * br_i)
    lib('kenney-impact-impact-bell-heavy-002', 330.20, 0.65, pan=0.0)
    lib('owlish-home-202-keys-locks-door-key-lock-door-11', 330.35, 0.52, pan=0.0)

    # 5E Dumping USDT + DeFi Press + 12:10 AM Shears
    hit(synth_keyboard_burst(14, 2.2), 335.00, 0.40, pan=-0.25)
    lib('owlish-home-202-money-money-16', 339.20, 0.42, pan=0.15)
    lib('kenney-impact-impact-punch-heavy-000', 344.60, 0.65, pan=0.0)
    lib('kenney-rpg-handle-coins2', 346.20, 0.46, pan=0.20)
    lib('kenney-digital-laser1', 351.80, 0.38, pan=-0.25)
    lib('kenney-digital-laser4', 353.30, 0.38, pan=0.25)
    lib('kenney-impact-impact-metal-heavy-002', 356.20, 0.85, pan=0.0)
    hit(synth_breaker_clank(), 356.25, 0.75, pan=0.0)

    # 5F Smoke Clears + Unfreezable Buttons
    lib('artisticdude-swishes-swish-1', 359.15, 0.42, pan=0.0)
    lib('kenney-impact-impact-bell-heavy-004', 364.60, 0.40, pan=0.30)
    for dead_i, dead_t in enumerate([371.40, 372.95, 374.50]):
        lib('kenney-interface-bong-001', dead_t, 0.48, pan=-0.25 + 0.25 * dead_i)
        lib('kenney-interface-error-005', dead_t + 0.03, 0.34, pan=-0.25 + 0.25 * dead_i)

    # ---- ACT 6 (378.00 - 483.50s) --------------------------------------------
    # 6A Withdrawals Live + Treasury Fills $6.3B Hole
    lib('kenney-interface-confirmation-002', 378.20, 0.48, pan=-0.20)
    lib('owlish-home-202-money-money-25', 381.40, 0.44, pan=0.10)
    lib('kenney-rpg-handle-coins', 387.80, 0.50, pan=0.0)
    lib('kenney-impact-impact-plate-heavy-000', 392.80, 0.65, pan=0.0)
    hit(synth_stamp_thud(heavy=True), 393.50, 0.88, pan=0.0)

    # 6B DOJ Gavel + DPRK Dossier + 4x Tower
    hit(synth_gavel_bang(), 396.50, 1.05, pan=-0.15)
    hit(synth_stamp_thud(heavy=False), 398.10, 0.78, pan=0.15)
    lib('owlish-home-202-camera-camera-02', 403.50, 0.48, pan=0.0)
    hit(synth_sub_swell(1.6, 36.0, 74.0), 406.80, 0.78, pan=0.15)

    # 6C "Not quite." Stamp Crack + Elephant in the Room
    lib('kenney-rpg-book-close', 413.50, 0.56, pan=0.0)
    lib('bf-cartoon-bounce-bounceyofrankie', 417.45, 0.52, pan=0.0)
    lib('kenney-impact-impact-glass-heavy-000', 417.65, 0.68, pan=0.0)
    hit(synth_elephant_stomp_trumpet(), 419.95, 1.05, pan=0.0)

    # 6D Unanswered Questions + Black Redaction Bars
    lib('kenney-interface-scratch-001', 426.40, 0.42, pan=-0.20)
    hit(synth_hourglass_whisper(2.6), 427.60, 0.42, pan=0.25)
    hit(synth_stamp_thud(heavy=False), 432.00, 0.76, pan=0.20)
    for red_t in (437.20, 443.40, 450.20):
        hit(synth_stamp_thud(heavy=True), red_t, 0.86, pan=0.0)
        lib('kenney-interface-question-001', red_t + 0.16, 0.34, pan=0.25)

    # 6E 57 Attempts Deflected -> Needle-Quiet 70-Byte Whisper
    lib('kenney-interface-glass-002', 452.80, 0.42, pan=-0.20)
    lib('kenney-interface-click-003', 457.50, 0.42, pan=0.0)
    for k in range(19):
        # 19 crisp metallic shield pings representing waves of 57 stopped attacks (460.8 - 472.3s)
        t_clang = 460.80 + k * 0.60 + (0.12 if k % 3 == 1 else 0.0)
        hit(synth_shield_clang(0.88 + 0.03 * (k % 5)), t_clang, 0.32, pan=-0.35 + 0.04 * k)
    hit(synth_whisper_blip(), 474.20, 0.62, pan=0.0)

    # 6F Closing Dossier Outro (478.30 - 483.50s)
    hit(synth_stamp_thud(heavy=True), 479.40, 1.20, pan=0.0)
    lib('owlish-home-202-paper-stationery-stationery-19', 481.20, 0.32, pan=0.0)

    return sfx, hits


# ---------------------------------------------------------------------------
# Master Bus Assembly, Normalization & Verification
# ---------------------------------------------------------------------------
def measure_ebur128(wav_path: Path) -> tuple[float, float, float]:
    res = subprocess.run(
        ['ffmpeg', '-hide_banner', '-nostats', '-i', str(wav_path), '-af', 'ebur128=peak=true', '-f', 'null', '-'],
        capture_output=True,
        text=True,
        check=True,
    )
    i_val = lra_val = pk_val = None
    for line in res.stderr.splitlines():
        s = line.strip()
        if s.startswith('I:'):
            i_val = float(s.split()[1])
        elif s.startswith('LRA:'):
            lra_val = float(s.split()[1])
        elif s.startswith('Peak:'):
            pk_val = float(s.split()[1])
    assert i_val is not None and pk_val is not None, f'Failed to parse ebur128 output:\n{res.stderr[-600:]}'
    return i_val, lra_val or 0.0, pk_val


def write_wav_s16(path: Path, stereo: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = np.clip(np.round(stereo * 32767.0), -32768, 32767).astype(np.int16)
    with wave.open(str(path), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(pcm.tobytes())


def main() -> None:
    print('1. Loading & conditioning VO (binance-hacking.wav -> 48kHz @ +1.500s)...')
    vo_mono, vo_active_rms = load_and_condition_vo()
    vo_bus = np.zeros((N_SAMPLES, 2), dtype=np.float64)
    place(vo_bus, vo_mono, VO_OFFSET_SEC, gain=1.0, pan=0.0)

    print(f'   VO active RMS: {vo_active_rms:.4f} ({20*math.log10(vo_active_rms):.2f} dBFS)')
    print('2. Computing RMS sidechain ducking envelope (attack=80ms, release=350ms)...')
    duck_env = compute_sidechain_duck_envelope(vo_bus[:, 0], vo_active_rms)
    # Lift closing outro gently between 478.55s and 481.20s so final cadence blooms naturally
    o0, o1 = int(478.55 * SR), int(481.50 * SR)
    duck_env[o0:o1] = np.maximum(duck_env[o0:o1], 10.0 ** (-12.5 / 20.0))

    print('3. Building 7-track CC-BY-4.0 music bed with silence pockets & fades...')
    music_raw = build_music_bed(vo_active_rms)
    music_bus = music_raw * duck_env[:, None]

    print('4. Placing 100+ tactile library SFX & documentary Foley hits...')
    sfx_bus, sfx_hits = build_sfx_track(vo_active_rms)
    print(f'   Placed {sfx_hits} SFX/Foley events across 483.500s.')

    # Combine stems and calibrate cleanly to -15.5 LUFS with soft 0.85 peak limiter
    raw_mix = vo_bus + music_bus + sfx_bus
    # 10ms fade-in at 0.00s and 200ms zero-guard fade-out at 483.30-483.50s
    raw_mix[:int(0.010 * SR)] *= np.linspace(0.0, 1.0, int(0.010 * SR))[:, None]
    raw_mix[-int(0.200 * SR):] *= np.linspace(1.0, 0.0, int(0.200 * SR))[:, None]

    tmp_wav = OUT_WAV.with_suffix('.pre_norm.wav')
    write_wav_s16(tmp_wav, lookahead_limit_stereo(raw_mix, ceil=0.92))
    meas_i, meas_lra, meas_pk = measure_ebur128(tmp_wav)
    tmp_wav.unlink()

    target_lufs = -15.5
    trim_db = target_lufs - meas_i
    trim_lin = 10.0 ** (trim_db / 20.0)
    print(f'5. Pre-norm measured I={meas_i:.2f} LUFS (trim {trim_db:+.2f} dB -> {target_lufs} LUFS)')

    final_mix = lookahead_limit_stereo(raw_mix * trim_lin, ceil=0.85, look_sec=0.005)
    assert len(final_mix) == N_SAMPLES, f'Sample count mismatch: {len(final_mix)} != {N_SAMPLES}'
    write_wav_s16(OUT_WAV, final_mix)

    fin_i, fin_lra, fin_pk = measure_ebur128(OUT_WAV)
    sample_pk = float(np.max(np.abs(final_mix)))
    print(
        f'Wrote {OUT_WAV}\n'
        f'  Samples: {N_SAMPLES} ({N_SAMPLES / SR:.4f}s @ {SR} Hz stereo)\n'
        f'  Loudness: I={fin_i:.2f} LUFS | LRA={fin_lra:.2f} LU | TruePeak={fin_pk:.2f} dBTP | SamplePeak={sample_pk:.4f}'
    )


if __name__ == '__main__':
    main()
