from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import soundfile as sf


DEFAULT_SAMPLE_RATE = 16000
DEFAULT_FRAME_SIZE = 2048
DEFAULT_HOP_SIZE = 512


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
    *,
    frames: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Compute a simple magnitude spectrogram, log-scaled.
    Returns a 2D array [frames, freq_bins].
    """
    # Frame the audio (reuse precomputed frames when provided)
    base_frames = frame_audio(samples, frame_size, hop_size) if frames is None else frames
    frame_block = base_frames.astype("float32", copy=True)
    window = np.hanning(frame_size).astype("float32")
    frame_block *= window[None, :]

    # FFT
    fft = np.fft.rfft(frame_block, axis=1)
    mag = np.abs(fft).astype("float32")

    # Log scale (add epsilon for safety)
    eps = 1e-8
    log_mag = np.log1p(mag / (mag.max() + eps))

    return log_mag


def frame_audio(
    samples: np.ndarray,
    frame_size: int,
    hop_size: int,
) -> np.ndarray:
    """
    Overlapping framing of audio into 2D [frames, frame_size].
    Pads the last frame if the audio length is shorter than frame_size.
    """
    samples = np.asarray(samples, dtype="float32")

    if len(samples) == 0:
        return np.zeros((0, frame_size), dtype="float32")

    num_frames = max(1, int(np.ceil((len(samples) - frame_size) / hop_size)) + 1)
    frames = np.zeros((num_frames, frame_size), dtype="float32")

    for i in range(num_frames):
        start = i * hop_size
        end = start + frame_size
        chunk = samples[start:end]
        frames[i, : len(chunk)] = chunk
        if len(chunk) < frame_size:
            break

    return frames


def extract_audio_features(path: Path, sr: int = DEFAULT_SAMPLE_RATE) -> np.ndarray:
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
    samples, sr = load_audio_mono(path, sr)
    return extract_audio_features_from_samples(samples, sr)


def extract_audio_features_from_samples(
    samples: np.ndarray,
    sr: int = DEFAULT_SAMPLE_RATE,
    frame_size: int = DEFAULT_FRAME_SIZE,
    hop_size: int = DEFAULT_HOP_SIZE,
    *,
    frames: Optional[np.ndarray] = None,
    spectral_map: Optional[np.ndarray] = None,
) -> np.ndarray:
    """
    Extract a compact, deterministic feature vector from in-memory audio for cryptographic use.

    Accepts precomputed frames/spectral_map to avoid redundant work on constrained devices (e.g. Orin).

    Returns: Fixed-size feature vector (256 float32 values)
    """
    frames = frame_audio(samples, frame_size, hop_size) if frames is None else frames
    frames = frames.astype("float32", copy=False)
    spec_map = (
        compute_spectral_map(samples, frame_size, hop_size, frames=frames)
        if spectral_map is None
        else spectral_map.astype("float32", copy=False)
    )

    features = []

    # 1. Spectral centroid (center of mass of spectrum)
    freqs = np.linspace(0, sr / 2, spec_map.shape[1], dtype="float32")
    energy = np.sum(spec_map, axis=1, dtype=np.float32)
    centroids = np.divide(
        np.sum(spec_map * freqs[None, :], axis=1, dtype=np.float32),
        energy + 1e-8,
    )
    features.extend(_compress_to_n(centroids, 32))

    # 2. Spectral flux (change in spectrum over time)
    flux = np.sum(np.diff(spec_map, axis=0) ** 2, axis=1, dtype=np.float32)
    features.extend(_compress_to_n(flux, 32))

    # 3. Loudness curve (RMS energy)
    rms = np.sqrt(np.mean(np.square(frames, dtype=np.float32), axis=1, dtype=np.float32))
    features.extend(_compress_to_n(rms, 64))

    # 4. Transient density (onset strength)
    onset_env = np.maximum(0, np.diff(rms))
    features.extend(_compress_to_n(onset_env, 32))

    # 5. Spectral rolloff (frequency below which 85% of energy is contained)
    cumsum_spec = np.cumsum(spec_map, axis=1, dtype=np.float32)
    total_energy = cumsum_spec[:, -1:]
    rolloff_idx = np.argmax(cumsum_spec >= 0.85 * total_energy, axis=1)
    rolloff = rolloff_idx.astype("float32") / spec_map.shape[1]
    features.extend(_compress_to_n(rolloff, 32))

    # 6. Zero-crossing rate
    zcr = np.mean(np.abs(np.diff(np.sign(frames), axis=1)), axis=1)
    features.extend(_compress_to_n(zcr, 32))

    # 7. Spectral statistics (mean, std per frame)
    spec_mean = np.mean(spec_map, axis=1, dtype=np.float32)
    spec_std = np.std(spec_map, axis=1, dtype=np.float32)
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
    sampled = np.percentile(data, percentiles).astype("float32")
    return sampled.tolist()


# Backwards compatibility for legacy imports
_frame_audio = frame_audio
