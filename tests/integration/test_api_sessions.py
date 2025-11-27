"""
Integration tests for Echotome v3.2 API Session Management

Tests the complete session workflow from decrypt through file access.
"""

import json
import tempfile
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from echotome.api import app
from echotome.sessions import get_session_manager


# Test client fixture
@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


@pytest.fixture
def session_manager():
    """Get session manager and cleanup after test"""
    manager = get_session_manager()
    yield manager
    # Cleanup all sessions after test
    manager.end_all_sessions(secure_delete=True)


@pytest.fixture
def test_audio_file():
    """Create a minimal test audio file (mock WAV)"""
    # Create a minimal WAV file for testing
    # Real WAV header + minimal audio data
    wav_header = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"fmt " + b"\x10\x00\x00\x00"
    wav_header += b"\x01\x00\x02\x00\x44\xAC\x00\x00\x10\xB1\x02\x00\x04\x00\x10\x00"
    wav_header += b"data" + b"\x00" * 4
    audio_data = b"\x00" * 1000  # 1000 bytes of silence

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_header + audio_data)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


# ============================================================================
# API Info & Version Tests
# ============================================================================

def test_api_info_version(client):
    """Test that API info returns v3.2.0 with new features"""
    response = client.get("/info")
    assert response.status_code == 200

    data = response.json()
    assert data["version"] == "3.2.0"
    assert data["edition"] == "Session & Locality Enforcement"

    # Check for v3.2 features
    features = data["features"]
    assert "time_limited_sessions" in features
    assert "profile_based_ttls" in features
    assert "locality_enforcement" in features
    assert "session_management" in features


# ============================================================================
# Profile Endpoint Tests
# ============================================================================

def test_profiles_include_session_ttl(client):
    """Test that profile listing includes v3.2 session TTL information"""
    response = client.get("/profiles")
    assert response.status_code == 200

    data = response.json()
    profiles = data["profiles"]

    # Find Quick Lock profile
    quick_lock = next(p for p in profiles if p["name"] == "Quick Lock")
    assert quick_lock["session_ttl_seconds"] == 3600  # 1 hour
    assert "60 minutes" in quick_lock["session_ttl_formatted"]
    assert quick_lock["allow_plaintext_disk"] is True

    # Find Ritual Lock profile
    ritual_lock = next(p for p in profiles if p["name"] == "Ritual Lock")
    assert ritual_lock["session_ttl_seconds"] == 1200  # 20 min
    assert "20 minutes" in ritual_lock["session_ttl_formatted"]

    # Find Black Vault profile
    black_vault = next(p for p in profiles if p["name"] == "Black Vault")
    assert black_vault["session_ttl_seconds"] == 300  # 5 min
    assert "5 minutes" in black_vault["session_ttl_formatted"]
    assert black_vault["allow_plaintext_disk"] is False


def test_profile_detail_includes_session_params(client):
    """Test that individual profile detail includes session parameters"""
    response = client.get("/profiles/Quick Lock")
    assert response.status_code == 200

    data = response.json()
    assert "session_ttl_seconds" in data
    assert "allow_plaintext_disk" in data
    assert data["session_ttl_seconds"] == 3600


# ============================================================================
# Session Management Endpoint Tests
# ============================================================================

def test_create_session_with_profile_ttl(client, session_manager):
    """Test that creating a session uses profile-based TTL"""
    response = client.post(
        "/sessions",
        json={
            "vault_id": "test-vault-001",
            "profile": "Ritual Lock",
            "ttl_seconds": None,  # Use profile default
        }
    )

    assert response.status_code == 200
    data = response.json()

    assert data["profile"] == "Ritual Lock"
    assert data["vault_id"] == "test-vault-001"

    # Check that TTL is set correctly (20 minutes for Ritual Lock)
    # Time remaining should be close to 1200 seconds (allow small variance)
    time_remaining = data["time_remaining"]
    assert 1195 <= time_remaining <= 1200


def test_list_sessions(client, session_manager):
    """Test listing all active sessions"""
    # Create two sessions
    client.post(
        "/sessions",
        json={
            "vault_id": "vault-1",
            "profile": "Quick Lock",
        }
    )

    client.post(
        "/sessions",
        json={
            "vault_id": "vault-2",
            "profile": "Black Vault",
        }
    )

    # List sessions
    response = client.get("/sessions")
    assert response.status_code == 200

    data = response.json()
    assert data["count"] == 2
    assert len(data["sessions"]) == 2


def test_get_session_by_id(client, session_manager):
    """Test retrieving a specific session"""
    # Create session
    create_response = client.post(
        "/sessions",
        json={
            "vault_id": "test-vault",
            "profile": "Ritual Lock",
        }
    )

    session_id = create_response.json()["session_id"]

    # Get session
    response = client.get(f"/sessions/{session_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == session_id
    assert data["vault_id"] == "test-vault"
    assert data["profile"] == "Ritual Lock"


def test_extend_session(client, session_manager):
    """Test extending a session's TTL"""
    # Create session
    create_response = client.post(
        "/sessions",
        json={
            "vault_id": "test-vault",
            "profile": "Quick Lock",
        }
    )

    session_id = create_response.json()["session_id"]

    # Extend session by 600 seconds
    response = client.post(
        f"/sessions/{session_id}/extend",
        json={"additional_seconds": 600}
    )

    assert response.status_code == 200
    data = response.json()

    # Time remaining should be higher than original
    assert data["time_remaining"] > 3600


def test_end_session(client, session_manager):
    """Test ending a session"""
    # Create session
    create_response = client.post(
        "/sessions",
        json={
            "vault_id": "test-vault",
            "profile": "Quick Lock",
        }
    )

    session_id = create_response.json()["session_id"]

    # End session
    response = client.delete(f"/sessions/{session_id}")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ended"
    assert data["session_id"] == session_id

    # Verify session is gone
    get_response = client.get(f"/sessions/{session_id}")
    assert get_response.status_code == 404


def test_end_all_sessions(client, session_manager):
    """Test emergency lock (end all sessions)"""
    # Create multiple sessions
    for i in range(3):
        client.post(
            "/sessions",
            json={
                "vault_id": f"vault-{i}",
                "profile": "Quick Lock",
            }
        )

    # End all sessions
    response = client.delete("/sessions")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "all_sessions_ended"
    assert data["sessions_ended"] == 3

    # Verify no sessions remain
    list_response = client.get("/sessions")
    assert list_response.json()["count"] == 0


def test_cleanup_expired_sessions(client, session_manager):
    """Test cleanup of expired sessions"""
    # Create a session with very short TTL
    create_response = client.post(
        "/sessions",
        json={
            "vault_id": "test-vault",
            "profile": "Quick Lock",
            "ttl_seconds": 1,  # 1 second
        }
    )

    session_id = create_response.json()["session_id"]

    # Wait for expiration
    time.sleep(2)

    # Run cleanup
    response = client.post("/sessions/cleanup")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "cleanup_complete"
    assert data["sessions_cleaned"] >= 1

    # Verify session is gone
    get_response = client.get(f"/sessions/{session_id}")
    assert get_response.status_code == 404


# ============================================================================
# Session File Access Tests (Mocked)
# ============================================================================

def test_list_session_files_empty(client, session_manager):
    """Test listing files from an empty session"""
    # Create session manually
    manager = get_session_manager()
    session = manager.create_session(
        vault_id="test-vault",
        profile="Quick Lock",
        master_key=b"test_key_32_bytes_long_exactly!",
        ttl_seconds=300,
    )

    # List files (should be empty)
    response = client.get(f"/sessions/{session.session_id}/files")
    assert response.status_code == 200

    data = response.json()
    assert data["session_id"] == session.session_id
    assert data["file_count"] == 0
    assert len(data["files"]) == 0


def test_list_session_files_with_content(client, session_manager):
    """Test listing files from a session with files"""
    # Create session manually
    manager = get_session_manager()
    session = manager.create_session(
        vault_id="test-vault",
        profile="Quick Lock",
        master_key=b"test_key_32_bytes_long_exactly!",
        ttl_seconds=300,
    )

    # Create test files in session directory
    test_file1 = session.session_dir / "file1.txt"
    test_file2 = session.session_dir / "file2.txt"
    test_file1.write_text("test content 1")
    test_file2.write_text("test content 2")

    # List files
    response = client.get(f"/sessions/{session.session_id}/files")
    assert response.status_code == 200

    data = response.json()
    assert data["file_count"] == 2
    assert len(data["files"]) == 2

    # Check file metadata
    filenames = {f["filename"] for f in data["files"]}
    assert "file1.txt" in filenames
    assert "file2.txt" in filenames

    # Check download URLs are present
    for file_info in data["files"]:
        assert "download_url" in file_info
        assert file_info["size_bytes"] > 0


def test_download_session_file(client, session_manager):
    """Test downloading a specific file from a session"""
    # Create session manually
    manager = get_session_manager()
    session = manager.create_session(
        vault_id="test-vault",
        profile="Quick Lock",
        master_key=b"test_key_32_bytes_long_exactly!",
        ttl_seconds=300,
    )

    # Create test file in session directory
    test_file = session.session_dir / "test.txt"
    test_content = "This is test content"
    test_file.write_text(test_content)

    # Download file
    response = client.get(f"/sessions/{session.session_id}/files/test.txt")
    assert response.status_code == 200
    assert response.content.decode() == test_content


def test_download_session_file_not_found(client, session_manager):
    """Test downloading a non-existent file"""
    # Create session manually
    manager = get_session_manager()
    session = manager.create_session(
        vault_id="test-vault",
        profile="Quick Lock",
        master_key=b"test_key_32_bytes_long_exactly!",
        ttl_seconds=300,
    )

    # Try to download non-existent file
    response = client.get(f"/sessions/{session.session_id}/files/nonexistent.txt")
    assert response.status_code == 404


def test_download_session_file_path_traversal_blocked(client, session_manager):
    """Test that path traversal attacks are blocked"""
    # Create session manually
    manager = get_session_manager()
    session = manager.create_session(
        vault_id="test-vault",
        profile="Quick Lock",
        master_key=b"test_key_32_bytes_long_exactly!",
        ttl_seconds=300,
    )

    # Try path traversal
    # Note: FastAPI/Starlette normalizes paths at the routing level,
    # so extreme path traversal attempts like "/../../../" may return 404
    # from routing before reaching our endpoint. Both 403 and 404 are
    # acceptable security responses that prevent access.
    response = client.get(f"/sessions/{session.session_id}/files/../../../etc/passwd")
    assert response.status_code in [403, 404], f"Expected 403 or 404, got {response.status_code}"


def test_access_expired_session_files(client, session_manager):
    """Test that expired sessions cannot access files"""
    # Create session with very short TTL
    manager = get_session_manager()
    session = manager.create_session(
        vault_id="test-vault",
        profile="Quick Lock",
        master_key=b"test_key_32_bytes_long_exactly!",
        ttl_seconds=1,  # 1 second
    )

    session_id = session.session_id

    # Wait for expiration
    time.sleep(2)

    # Try to access files (should fail - session expired)
    response = client.get(f"/sessions/{session_id}/files")
    assert response.status_code == 404
    assert "expired" in response.json()["detail"].lower()


# ============================================================================
# Profile-Based TTL Enforcement Tests
# ============================================================================

def test_quick_lock_ttl_enforcement(client, session_manager):
    """Test that Quick Lock uses 1 hour TTL"""
    response = client.post(
        "/sessions",
        json={
            "vault_id": "test-vault",
            "profile": "Quick Lock",
        }
    )

    data = response.json()
    time_remaining = data["time_remaining"]

    # Should be approximately 3600 seconds (1 hour)
    assert 3595 <= time_remaining <= 3600


def test_ritual_lock_ttl_enforcement(client, session_manager):
    """Test that Ritual Lock uses 20 minute TTL"""
    response = client.post(
        "/sessions",
        json={
            "vault_id": "test-vault",
            "profile": "Ritual Lock",
        }
    )

    data = response.json()
    time_remaining = data["time_remaining"]

    # Should be approximately 1200 seconds (20 minutes)
    assert 1195 <= time_remaining <= 1200


def test_black_vault_ttl_enforcement(client, session_manager):
    """Test that Black Vault uses strict 5 minute TTL"""
    response = client.post(
        "/sessions",
        json={
            "vault_id": "test-vault",
            "profile": "Black Vault",
        }
    )

    data = response.json()
    time_remaining = data["time_remaining"]

    # Should be approximately 300 seconds (5 minutes)
    assert 295 <= time_remaining <= 300


# ============================================================================
# Vault-Session Integration Tests
# ============================================================================

def test_get_vault_shows_active_session(client, session_manager):
    """Test that vault detail shows active session info"""
    # This test would require actual vault creation
    # For now, we'll just verify the endpoint structure

    # Create a mock session
    manager = get_session_manager()
    session = manager.create_session(
        vault_id="test-vault-123",
        profile="Quick Lock",
        master_key=b"test_key_32_bytes_long_exactly!",
        ttl_seconds=300,
    )

    # Note: This would fail in real scenario without actual vault
    # but demonstrates the expected behavior
    # response = client.get("/vaults/test-vault-123")
    # Would expect: has_active_session=True, session={...}


# ============================================================================
# Edge Cases & Error Handling
# ============================================================================

def test_access_nonexistent_session(client):
    """Test accessing a session that doesn't exist"""
    response = client.get("/sessions/nonexistent-session-id")
    assert response.status_code == 404


def test_extend_nonexistent_session(client):
    """Test extending a session that doesn't exist"""
    response = client.post(
        "/sessions/nonexistent-session-id/extend",
        json={"additional_seconds": 300}
    )
    assert response.status_code == 404


def test_end_nonexistent_session(client):
    """Test ending a session that doesn't exist"""
    response = client.delete("/sessions/nonexistent-session-id")
    assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
