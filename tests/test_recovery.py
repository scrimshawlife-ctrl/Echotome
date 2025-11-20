"""
Echotome v3.1 Test Suite - Recovery Codes

Tests for recovery code generation and validation.
"""

import time
import pytest
from echotome.recovery import (
    generate_recovery_codes,
    hash_recovery_codes,
    verify_recovery_code,
    create_recovery_config,
    validate_and_mark_used,
    disable_recovery,
    get_recovery_strength,
    RecoveryConfig,
)


def test_generate_recovery_codes():
    """Test recovery code generation"""
    codes = generate_recovery_codes(5)

    assert len(codes) == 5
    assert all(len(code) == 19 for code in codes)  # XXXX-XXXX-XXXX-XXXX format
    assert all(code.count("-") == 3 for code in codes)
    assert all(c.isupper() or c == "-" or c.isdigit() for code in codes for c in code)

    # Codes should be unique
    assert len(set(codes)) == 5


def test_hash_recovery_codes():
    """Test recovery code hashing"""
    codes = ["A3F7-9B2D-4E8C-1FA6", "B8E4-1C9F-7A3D-2E5B"]
    hashes = hash_recovery_codes(codes)

    assert len(hashes) == 2
    assert all(len(h) == 64 for h in hashes)  # SHA-256 = 64 hex chars
    assert hashes[0] != hashes[1]  # Different codes -> different hashes


def test_verify_recovery_code():
    """Test recovery code verification"""
    codes = generate_recovery_codes(3)
    hashes = hash_recovery_codes(codes)

    # Valid codes should verify
    for code in codes:
        assert verify_recovery_code(code, hashes) == True

    # Invalid code should not verify
    assert verify_recovery_code("0000-0000-0000-0000", hashes) == False


def test_verify_recovery_code_normalization():
    """Test code verification with different formats"""
    code = "A3F7-9B2D-4E8C-1FA6"
    hashes = hash_recovery_codes([code])

    # Should work without hyphens
    assert verify_recovery_code("A3F79B2D4E8C1FA6", hashes) == True

    # Should work with spaces
    assert verify_recovery_code("A3F7 9B2D 4E8C 1FA6", hashes) == True

    # Should work lowercase
    assert verify_recovery_code("a3f7-9b2d-4e8c-1fa6", hashes) == True


def test_create_recovery_config():
    """Test recovery config creation"""
    config, codes = create_recovery_config(enabled=True, count=5)

    assert config.enabled == True
    assert len(config.codes_hashes) == 5
    assert len(codes) == 5
    assert config.use_count == 0
    assert config.last_used_timestamp is None

    # Verify all codes work
    for code in codes:
        assert verify_recovery_code(code, config.codes_hashes) == True


def test_create_recovery_config_disabled():
    """Test creating disabled recovery config"""
    config, codes = create_recovery_config(enabled=False)

    assert config.enabled == False
    assert len(config.codes_hashes) == 0
    assert len(codes) == 0


def test_validate_and_mark_used():
    """Test validating and marking codes as used"""
    config, codes = create_recovery_config(enabled=True, count=3)

    # Valid code should work
    timestamp = time.time()
    assert validate_and_mark_used(config, codes[0], timestamp) == True
    assert config.use_count == 1
    assert config.last_used_timestamp == timestamp

    # Using same code again should still work (codes don't expire)
    assert validate_and_mark_used(config, codes[0], timestamp + 10) == True
    assert config.use_count == 2

    # Invalid code should fail
    assert validate_and_mark_used(config, "INVALID-CODE", timestamp) == False
    assert config.use_count == 2  # Count should not increment


def test_validate_and_mark_used_disabled():
    """Test validation fails when recovery is disabled"""
    config, codes = create_recovery_config(enabled=False)

    timestamp = time.time()
    assert validate_and_mark_used(config, "any-code", timestamp) == False


def test_disable_recovery():
    """Test disabling recovery"""
    config, codes = create_recovery_config(enabled=True, count=5)

    disable_recovery(config)

    assert config.enabled == False
    assert len(config.codes_hashes) == 0

    # Should not validate anymore
    assert validate_and_mark_used(config, codes[0], time.time()) == False


def test_get_recovery_strength():
    """Test recovery strength descriptions"""
    # Disabled config
    config = RecoveryConfig(enabled=False, codes_hashes=[])
    assert get_recovery_strength(config) == "Unrecoverable (no recovery codes)"

    # Enabled with codes
    config, codes = create_recovery_config(enabled=True, count=5)
    assert get_recovery_strength(config) == "Recoverable (5 codes remaining)"

    # After using some codes
    config.use_count = 2
    assert get_recovery_strength(config) == "Recoverable (3 codes remaining)"

    # All codes used
    config.use_count = 5
    assert get_recovery_strength(config) == "Unrecoverable (all recovery codes used)"


def test_recovery_config_serialization():
    """Test recovery config can be serialized/deserialized"""
    config, codes = create_recovery_config(enabled=True, count=3)
    config.use_count = 1
    config.last_used_timestamp = time.time()

    # Serialize
    data = config.to_dict()

    # Deserialize
    config2 = RecoveryConfig.from_dict(data)

    assert config2.enabled == config.enabled
    assert config2.codes_hashes == config.codes_hashes
    assert config2.use_count == config.use_count
    assert config2.last_used_timestamp == config.last_used_timestamp
