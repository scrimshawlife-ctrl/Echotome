from __future__ import annotations

import base64
import hashlib
import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, List

from .identity_keys import (
    IdentityKeypair,
    ensure_identity_keypair,
    sign_data,
    verify_signature,
)


# Ritual certificate storage
RITUALS_DIR = Path.home() / ".echotome" / "rituals"


@dataclass
class RitualTrack:
    """
    Single audio track in a ritual binding.

    v3.1: Supports multi-part rituals where multiple tracks must be played in sequence.
    """

    audio_hash: str  # SHA-256 of audio file (hex)
    active_start: int  # Start frame of active region
    active_end: int  # End frame of active region
    riv: str  # Ritual Imprint Vector (hex)
    temporal_hash: Optional[str] = None  # Hex-encoded temporal hash
    track_length: Optional[int] = None  # Track length in samples

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "RitualTrack":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class RitualCertificatePayload:
    """
    Payload of a Ritual Ownership Certificate (ROC).

    Contains all metadata about the ritual binding, excluding signature.

    v3.1: Supports multi-part rituals via 'tracks' field.
    For backward compatibility, single-track fields are kept.
    """

    version: str  # ROC format version (e.g., "3.0", "3.1")
    owner_pub: str  # Base64-encoded owner public key
    rune_id: str  # Unique rune identifier
    profile: str  # Privacy profile name
    created_at: float  # Unix timestamp

    # Single-track fields (v3.0 compat - deprecated in v3.1)
    audio_hash: Optional[str] = None  # SHA-256 of audio file (hex)
    active_start: Optional[int] = None  # Start frame of active region
    active_end: Optional[int] = None  # End frame of active region
    temporal_hash: Optional[str] = None  # Hex-encoded temporal hash
    track_length: Optional[int] = None  # Track length in samples

    # Multi-track field (v3.1+)
    tracks: Optional[List[RitualTrack]] = None  # List of tracks in sequence

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        d = asdict(self)

        # Convert RitualTrack objects in tracks list
        if d.get("tracks"):
            d["tracks"] = [track.to_dict() if hasattr(track, 'to_dict') else track
                          for track in d["tracks"]]

        return d

    @classmethod
    def from_dict(cls, data: dict) -> RitualCertificatePayload:
        """Create from dictionary."""
        # Convert tracks if present
        if "tracks" in data and data["tracks"]:
            data = data.copy()
            data["tracks"] = [
                RitualTrack.from_dict(t) if isinstance(t, dict) else t
                for t in data["tracks"]
            ]
        return cls(**data)

    def is_multi_track(self) -> bool:
        """Check if this is a multi-track ritual."""
        return self.tracks is not None and len(self.tracks) > 1

    def get_track_count(self) -> int:
        """Get number of tracks in this ritual."""
        if self.tracks:
            return len(self.tracks)
        elif self.audio_hash:  # Legacy single-track
            return 1
        return 0

    def get_all_audio_hashes(self) -> List[str]:
        """Get all audio hashes (supports both single and multi-track)."""
        if self.tracks:
            return [track.audio_hash for track in self.tracks]
        elif self.audio_hash:
            return [self.audio_hash]
        return []

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), sort_keys=True, indent=2)

    def to_bytes(self) -> bytes:
        """
        Convert to canonical bytes representation for signing.

        Returns:
            UTF-8 encoded JSON with sorted keys
        """
        # Use sorted keys for deterministic serialization
        return json.dumps(self.to_dict(), sort_keys=True).encode("utf-8")


@dataclass
class RitualCertificate:
    """
    Complete Ritual Ownership Certificate (ROC).

    A ROC is a cryptographically signed document that proves:
    - Who created the ritual binding (owner_pub)
    - What audio was bound (audio_hash, active region)
    - When it was created (created_at)
    - What profile was used (profile)

    The signature prevents forgery and ensures authenticity.
    """

    payload: RitualCertificatePayload
    signature: str  # Base64-encoded Ed25519 signature

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "payload": self.payload.to_dict(),
            "signature": self.signature,
        }

    @classmethod
    def from_dict(cls, data: dict) -> RitualCertificate:
        """Create from dictionary."""
        return cls(
            payload=RitualCertificatePayload.from_dict(data["payload"]),
            signature=data["signature"],
        )

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    @classmethod
    def from_json(cls, json_str: str) -> RitualCertificate:
        """Deserialize from JSON."""
        return cls.from_dict(json.loads(json_str))


def create_ritual_certificate(
    rune_id: str,
    audio_hash: str,
    active_start: int,
    active_end: int,
    profile: str,
    temporal_hash: Optional[bytes] = None,
    track_length: Optional[int] = None,
    riv: Optional[str] = None,
    keypair: Optional[IdentityKeypair] = None,
) -> RitualCertificate:
    """
    Create a new single-track Ritual Ownership Certificate (ROC).

    v3.1: Creates backward-compatible v3.0 format but also includes tracks list
    with single track for forward compatibility.

    Args:
        rune_id: Unique rune identifier
        audio_hash: SHA-256 hash of audio file (hex string)
        active_start: Start frame index of active region
        active_end: End frame index of active region
        profile: Privacy profile name
        temporal_hash: Optional temporal hash bytes
        track_length: Optional track length in samples
        riv: Optional Ritual Imprint Vector (hex)
        keypair: Optional identity keypair (loads from disk if None)

    Returns:
        Signed RitualCertificate

    Raises:
        ValueError: If parameters invalid
    """
    if keypair is None:
        keypair = ensure_identity_keypair()

    # Create single track
    track = RitualTrack(
        audio_hash=audio_hash,
        active_start=active_start,
        active_end=active_end,
        riv=riv or "",
        temporal_hash=temporal_hash.hex() if temporal_hash else None,
        track_length=track_length,
    )

    # Create payload (v3.1 format with both legacy and new fields)
    payload = RitualCertificatePayload(
        version="3.1",
        owner_pub=base64.b64encode(keypair.pub).decode("ascii"),
        rune_id=rune_id,
        profile=profile,
        created_at=time.time(),
        # Legacy fields for v3.0 compat
        audio_hash=audio_hash,
        active_start=active_start,
        active_end=active_end,
        temporal_hash=temporal_hash.hex() if temporal_hash else None,
        track_length=track_length,
        # v3.1 multi-track field
        tracks=[track],
    )

    # Sign payload
    payload_bytes = payload.to_bytes()
    signature_bytes = sign_data(payload_bytes, keypair)
    signature_b64 = base64.b64encode(signature_bytes).decode("ascii")

    return RitualCertificate(payload=payload, signature=signature_b64)


def create_multi_track_ritual_certificate(
    rune_id: str,
    tracks: List[RitualTrack],
    profile: str,
    keypair: Optional[IdentityKeypair] = None,
) -> RitualCertificate:
    """
    Create a multi-track Ritual Ownership Certificate (ROC).

    v3.1: Supports multiple tracks that must be played in sequence.

    Args:
        rune_id: Unique rune identifier
        tracks: List of RitualTrack objects in order
        profile: Privacy profile name
        keypair: Optional identity keypair (loads from disk if None)

    Returns:
        Signed RitualCertificate

    Raises:
        ValueError: If tracks list is empty or invalid
    """
    if not tracks:
        raise ValueError("Must provide at least one track")

    if keypair is None:
        keypair = ensure_identity_keypair()

    # Create payload (v3.1 format, no legacy fields for multi-track)
    payload = RitualCertificatePayload(
        version="3.1",
        owner_pub=base64.b64encode(keypair.pub).decode("ascii"),
        rune_id=rune_id,
        profile=profile,
        created_at=time.time(),
        tracks=tracks,
        # No legacy fields - multi-track only
    )

    # Sign payload
    payload_bytes = payload.to_bytes()
    signature_bytes = sign_data(payload_bytes, keypair)
    signature_b64 = base64.b64encode(signature_bytes).decode("ascii")

    return RitualCertificate(payload=payload, signature=signature_b64)


def verify_ritual_certificate(
    cert: RitualCertificate,
    expected_audio_hash: Optional[str] = None,
    allowed_pub_keys: Optional[List[bytes]] = None,
) -> bool:
    """
    Verify a Ritual Ownership Certificate.

    Checks:
    1. Signature is valid for payload
    2. Audio hash matches expected (if provided)
    3. Owner public key is in allowed list (if provided)

    Args:
        cert: RitualCertificate to verify
        expected_audio_hash: Optional expected audio hash (hex)
        allowed_pub_keys: Optional list of allowed public key bytes

    Returns:
        True if certificate is valid, False otherwise
    """
    try:
        # Decode signature and public key
        signature_bytes = base64.b64decode(cert.signature)
        owner_pub_bytes = base64.b64decode(cert.payload.owner_pub)

        # Verify signature
        payload_bytes = cert.payload.to_bytes()
        if not verify_signature(payload_bytes, signature_bytes, owner_pub_bytes):
            return False

        # Check audio hash if provided
        if expected_audio_hash is not None:
            if cert.payload.audio_hash != expected_audio_hash:
                return False

        # Check public key whitelist if provided
        if allowed_pub_keys is not None:
            if owner_pub_bytes not in allowed_pub_keys:
                return False

        return True

    except Exception:
        return False


def save_ritual_certificate(cert: RitualCertificate) -> Path:
    """
    Save Ritual Certificate to disk.

    Certificates are stored as:
    ~/.echotome/rituals/<rune_id>.roc.json

    Args:
        cert: RitualCertificate to save

    Returns:
        Path to saved certificate file

    Raises:
        PermissionError: If cannot create rituals directory
    """
    # Ensure directory exists
    RITUALS_DIR.mkdir(parents=True, exist_ok=True)

    # Build filename
    filename = f"{cert.payload.rune_id}.roc.json"
    cert_path = RITUALS_DIR / filename

    # Save certificate
    with open(cert_path, "w") as f:
        f.write(cert.to_json())

    return cert_path


def load_certificate_by_rune_id(rune_id: str) -> Optional[RitualCertificate]:
    """
    Load certificate by rune ID.

    Args:
        rune_id: Rune identifier

    Returns:
        RitualCertificate if found, None otherwise
    """
    filename = f"{rune_id}.roc.json"
    cert_path = RITUALS_DIR / filename

    if not cert_path.exists():
        return None

    try:
        with open(cert_path, "r") as f:
            return RitualCertificate.from_json(f.read())
    except Exception:
        return None


def load_certificate_by_audio_hash(audio_hash: str) -> Optional[RitualCertificate]:
    """
    Load certificate by audio hash.

    Searches all certificates for matching audio_hash.

    Args:
        audio_hash: SHA-256 audio hash (hex)

    Returns:
        First matching RitualCertificate, or None if not found
    """
    if not RITUALS_DIR.exists():
        return None

    # Search all .roc.json files
    for cert_file in RITUALS_DIR.glob("*.roc.json"):
        try:
            with open(cert_file, "r") as f:
                cert = RitualCertificate.from_json(f.read())

            if cert.payload.audio_hash == audio_hash:
                return cert

        except Exception:
            continue

    return None


def list_all_certificates() -> List[RitualCertificate]:
    """
    List all ritual certificates.

    Returns:
        List of RitualCertificate instances
    """
    if not RITUALS_DIR.exists():
        return []

    certs = []

    for cert_file in RITUALS_DIR.glob("*.roc.json"):
        try:
            with open(cert_file, "r") as f:
                cert = RitualCertificate.from_json(f.read())
            certs.append(cert)
        except Exception:
            continue

    # Sort by created_at (newest first)
    certs.sort(key=lambda c: c.payload.created_at, reverse=True)

    return certs


def delete_certificate(rune_id: str) -> bool:
    """
    Delete a ritual certificate.

    Args:
        rune_id: Rune identifier

    Returns:
        True if deleted, False if not found
    """
    filename = f"{rune_id}.roc.json"
    cert_path = RITUALS_DIR / filename

    if cert_path.exists():
        cert_path.unlink()
        return True

    return False


def compute_audio_hash(audio_path: Path) -> str:
    """
    Compute SHA-256 hash of audio file.

    Args:
        audio_path: Path to audio file

    Returns:
        Hex-encoded SHA-256 hash
    """
    h = hashlib.sha256()

    with open(audio_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)

    return h.hexdigest()


def compute_roc_hash(cert: RitualCertificate) -> str:
    """
    Compute hash of ROC for cross-verification.

    Used in steganography payload to link sigil to ROC.

    Args:
        cert: RitualCertificate

    Returns:
        Hex-encoded SHA-256 hash of ROC JSON
    """
    cert_json = cert.to_json()
    return hashlib.sha256(cert_json.encode("utf-8")).hexdigest()


def get_certificate_summary(cert: RitualCertificate) -> dict:
    """
    Get human-readable summary of certificate.

    Args:
        cert: RitualCertificate

    Returns:
        Dictionary with summary information
    """
    import datetime

    created_dt = datetime.datetime.fromtimestamp(cert.payload.created_at)

    return {
        "rune_id": cert.payload.rune_id,
        "profile": cert.payload.profile,
        "created_at": created_dt.isoformat(),
        "audio_hash": cert.payload.audio_hash[:16] + "...",  # Truncated
        "active_region": f"frames {cert.payload.active_start}-{cert.payload.active_end}",
        "owner_fingerprint": base64.b64decode(cert.payload.owner_pub)[:8].hex().upper(),
    }
