from __future__ import annotations

import hashlib
from typing import Tuple

import numpy as np


# RIV Constants
RIV_VERSION = "3.0"
RIV_SIZE = 32  # 32 bytes = 256 bits


def compute_riv(features: np.ndarray, temporal_hash: bytes) -> bytes:
    """
    Compute Ritual Imprint Vector (RIV).

    The RIV is a 32-byte fingerprint that uniquely identifies a ritual binding
    by combining:
    - Spectral signature (frequency characteristics)
    - Rhythm signature (temporal patterns)
    - Temporal hash (from TSC)

    This creates a compact, deterministic identifier used for:
    - Steganography payload verification
    - ROC cross-validation
    - Ritual matching and lookup

    Args:
        features: Audio feature vector (256 floats from extract_audio_features)
        temporal_hash: 32-byte temporal hash from TSC

    Returns:
        32-byte RIV

    Raises:
        ValueError: If inputs invalid
    """
    if len(temporal_hash) != 32:
        raise ValueError(f"Invalid temporal_hash length: {len(temporal_hash)}")

    if features.size == 0:
        raise ValueError("Empty feature vector")

    # Compute spectral signature
    spectral_sig = _compute_spectral_signature(features)

    # Compute rhythm signature
    rhythm_sig = _compute_rhythm_signature(features)

    # Combine signatures with temporal hash
    riv = _combine_signatures(spectral_sig, rhythm_sig, temporal_hash)

    return riv


def _compute_spectral_signature(features: np.ndarray) -> bytes:
    """
    Compute spectral signature from audio features.

    Spectral signature captures frequency-domain characteristics:
    - Spectral centroid (tone brightness)
    - Spectral rolloff (frequency distribution)
    - Spectral statistics

    Args:
        features: Feature vector

    Returns:
        16-byte spectral signature
    """
    # Features are structured as (from audio_layer.py):
    # [0:32]   - spectral centroid
    # [32:64]  - spectral flux
    # [64:128] - loudness curve
    # [128:160] - transient density
    # [160:192] - spectral rolloff
    # [192:224] - zero-crossing rate
    # [224:240] - spectral mean
    # [240:256] - spectral std

    # Extract spectral components
    centroid = features[:32] if len(features) >= 32 else features
    rolloff = features[160:192] if len(features) >= 192 else features
    spec_mean = features[224:240] if len(features) >= 240 else features
    spec_std = features[240:256] if len(features) >= 256 else features

    # Combine and hash
    h = hashlib.sha256()
    h.update(b"SPECTRAL_SIG_V3")
    h.update(centroid.astype("float32").tobytes())
    h.update(rolloff.astype("float32").tobytes())
    h.update(spec_mean.astype("float32").tobytes())
    h.update(spec_std.astype("float32").tobytes())

    return h.digest()[:16]


def _compute_rhythm_signature(features: np.ndarray) -> bytes:
    """
    Compute rhythm signature from audio features.

    Rhythm signature captures temporal patterns:
    - Spectral flux (note onsets)
    - Transient density (rhythmic events)
    - Loudness curve (dynamic envelope)

    Args:
        features: Feature vector

    Returns:
        16-byte rhythm signature
    """
    # Extract rhythm components
    flux = features[32:64] if len(features) >= 64 else features
    loudness = features[64:128] if len(features) >= 128 else features
    transients = features[128:160] if len(features) >= 160 else features

    # Combine and hash
    h = hashlib.sha256()
    h.update(b"RHYTHM_SIG_V3")
    h.update(flux.astype("float32").tobytes())
    h.update(loudness.astype("float32").tobytes())
    h.update(transients.astype("float32").tobytes())

    return h.digest()[:16]


def _combine_signatures(
    spectral_sig: bytes,
    rhythm_sig: bytes,
    temporal_hash: bytes,
) -> bytes:
    """
    Combine signatures into final RIV.

    Uses layered hashing to create a 32-byte RIV that binds:
    - What the audio sounds like (spectral)
    - How it moves through time (rhythm)
    - When it was played (temporal)

    Args:
        spectral_sig: 16-byte spectral signature
        rhythm_sig: 16-byte rhythm signature
        temporal_hash: 32-byte temporal hash

    Returns:
        32-byte RIV
    """
    h = hashlib.sha256()
    h.update(b"ECHOTOME_RIV_V3")
    h.update(spectral_sig)
    h.update(rhythm_sig)
    h.update(temporal_hash)

    return h.digest()


def riv_to_hex(riv: bytes) -> str:
    """
    Convert RIV to hex string.

    Args:
        riv: 32-byte RIV

    Returns:
        64-character hex string
    """
    return riv.hex()


def riv_from_hex(hex_str: str) -> bytes:
    """
    Convert hex string to RIV.

    Args:
        hex_str: 64-character hex string

    Returns:
        32-byte RIV

    Raises:
        ValueError: If invalid hex or wrong length
    """
    riv = bytes.fromhex(hex_str)

    if len(riv) != RIV_SIZE:
        raise ValueError(f"Invalid RIV size: {len(riv)}, expected {RIV_SIZE}")

    return riv


def compare_rivs(riv1: bytes, riv2: bytes, tolerance: float = 0.0) -> bool:
    """
    Compare two RIVs for equality.

    Args:
        riv1: First RIV
        riv2: Second RIV
        tolerance: Hamming distance tolerance (0.0 = exact match)

    Returns:
        True if RIVs match within tolerance
    """
    if len(riv1) != RIV_SIZE or len(riv2) != RIV_SIZE:
        return False

    if tolerance == 0.0:
        # Exact match
        return riv1 == riv2

    # Hamming distance
    hamming = sum(bin(b1 ^ b2).count("1") for b1, b2 in zip(riv1, riv2))
    max_distance = RIV_SIZE * 8 * tolerance

    return hamming <= max_distance


def riv_distance(riv1: bytes, riv2: bytes) -> float:
    """
    Compute normalized Hamming distance between RIVs.

    Args:
        riv1: First RIV
        riv2: Second RIV

    Returns:
        Distance in [0.0, 1.0] where 0.0 = identical, 1.0 = completely different
    """
    if len(riv1) != RIV_SIZE or len(riv2) != RIV_SIZE:
        return 1.0

    hamming = sum(bin(b1 ^ b2).count("1") for b1, b2 in zip(riv1, riv2))
    max_bits = RIV_SIZE * 8

    return hamming / max_bits


def get_riv_fingerprint(riv: bytes, length: int = 8) -> str:
    """
    Get short human-readable fingerprint of RIV.

    Args:
        riv: 32-byte RIV
        length: Number of hex characters

    Returns:
        Hex fingerprint
    """
    return riv[:length // 2].hex().upper()


def verify_riv_consistency(
    riv: bytes,
    features: np.ndarray,
    temporal_hash: bytes,
) -> bool:
    """
    Verify that RIV was computed from given inputs.

    Recomputes RIV and checks for exact match.

    Args:
        riv: RIV to verify
        features: Audio features
        temporal_hash: Temporal hash

    Returns:
        True if RIV matches recomputed value
    """
    try:
        recomputed = compute_riv(features, temporal_hash)
        return riv == recomputed
    except Exception:
        return False


def compute_riv_from_spectral_map(
    spectral_map: np.ndarray,
    temporal_hash: bytes,
) -> bytes:
    """
    Compute RIV from 2D spectral map instead of feature vector.

    Useful when working directly with spectrograms.

    Args:
        spectral_map: 2D spectral map [frames, freq_bins]
        temporal_hash: Temporal hash

    Returns:
        32-byte RIV
    """
    # Convert spectral map to pseudo-features
    # This is a simplified version for compatibility

    # Compute statistics across frames
    spec_mean = np.mean(spectral_map, axis=0)
    spec_std = np.std(spectral_map, axis=0)
    spec_max = np.max(spectral_map, axis=0)

    # Compute temporal statistics
    temporal_mean = np.mean(spectral_map, axis=1)
    temporal_std = np.std(spectral_map, axis=1)

    # Build pseudo-feature vector
    features = np.concatenate([
        _compress_to_n(spec_mean, 80),
        _compress_to_n(spec_std, 80),
        _compress_to_n(spec_max, 32),
        _compress_to_n(temporal_mean, 32),
        _compress_to_n(temporal_std, 32),
    ])

    return compute_riv(features, temporal_hash)


def _compress_to_n(data: np.ndarray, n: int) -> np.ndarray:
    """
    Compress data array to n values using percentile sampling.

    Args:
        data: Input array
        n: Target size

    Returns:
        Compressed array of size n
    """
    if len(data) == 0:
        return np.zeros(n, dtype="float32")

    if len(data) <= n:
        # Pad with zeros
        return np.pad(data.astype("float32"), (0, n - len(data)), mode="constant")

    # Sample at regular percentiles
    percentiles = np.linspace(0, 100, n)
    sampled = np.percentile(data, percentiles)
    return sampled.astype("float32")
