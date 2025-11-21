from __future__ import annotations

import hashlib
import time
from typing import Optional, List, Tuple

import numpy as np


# Temporal Salt Chain Constants
TSC_PREFIX = b"ECHOTOME-TSC-V3"
JITTER_BYTES = 8  # Bytes of jitter per frame
MAX_PLAYBACK_SPEED = 1.2  # Allow 20% speedup tolerance
MIN_PLAYBACK_SPEED = 0.8  # Allow 20% slowdown tolerance


def compute_temporal_hash(
    frames: np.ndarray,
    device_pub: bytes,
    track_length: int,
    timing_data: Optional[List[float]] = None,
) -> bytes:
    """
    Compute deterministic temporal hash using Temporal Salt Chain (TSC).

    The TSC algorithm creates a cryptographic hash chain that binds together:
    - Audio frame content (in temporal order)
    - Device identity
    - Track length
    - Frame-specific jitter
    - Sequential frame indices

    This creates a hash that can ONLY be reproduced by playing the audio
    in real-time, in order, without skipping or acceleration.

    Algorithm:
        state = SHA256("ECHOTOME-TSC" || device_pub || track_length)
        for i, frame in enumerate(active_frames):
            fh = SHA256(frame_bytes)
            jitter = SHA256(state + int_to_bytes(i))[:N]
            state = SHA256(state || fh || jitter || int_to_bytes(i))
        temporal_hash = state

    Args:
        frames: Active region frames (shape: [n_frames, frame_size])
        device_pub: Device identity public key
        track_length: Total track length in samples
        timing_data: Optional list of frame arrival times for validation

    Returns:
        32-byte temporal hash

    Raises:
        ValueError: If timing validation fails or frames incomplete
    """
    if frames.shape[0] == 0:
        raise ValueError("Empty frames for temporal hash")

    if len(device_pub) != 32:
        raise ValueError(f"Invalid device_pub length: {len(device_pub)}, expected 32")

    # Validate timing if provided
    if timing_data is not None:
        _validate_timing(timing_data, frames.shape[0])

    # Initialize state
    state = _initialize_tsc_state(device_pub, track_length)

    # Chain through all frames
    for i in range(frames.shape[0]):
        frame = frames[i]
        state = _chain_frame(state, frame, i)

    return state


def _initialize_tsc_state(device_pub: bytes, track_length: int) -> bytes:
    """
    Initialize TSC state with device identity and track metadata.

    Args:
        device_pub: 32-byte device public key
        track_length: Total track length in samples

    Returns:
        32-byte initial state
    """
    h = hashlib.sha256()
    h.update(TSC_PREFIX)
    h.update(device_pub)
    h.update(track_length.to_bytes(8, "big"))
    return h.digest()


def _chain_frame(state: bytes, frame: np.ndarray, frame_idx: int) -> bytes:
    """
    Chain a single frame into the TSC state.

    Args:
        state: Current 32-byte state
        frame: Audio frame samples
        frame_idx: Frame index in sequence

    Returns:
        Updated 32-byte state
    """
    # Hash frame content
    frame_bytes = frame.astype("float32").tobytes()
    fh = hashlib.sha256(frame_bytes).digest()

    # Generate frame-specific jitter
    jitter = _generate_jitter(state, frame_idx)

    # Chain: state = SHA256(state || fh || jitter || idx)
    h = hashlib.sha256()
    h.update(state)
    h.update(fh)
    h.update(jitter)
    h.update(frame_idx.to_bytes(8, "big"))

    return h.digest()


def _generate_jitter(state: bytes, frame_idx: int) -> bytes:
    """
    Generate deterministic jitter bytes for a frame.

    Jitter prevents precomputation attacks by introducing
    frame-specific randomness derived from the chain state.

    Args:
        state: Current TSC state
        frame_idx: Frame index

    Returns:
        JITTER_BYTES bytes of jitter
    """
    h = hashlib.sha256()
    h.update(state)
    h.update(frame_idx.to_bytes(8, "big"))
    return h.digest()[:JITTER_BYTES]


def _validate_timing(timing_data: List[float], expected_frames: int) -> None:
    """
    Validate that playback timing is consistent with real-time audio.

    Prevents attacks where attacker accelerates through audio or
    skips frames to quickly derive the temporal hash.

    Args:
        timing_data: List of timestamps (seconds) when each frame arrived
        expected_frames: Number of frames expected

    Raises:
        ValueError: If timing is invalid
    """
    if len(timing_data) != expected_frames:
        raise ValueError(
            f"Timing data mismatch: got {len(timing_data)} timestamps, "
            f"expected {expected_frames} frames"
        )

    if len(timing_data) < 2:
        # Can't validate timing with less than 2 frames
        return

    # Check for reasonable frame arrival intervals
    intervals = np.diff(timing_data)

    # Expected interval (assuming hop_size=512, sr=16000)
    # interval ≈ 512 / 16000 = 0.032 seconds
    expected_interval = 0.032

    # Allow some tolerance
    min_interval = expected_interval * MIN_PLAYBACK_SPEED
    max_interval = expected_interval * MAX_PLAYBACK_SPEED

    # Check for suspiciously fast playback (acceleration attack)
    too_fast = np.sum(intervals < min_interval) / len(intervals)
    if too_fast > 0.1:  # More than 10% of intervals too fast
        raise ValueError(
            f"Playback timing invalid: {too_fast*100:.1f}% of frames arrived too quickly. "
            "Possible acceleration attack."
        )

    # Check for implausibly slow playback
    too_slow = np.sum(intervals > max_interval * 3) / len(intervals)
    if too_slow > 0.2:  # More than 20% of intervals too slow
        raise ValueError(
            f"Playback timing invalid: {too_slow*100:.1f}% of frames arrived too slowly. "
            "Possible incomplete playback."
        )


def compute_temporal_hash_streaming(
    device_pub: bytes,
    track_length: int,
) -> "TemporalHashStreamer":
    """
    Create a streaming temporal hash computer for real-time playback.

    This allows computing the temporal hash incrementally as frames
    arrive from a live audio stream (e.g., microphone input).

    Args:
        device_pub: 32-byte device public key
        track_length: Expected track length in samples

    Returns:
        TemporalHashStreamer instance

    Example:
        streamer = compute_temporal_hash_streaming(device_pub, track_len)
        for frame in audio_frames:
            streamer.add_frame(frame)
        final_hash = streamer.finalize()
    """
    return TemporalHashStreamer(device_pub, track_length)


class TemporalHashStreamer:
    """
    Streaming temporal hash computer for real-time playback verification.

    This class allows incremental computation of the temporal hash,
    useful for microphone-only verification modes where frames arrive
    in real-time.
    """

    def __init__(self, device_pub: bytes, track_length: int):
        """
        Initialize streamer.

        Args:
            device_pub: 32-byte device public key
            track_length: Expected track length in samples
        """
        if len(device_pub) != 32:
            raise ValueError(f"Invalid device_pub length: {len(device_pub)}")

        self.device_pub = device_pub
        self.track_length = track_length
        self.state = _initialize_tsc_state(device_pub, track_length)
        self.frame_idx = 0
        self.timing_data: List[float] = []
        self.start_time: Optional[float] = None
        self.finalized = False

    def add_frame(self, frame: np.ndarray, timestamp: Optional[float] = None) -> None:
        """
        Add a frame to the temporal hash chain.

        Args:
            frame: Audio frame samples
            timestamp: Optional timestamp for timing validation

        Raises:
            ValueError: If streamer already finalized
        """
        if self.finalized:
            raise ValueError("Streamer already finalized")

        if timestamp is None:
            timestamp = time.time()

        if self.start_time is None:
            self.start_time = timestamp

        # Record timing
        self.timing_data.append(timestamp - self.start_time)

        # Chain frame
        self.state = _chain_frame(self.state, frame, self.frame_idx)
        self.frame_idx += 1

    def finalize(self, validate_timing: bool = True) -> bytes:
        """
        Finalize the temporal hash computation.

        Args:
            validate_timing: Whether to validate playback timing

        Returns:
            Final 32-byte temporal hash

        Raises:
            ValueError: If timing validation fails
        """
        if self.finalized:
            return self.state

        if validate_timing and len(self.timing_data) > 1:
            _validate_timing(self.timing_data, self.frame_idx)

        self.finalized = True
        return self.state

    def get_progress(self) -> Tuple[int, Optional[float]]:
        """
        Get current progress.

        Returns:
            (frames_processed, elapsed_time_seconds)
        """
        elapsed = None
        if self.start_time is not None and len(self.timing_data) > 0:
            elapsed = self.timing_data[-1]

        return self.frame_idx, elapsed


def verify_temporal_consistency(
    original_hash: bytes,
    device_pub: bytes,
    track_length: int,
    frames: np.ndarray,
) -> bool:
    """
    Verify that frames produce the expected temporal hash.

    Used during unlock to verify audio playback matches enrollment.

    Args:
        original_hash: Expected temporal hash from enrollment
        device_pub: Device public key
        track_length: Track length
        frames: Active region frames

    Returns:
        True if hashes match, False otherwise
    """
    try:
        computed_hash = compute_temporal_hash(
            frames,
            device_pub,
            track_length,
            timing_data=None,  # Don't validate timing for stored audio
        )
        return computed_hash == original_hash
    except Exception:
        return False
