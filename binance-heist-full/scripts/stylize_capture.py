import os
import glob
import numpy as np
from PIL import Image, ImageDraw

RAW_DIR = '/home/devuser/projects/rea-video/binance-heist-full/captures/_raw'
OUT_DIR = '/home/devuser/projects/rea-video/binance-heist-full/captures'


def halftone_dossier_stylize(src_path: str, dst_path: str, seed: int = 1):
    im = Image.open(src_path).convert('RGBA')
    w, h = im.size
    arr = np.array(im, dtype=np.float32)

    rng = np.random.default_rng(seed)

    # 1. Risograph paper tooth stipple grain (subtle salt-and-pepper tooth across fills like #boil grain)
    noise = rng.random((h, w))
    # Light paper specks across mid-dark areas + ink tooth across bright areas
    lum = (0.299 * arr[..., 0] + 0.587 * arr[..., 1] + 0.114 * arr[..., 2]) / 255.0

    # Subtle paper stipple punch-outs on saturated/dark blocks (clean Act-1 print tooth!)
    paper_speck = (noise < 0.032) & (lum < 0.85)
    arr[paper_speck, 0] = arr[paper_speck, 0] * 0.72 + 244 * 0.28
    arr[paper_speck, 1] = arr[paper_speck, 1] * 0.72 + 236 * 0.28
    arr[paper_speck, 2] = arr[paper_speck, 2] * 0.72 + 221 * 0.28

    # Faint dark ink specks in light paper fields
    ink_speck = (noise > 0.972) & (lum >= 0.85)
    arr[ink_speck, 0] = arr[ink_speck, 0] * 0.78 + 29 * 0.22
    arr[ink_speck, 1] = arr[ink_speck, 1] * 0.78 + 35 * 0.22
    arr[ink_speck, 2] = arr[ink_speck, 2] * 0.78 + 64 * 0.22

    # 2. Subtle rotated Ben-Day corner dot vignette overlay (additive print feel, keeps text razor sharp)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    ang = np.deg2rad(18.0)
    u = xx * np.cos(ang) - yy * np.sin(ang)
    v = xx * np.sin(ang) + yy * np.cos(ang)
    step = 18.0
    du = ((u % step) - step * 0.5)
    dv = ((v % step) - step * 0.5)
    dist = np.hypot(du, dv)

    # Gentle radial edge screening near margins so the document looks offset-printed
    edge_d = np.hypot((xx - w * 0.5) / (w * 0.52), (yy - h * 0.5) / (h * 0.52))
    dot_r = np.clip((edge_d - 0.55) * 5.2, 0.0, 4.0)
    in_dot = dist < dot_r
    arr[in_dot, 0] = arr[in_dot, 0] * 0.88 + 46 * 0.12
    arr[in_dot, 1] = arr[in_dot, 1] * 0.88 + 85 * 0.12
    arr[in_dot, 2] = arr[in_dot, 2] * 0.88 + 214 * 0.12

    # 3. Slight warm archive paper vignette at borders
    vig = np.clip(1.0 - np.clip(edge_d - 0.75, 0.0, 0.6) * 0.16, 0.86, 1.0)[..., None]
    arr[..., :3] = np.clip(arr[..., :3] * vig, 0, 255)

    out = Image.fromarray(arr.astype(np.uint8), 'RGBA')
    out.save(dst_path)
    print(f'Stylized: {dst_path} ({w}x{h})')


def main():
    files = sorted(glob.glob(os.path.join(RAW_DIR, 'cap_*.png')))
    for idx, f in enumerate(files, 1):
        name = os.path.basename(f)
        halftone_dossier_stylize(f, os.path.join(OUT_DIR, name), seed=100 + idx)


if __name__ == '__main__':
    main()
