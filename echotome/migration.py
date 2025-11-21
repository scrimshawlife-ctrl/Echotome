"""
Echotome v3.1 Versioning & Migration

Ensures forward compatibility and handles data structure migrations
between Echotome versions.

Version History:
- v3.0: Initial Ritual Cryptography Engine release
- v3.1: Threat models, recovery codes, multi-part rituals, privacy guardrails
"""

from dataclasses import dataclass
from typing import Any, Optional
from packaging import version as pkg_version


# Current version
ECHOTOME_VERSION = "3.1.0"

# Version component identifiers
KDF_VERSION = "argon2id-v1"
TSC_VERSION = "tsc-v1"
RITUAL_MODE_VERSION = "ritual-v1"
ROC_VERSION = "roc-v1"
STEGO_VERSION = "steg-v1"


@dataclass
class VersionInfo:
    """Version information for Echotome artifacts"""

    echotome_version: str
    kdf_version: str
    tsc_version: str
    ritual_mode_version: str
    roc_version: Optional[str] = None
    stego_version: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary"""
        return {
            "echotome_version": self.echotome_version,
            "kdf_version": self.kdf_version,
            "tsc_version": self.tsc_version,
            "ritual_mode_version": self.ritual_mode_version,
            "roc_version": self.roc_version,
            "stego_version": self.stego_version,
        }

    @staticmethod
    def from_dict(data: dict) -> "VersionInfo":
        """Deserialize from dictionary"""
        return VersionInfo(
            echotome_version=data.get("echotome_version", "3.0.0"),
            kdf_version=data.get("kdf_version", KDF_VERSION),
            tsc_version=data.get("tsc_version", TSC_VERSION),
            ritual_mode_version=data.get("ritual_mode_version", RITUAL_MODE_VERSION),
            roc_version=data.get("roc_version"),
            stego_version=data.get("stego_version"),
        )

    @staticmethod
    def current() -> "VersionInfo":
        """Get current version info"""
        return VersionInfo(
            echotome_version=ECHOTOME_VERSION,
            kdf_version=KDF_VERSION,
            tsc_version=TSC_VERSION,
            ritual_mode_version=RITUAL_MODE_VERSION,
            roc_version=ROC_VERSION,
            stego_version=STEGO_VERSION,
        )


def parse_version(version_str: str) -> tuple[int, int, int]:
    """
    Parse semantic version string.

    Args:
        version_str: Version string (e.g., "3.1.0")

    Returns:
        Tuple of (major, minor, patch)
    """
    v = pkg_version.parse(version_str)
    return (v.major, v.minor, v.micro)


def is_compatible(artifact_version: str, current_version: str) -> bool:
    """
    Check if artifact version is compatible with current version.

    Compatibility rules:
    - Same major version is compatible
    - Newer minor version within same major is compatible
    - Older minor version within same major may be compatible (requires migration)

    Args:
        artifact_version: Version of the artifact
        current_version: Current Echotome version

    Returns:
        True if compatible (possibly with migration)
    """
    artifact_major, artifact_minor, artifact_patch = parse_version(artifact_version)
    current_major, current_minor, current_patch = parse_version(current_version)

    # Different major version = incompatible
    if artifact_major != current_major:
        return False

    # Same major version = compatible
    return True


def needs_migration(artifact_version: str, current_version: str) -> bool:
    """
    Check if artifact needs migration.

    Args:
        artifact_version: Version of the artifact
        current_version: Current Echotome version

    Returns:
        True if migration is needed
    """
    if not is_compatible(artifact_version, current_version):
        return False

    artifact_major, artifact_minor, artifact_patch = parse_version(artifact_version)
    current_major, current_minor, current_patch = parse_version(current_version)

    # If artifact is older minor version, needs migration
    return artifact_minor < current_minor


def migrate_vault(vault_dict: dict, from_version: str, to_version: str) -> dict:
    """
    Migrate vault metadata from one version to another.

    Args:
        vault_dict: Vault metadata dictionary
        from_version: Source version
        to_version: Target version

    Returns:
        Migrated vault dictionary

    Raises:
        ValueError: If migration is not supported
    """
    if not is_compatible(from_version, to_version):
        raise ValueError(
            f"Cannot migrate from {from_version} to {to_version}: incompatible major versions"
        )

    # No migration needed if same version
    if from_version == to_version:
        return vault_dict

    # Parse versions
    from_major, from_minor, _ = parse_version(from_version)
    to_major, to_minor, _ = parse_version(to_version)

    # Apply migrations in sequence
    current_dict = vault_dict.copy()

    # v3.0 -> v3.1
    if from_major == 3 and from_minor == 0 and to_minor >= 1:
        current_dict = _migrate_v30_to_v31(current_dict)

    # Update version info
    if "version_info" not in current_dict:
        current_dict["version_info"] = {}

    current_dict["version_info"]["echotome_version"] = to_version

    return current_dict


def _migrate_v30_to_v31(vault_dict: dict) -> dict:
    """
    Migrate vault from v3.0 to v3.1.

    Changes:
    - Add recovery config (disabled by default)
    - Add unrecoverable flag
    - Add version_info if missing
    - Convert ritual metadata to support multi-part (single track becomes list)
    """
    migrated = vault_dict.copy()

    # Add recovery config (disabled by default for backwards compat)
    if "recovery" not in migrated:
        migrated["recovery"] = {
            "enabled": False,
            "codes_hashes": [],
            "use_count": 0,
            "last_used_timestamp": None,
        }

    # Add unrecoverable flag
    if "unrecoverable" not in migrated:
        # Check profile to determine default
        profile = migrated.get("profile", "Quick Lock")
        if profile == "Black Vault":
            migrated["unrecoverable"] = True
        else:
            migrated["unrecoverable"] = False

    # Add version info if missing
    if "version_info" not in migrated:
        migrated["version_info"] = {
            "echotome_version": "3.1.0",
            "kdf_version": KDF_VERSION,
            "tsc_version": TSC_VERSION,
            "ritual_mode_version": RITUAL_MODE_VERSION,
        }

    # Convert ritual metadata to multi-part format (if exists)
    if "roc" in migrated and isinstance(migrated["roc"], dict):
        roc = migrated["roc"]

        # Check if already multi-part format
        if "tracks" not in roc:
            # Single track format - convert to list
            single_track = {
                "audio_hash": roc.get("audio_hash", ""),
                "active_start": roc.get("active_start", 0),
                "active_end": roc.get("active_end", 0),
                "riv": roc.get("riv", ""),
            }

            # Create multi-part structure
            migrated["roc"]["tracks"] = [single_track]

            # Keep old fields for compatibility
            # (they will be ignored by v3.1 but v3.0 can still read them)

    return migrated


def migrate_roc(roc_dict: dict, from_version: str, to_version: str) -> dict:
    """
    Migrate ROC (Ritual Ownership Certificate) from one version to another.

    Args:
        roc_dict: ROC dictionary
        from_version: Source version
        to_version: Target version

    Returns:
        Migrated ROC dictionary
    """
    if not is_compatible(from_version, to_version):
        raise ValueError(
            f"Cannot migrate ROC from {from_version} to {to_version}: incompatible major versions"
        )

    if from_version == to_version:
        return roc_dict

    # Parse versions
    from_major, from_minor, _ = parse_version(from_version)
    to_major, to_minor, _ = parse_version(to_version)

    current_dict = roc_dict.copy()

    # v3.0 -> v3.1 (same migration as vault)
    if from_major == 3 and from_minor == 0 and to_minor >= 1:
        if "tracks" not in current_dict:
            # Convert to multi-track format
            single_track = {
                "audio_hash": current_dict.get("audio_hash", ""),
                "active_start": current_dict.get("active_start", 0),
                "active_end": current_dict.get("active_end", 0),
                "riv": current_dict.get("riv", ""),
            }
            current_dict["tracks"] = [single_track]

        # Update version
        current_dict["version"] = "3.1"

    return current_dict


def get_migration_summary(from_version: str, to_version: str) -> str:
    """
    Get human-readable summary of migration changes.

    Args:
        from_version: Source version
        to_version: Target version

    Returns:
        Summary string describing changes
    """
    if from_version == to_version:
        return "No migration needed (same version)"

    from_major, from_minor, _ = parse_version(from_version)
    to_major, to_minor, _ = parse_version(to_version)

    if from_major != to_major:
        return f"ERROR: Cannot migrate across major versions ({from_version} -> {to_version})"

    changes = []

    # v3.0 -> v3.1
    if from_major == 3 and from_minor == 0 and to_minor >= 1:
        changes.append("• Added recovery code support (disabled by default)")
        changes.append("• Added unrecoverable flag for vaults")
        changes.append("• Converted ritual metadata to multi-part format")
        changes.append("• Added comprehensive version tracking")

    if not changes:
        return f"Migration from {from_version} to {to_version}: no structural changes"

    return f"Migration from {from_version} to {to_version}:\n" + "\n".join(changes)


def validate_version_compatibility(vault_dict: dict) -> tuple[bool, str]:
    """
    Validate that a vault can be loaded with current version.

    Args:
        vault_dict: Vault metadata dictionary

    Returns:
        Tuple of (is_compatible, message)
    """
    if "version_info" not in vault_dict:
        # Assume v3.0 if no version info
        artifact_version = "3.0.0"
    else:
        artifact_version = vault_dict["version_info"].get("echotome_version", "3.0.0")

    if not is_compatible(artifact_version, ECHOTOME_VERSION):
        return False, (
            f"Vault version {artifact_version} is incompatible with "
            f"Echotome {ECHOTOME_VERSION}. Major version mismatch."
        )

    if needs_migration(artifact_version, ECHOTOME_VERSION):
        return True, (
            f"Vault can be loaded but requires migration from "
            f"{artifact_version} to {ECHOTOME_VERSION}."
        )

    return True, f"Vault version {artifact_version} is compatible."
