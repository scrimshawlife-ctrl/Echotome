"""
Echotome v3.1 Session Management

Time-limited "ritual windows" where decrypted content exists ephemerally.

Architecture:
- Unlock creates a session with unique session_id
- Decrypted files live in ~/.echotome/sessions/<session_id>/
- Master keys held in memory only during session
- Session auto-expires after TTL (profile-dependent)
- On expiry: plaintext wiped, keys discarded, vault locked

This shrinks the attack window to the ritual duration itself.
"""

import hashlib
import secrets
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, List
from threading import Lock

from .privacy import get_logger


# Session storage directory
SESSIONS_DIR = Path.home() / ".echotome" / "sessions"

logger = get_logger(__name__)


@dataclass
class SessionConfig:
    """Session configuration per privacy profile"""

    default_ttl_seconds: int  # Default time-to-live
    max_ttl_seconds: int      # Maximum allowed TTL
    auto_lock_on_background: bool  # Lock when app goes to background
    allow_external_apps: bool  # Allow opening files in external apps
    secure_delete: bool        # Attempt secure delete on cleanup

    @staticmethod
    def for_profile(profile_name: str) -> "SessionConfig":
        """Get session config for a privacy profile"""
        if profile_name == "Quick Lock":
            return SessionConfig(
                default_ttl_seconds=30 * 60,  # 30 minutes
                max_ttl_seconds=120 * 60,     # 2 hours
                auto_lock_on_background=False,
                allow_external_apps=True,
                secure_delete=False,
            )
        elif profile_name == "Ritual Lock":
            return SessionConfig(
                default_ttl_seconds=15 * 60,  # 15 minutes
                max_ttl_seconds=60 * 60,      # 1 hour
                auto_lock_on_background=False,
                allow_external_apps=True,
                secure_delete=True,
            )
        elif profile_name == "Black Vault":
            return SessionConfig(
                default_ttl_seconds=5 * 60,   # 5 minutes
                max_ttl_seconds=15 * 60,      # 15 minutes max
                auto_lock_on_background=True,
                allow_external_apps=False,    # Never allow external apps
                secure_delete=True,
            )
        else:
            # Default: moderate security
            return SessionConfig(
                default_ttl_seconds=15 * 60,
                max_ttl_seconds=60 * 60,
                auto_lock_on_background=False,
                allow_external_apps=True,
                secure_delete=True,
            )


@dataclass
class Session:
    """
    Active decryption session (ritual window).

    Represents a time-bounded period where vault content is accessible.
    """

    session_id: str
    vault_id: str
    profile: str
    created_at: float
    expires_at: float
    last_activity: float
    session_dir: Path
    decrypted_files: List[Path] = field(default_factory=list)
    master_key: Optional[bytes] = None  # In-memory only, never persisted

    def is_expired(self) -> bool:
        """Check if session has expired"""
        return time.time() > self.expires_at

    def time_remaining(self) -> int:
        """Get seconds remaining in session"""
        remaining = self.expires_at - time.time()
        return max(0, int(remaining))

    def format_time_remaining(self) -> str:
        """Format time remaining as MM:SS"""
        remaining = self.time_remaining()
        minutes = remaining // 60
        seconds = remaining % 60
        return f"{minutes:02d}:{seconds:02d}"

    def touch(self) -> None:
        """Update last activity timestamp"""
        self.last_activity = time.time()

    def extend(self, additional_seconds: int, max_ttl: int) -> None:
        """
        Extend session expiry.

        Args:
            additional_seconds: Seconds to add
            max_ttl: Maximum TTL allowed
        """
        current_remaining = self.time_remaining()
        new_remaining = min(current_remaining + additional_seconds, max_ttl)
        self.expires_at = time.time() + new_remaining


class SessionManager:
    """
    Manages active decryption sessions.

    Responsibilities:
    - Create time-limited sessions on vault unlock
    - Track decrypted file paths per session
    - Auto-expire sessions and cleanup plaintext
    - Provide session status for UI
    """

    def __init__(self):
        self._sessions: Dict[str, Session] = {}
        self._lock = Lock()

        # Ensure sessions directory exists
        SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

        # Cleanup any stale session directories from previous runs
        self._cleanup_stale_session_dirs()

    def create_session(
        self,
        vault_id: str,
        profile: str,
        master_key: bytes,
        ttl_seconds: Optional[int] = None,
    ) -> Session:
        """
        Create a new decryption session.

        Args:
            vault_id: Vault identifier
            profile: Privacy profile name
            master_key: Master key (stored in memory only)
            ttl_seconds: Optional TTL override

        Returns:
            Session instance
        """
        with self._lock:
            # Get session config for profile
            config = SessionConfig.for_profile(profile)

            # Determine TTL
            if ttl_seconds is None:
                ttl = config.default_ttl_seconds
            else:
                ttl = min(ttl_seconds, config.max_ttl_seconds)

            # Generate session ID
            session_id = self._generate_session_id(vault_id)

            # Create session directory
            session_dir = SESSIONS_DIR / session_id
            session_dir.mkdir(parents=True, exist_ok=True)

            # Set restrictive permissions (owner only)
            session_dir.chmod(0o700)

            # Create session
            now = time.time()
            session = Session(
                session_id=session_id,
                vault_id=vault_id,
                profile=profile,
                created_at=now,
                expires_at=now + ttl,
                last_activity=now,
                session_dir=session_dir,
                master_key=master_key,
            )

            self._sessions[session_id] = session

            logger.info(
                f"Session created: {session_id[:8]}... for vault {vault_id}, "
                f"TTL {ttl}s, expires {session.format_time_remaining()}"
            )

            return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get session by ID if it exists and hasn't expired"""
        with self._lock:
            session = self._sessions.get(session_id)

            if session is None:
                return None

            # Check expiry
            if session.is_expired():
                logger.warning(f"Session {session_id[:8]}... has expired, ending")
                self.end_session(session_id)
                return None

            # Touch activity
            session.touch()

            return session

    def get_session_by_vault(self, vault_id: str) -> Optional[Session]:
        """Get active session for a vault"""
        with self._lock:
            for session in self._sessions.values():
                if session.vault_id == vault_id and not session.is_expired():
                    session.touch()
                    return session
            return None

    def end_session(self, session_id: str, secure_delete: bool = True) -> None:
        """
        End a session and cleanup all decrypted content.

        Args:
            session_id: Session to end
            secure_delete: Whether to attempt secure deletion
        """
        with self._lock:
            session = self._sessions.get(session_id)

            if session is None:
                logger.warning(f"Attempted to end non-existent session: {session_id[:8]}...")
                return

            logger.info(f"Ending session {session_id[:8]}... for vault {session.vault_id}")

            # Wipe master key from memory
            if session.master_key:
                # Overwrite with zeros (best effort)
                session.master_key = b'\x00' * len(session.master_key)
                session.master_key = None

            # Delete decrypted files
            if session.session_dir.exists():
                try:
                    if secure_delete:
                        self._secure_delete_directory(session.session_dir)
                    else:
                        shutil.rmtree(session.session_dir)

                    logger.info(f"Session directory cleaned: {session.session_dir}")
                except Exception as e:
                    logger.error(f"Failed to cleanup session directory: {e}")

            # Remove from active sessions
            del self._sessions[session_id]

    def extend_session(self, session_id: str, additional_seconds: int) -> bool:
        """
        Extend an active session.

        Args:
            session_id: Session to extend
            additional_seconds: Seconds to add

        Returns:
            True if extended successfully
        """
        with self._lock:
            session = self.get_session(session_id)

            if session is None:
                return False

            config = SessionConfig.for_profile(session.profile)
            session.extend(additional_seconds, config.max_ttl_seconds)

            logger.info(
                f"Session {session_id[:8]}... extended by {additional_seconds}s, "
                f"new expiry: {session.format_time_remaining()}"
            )

            return True

    def cleanup_expired_sessions(self) -> int:
        """
        Cleanup all expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        with self._lock:
            expired_ids = [
                sid for sid, session in self._sessions.items()
                if session.is_expired()
            ]

            for session_id in expired_ids:
                self.end_session(session_id)

            if expired_ids:
                logger.info(f"Cleaned up {len(expired_ids)} expired sessions")

            return len(expired_ids)

    def list_active_sessions(self) -> List[Session]:
        """Get list of all active (non-expired) sessions"""
        with self._lock:
            # Cleanup expired first
            self.cleanup_expired_sessions()

            return list(self._sessions.values())

    def end_all_sessions(self) -> None:
        """End all active sessions (use on shutdown)"""
        with self._lock:
            session_ids = list(self._sessions.keys())

            for session_id in session_ids:
                self.end_session(session_id)

            logger.info(f"Ended all sessions ({len(session_ids)} total)")

    def _generate_session_id(self, vault_id: str) -> str:
        """Generate unique session ID"""
        # session_id = HMAC(vault_id || timestamp || random)
        data = f"{vault_id}{time.time()}{secrets.token_hex(16)}".encode()
        return hashlib.sha256(data).hexdigest()

    def _cleanup_stale_session_dirs(self) -> None:
        """Cleanup session directories left from previous runs"""
        if not SESSIONS_DIR.exists():
            return

        for session_dir in SESSIONS_DIR.iterdir():
            if session_dir.is_dir():
                try:
                    shutil.rmtree(session_dir)
                    logger.debug(f"Cleaned stale session directory: {session_dir.name}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup stale session dir: {e}")

    def _secure_delete_directory(self, directory: Path) -> None:
        """
        Attempt secure deletion of directory contents.

        Best-effort: overwrites files with random data before deletion.
        Not cryptographically guaranteed (OS may cache, etc.)
        """
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                try:
                    # Overwrite with random data
                    file_size = file_path.stat().st_size
                    with open(file_path, "wb") as f:
                        # Write random data
                        f.write(secrets.token_bytes(file_size))
                        f.flush()

                    # Delete
                    file_path.unlink()
                except Exception as e:
                    logger.warning(f"Secure delete failed for {file_path}: {e}")

        # Remove directory
        shutil.rmtree(directory)


# Global session manager instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """Get or create global session manager"""
    global _session_manager

    if _session_manager is None:
        _session_manager = SessionManager()

    return _session_manager


def create_session(
    vault_id: str,
    profile: str,
    master_key: bytes,
    ttl_seconds: Optional[int] = None,
) -> Session:
    """Create a new session (convenience wrapper)"""
    manager = get_session_manager()
    return manager.create_session(vault_id, profile, master_key, ttl_seconds)


def get_session(session_id: str) -> Optional[Session]:
    """Get session by ID (convenience wrapper)"""
    manager = get_session_manager()
    return manager.get_session(session_id)


def end_session(session_id: str) -> None:
    """End session (convenience wrapper)"""
    manager = get_session_manager()
    manager.end_session(session_id)


def cleanup_expired_sessions() -> int:
    """Cleanup expired sessions (convenience wrapper)"""
    manager = get_session_manager()
    return manager.cleanup_expired_sessions()
