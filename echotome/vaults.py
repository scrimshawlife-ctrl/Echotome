from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

from .crypto_core import encrypt_bytes, decrypt_bytes, EncryptedBlob
from .privacy_profiles import get_profile


# Default vault storage location
VAULT_DIR = Path.home() / ".echotome"
VAULT_DB = VAULT_DIR / "vaults.json"


@dataclass
class Vault:
    """
    Vault metadata container.

    A vault represents an encrypted storage space with specific profile.
    """
    id: str
    name: str
    profile: str
    rune_id: str
    created_at: float
    updated_at: float
    file_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Vault:
        return cls(**data)


def _ensure_vault_dir():
    """Ensure vault directory exists."""
    VAULT_DIR.mkdir(parents=True, exist_ok=True)


def _load_vault_db() -> dict:
    """Load vault database from disk."""
    _ensure_vault_dir()
    if not VAULT_DB.exists():
        return {"vaults": {}}

    with open(VAULT_DB, "r") as f:
        return json.load(f)


def _save_vault_db(db: dict):
    """Save vault database to disk."""
    _ensure_vault_dir()
    with open(VAULT_DB, "w") as f:
        json.dump(db, f, indent=2)


def create_vault(name: str, profile: str, rune_id: str) -> Vault:
    """
    Create a new vault.

    Args:
        name: Human-readable vault name
        profile: Privacy profile name
        rune_id: Rune ID from key derivation

    Returns:
        Vault instance
    """
    # Validate profile
    get_profile(profile)  # Raises if invalid

    vault = Vault(
        id=str(uuid.uuid4()),
        name=name,
        profile=profile,
        rune_id=rune_id,
        created_at=time.time(),
        updated_at=time.time(),
        file_count=0,
    )

    # Save to database
    db = _load_vault_db()
    db["vaults"][vault.id] = vault.to_dict()
    _save_vault_db(db)

    return vault


def get_vault(vault_id: str) -> Optional[Vault]:
    """
    Get vault by ID.

    Args:
        vault_id: Vault UUID

    Returns:
        Vault instance or None if not found
    """
    db = _load_vault_db()
    vault_data = db["vaults"].get(vault_id)
    if vault_data:
        return Vault.from_dict(vault_data)
    return None


def list_vaults() -> List[Vault]:
    """
    List all vaults.

    Returns:
        List of Vault instances
    """
    db = _load_vault_db()
    vaults = [Vault.from_dict(v) for v in db["vaults"].values()]
    return sorted(vaults, key=lambda v: v.updated_at, reverse=True)


def update_vault(vault: Vault):
    """
    Update vault metadata.

    Args:
        vault: Vault instance with updated fields
    """
    vault.updated_at = time.time()
    db = _load_vault_db()
    db["vaults"][vault.id] = vault.to_dict()
    _save_vault_db(db)


def delete_vault(vault_id: str) -> bool:
    """
    Delete a vault and its files.

    Args:
        vault_id: Vault UUID

    Returns:
        True if deleted, False if not found
    """
    db = _load_vault_db()
    if vault_id in db["vaults"]:
        # Delete vault files
        vault_path = VAULT_DIR / vault_id
        if vault_path.exists():
            import shutil
            shutil.rmtree(vault_path)

        # Remove from database
        del db["vaults"][vault_id]
        _save_vault_db(db)
        return True
    return False


def encrypt_file_to_vault(
    vault_id: str,
    file_bytes: bytes,
    key: bytes,
    filename: str = "encrypted.dat",
) -> Path:
    """
    Encrypt a file and save it to a vault.

    Args:
        vault_id: Target vault UUID
        file_bytes: File data to encrypt
        key: Encryption key
        filename: Name for the encrypted file

    Returns:
        Path to encrypted file

    Raises:
        ValueError: If vault not found
    """
    vault = get_vault(vault_id)
    if not vault:
        raise ValueError(f"Vault not found: {vault_id}")

    # Create vault directory
    vault_path = VAULT_DIR / vault_id
    vault_path.mkdir(parents=True, exist_ok=True)

    # Encrypt data
    context = {
        "profile_name": vault.profile,
        "rune_id": vault.rune_id,
        "filename": filename,
    }
    profile = get_profile(vault.profile)
    if profile.deniable:
        context["deniable"] = True

    blob = encrypt_bytes(file_bytes, key, context)

    # Save encrypted file
    output_path = vault_path / filename
    with open(output_path, "w") as f:
        f.write(blob.to_json())

    # Update vault metadata
    vault.file_count += 1
    update_vault(vault)

    return output_path


def decrypt_file_from_vault(
    vault_id: str,
    filename: str,
    key: bytes,
) -> bytes:
    """
    Decrypt a file from a vault.

    Args:
        vault_id: Source vault UUID
        filename: Name of encrypted file
        key: Decryption key

    Returns:
        Decrypted file bytes

    Raises:
        ValueError: If vault or file not found, or decryption fails
    """
    vault = get_vault(vault_id)
    if not vault:
        raise ValueError(f"Vault not found: {vault_id}")

    # Load encrypted file
    vault_path = VAULT_DIR / vault_id
    file_path = vault_path / filename

    if not file_path.exists():
        raise ValueError(f"File not found in vault: {filename}")

    with open(file_path, "r") as f:
        blob = EncryptedBlob.from_json(f.read())

    # Decrypt
    plaintext = decrypt_bytes(blob, key)

    # Update vault access time
    update_vault(vault)

    return plaintext


def list_vault_files(vault_id: str) -> List[str]:
    """
    List all files in a vault.

    Args:
        vault_id: Vault UUID

    Returns:
        List of filenames
    """
    vault_path = VAULT_DIR / vault_id
    if not vault_path.exists():
        return []

    files = [f.name for f in vault_path.iterdir() if f.is_file()]
    return sorted(files)


def get_vault_stats() -> dict:
    """
    Get statistics about all vaults.

    Returns:
        Dictionary with vault statistics
    """
    vaults = list_vaults()
    total_files = sum(v.file_count for v in vaults)

    profiles = {}
    for v in vaults:
        profiles[v.profile] = profiles.get(v.profile, 0) + 1

    return {
        "total_vaults": len(vaults),
        "total_files": total_files,
        "profiles": profiles,
        "vault_dir": str(VAULT_DIR),
    }
