"""Per-frame audio feature extraction using librosa."""
from __future__ import annotations

import numpy as np
import librosa

# Analysis config.
SAMPLE_RATE = 22050
N_FFT = 1024
HOP_LENGTH = 512
N_MELS = 40
N_MFCC = 13


def extract_features(y: np.ndarray, sr: int = SAMPLE_RATE) -> dict:
    """Compute a dict of per-frame feature arrays from a mono waveform.
    Returns features aligned on the same frame axis (T frames). The stacked
    feature matrix has shape (T, D) where D = N_MELS + N_MFCC + 5.
    """
    stft = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH))

    mel = librosa.feature.melspectrogram(S=stft ** 2, sr=sr, n_mels=N_MELS, n_fft=N_FFT, hop_length=HOP_LENGTH)
    log_mel = librosa.power_to_db(mel, ref=np.max)

    mfcc = librosa.feature.mfcc(S=log_mel, n_mfcc=N_MFCC)

    centroid = librosa.feature.spectral_centroid(S=stft, sr=sr, hop_length=HOP_LENGTH)
    rolloff = librosa.feature.spectral_rolloff(S=stft, sr=sr, hop_length=HOP_LENGTH)
    bandwidth = librosa.feature.spectral_bandwidth(S=stft, sr=sr, hop_length=HOP_LENGTH)
    rms = librosa.feature.rms(S=stft, frame_length=N_FFT, hop_length=HOP_LENGTH)

    # spectral novelty: frame-to-frame flux (positive changes in log-mel)
    flux = np.diff(log_mel, axis=1, prepend=log_mel[:, :1])
    novelty = np.maximum(flux, 0).sum(axis=0, keepdims=True)

    # stack to (T, D)
    stacked = np.concatenate(
        [log_mel, mfcc, centroid, rolloff, bandwidth, rms, novelty], axis=0
    ).T.astype(np.float32)

    # expose auxiliary per-frame signals used for render metadata
    aux = {
        "rms": rms[0].astype(np.float32),
        "centroid_hz": centroid[0].astype(np.float32),
        "novelty": novelty[0].astype(np.float32),
    }
    return {"features": stacked, "aux": aux}


def frame_times(n_frames: int, sr: int = SAMPLE_RATE, hop_length: int = HOP_LENGTH) -> np.ndarray:
    """Return start time in seconds for each frame."""
    return (np.arange(n_frames) * hop_length / sr).astype(np.float32)
