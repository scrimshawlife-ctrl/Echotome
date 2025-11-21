"""
Echotome v3.1 Test Suite - Privacy Profiles

Tests for threat models and profile validation.
"""

import pytest
from echotome.privacy_profiles import (
    get_profile,
    list_profiles,
    describe_profile,
    validate_ritual_mode,
    QUICK_LOCK,
    RITUAL_LOCK,
    BLACK_VAULT,
)


def test_get_profile():
    """Test getting profiles by name"""
    assert get_profile("Quick Lock").name == "Quick Lock"
    assert get_profile("quick").name == "Quick Lock"
    assert get_profile("q").name == "Quick Lock"

    assert get_profile("Ritual Lock").name == "Ritual Lock"
    assert get_profile("Black Vault").name == "Black Vault"


def test_get_profile_invalid():
    """Test invalid profile names raise ValueError"""
    with pytest.raises(ValueError):
        get_profile("invalid_profile")


def test_list_profiles():
    """Test listing all profiles"""
    profiles = list_profiles()
    assert len(profiles) == 3
    assert QUICK_LOCK in profiles
    assert RITUAL_LOCK in profiles
    assert BLACK_VAULT in profiles


def test_threat_models():
    """Test that all profiles have threat models"""
    for profile in list_profiles():
        assert profile.threat_model_id in ["casual", "focused", "targeted"]
        assert len(profile.threat_model_description) > 0
        assert len(profile.threat_model_assumptions) > 0
        assert len(profile.threat_model_protects_against) > 0
        assert len(profile.threat_model_does_not_protect_against) > 0


def test_describe_profile():
    """Test profile description includes all v3.1 fields"""
    desc = describe_profile("Quick Lock")

    assert desc["name"] == "Quick Lock"
    assert desc["threat_model_id"] == "casual"
    assert "audio_weight" in desc
    assert "requires_mic" in desc
    assert "requires_timing" in desc
    assert "kdf_time" in desc
    assert "kdf_memory" in desc
    assert "kdf_parallelism" in desc


def test_validate_ritual_mode():
    """Test ritual mode validation per profile"""
    # Quick Lock allows all modes
    assert validate_ritual_mode("Quick Lock", "file") == True
    assert validate_ritual_mode("Quick Lock", "mic") == True
    assert validate_ritual_mode("Quick Lock", "visual") == True

    # Ritual Lock allows file and mic
    assert validate_ritual_mode("Ritual Lock", "file") == True
    assert validate_ritual_mode("Ritual Lock", "mic") == True
    assert validate_ritual_mode("Ritual Lock", "visual") == True

    # Black Vault requires mic only
    assert validate_ritual_mode("Black Vault", "file") == False
    assert validate_ritual_mode("Black Vault", "mic") == True
    assert validate_ritual_mode("Black Vault", "visual") == False


def test_validate_ritual_mode_invalid():
    """Test invalid ritual mode raises ValueError"""
    with pytest.raises(ValueError):
        validate_ritual_mode("Quick Lock", "invalid_mode")


def test_profile_security_parameters():
    """Test security parameters are properly set"""
    # Quick Lock: minimal security
    assert QUICK_LOCK.audio_weight == 0.0
    assert QUICK_LOCK.requires_mic == False
    assert QUICK_LOCK.requires_timing == False
    assert QUICK_LOCK.deniable == False

    # Ritual Lock: balanced security
    assert RITUAL_LOCK.audio_weight == 0.7
    assert RITUAL_LOCK.requires_mic == False
    assert RITUAL_LOCK.requires_timing == True
    assert RITUAL_LOCK.deniable == False

    # Black Vault: maximum security
    assert BLACK_VAULT.audio_weight == 1.0
    assert BLACK_VAULT.requires_mic == True
    assert BLACK_VAULT.requires_timing == True
    assert BLACK_VAULT.deniable == True


def test_kdf_parameters():
    """Test KDF parameters increase with security"""
    quick_time, quick_mem, quick_par = QUICK_LOCK.kdf_time, QUICK_LOCK.kdf_memory, QUICK_LOCK.kdf_parallelism
    ritual_time, ritual_mem, ritual_par = RITUAL_LOCK.kdf_time, RITUAL_LOCK.kdf_memory, RITUAL_LOCK.kdf_parallelism
    black_time, black_mem, black_par = BLACK_VAULT.kdf_time, BLACK_VAULT.kdf_memory, BLACK_VAULT.kdf_parallelism

    # Time should increase
    assert quick_time < ritual_time < black_time

    # Memory should increase
    assert quick_mem < black_mem

    # Parallelism should increase
    assert quick_par <= black_par
