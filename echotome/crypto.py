from __future__ import annotations

import hashlib
from typing import Tuple


def derive_feature_hash(audio_features, secret_key: str) -> Tuple[str, int]:
    """
    Derive a deterministic hash and RNG seed from audio features + secret key.

    This is NOT a secure cryptosystem for real-world cryptography.
    It's a deterministic mapping used for art / symbolic work.
    """
    import numpy as np

    # Flatten and compress features
    flat = np.asarray(audio_features, dtype="float32").flatten()
    # Reduce size for hashing to keep cost predictable
    if flat.size > 4096:
        # Simple deterministic downsample
        stride = max(1, flat.size // 4096)
        flat = flat[::stride]

    payload = flat.tobytes() + secret_key.encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()

    # Use first 8 bytes of hex as RNG seed
    seed_int = int(digest[:16], 16)
    return digest, seed_int


def build_rune_id(digest: str, prefix: str = "ECH", length: int = 8) -> str:
    """
    Short rune identifier: prefix + leading digest chars, all uppercase.
    """
    core = digest[:length].upper()
    return f"{prefix}-{core}"
