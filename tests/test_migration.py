"""
Echotome v3.1 Test Suite - Versioning & Migration

Tests for version compatibility and data migration.
"""

import pytest
from echotome.migration import (
    parse_version,
    is_compatible,
    needs_migration,
    migrate_vault,
    validate_version_compatibility,
    ECHOTOME_VERSION,
    VersionInfo,
)


def test_parse_version():
    """Test version string parsing"""
    assert parse_version("3.0.0") == (3, 0, 0)
    assert parse_version("3.1.0") == (3, 1, 0)
    assert parse_version("4.0.0") == (4, 0, 0)


def test_is_compatible():
    """Test version compatibility checks"""
    # Same major version is compatible
    assert is_compatible("3.0.0", "3.1.0") == True
    assert is_compatible("3.1.0", "3.0.0") == True
    assert is_compatible("3.1.0", "3.1.0") == True

    # Different major version is incompatible
    assert is_compatible("3.0.0", "4.0.0") == False
    assert is_compatible("4.0.0", "3.0.0") == False


def test_needs_migration():
    """Test migration need detection"""
    # Older minor version needs migration
    assert needs_migration("3.0.0", "3.1.0") == True

    # Same version doesn't need migration
    assert needs_migration("3.1.0", "3.1.0") == False

    # Newer version doesn't need migration
    assert needs_migration("3.1.0", "3.0.0") == False

    # Different major version is incompatible
    assert needs_migration("3.0.0", "4.0.0") == False


def test_migrate_vault_v30_to_v31():
    """Test vault migration from v3.0 to v3.1"""
    # v3.0 vault format
    vault_v30 = {
        "name": "Test Vault",
        "profile": "Quick Lock",
        "rune_id": "ECH-A1B2C3D4",
        "created_at": 1234567890.0,
        "roc": {
            "audio_hash": "abc123",
            "active_start": 100,
            "active_end": 200,
            "riv": "def456",
        },
    }

    # Migrate to v3.1
    vault_v31 = migrate_vault(vault_v30, "3.0.0", "3.1.0")

    # Should have new v3.1 fields
    assert "recovery" in vault_v31
    assert vault_v31["recovery"]["enabled"] == False
    assert "unrecoverable" in vault_v31
    assert "version_info" in vault_v31
    assert vault_v31["version_info"]["echotome_version"] == "3.1.0"

    # Should convert ROC to multi-track format
    assert "tracks" in vault_v31["roc"]
    assert len(vault_v31["roc"]["tracks"]) == 1
    assert vault_v31["roc"]["tracks"][0]["audio_hash"] == "abc123"


def test_migrate_vault_same_version():
    """Test migration with same version is no-op"""
    vault = {
        "name": "Test Vault",
        "profile": "Quick Lock",
        "version_info": {"echotome_version": "3.1.0"},
    }

    migrated = migrate_vault(vault, "3.1.0", "3.1.0")

    # Should be unchanged (except deep copy)
    assert migrated["name"] == vault["name"]
    assert migrated["profile"] == vault["profile"]


def test_migrate_vault_incompatible():
    """Test migration fails for incompatible versions"""
    vault = {"name": "Test Vault"}

    with pytest.raises(ValueError, match="incompatible major versions"):
        migrate_vault(vault, "3.0.0", "4.0.0")


def test_validate_version_compatibility():
    """Test vault version validation"""
    # v3.0 vault should be compatible but need migration
    vault_v30 = {
        "version_info": {"echotome_version": "3.0.0"}
    }
    compatible, message = validate_version_compatibility(vault_v30)
    assert compatible == True
    assert "migration" in message.lower()

    # v3.1 vault should be compatible
    vault_v31 = {
        "version_info": {"echotome_version": "3.1.0"}
    }
    compatible, message = validate_version_compatibility(vault_v31)
    assert compatible == True

    # v4.0 vault should be incompatible
    vault_v40 = {
        "version_info": {"echotome_version": "4.0.0"}
    }
    compatible, message = validate_version_compatibility(vault_v40)
    assert compatible == False
    assert "incompatible" in message.lower()


def test_validate_version_compatibility_missing():
    """Test validation assumes v3.0 if no version info"""
    vault_no_version = {"name": "Test Vault"}

    compatible, message = validate_version_compatibility(vault_no_version)
    assert compatible == True
    assert "migration" in message.lower()


def test_version_info():
    """Test VersionInfo dataclass"""
    version = VersionInfo.current()

    assert version.echotome_version == ECHOTOME_VERSION
    assert version.kdf_version is not None
    assert version.tsc_version is not None
    assert version.ritual_mode_version is not None


def test_version_info_serialization():
    """Test VersionInfo serialization"""
    version = VersionInfo.current()

    # Serialize
    data = version.to_dict()

    # Deserialize
    version2 = VersionInfo.from_dict(data)

    assert version2.echotome_version == version.echotome_version
    assert version2.kdf_version == version.kdf_version
    assert version2.tsc_version == version.tsc_version
