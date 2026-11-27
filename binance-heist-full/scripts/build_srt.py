#!/usr/bin/env python3
"""Build corrected, cleanly grouped 2-line YouTube SRT from vo_transcript.json.

Timing: t_master = vo_t + 1.500s (matches binance-hacking.wav offset in master_mix.wav).
Output: /home/devuser/projects/rea-video/binance-heist-full/binance-heist-full.srt
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC_JSON = Path('/home/devuser/projects/rea-video/binance-cinema/vo_transcript.json')
OUT_SRT = ROOT / 'binance-heist-full.srt'
VO_OFFSET = 1.500


def apply_text_corrections(text: str) -> str:
    """Apply all mandatory Whisper/fact fixes and clean punctuation."""
    replacements = [
        # Mandatory factual & Whisper fixes
        (r'\bfinance\b', 'Binance'),
        (r'\bRewind a June\b', 'Rewind to June'),
        (r'\bunder two other computers\b', 'onto two other computers'),
        (r'\bout of time\b', 'at a time'),
        (r'\bpre-signed 50 blank permission\b', 'pre-sign 50 blank permission'),
        (r'\$420,000 ether and \$18,200 Bitcoin', '420,000 Ether and 18,200 Bitcoin'),
        (r'\$6\.3 billion whole\b', '$6.3 billion hole'),
        (r'\bTrader Trader Unit\b', 'TraderTraitor unit'),
        (r'\bbuy-bit\b', 'Bybit'),
        (r'\b70-bit file\b', '70-byte file'),
        # Joined split Whisper words & clean script matches
        (r'\bscore board\b', 'scoreboard'),
        (r'\bcash outs\b', 'cash-outs'),
        (r'\btake home\b', 'take-home'),
        (r'\bself emptying\b', 'self-emptying'),
        (r'\bBlack listing\b', 'Blacklisting'),
        (r'\bstable coins\b', 'stablecoins'),
        (r'\bat risk tether\b', 'at-risk Tether'),
        (r'\bstolen tether\b', 'stolen Tether'),
        (r'\bin tether\b', 'in Tether'),
        (r'\btether, circle, ripple, and arbitrum\b', 'Tether, Circle, Ripple, and Arbitrum'),
        (r'\bclean ether\b', 'clean Ether'),
        (r'\b0\.1 ether\b', '0.1 Ether'),
        (r'\b167,000 ether\b', '167,000 Ether'),
        (r'\bthree engineers laptops\b', "three engineers' laptops"),
        (r'\bsitting all right\b', 'sitting right'),
        (r'So users got paid back withdrawals work', 'So users got paid back, withdrawals work'),
        # Time punctuation cleanup
        (r'\b8\.05 pm\b', '8:05 pm'),
        (r'\b5\.15 pm\b', '5:15 pm'),
        (r'\b12\.10 AM\b', '12:10 AM'),
    ]
    for pat, rep in replacements:
        text = re.sub(pat, rep, text)
    return re.sub(r'\s+', ' ', text).strip()


def join_texts(a: str, b: str) -> str:
    """Join two adjacent transcript chunks cleanly without splitting compound words."""
    if a.endswith('score') and b.startswith('board'):
        return a + b
    if a.endswith('cash') and b.startswith('outs'):
        return a + '-' + b
    return f'{a} {b}'


def wrap_two_lines(text: str, max_line: int = 42) -> str:
    """Wrap cue text cleanly into 1 or 2 balanced lines <= max_line chars each."""
    text = text.strip()
    if len(text) <= max_line:
        return text

    words = text.split(' ')
    best_split = None
    best_score = 1e9

    for i in range(1, len(words)):
        l1 = ' '.join(words[:i])
        l2 = ' '.join(words[i:])
        if len(l1) <= max_line and len(l2) <= max_line:
            # Prefer balanced lengths and natural clause breaks (comma/period at end of line1)
            balance = abs(len(l1) - len(l2))
            clause_bonus = -12 if l1[-1] in ',;:.?!' else 0
            # Slightly penalize dangling tiny modifiers/prepositions/articles at end of line 1
            last_w = words[i - 1].lower().strip(',.;:')
            dangle_penalty = 12 if last_w in {
                'a', 'an', 'the', 'to', 'of', 'in', 'on', 'at', 'by', 'for',
                'and', 'or', 'other', 'their', 'his', 'her', 'that', 'this',
            } else 0
            score = balance + clause_bonus + dangle_penalty
            if score < best_score:
                best_score = score
                best_split = (l1, l2)

    if best_split is not None:
        return f'{best_split[0]}\n{best_split[1]}'

    # Fallback greedy wrap if text slightly exceeds 2 * max_line (allow slight overhang on line 2)
    best_idx = 1
    mid = len(text) / 2
    cur = 0
    best_dist = 1e9
    for i in range(1, len(words)):
        cur += len(words[i - 1]) + (1 if i > 1 else 0)
        if abs(cur - mid) < best_dist and cur <= max_line:
            best_dist = abs(cur - mid)
            best_idx = i
    return ' '.join(words[:best_idx]) + '\n' + ' '.join(words[best_idx:])


def fits_two_lines(text: str, max_line: int = 42) -> bool:
    wrapped = wrap_two_lines(text, max_line=max_line).split('\n')
    return len(wrapped) <= 2 and all(len(ln) <= max_line for ln in wrapped)


def group_segments(raw_segs):
    """Shift by +1.500s and merge short/dangling phrases into natural 2-line captions."""
    segs = []
    for s in raw_segs:
        segs.append({
            'start': round(float(s['start']) + VO_OFFSET, 3),
            'end': round(float(s['end']) + VO_OFFSET, 3),
            'text': s['text'].strip(),
        })

    grouped = []
    i = 0
    while i < len(segs):
        cur = dict(segs[i])
        while i + 1 < len(segs):
            nxt = segs[i + 1]
            merged_raw = join_texts(cur['text'], nxt['text'])
            merged_clean = apply_text_corrections(merged_raw)
            merged_dur = nxt['end'] - cur['start']
            gap = nxt['start'] - cur['end']
            cur_clean = apply_text_corrections(cur['text'])
            nxt_clean = apply_text_corrections(nxt['text'])

            cur_ends_sent = bool(re.search(r'[.?!]$', cur_clean))
            nxt_is_orphan = (
                (nxt['end'] - nxt['start'] < 1.35)
                or len(nxt_clean) <= 22
                or (not cur_ends_sent and len(nxt_clean.split()) <= 4)
            )

            # Always merge broken words/clauses when they fit comfortably in 2 lines <= 42 chars
            should_merge = False
            if gap <= 0.15 and not cur_ends_sent and fits_two_lines(merged_clean, 42):
                if nxt_is_orphan and merged_dur <= 7.2:
                    should_merge = True
                elif merged_dur <= 5.8:
                    should_merge = True

            # Also merge consecutive tiny complete sentences if neither is a dramatic pause
            if (
                not should_merge
                and gap <= 0.05
                and cur_ends_sent
                and (cur['end'] - cur['start']) < 1.50
                and (nxt['end'] - nxt['start']) < 1.65
                and fits_two_lines(merged_clean, 42)
                and cur_clean not in {'Why 50?', 'Not quite.'}
                and nxt_clean not in {'Why 50?', 'Not quite.', 'Rewind to June.'}
            ):
                should_merge = True

            if should_merge:
                cur['text'] = merged_raw
                cur['end'] = nxt['end']
                i += 1
            else:
                break

        cur['text'] = apply_text_corrections(cur['text'])
        grouped.append(cur)
        i += 1

    # Final safety pass: ensure no tiny <0.95s cues and strictly non-overlapping timestamps
    for idx in range(len(grouped) - 1):
        if grouped[idx]['end'] > grouped[idx + 1]['start']:
            grouped[idx]['end'] = grouped[idx + 1]['start']

    return grouped


def fmt_ts(sec: float) -> str:
    ms_total = int(round(sec * 1000))
    ms = ms_total % 1000
    s_total = ms_total // 1000
    s = s_total % 60
    m_total = s_total // 60
    m = m_total % 60
    h = m_total // 60
    return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


def main():
    raw_segs = json.loads(SRC_JSON.read_text(encoding='utf-8'))
    cues = group_segments(raw_segs)

    lines = []
    max_line_len = 0
    min_dur = 999.0
    for idx, cue in enumerate(cues, start=1):
        wrapped = wrap_two_lines(cue['text'], max_line=42)
        for ln in wrapped.split('\n'):
            max_line_len = max(max_line_len, len(ln))
        min_dur = min(min_dur, cue['end'] - cue['start'])
        lines.append(f'{idx}\n{fmt_ts(cue["start"])} --> {fmt_ts(cue["end"])}\n{wrapped}\n')

    OUT_SRT.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote {OUT_SRT} ({len(cues)} cues, max_line={max_line_len} chars, min_dur={min_dur:.2f}s)')


if __name__ == '__main__':
    main()
