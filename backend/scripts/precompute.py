"""CLI: compute and cache 3D embedding JSON for one or more audio files.

Usage:
    python -m backend.scripts.precompute <audio_path> [<audio_path> ...]
    python -m backend.scripts.precompute --all
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# run as a script without installing the package:
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.app.pipeline import load_or_compute  # noqa: E402

AUDIO_EXTS = {".flac", ".wav", ".mp3", ".ogg"}


def iter_audio(data_dir: Path):
    for p in sorted(data_dir.rglob("*")):
        if p.suffix.lower() in AUDIO_EXTS:
            yield p


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path)
    parser.add_argument("--all", action="store_true", help="process every audio file under --data-dir")
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("DATA_DIR", "data/songs")))
    parser.add_argument("--cache-dir", type=Path, default=Path(os.environ.get("CACHE_DIR", "cache")))
    args = parser.parse_args()

    if args.all: targets = list(iter_audio(args.data_dir))
    else: targets = args.paths
    if not targets: parser.error("provide audio paths or --all")

    for i, path in enumerate(targets, 1):
        t0 = time.time()
        payload = load_or_compute(path, args.cache_dir)
        dt = time.time() - t0
        print(
            f"[{i}/{len(targets)}] {path.name}: "
            f"{payload['n_frames']} frames, {payload['duration_seconds']:.1f}s audio, {dt:.1f}s compute"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
