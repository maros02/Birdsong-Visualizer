"""End-to-end pipeline: audio file to embedding JSON."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import librosa
import numpy as np

from .features import SAMPLE_RATE, HOP_LENGTH, extract_features, frame_times
from .embedding import embed_3d, ema_smooth, normalize_to_unit_cube

PIPELINE_VERSION = "1"


def _hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def cache_key(audio_path: Path) -> str:
    return f"{audio_path.stem}_{_hash_file(audio_path)}_v{PIPELINE_VERSION}"


def run_pipeline(audio_path: Path, ema_alpha: float = 0.3) -> dict[str, Any]:
    """Load audio, extract features, embed to 3D, smooth, return payload."""
    y, sr = librosa.load(audio_path, sr=SAMPLE_RATE, mono=True)

    feats = extract_features(y, sr=sr)
    coords = embed_3d(feats["features"])
    coords = ema_smooth(coords, alpha=ema_alpha)
    coords = normalize_to_unit_cube(coords)

    times = frame_times(coords.shape[0], sr=sr, hop_length=HOP_LENGTH)

    aux = feats["aux"]
    # normalize (aux) signals to [0, 1]
    def norm01(a: np.ndarray) -> np.ndarray:
        lo, hi = float(a.min()), float(a.max())
        if hi - lo < 1e-9:
            return np.zeros_like(a)
        return ((a - lo) / (hi - lo)).astype(np.float32)

    rms_n = norm01(aux["rms"])
    centroid_n = norm01(aux["centroid_hz"])
    novelty_n = norm01(aux["novelty"])

    return {
        "recording_id": audio_path.stem,
        "sample_rate": int(sr),
        "hop_length": int(HOP_LENGTH),
        "hop_seconds": float(HOP_LENGTH / sr),
        "duration_seconds": float(len(y) / sr),
        "n_frames": int(coords.shape[0]),
        "pipeline_version": PIPELINE_VERSION,
        "frames": {
            "t": times.tolist(),
            "xyz": coords.tolist(),
            "rms": rms_n.tolist(),
            "centroid": centroid_n.tolist(),
            "novelty": novelty_n.tolist(),
            "centroid_hz": aux["centroid_hz"].tolist(),
        },
    }


def load_or_compute(audio_path: Path, cache_dir: Path) -> dict[str, Any]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    key = cache_key(audio_path)
    cache_file = cache_dir / f"{key}.json"
    if cache_file.exists():
        with cache_file.open("r", encoding="utf-8") as f:
            return json.load(f)
    payload = run_pipeline(audio_path)
    with cache_file.open("w", encoding="utf-8") as f:
        json.dump(payload, f)
    return payload
