from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

import numpy as np
from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305, AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend

# Try to import Argon2, fallback to scrypt if not available
try:
    from cryptography.hazmat.primitives.kdf.argon2 import Argon2id
    ARGON2_AVAILABLE = True
except ImportError:
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    ARGON2_AVAILABLE = False


@dataclass
class EncryptedBlob:
    """
    Container for encrypted data with metadata.
    """
    version: str = "2.0"
    nonce: str = ""  # hex-encoded
    ciphertext: str = ""  # hex-encoded
    auth_tag: str = ""  # hex-encoded (included in ciphertext for AEAD)
    profile_name: str = ""
    rune_id: str = ""
    decoy_header: Optional[str] = None  # For Black Vault deniability

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_dict(cls, data: dict) -> EncryptedBlob:
        return cls(**data)

    @classmethod
    def from_json(cls, json_str: str) -> EncryptedBlob:
        return cls.from_dict(json.loads(json_str))


def hash_audio_features(audio_features: np.ndarray) -> bytes:
    """
    Hash audio feature vector to a fixed-size digest.
    """
    flat = np.asarray(audio_features, dtype="float32").flatten()
    return hashlib.sha256(flat.tobytes()).digest()


def derive_final_key(
    passphrase: str,
    audio_features: np.ndarray,
    profile: "PrivacyProfile",  # type: ignore
) -> bytes:
    """
    Audio-Field Key Derivation Function (AF-KDF).

    Pipeline:
    1. Hash audio features → SHA-256
    2. HKDF(passphrase || audio_hash || profile.name)
    3. Feed into Argon2id (or scrypt) using profile parameters
    4. Output 32-byte key

    Args:
        passphrase: User's secret passphrase
        audio_features: Fixed-size feature vector from audio
        profile: Privacy profile with KDF parameters

    Returns:
        32-byte cryptographic key
    """
    # Step 1: Hash audio features
    audio_hash = hash_audio_features(audio_features)

    # Step 2: Combine passphrase + audio_hash + profile name
    passphrase_bytes = passphrase.encode("utf-8")
    profile_bytes = profile.name.encode("utf-8")

    # Use HKDF to expand and mix inputs
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=audio_hash,
        info=profile_bytes,
        backend=default_backend()
    )
    intermediate_key = hkdf.derive(passphrase_bytes)

    # Step 3: Apply memory-hard KDF based on profile
    # Weight audio contribution
    if profile.audio_weight > 0:
        # Mix audio hash into salt
        salt = hashlib.sha256(audio_hash + profile_bytes).digest()[:16]
    else:
        # Use deterministic salt without audio
        salt = hashlib.sha256(profile_bytes).digest()[:16]

    # Apply Argon2id or scrypt
    if ARGON2_AVAILABLE:
        kdf = Argon2id(
            salt=salt,
            length=32,
            iterations=profile.kdf_time,
            lanes=4,
            memory_cost=profile.kdf_memory,
            backend=default_backend()
        )
    else:
        # Fallback to scrypt
        # Convert Argon2 parameters to scrypt equivalents
        kdf = Scrypt(
            salt=salt,
            length=32,
            n=2 ** min(14, profile.kdf_memory // 1024),  # Adjust for scrypt
            r=8,
            p=1,
            backend=default_backend()
        )

    final_key = kdf.derive(intermediate_key)
    return final_key


def encrypt_bytes(data: bytes, key: bytes, context: dict) -> EncryptedBlob:
    """
    Encrypt data using AEAD (XChaCha20-Poly1305 preferred, AES-GCM fallback).

    Args:
        data: Plaintext bytes to encrypt
        key: 32-byte encryption key
        context: Dictionary with profile_name, rune_id, etc.

    Returns:
        EncryptedBlob with all metadata
    """
    # Generate random nonce
    nonce = os.urandom(24)  # XChaCha20-Poly1305 uses 24-byte nonce

    # Try XChaCha20-Poly1305 first
    try:
        cipher = ChaCha20Poly1305(key)
        # Additional authenticated data (AAD)
        aad = json.dumps(context, sort_keys=True).encode("utf-8")
        ciphertext = cipher.encrypt(nonce, data, aad)
    except Exception:
        # Fallback to AES-GCM
        nonce = os.urandom(12)  # AES-GCM uses 12-byte nonce
        cipher = AESGCM(key)
        aad = json.dumps(context, sort_keys=True).encode("utf-8")
        ciphertext = cipher.encrypt(nonce, data, aad)

    blob = EncryptedBlob(
        version="2.0",
        nonce=nonce.hex(),
        ciphertext=ciphertext.hex(),
        auth_tag="",  # Included in ciphertext for AEAD
        profile_name=context.get("profile_name", ""),
        rune_id=context.get("rune_id", ""),
    )

    # Add decoy header for Black Vault
    if context.get("deniable", False):
        blob.decoy_header = _generate_decoy_header()

    return blob


def decrypt_bytes(blob: EncryptedBlob, key: bytes) -> bytes:
    """
    Decrypt data from EncryptedBlob.

    Args:
        blob: EncryptedBlob containing encrypted data
        key: 32-byte decryption key

    Returns:
        Plaintext bytes

    Raises:
        ValueError: If decryption fails (wrong key, corrupted data, etc.)
    """
    nonce = bytes.fromhex(blob.nonce)
    ciphertext = bytes.fromhex(blob.ciphertext)

    # Reconstruct AAD context
    context = {
        "profile_name": blob.profile_name,
        "rune_id": blob.rune_id,
    }
    aad = json.dumps(context, sort_keys=True).encode("utf-8")

    # Try XChaCha20-Poly1305 first (24-byte nonce)
    if len(nonce) == 24:
        try:
            cipher = ChaCha20Poly1305(key)
            plaintext = cipher.decrypt(nonce, ciphertext, aad)
            return plaintext
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    # Try AES-GCM (12-byte nonce)
    elif len(nonce) == 12:
        try:
            cipher = AESGCM(key)
            plaintext = cipher.decrypt(nonce, ciphertext, aad)
            return plaintext
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")

    else:
        raise ValueError(f"Invalid nonce length: {len(nonce)}")


def _generate_decoy_header() -> str:
    """
    Generate a plausible decoy header for deniability.
    Makes encrypted data look like a corrupted/random file.
    """
    decoy_types = [
        "PNG",
        "JPEG",
        "PDF",
        "ZIP",
        "MP3",
    ]
    decoy_type = decoy_types[os.urandom(1)[0] % len(decoy_types)]
    random_bytes = os.urandom(16)
    return f"DECOY_{decoy_type}_{random_bytes.hex()}"


def rune_id_from_key(key: bytes, prefix: str = "ECH") -> str:
    """
    Generate a rune ID from a cryptographic key.

    Args:
        key: Key bytes
        prefix: Prefix for rune ID

    Returns:
        Rune ID string (e.g., "ECH-A1B2C3D4")
    """
    digest = hashlib.sha256(key).hexdigest()
    core = digest[:8].upper()
    return f"{prefix}-{core}"
