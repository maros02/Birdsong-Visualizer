"""Feature extraction functions."""
from __future__ import annotations

import numpy as np
import librosa

# config
SAMPLE_RATE = 22050 # Hz
N_FFT = 1024 # FFT window size (in samples), ~46ms
HOP_LENGTH = 512 # samples between subsequent frames
N_MELS = 40 # Mel-frequency filter banks
N_MFCC = 13 # MFCCs extracted from log-Mel spectrogram


def extract_features(y: np.ndarray, sr: int = SAMPLE_RATE) -> dict:
    """Extract audio features per frame. Returns shape (T, D)."""

    # magnitude spectrogram
    stft = np.abs(librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH))

    # mel spectrogram + MFCCs
    mel = librosa.feature.melspectrogram(S=stft ** 2, sr=sr, n_mels=N_MELS, n_fft=N_FFT, hop_length=HOP_LENGTH)
    log_mel = librosa.power_to_db(mel, ref=np.max)
    mfcc = librosa.feature.mfcc(S=log_mel, n_mfcc=N_MFCC)

    # scalar spectral descriptors
    centroid = librosa.feature.spectral_centroid(S=stft, sr=sr, hop_length=HOP_LENGTH)
    rolloff = librosa.feature.spectral_rolloff(S=stft, sr=sr, hop_length=HOP_LENGTH)
    bandwidth = librosa.feature.spectral_bandwidth(S=stft, sr=sr, hop_length=HOP_LENGTH)
    rms = librosa.feature.rms(S=stft, frame_length=N_FFT, hop_length=HOP_LENGTH)

    # spectral novelty: sum of positive frame-to-frame changes in log-mel
    flux = np.diff(log_mel, axis=1, prepend=log_mel[:, :1])
    novelty = np.maximum(flux, 0).sum(axis=0, keepdims=True)

    # (T, D)
    stacked = np.concatenate(
        [log_mel, mfcc, centroid, rolloff, bandwidth, rms, novelty], axis=0
    ).T.astype(np.float32)

    # auxiliary signals for renderer
    aux = {
        "rms": rms[0].astype(np.float32),
        "centroid_hz": centroid[0].astype(np.float32),
        "novelty": novelty[0].astype(np.float32),
    }
    return {"features": stacked, "aux": aux}


def frame_times(n_frames: int, sr: int = SAMPLE_RATE, hop_length: int = HOP_LENGTH) -> np.ndarray:
    """Return start time (s) per frame."""
    return (np.arange(n_frames) * hop_length / sr).astype(np.float32)
