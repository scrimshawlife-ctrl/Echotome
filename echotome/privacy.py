"""
Echotome v3.2 Privacy Posture, Telemetry Guardrails & Locality Enforcement

Enforces strict privacy controls and prevents accidental data leakage.

Privacy Principles:
- No external network calls except API request handling
- No telemetry or analytics by default
- Minimal logging (generic events only, no PII)
- No storage of sensitive artifacts in logs
- All optional features must be explicitly opt-in

V3.2 Locality Enforcement:
- PRIVACY_STRICT: Must be True (enforces local-only operation)
- ALLOW_THIRD_PARTY_UPLOADS: Must be False (no cloud sync)
- ALLOW_EXTERNAL_TELEMETRY: Must be False (no analytics)
- NETWORK_ISOLATED: Must be True (no outbound network calls)
"""

import logging
from typing import Optional, Any
from enum import Enum


# ========================
# V3.2: LOCALITY ENFORCEMENT CONSTANTS
# ========================

# Strict privacy mode - MUST be True for production
PRIVACY_STRICT = True

# Third-party upload/sync - MUST be False for local-only operation
ALLOW_THIRD_PARTY_UPLOADS = False

# External telemetry - MUST be False for privacy
ALLOW_EXTERNAL_TELEMETRY = False

# Network isolation - MUST be True to prevent external calls
NETWORK_ISOLATED = True


class PrivacyLevel(Enum):
    """Privacy enforcement levels"""
    STRICT = "strict"      # Minimal logging, no metrics
    NORMAL = "normal"      # Standard logging, no metrics
    VERBOSE = "verbose"    # Detailed logging for debugging (use with caution)


# Default privacy level (can be overridden via config)
PRIVACY_LEVEL = PrivacyLevel.STRICT


def set_privacy_level(level: PrivacyLevel) -> None:
    """
    Set global privacy level.

    Args:
        level: Privacy level to enforce
    """
    global PRIVACY_LEVEL
    PRIVACY_LEVEL = level


def get_privacy_level() -> PrivacyLevel:
    """Get current privacy level"""
    return PRIVACY_LEVEL


# Redaction patterns for sensitive data
SENSITIVE_PATTERNS = [
    "passphrase",
    "password",
    "key",
    "secret",
    "token",
    "master_key",
    "mk",
    "salt",
    "nonce",
    "audio_samples",
    "track_name",
    "file_content",
    "roc_payload",
]


def is_sensitive_field(field_name: str) -> bool:
    """
    Check if a field name indicates sensitive data.

    Args:
        field_name: Field or variable name

    Returns:
        True if field appears to contain sensitive data
    """
    field_lower = field_name.lower()
    return any(pattern in field_lower for pattern in SENSITIVE_PATTERNS)


def redact_if_sensitive(field_name: str, value: Any) -> Any:
    """
    Redact value if field name indicates sensitive data.

    Args:
        field_name: Field name
        value: Value to potentially redact

    Returns:
        Original value if not sensitive, "[REDACTED]" otherwise
    """
    if is_sensitive_field(field_name):
        return "[REDACTED]"
    return value


def sanitize_log_data(data: dict) -> dict:
    """
    Sanitize dictionary for logging by redacting sensitive fields.

    Args:
        data: Dictionary to sanitize

    Returns:
        New dictionary with sensitive fields redacted
    """
    sanitized = {}

    for key, value in data.items():
        if is_sensitive_field(key):
            sanitized[key] = "[REDACTED]"
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value)
        elif isinstance(value, (list, tuple)):
            # Don't try to sanitize large binary arrays
            if len(str(value)) > 100:
                sanitized[key] = f"[{type(value).__name__} of length {len(value)}]"
            else:
                sanitized[key] = value
        elif isinstance(value, bytes):
            # Never log raw bytes (could be keys, audio, etc.)
            sanitized[key] = f"[bytes: {len(value)} bytes]"
        else:
            sanitized[key] = value

    return sanitized


class PrivacyAwareLogger:
    """
    Logger that enforces privacy controls.

    Automatically redacts sensitive fields and respects privacy level.
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _should_log(self, level: int) -> bool:
        """Check if logging is allowed at this level given privacy settings"""
        if PRIVACY_LEVEL == PrivacyLevel.STRICT:
            # Only warnings and errors in strict mode
            return level >= logging.WARNING
        elif PRIVACY_LEVEL == PrivacyLevel.NORMAL:
            # Info and above in normal mode
            return level >= logging.INFO
        else:  # VERBOSE
            # Everything in verbose mode
            return True

    def debug(self, msg: str, extra: Optional[dict] = None) -> None:
        """Log debug message (only in verbose mode)"""
        if self._should_log(logging.DEBUG):
            if extra:
                extra = sanitize_log_data(extra)
            self.logger.debug(msg, extra=extra)

    def info(self, msg: str, extra: Optional[dict] = None) -> None:
        """Log info message (normal and verbose modes)"""
        if self._should_log(logging.INFO):
            if extra:
                extra = sanitize_log_data(extra)
            self.logger.info(msg, extra=extra)

    def warning(self, msg: str, extra: Optional[dict] = None) -> None:
        """Log warning message (all modes)"""
        if self._should_log(logging.WARNING):
            if extra:
                extra = sanitize_log_data(extra)
            self.logger.warning(msg, extra=extra)

    def error(self, msg: str, extra: Optional[dict] = None) -> None:
        """Log error message (all modes)"""
        if self._should_log(logging.ERROR):
            if extra:
                extra = sanitize_log_data(extra)
            self.logger.error(msg, extra=extra)

    def log_event(self, event_type: str, success: bool, **kwargs) -> None:
        """
        Log a generic event (allowed in all privacy modes).

        Events are logged without sensitive data, only generic outcome.

        Args:
            event_type: Type of event (e.g., "vault_create", "ritual_bind", "unlock")
            success: Whether event succeeded
            **kwargs: Additional context (will be sanitized)
        """
        outcome = "success" if success else "failure"
        sanitized = sanitize_log_data(kwargs)

        self.info(f"Event: {event_type} - {outcome}", extra=sanitized)


def get_logger(name: str) -> PrivacyAwareLogger:
    """
    Get a privacy-aware logger.

    Args:
        name: Logger name (typically __name__)

    Returns:
        PrivacyAwareLogger instance
    """
    return PrivacyAwareLogger(name)


# Privacy policy enforcement

ALLOWED_LOG_EVENTS = [
    "vault_created",
    "vault_deleted",
    "ritual_bound",
    "file_encrypted",
    "unlock_attempt",
    "unlock_success",
    "unlock_failure",
    "recovery_used",
    "identity_rotated",
]


def is_allowed_log_event(event_type: str) -> bool:
    """
    Check if an event type is allowed to be logged.

    Args:
        event_type: Event type identifier

    Returns:
        True if event is allowed
    """
    return event_type in ALLOWED_LOG_EVENTS


def validate_no_pii(data: str) -> bool:
    """
    Validate that data does not contain obvious PII.

    Simple heuristic check for common PII patterns.

    Args:
        data: String to check

    Returns:
        True if data appears safe, False if it may contain PII
    """
    # Check for email patterns
    if "@" in data and "." in data:
        return False

    # Check for phone patterns
    if any(c.isdigit() for c in data):
        digit_count = sum(c.isdigit() for c in data)
        if digit_count >= 10:  # Likely phone number
            return False

    # Check for file paths that might contain usernames
    if "/home/" in data or "/Users/" in data or "C:\\" in data:
        return False

    return True


# Privacy posture documentation

PRIVACY_POSTURE = """
Echotome v3.1 Privacy Posture
==============================

Locality Guarantee:
-------------------
Echotome performs ALL cryptographic operations locally. The system is designed
to be completely self-contained:

✓ Backend runs on YOUR machine (localhost) or YOUR self-hosted server
✓ Mobile app talks ONLY to your backend (configurable API URL)
✓ Network traffic limited to: client ↔ self-hosted Echotome API
✓ No raw audio, decrypted content, or keys ever leave your control
✓ No third-party servers, no cloud dependencies, no external APIs

What Echotome NEVER Does:
--------------------------
✗ No external network calls (except your own API endpoint)
✗ No telemetry or analytics
✗ No third-party service integration
✗ No cloud upload of audio, keys, or encrypted files
✗ No advertising or tracking
✗ No logging of passphrases, keys, or file contents
✗ No storage of audio samples in logs
✗ No automatic updates that could introduce vulnerabilities

What Echotome Does Locally:
----------------------------
✓ Generates and stores device identity keys locally (~/.echotome/identity/)
✓ Stores vault metadata locally (~/.echotome/vaults/)
✓ Stores ROCs locally (~/.echotome/rituals/)
✓ Logs generic events (create/unlock/failure) with timestamps
✓ Computes cryptographic operations entirely on-device
✓ Keeps all ritual audio processing in memory (never persisted)

Session Semantics (Ritual Windows):
------------------------------------
Decryption creates a time-limited session where plaintext exists ephemerally:

✓ Session creates isolated directory: ~/.echotome/sessions/<session_id>/
✓ Master keys reside in memory ONLY during session
✓ Decrypted files live ONLY in session directory
✓ Session auto-expires after profile-dependent TTL:
  - Quick Lock: 30 min default (max 2 hours)
  - Ritual Lock: 15 min default (max 1 hour)
  - Black Vault: 5 min default (max 15 min)
✓ On session end (timeout or manual lock):
  - Master key zeroized from memory
  - Session directory securely wiped (files overwritten then deleted)
  - Vault returns to locked state
✓ UI shows countdown timer during active session

This shrinks the plaintext attack window to the ritual duration itself.

Privacy Levels:
---------------
STRICT (default):
  - Only warnings and errors logged
  - No metrics collected
  - Minimal disk writes

NORMAL:
  - Info-level logging for operational events
  - Still no metrics or telemetry
  - Generic event logging (vault created, unlock attempt, etc.)

VERBOSE:
  - Detailed debug logging for troubleshooting
  - USE WITH CAUTION: may log detailed operation state
  - Should only be used during development/debugging

Recommended Usage:
------------------
1. Keep PRIVACY_LEVEL = STRICT for production use
2. Regularly review ~/.echotome/ directory permissions (should be 0700)
3. Do not store vaults or ROCs in cloud-synced directories unless encrypted
4. Use hardware-backed identity keys when available
5. Enable recovery codes only if you accept the reduced security posture

Data Minimization:
------------------
- Vault metadata includes only: name, creation time, profile, rune ID
- ROCs include only: audio hash, active region indices, temporal hash
- Logs include only: event type, timestamp, success/failure
- No audio metadata (artist, title, album) is ever stored or logged
"""


def print_privacy_posture() -> None:
    """Print privacy posture statement"""
    print(PRIVACY_POSTURE)


def get_privacy_posture() -> str:
    """Get privacy posture statement as string"""
    return PRIVACY_POSTURE
