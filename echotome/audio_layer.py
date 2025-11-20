from __future__ import annotations

from pathlib import Path
from typing import Tuple

import numpy as np
import soundfile as sf


def load_audio_mono(
    path: Path,
    target_sample_rate: int,
) -> Tuple[np.ndarray, int]:
    """
    Load an audio file and return mono float32 samples at target_sample_rate.
    """
    data, sr = sf.read(str(path), always_2d=True)
    # Average channels to mono
    mono = data.mean(axis=1).astype("float32")

    if sr != target_sample_rate:
        # Simple deterministic resample using linear interpolation
        mono = _resample_linear(mono, sr, target_sample_rate)
        sr = target_sample_rate

    return mono, sr


def _resample_linear(
    samples: np.ndarray,
    sr_in: int,
    sr_out: int,
) -> np.ndarray:
    """
    Very simple linear resampling (deterministic, CPU-cheap).
    """
    if sr_in == sr_out:
        return samples

    ratio = sr_out / sr_in
    new_length = int(len(samples) * ratio)
    x_old = np.linspace(0.0, 1.0, num=len(samples), endpoint=False)
    x_new = np.linspace(0.0, 1.0, num=new_length, endpoint=False)
    return np.interp(x_new, x_old, samples).astype("float32")


def compute_spectral_map(
    samples: np.ndarray,
    frame_size: int,
    hop_size: int,
) -> np.ndarray:
    """
    Compute a simple magnitude spectrogram, log-scaled.
    Returns a 2D array [frames, freq_bins].
    """
    # Frame the audio
    frames = _frame_audio(samples, frame_size, hop_size)
    # Apply Hann window
    window = np.hanning(frame_size).astype("float32")
    frames *= window[None, :]

    # FFT
    fft = np.fft.rfft(frames, axis=1)
    mag = np.abs(fft).astype("float32")

    # Log scale (add epsilon for safety)
    eps = 1e-8
    log_mag = np.log1p(mag / (mag.max() + eps))

    return log_mag


def _frame_audio(
    samples: np.ndarray,
    frame_size: int,
    hop_size: int,
) -> np.ndarray:
    """
    Overlapping framing of audio into 2D [frames, frame_size].
    """
    num_frames = 1 + max(0, (len(samples) - frame_size) // hop_size)
    frames = np.zeros((num_frames, frame_size), dtype="float32")

    for i in range(num_frames):
        start = i * hop_size
        end = start + frame_size
        frames[i, :] = samples[start:end]

    return frames


def extract_audio_features(path: Path, sr: int = 16000) -> np.ndarray:
    """
    Extract a compact, deterministic feature vector from audio for cryptographic use.

    Features extracted:
    - Spectral centroid (32 values)
    - Spectral flux (32 values)
    - Loudness curve (64 values)
    - Transient density (32 values)
    - Spectral rolloff (32 values)
    - Zero-crossing rate (32 values)
    - Spectral statistics (32 values)
    - Padding to exactly 256 floats

    Returns: Fixed-size feature vector (256 float32 values)
    """
    # Load audio
    samples, _ = load_audio_mono(path, sr)

    # Compute spectral map
    frame_size = 2048
    hop_size = 512
    spec_map = compute_spectral_map(samples, frame_size, hop_size)

    features = []

    # 1. Spectral centroid (center of mass of spectrum)
    freqs = np.linspace(0, sr / 2, spec_map.shape[1])
    centroids = np.sum(spec_map * freqs[None, :], axis=1) / (np.sum(spec_map, axis=1) + 1e-8)
    features.extend(_compress_to_n(centroids, 32))

    # 2. Spectral flux (change in spectrum over time)
    flux = np.sum(np.diff(spec_map, axis=0) ** 2, axis=1)
    features.extend(_compress_to_n(flux, 32))

    # 3. Loudness curve (RMS energy)
    frames = _frame_audio(samples, frame_size, hop_size)
    rms = np.sqrt(np.mean(frames ** 2, axis=1))
    features.extend(_compress_to_n(rms, 64))

    # 4. Transient density (onset strength)
    onset_env = np.maximum(0, np.diff(rms))
    features.extend(_compress_to_n(onset_env, 32))

    # 5. Spectral rolloff (frequency below which 85% of energy is contained)
    cumsum_spec = np.cumsum(spec_map, axis=1)
    total_energy = cumsum_spec[:, -1:]
    rolloff_idx = np.argmax(cumsum_spec >= 0.85 * total_energy, axis=1)
    rolloff = rolloff_idx.astype("float32") / spec_map.shape[1]
    features.extend(_compress_to_n(rolloff, 32))

    # 6. Zero-crossing rate
    zcr_frames = _frame_audio(samples, frame_size, hop_size)
    zcr = np.mean(np.abs(np.diff(np.sign(zcr_frames), axis=1)), axis=1)
    features.extend(_compress_to_n(zcr, 32))

    # 7. Spectral statistics (mean, std, skewness per frame)
    spec_mean = np.mean(spec_map, axis=1)
    spec_std = np.std(spec_map, axis=1)
    features.extend(_compress_to_n(spec_mean, 16))
    features.extend(_compress_to_n(spec_std, 16))

    # Ensure exactly 256 features
    features = np.array(features[:256], dtype="float32")
    if len(features) < 256:
        features = np.pad(features, (0, 256 - len(features)), mode="constant")

    return features


def _compress_to_n(data: np.ndarray, n: int) -> list:
    """
    Deterministically compress a data array to exactly n values.
    Uses percentile sampling for determinism.
    """
    if len(data) == 0:
        return [0.0] * n

    if len(data) <= n:
        # Pad with zeros
        result = data.tolist() + [0.0] * (n - len(data))
        return result[:n]

    # Sample at regular percentiles
    percentiles = np.linspace(0, 100, n)
    sampled = np.percentile(data, percentiles)
    return sampled.tolist()
