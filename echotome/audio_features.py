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
