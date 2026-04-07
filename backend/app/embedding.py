"""3D embedding via StandardScaler + UMAP + temporal smoothing."""
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
    """Fit a per-recording scaler + UMAP (in 3D) and return (T, 3) coords."""
    scaler = StandardScaler()
    scaled = scaler.fit_transform(features)

    # cap nr of neighbors so short clips still fit.
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
    """Exponential moving average (EMA) along the time axis, seeded with coords[0]."""
    smoothed = np.empty_like(coords)
    smoothed[0] = coords[0]
    for i in range(1, len(coords)):
        smoothed[i] = alpha * coords[i] + (1 - alpha) * smoothed[i - 1]
    return smoothed


def normalize_to_unit_cube(coords: np.ndarray) -> np.ndarray:
    """Center on centroid and scale so the largest axis spans [-1, 1]."""
    centered = coords - coords.mean(axis=0, keepdims=True)
    max_abs = np.abs(centered).max()
    if max_abs < 1e-9:
        return centered
    return centered / max_abs
