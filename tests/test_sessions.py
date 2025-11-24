"""
Echotome v3.2 Test Suite - Session Management

Tests for time-limited ritual windows and ephemeral plaintext.

v3.2: Updated TTLs - Quick: 1h, Ritual: 20m, Black: 5m
"""

import time
import pytest
from pathlib import Path
from echotome.sessions import (
    Session,
    SessionConfig,
    SessionManager,
    create_session,
    get_session,
    end_session,
    cleanup_expired_sessions,
)


def test_session_config_for_profiles():
    """Test session configs are appropriate for each profile (v3.2 TTLs)"""
    quick_config = SessionConfig.for_profile("Quick Lock")
    assert quick_config.default_ttl_seconds == 60 * 60  # v3.2: 1 hour
    assert quick_config.allow_external_apps == True
    assert quick_config.secure_delete == False

    ritual_config = SessionConfig.for_profile("Ritual Lock")
    assert ritual_config.default_ttl_seconds == 20 * 60  # v3.2: 20 min
    assert ritual_config.secure_delete == True

    black_config = SessionConfig.for_profile("Black Vault")
    assert black_config.default_ttl_seconds == 5 * 60  # v3.2: 5 min (unchanged)
    assert black_config.auto_lock_on_background == True
    assert black_config.allow_external_apps == False  # Never for Black Vault
    assert black_config.secure_delete == True


def test_create_session():
    """Test session creation"""
    manager = SessionManager()
    master_key = b"test_master_key_32_bytes_long_1"

    session = manager.create_session(
        vault_id="test_vault",
        profile="Quick Lock",
        master_key=master_key,
    )

    assert session.session_id is not None
    assert len(session.session_id) == 64  # SHA-256 hex
    assert session.vault_id == "test_vault"
    assert session.profile == "Quick Lock"
    assert session.master_key == master_key
    assert session.session_dir.exists()
    assert session.session_dir.stat().st_mode & 0o777 == 0o700  # Owner-only perms

    # Cleanup
    manager.end_session(session.session_id)


def test_session_expiry():
    """Test session expires after TTL"""
    manager = SessionManager()
    master_key = b"test_master_key"

    # Create session with 1 second TTL
    session = manager.create_session(
        vault_id="test_vault",
        profile="Quick Lock",
        master_key=master_key,
        ttl_seconds=1,
    )

    session_id = session.session_id

    # Should be active immediately
    assert manager.get_session(session_id) is not None

    # Wait for expiry
    time.sleep(1.5)

    # Should be expired now
    assert manager.get_session(session_id) is None


def test_session_time_remaining():
    """Test session time tracking"""
    manager = SessionManager()

    session = manager.create_session(
        vault_id="test_vault",
        profile="Quick Lock",
        master_key=b"test_key",
        ttl_seconds=60,  # 1 minute
    )

    # Should have ~60 seconds remaining
    remaining = session.time_remaining()
    assert 58 <= remaining <= 60

    # Format should be MM:SS
    formatted = session.format_time_remaining()
    assert formatted.startswith("00:") or formatted.startswith("01:")

    # Cleanup
    manager.end_session(session.session_id)


def test_extend_session():
    """Test extending session TTL"""
    manager = SessionManager()

    session = manager.create_session(
        vault_id="test_vault",
        profile="Quick Lock",
        master_key=b"test_key",
        ttl_seconds=60,
    )

    initial_remaining = session.time_remaining()

    # Extend by 30 seconds
    manager.extend_session(session.session_id, 30)

    new_remaining = session.time_remaining()

    # Should have ~30 more seconds
    assert new_remaining >= initial_remaining + 25

    # Cleanup
    manager.end_session(session.session_id)


def test_extend_session_respects_max_ttl():
    """Test session extension is capped at max TTL"""
    manager = SessionManager()

    session = manager.create_session(
        vault_id="test_vault",
        profile="Black Vault",  # Max TTL = 15 min
        master_key=b"test_key",
        ttl_seconds=300,  # 5 min
    )

    # Try to extend by 1 hour (should be capped at 15 min total)
    manager.extend_session(session.session_id, 3600)

    remaining = session.time_remaining()

    # Should be capped at 15 min (900 seconds)
    assert remaining <= 900

    # Cleanup
    manager.end_session(session.session_id)


def test_end_session_cleanup():
    """Test ending session cleans up directory and keys"""
    manager = SessionManager()
    master_key = b"test_master_key_sensitive_data"

    session = manager.create_session(
        vault_id="test_vault",
        profile="Quick Lock",
        master_key=master_key,
    )

    session_dir = session.session_dir
    session_id = session.session_id

    # Session and directory should exist
    assert session_dir.exists()
    assert manager.get_session(session_id) is not None

    # End session
    manager.end_session(session_id)

    # Directory should be deleted
    assert not session_dir.exists()

    # Session should be gone
    assert manager.get_session(session_id) is None


def test_get_session_by_vault():
    """Test retrieving session by vault ID"""
    manager = SessionManager()

    session = manager.create_session(
        vault_id="test_vault_123",
        profile="Ritual Lock",
        master_key=b"test_key",
    )

    # Should find by vault ID
    found = manager.get_session_by_vault("test_vault_123")
    assert found is not None
    assert found.session_id == session.session_id

    # Should not find non-existent vault
    not_found = manager.get_session_by_vault("non_existent")
    assert not_found is None

    # Cleanup
    manager.end_session(session.session_id)


def test_cleanup_expired_sessions():
    """Test batch cleanup of expired sessions"""
    manager = SessionManager()

    # Create 3 sessions with short TTL
    for i in range(3):
        manager.create_session(
            vault_id=f"vault_{i}",
            profile="Quick Lock",
            master_key=b"test_key",
            ttl_seconds=1,
        )

    # All should be active
    assert len(manager.list_active_sessions()) == 3

    # Wait for expiry
    time.sleep(1.5)

    # Cleanup expired
    count = manager.cleanup_expired_sessions()

    assert count == 3
    assert len(manager.list_active_sessions()) == 0


def test_session_touch_updates_activity():
    """Test touching session updates last activity"""
    manager = SessionManager()

    session = manager.create_session(
        vault_id="test_vault",
        profile="Quick Lock",
        master_key=b"test_key",
    )

    initial_activity = session.last_activity

    time.sleep(0.1)

    # Getting session should touch it
    manager.get_session(session.session_id)

    # Activity should be updated
    assert session.last_activity > initial_activity

    # Cleanup
    manager.end_session(session.session_id)


def test_end_all_sessions():
    """Test ending all sessions at once"""
    manager = SessionManager()

    # Create multiple sessions
    for i in range(5):
        manager.create_session(
            vault_id=f"vault_{i}",
            profile="Ritual Lock",
            master_key=b"test_key",
        )

    assert len(manager.list_active_sessions()) == 5

    # End all
    manager.end_all_sessions()

    assert len(manager.list_active_sessions()) == 0


def test_session_is_expired():
    """Test session expiry checking"""
    manager = SessionManager()

    session = manager.create_session(
        vault_id="test_vault",
        profile="Quick Lock",
        master_key=b"test_key",
        ttl_seconds=1,
    )

    # Should not be expired initially
    assert session.is_expired() == False

    # Wait for expiry
    time.sleep(1.5)

    # Should be expired now
    assert session.is_expired() == True

    # Cleanup (even though expired)
    manager.end_session(session.session_id)


def test_convenience_wrappers():
    """Test module-level convenience functions"""
    # create_session
    session = create_session(
        vault_id="test_vault",
        profile="Ritual Lock",
        master_key=b"test_key",
    )

    session_id = session.session_id

    # get_session
    retrieved = get_session(session_id)
    assert retrieved is not None
    assert retrieved.session_id == session_id

    # end_session
    end_session(session_id)

    # Should be gone
    assert get_session(session_id) is None


def test_cleanup_expired_sessions_convenience():
    """Test cleanup_expired_sessions convenience wrapper"""
    # Create expired session
    session = create_session(
        vault_id="test_vault",
        profile="Quick Lock",
        master_key=b"test_key",
        ttl_seconds=1,
    )

    time.sleep(1.5)

    # Cleanup using convenience function
    count = cleanup_expired_sessions()

    assert count >= 1
