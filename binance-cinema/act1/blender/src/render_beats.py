import sys
import os
import argparse

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

OUT_DIR = "/home/devuser/projects/rea-video/binance-cinema/act1/blender"

from beats_1_to_3 import build_beat01, build_beat02, build_beat03
from beats_7_8_10 import build_beat07, build_beat08, build_beat10

BEATS = {
    "1": ("beat01_monolith.png", build_beat01),
    "2": ("beat02_overhead_nodes.png", build_beat02),
    "3": ("beat03_void_ledger.png", build_beat03),
    "7": ("beat07_padlock.png", build_beat07),
    "8": ("beat08_stamp.png", build_beat08),
    "10": ("beat10_corridor.png", build_beat10),
}


def main():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = []

    parser = argparse.ArgumentParser()
    parser.add_argument("--beat", default="all", help="Beat ID (1,2,3,7,8,10 or all)")
    args = parser.parse_args(argv)

    os.makedirs(OUT_DIR, exist_ok=True)
    targets = list(BEATS.keys()) if args.beat == "all" else [args.beat]

    for b in targets:
        if b not in BEATS:
            print(f"Unknown beat: {b}")
            continue
        filename, builder = BEATS[b]
        out_path = os.path.join(OUT_DIR, filename)
        print(f"=== Building Beat {b} -> {out_path} ===")
        scene = builder()
        scene.render.filepath = out_path
        import bpy
        bpy.ops.render.render(write_still=True)
        print(f"=== Finished Beat {b}: {out_path} ===")


if __name__ == "__main__":
    main()
