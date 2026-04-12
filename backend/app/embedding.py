"""Embedding functions."""
from __future__ import annotations

import numpy as np
from sklearn.preprocessing import StandardScaler
import umap


def embed_3d(
    features: np.ndarray,
    n_neighbors: int = 15,
    min_dist: float = 0.7,
    random_state: int = 42,
) -> np.ndarray:
    """Create a (per recording) 3D embedding with UMAP. Return (T, 3) coords."""
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    # cap nr of neighbors so short clips still fit
    effective_nn = max(2, min(n_neighbors, scaled.shape[0] - 1))

    emb = umap.UMAP(
        n_components=3,
        n_neighbors=effective_nn,
        min_dist=min_dist,
        metric="euclidean",
        random_state=random_state,
    )
    return emb.fit_transform(scaled).astype(np.float32)


def ema_smooth(coords: np.ndarray, alpha: float = 0.3) -> np.ndarray:
    """Exponential Moving Average (EMA) smoothing function."""
    smoothed = np.empty_like(coords)
    smoothed[0] = coords[0]
    for i in range(1, len(coords)):
        # EMA = a*P(t) + (1-a) * EMA(t-1)
        smoothed[i] = alpha * coords[i] + (1 - alpha) * smoothed[i - 1]
    return smoothed


def normalize_to_unit_cube(coords: np.ndarray) -> np.ndarray:
    """Normalize on centroid. Largest axis will span [-1, 1]."""
    centered = coords - coords.mean(axis=0, keepdims=True)
    max_abs = np.abs(centered).max()
    if max_abs < 1e-9: return centered
    return centered / max_abs
