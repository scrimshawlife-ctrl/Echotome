from __future__ import annotations

from typing import Tuple

import numpy as np


# Active Region Detection Parameters
FRAME_SIZE = 2048
HOP_SIZE = 512
RMS_THRESHOLD = 0.01  # Minimum RMS energy for active frame
FLUX_THRESHOLD = 0.02  # Minimum spectral flux for active frame
CENTROID_SHIFT_THRESHOLD = 500  # Hz shift for active detection
MIN_ACTIVE_DURATION = 1.0  # Minimum active region duration in seconds
HYSTERESIS_FACTOR = 0.8  # Prevent false positives at boundaries


def detect_active_region(
    samples: np.ndarray,
    sr: int,
    frame_size: int = FRAME_SIZE,
    hop_size: int = HOP_SIZE,
) -> Tuple[np.ndarray, int, int]:
    """
    Detect the active region of audio for ritual binding.

    Active region is the contiguous segment where meaningful audio content exists,
    filtering out silence, noise, and lead-in/lead-out periods.

    Algorithm:
    1. Frame audio into overlapping windows
    2. Compute per-frame metrics: RMS, spectral flux, centroid shift
    3. Mark frames as active if ANY metric exceeds threshold
    4. Find largest contiguous active block >= MIN_ACTIVE_DURATION
    5. Apply hysteresis to prevent false boundary detection

    Args:
        samples: Mono audio samples (float32)
        sr: Sample rate
        frame_size: FFT frame size
        hop_size: Hop size between frames

    Returns:
        Tuple of (active_frames, start_frame_idx, end_frame_idx)

    Raises:
        ValueError: If no active region found meeting minimum duration
    """
    if len(samples) == 0:
        raise ValueError("Empty audio samples")

    # Frame the audio
    frames = _frame_audio(samples, frame_size, hop_size)
    n_frames = frames.shape[0]

    # Compute activity metrics
    rms = _compute_rms(frames)
    flux = _compute_spectral_flux(frames, frame_size, sr)
    centroid_shift = _compute_centroid_shift(frames, frame_size, sr)

    # Apply thresholds with hysteresis
    rms_active = rms > (RMS_THRESHOLD * HYSTERESIS_FACTOR)
    flux_active = flux > (FLUX_THRESHOLD * HYSTERESIS_FACTOR)
    centroid_active = centroid_shift > (CENTROID_SHIFT_THRESHOLD * HYSTERESIS_FACTOR)

    # Frame is active if ANY metric exceeds threshold
    is_active = rms_active | flux_active | centroid_active

    # Find contiguous active regions
    min_frames = int(MIN_ACTIVE_DURATION * sr / hop_size)
    start, end = _find_longest_active_region(is_active, min_frames)

    if start is None or end is None:
        raise ValueError(
            f"No active region found meeting minimum duration of {MIN_ACTIVE_DURATION}s"
        )

    # Return active frames slice
    active_frames = frames[start : end + 1]

    return active_frames, start, end


def _frame_audio(
    samples: np.ndarray,
    frame_size: int,
    hop_size: int,
) -> np.ndarray:
    """Frame audio into overlapping windows."""
    n_frames = 1 + max(0, (len(samples) - frame_size) // hop_size)
    frames = np.zeros((n_frames, frame_size), dtype="float32")

    for i in range(n_frames):
        start = i * hop_size
        end = start + frame_size
        if end <= len(samples):
            frames[i, :] = samples[start:end]
        else:
            # Pad last frame if needed
            remaining = len(samples) - start
            frames[i, :remaining] = samples[start:]

    return frames


def _compute_rms(frames: np.ndarray) -> np.ndarray:
    """Compute RMS energy per frame."""
    return np.sqrt(np.mean(frames**2, axis=1))


def _compute_spectral_flux(
    frames: np.ndarray,
    frame_size: int,
    sr: int,
) -> np.ndarray:
    """
    Compute spectral flux (change in spectrum over time).

    Spectral flux measures the rate of change in the spectrum,
    useful for detecting onsets and transients.
    """
    # Apply window
    window = np.hanning(frame_size).astype("float32")
    windowed = frames * window[None, :]

    # Compute magnitude spectrum
    fft = np.fft.rfft(windowed, axis=1)
    mag = np.abs(fft).astype("float32")

    # Compute flux as squared difference between consecutive frames
    flux = np.zeros(len(frames), dtype="float32")
    if len(frames) > 1:
        diff = np.diff(mag, axis=0)
        flux[1:] = np.sqrt(np.sum(diff**2, axis=1))

    return flux


def _compute_centroid_shift(
    frames: np.ndarray,
    frame_size: int,
    sr: int,
) -> np.ndarray:
    """
    Compute spectral centroid shift between consecutive frames.

    Spectral centroid is the "center of mass" of the spectrum.
    Large shifts indicate significant spectral changes.
    """
    # Apply window
    window = np.hanning(frame_size).astype("float32")
    windowed = frames * window[None, :]

    # Compute magnitude spectrum
    fft = np.fft.rfft(windowed, axis=1)
    mag = np.abs(fft).astype("float32")

    # Frequency bins
    freqs = np.linspace(0, sr / 2, mag.shape[1])

    # Compute centroid for each frame
    centroids = np.sum(mag * freqs[None, :], axis=1) / (np.sum(mag, axis=1) + 1e-8)

    # Compute shift between consecutive frames
    shift = np.zeros(len(frames), dtype="float32")
    if len(frames) > 1:
        shift[1:] = np.abs(np.diff(centroids))

    return shift


def _find_longest_active_region(
    is_active: np.ndarray,
    min_frames: int,
) -> Tuple[int | None, int | None]:
    """
    Find the longest contiguous active region meeting minimum duration.

    Args:
        is_active: Boolean array indicating active frames
        min_frames: Minimum number of contiguous active frames

    Returns:
        (start_idx, end_idx) or (None, None) if no region found
    """
    # Find contiguous runs of True values
    padded = np.concatenate([[False], is_active, [False]])
    edges = np.diff(padded.astype(int))

    starts = np.where(edges == 1)[0]
    ends = np.where(edges == -1)[0] - 1

    if len(starts) == 0:
        return None, None

    # Find longest run
    lengths = ends - starts + 1
    valid = lengths >= min_frames

    if not np.any(valid):
        return None, None

    longest_idx = np.argmax(lengths * valid)
    return int(starts[longest_idx]), int(ends[longest_idx])


def get_active_region_info(
    samples: np.ndarray,
    sr: int,
    start_frame: int,
    end_frame: int,
    hop_size: int = HOP_SIZE,
) -> dict:
    """
    Get metadata about the detected active region.

    Args:
        samples: Original audio samples
        sr: Sample rate
        start_frame: Start frame index
        end_frame: End frame index
        hop_size: Hop size used for framing

    Returns:
        Dictionary with region metadata
    """
    start_time = start_frame * hop_size / sr
    end_time = (end_frame + 1) * hop_size / sr
    duration = end_time - start_time

    start_sample = start_frame * hop_size
    end_sample = (end_frame + 1) * hop_size

    return {
        "start_frame": start_frame,
        "end_frame": end_frame,
        "start_time_seconds": start_time,
        "end_time_seconds": end_time,
        "duration_seconds": duration,
        "start_sample": start_sample,
        "end_sample": min(end_sample, len(samples)),
        "n_frames": end_frame - start_frame + 1,
    }
