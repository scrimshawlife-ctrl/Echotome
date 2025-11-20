from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives import serialization


# Identity key storage paths
IDENTITY_DIR = Path.home() / ".echotome" / "identity"
PRIVATE_KEY_FILE = IDENTITY_DIR / "identity.key"
PUBLIC_KEY_FILE = IDENTITY_DIR / "identity.pub"


@dataclass
class IdentityKeypair:
    """
    Device identity keypair.

    Attributes:
        priv: 32-byte private key (raw bytes)
        pub: 32-byte public key (raw bytes)
    """

    priv: bytes
    pub: bytes

    def __post_init__(self):
        """Validate key lengths."""
        if len(self.priv) != 32:
            raise ValueError(f"Invalid private key length: {len(self.priv)}, expected 32")
        if len(self.pub) != 32:
            raise ValueError(f"Invalid public key length: {len(self.pub)}, expected 32")

    @classmethod
    def from_ed25519(
        cls, private_key: Ed25519PrivateKey
    ) -> IdentityKeypair:
        """
        Create IdentityKeypair from Ed25519PrivateKey.

        Args:
            private_key: Ed25519PrivateKey instance

        Returns:
            IdentityKeypair with raw bytes
        """
        priv_bytes = private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        )

        pub_bytes = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        )

        return cls(priv=priv_bytes, pub=pub_bytes)

    def to_ed25519_private_key(self) -> Ed25519PrivateKey:
        """
        Convert to Ed25519PrivateKey.

        Returns:
            Ed25519PrivateKey instance
        """
        return Ed25519PrivateKey.from_private_bytes(self.priv)

    def to_ed25519_public_key(self) -> Ed25519PublicKey:
        """
        Convert to Ed25519PublicKey.

        Returns:
            Ed25519PublicKey instance
        """
        return Ed25519PublicKey.from_public_bytes(self.pub)


def ensure_identity_keypair() -> IdentityKeypair:
    """
    Ensure device identity keypair exists, creating if necessary.

    On first run:
    - Generates Ed25519 keypair
    - Stores in ~/.echotome/identity/
    - Locks file permissions to user-only (0600)

    On subsequent runs:
    - Loads existing keypair

    Returns:
        IdentityKeypair instance

    Raises:
        PermissionError: If cannot create/access identity directory
        ValueError: If stored keys are invalid
    """
    # Check if keys exist
    if PRIVATE_KEY_FILE.exists() and PUBLIC_KEY_FILE.exists():
        return load_identity_keypair()

    # Generate new keypair
    return generate_identity_keypair()


def generate_identity_keypair() -> IdentityKeypair:
    """
    Generate new Ed25519 identity keypair and save to disk.

    Returns:
        Newly generated IdentityKeypair

    Raises:
        PermissionError: If cannot create identity directory
    """
    # Ensure directory exists
    IDENTITY_DIR.mkdir(parents=True, exist_ok=True)

    # Set directory permissions to user-only (0700)
    os.chmod(IDENTITY_DIR, stat.S_IRWXU)

    # Generate Ed25519 keypair
    private_key = Ed25519PrivateKey.generate()
    keypair = IdentityKeypair.from_ed25519(private_key)

    # Save private key
    with open(PRIVATE_KEY_FILE, "wb") as f:
        f.write(keypair.priv)

    # Set private key permissions to user read/write only (0600)
    os.chmod(PRIVATE_KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)

    # Save public key
    with open(PUBLIC_KEY_FILE, "wb") as f:
        f.write(keypair.pub)

    # Set public key permissions to user read/write only (0600)
    os.chmod(PUBLIC_KEY_FILE, stat.S_IRUSR | stat.S_IWUSR)

    return keypair


def load_identity_keypair() -> IdentityKeypair:
    """
    Load existing identity keypair from disk.

    Returns:
        IdentityKeypair instance

    Raises:
        FileNotFoundError: If keys don't exist
        ValueError: If keys are invalid
    """
    if not PRIVATE_KEY_FILE.exists():
        raise FileNotFoundError(f"Private key not found: {PRIVATE_KEY_FILE}")

    if not PUBLIC_KEY_FILE.exists():
        raise FileNotFoundError(f"Public key not found: {PUBLIC_KEY_FILE}")

    # Load private key
    with open(PRIVATE_KEY_FILE, "rb") as f:
        priv = f.read()

    # Load public key
    with open(PUBLIC_KEY_FILE, "rb") as f:
        pub = f.read()

    # Validate and create keypair
    keypair = IdentityKeypair(priv=priv, pub=pub)

    # Verify keys are valid by attempting to construct Ed25519 objects
    try:
        keypair.to_ed25519_private_key()
        keypair.to_ed25519_public_key()
    except Exception as e:
        raise ValueError(f"Invalid identity keys: {e}")

    return keypair


def get_identity_fingerprint(keypair: Optional[IdentityKeypair] = None) -> str:
    """
    Get human-readable fingerprint of identity public key.

    Args:
        keypair: Optional IdentityKeypair (loads from disk if None)

    Returns:
        Hex-encoded fingerprint (first 16 bytes of public key)
    """
    if keypair is None:
        keypair = ensure_identity_keypair()

    return keypair.pub[:16].hex().upper()


def sign_data(data: bytes, keypair: Optional[IdentityKeypair] = None) -> bytes:
    """
    Sign data using device identity private key.

    Args:
        data: Data to sign
        keypair: Optional IdentityKeypair (loads from disk if None)

    Returns:
        64-byte Ed25519 signature
    """
    if keypair is None:
        keypair = ensure_identity_keypair()

    private_key = keypair.to_ed25519_private_key()
    signature = private_key.sign(data)

    return signature


def verify_signature(
    data: bytes,
    signature: bytes,
    public_key_bytes: bytes,
) -> bool:
    """
    Verify Ed25519 signature.

    Args:
        data: Original data
        signature: 64-byte Ed25519 signature
        public_key_bytes: 32-byte public key

    Returns:
        True if signature valid, False otherwise
    """
    try:
        public_key = Ed25519PublicKey.from_public_bytes(public_key_bytes)
        public_key.verify(signature, data)
        return True
    except Exception:
        return False


def reset_identity_keypair() -> IdentityKeypair:
    """
    Reset device identity by deleting old keys and generating new ones.

    WARNING: This will invalidate all existing ritual certificates!

    Returns:
        Newly generated IdentityKeypair
    """
    # Delete old keys if they exist
    if PRIVATE_KEY_FILE.exists():
        PRIVATE_KEY_FILE.unlink()

    if PUBLIC_KEY_FILE.exists():
        PUBLIC_KEY_FILE.unlink()

    # Generate new keypair
    return generate_identity_keypair()


def export_public_key_base64(keypair: Optional[IdentityKeypair] = None) -> str:
    """
    Export public key as base64 string.

    Args:
        keypair: Optional IdentityKeypair (loads from disk if None)

    Returns:
        Base64-encoded public key
    """
    import base64

    if keypair is None:
        keypair = ensure_identity_keypair()

    return base64.b64encode(keypair.pub).decode("ascii")


def import_public_key_base64(b64_string: str) -> bytes:
    """
    Import public key from base64 string.

    Args:
        b64_string: Base64-encoded public key

    Returns:
        32-byte public key

    Raises:
        ValueError: If invalid base64 or wrong length
    """
    import base64

    pub = base64.b64decode(b64_string)

    if len(pub) != 32:
        raise ValueError(f"Invalid public key length: {len(pub)}, expected 32")

    return pub
