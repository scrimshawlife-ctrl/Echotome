"""
Echotome v3.1 Recovery Codes System

Optional recovery paths for users who don't want total unrecoverable abyss-mode.
Recovery codes provide a fallback mechanism in case identity keys are lost.

Security Notes:
- Recovery codes, if enabled, reduce security posture
- Black Vault defaults to unrecoverable but user can override
- Using a recovery code is logged as a recovery event
- Recovery can trigger identity key rotation
"""

import hashlib
import secrets
from dataclasses import dataclass
from typing import Optional


@dataclass
class RecoveryConfig:
    """
    Recovery configuration for a vault.

    Attributes:
        enabled: Whether recovery is enabled
        codes_hashes: SHA-256 hashes of recovery codes
        use_count: Number of times recovery has been used
        last_used_timestamp: Timestamp of last recovery use
    """
    enabled: bool
    codes_hashes: list[str]
    use_count: int = 0
    last_used_timestamp: Optional[float] = None

    def to_dict(self) -> dict:
        """Serialize to dictionary for storage"""
        return {
            "enabled": self.enabled,
            "codes_hashes": self.codes_hashes,
            "use_count": self.use_count,
            "last_used_timestamp": self.last_used_timestamp,
        }

    @staticmethod
    def from_dict(data: dict) -> "RecoveryConfig":
        """Deserialize from dictionary"""
        return RecoveryConfig(
            enabled=data["enabled"],
            codes_hashes=data["codes_hashes"],
            use_count=data.get("use_count", 0),
            last_used_timestamp=data.get("last_used_timestamp"),
        )


def generate_recovery_codes(count: int = 5) -> list[str]:
    """
    Generate cryptographically secure recovery codes.

    Args:
        count: Number of recovery codes to generate (default: 5)

    Returns:
        List of recovery codes in format: XXXX-XXXX-XXXX-XXXX

    Example:
        >>> codes = generate_recovery_codes(5)
        >>> codes[0]
        'A3F7-9B2D-4E8C-1FA6'
    """
    codes = []

    for _ in range(count):
        # Generate 8 random bytes (64 bits)
        random_bytes = secrets.token_bytes(8)

        # Convert to hex and format as XXXX-XXXX-XXXX-XXXX
        hex_str = random_bytes.hex().upper()
        formatted = f"{hex_str[0:4]}-{hex_str[4:8]}-{hex_str[8:12]}-{hex_str[12:16]}"

        codes.append(formatted)

    return codes


def hash_recovery_codes(codes: list[str]) -> list[str]:
    """
    Hash recovery codes for secure storage.

    Uses SHA-256 to hash codes so they cannot be recovered from storage.

    Args:
        codes: List of recovery codes

    Returns:
        List of SHA-256 hashes (hex strings)
    """
    hashes = []

    for code in codes:
        # Normalize: remove hyphens, uppercase
        normalized = code.replace("-", "").upper()

        # Hash with SHA-256
        code_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
        hashes.append(code_hash)

    return hashes


def verify_recovery_code(code: str, hashes: list[str]) -> bool:
    """
    Verify a recovery code against stored hashes.

    Args:
        code: Recovery code to verify
        hashes: List of valid code hashes

    Returns:
        True if code matches any hash
    """
    # Normalize input code
    normalized = code.replace("-", "").replace(" ", "").upper()

    # Hash the input
    code_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    # Check against all hashes
    return code_hash in hashes


def create_recovery_config(enabled: bool = True, count: int = 5) -> tuple[RecoveryConfig, list[str]]:
    """
    Create a recovery configuration with generated codes.

    Args:
        enabled: Whether recovery is enabled
        count: Number of recovery codes to generate

    Returns:
        Tuple of (RecoveryConfig, plaintext_codes)

    Note:
        Plaintext codes are returned ONCE and must be shown to user.
        They cannot be recovered after this point.
    """
    if not enabled:
        return RecoveryConfig(enabled=False, codes_hashes=[]), []

    # Generate codes
    codes = generate_recovery_codes(count)

    # Hash codes for storage
    hashes = hash_recovery_codes(codes)

    # Create config
    config = RecoveryConfig(
        enabled=True,
        codes_hashes=hashes,
        use_count=0,
        last_used_timestamp=None,
    )

    return config, codes


def validate_and_mark_used(config: RecoveryConfig, code: str, current_timestamp: float) -> bool:
    """
    Validate a recovery code and mark it as used.

    Args:
        config: Recovery configuration
        code: Recovery code to validate
        current_timestamp: Current Unix timestamp

    Returns:
        True if code is valid

    Side Effects:
        - Increments use_count if code is valid
        - Updates last_used_timestamp
    """
    if not config.enabled:
        return False

    if not verify_recovery_code(code, config.codes_hashes):
        return False

    # Mark as used
    config.use_count += 1
    config.last_used_timestamp = current_timestamp

    return True


def disable_recovery(config: RecoveryConfig) -> None:
    """
    Disable recovery for a vault.

    Clears all recovery code hashes and disables recovery.

    Args:
        config: Recovery configuration to disable
    """
    config.enabled = False
    config.codes_hashes = []


def format_codes_for_display(codes: list[str]) -> str:
    """
    Format recovery codes for user display/printing.

    Args:
        codes: List of recovery codes

    Returns:
        Formatted string ready for display

    Example:
        RECOVERY CODES - KEEP SAFE

        1. A3F7-9B2D-4E8C-1FA6
        2. B8E4-1C9F-7A3D-2E5B
        ...
    """
    lines = [
        "=" * 50,
        "ECHOTOME RECOVERY CODES - KEEP SAFE",
        "=" * 50,
        "",
        "⚠️  IMPORTANT:",
        "- These codes can unlock your vault if you lose your device identity",
        "- Store them securely (print, write down, password manager)",
        "- Each code can be used once",
        "- If you lose these codes, your vault may become unrecoverable",
        "",
        "CODES:",
        ""
    ]

    for i, code in enumerate(codes, 1):
        lines.append(f"{i}. {code}")

    lines.append("")
    lines.append("=" * 50)

    return "\n".join(lines)


def get_recovery_strength(config: RecoveryConfig) -> str:
    """
    Get a human-readable description of recovery strength.

    Args:
        config: Recovery configuration

    Returns:
        String describing recovery strength
    """
    if not config.enabled:
        return "Unrecoverable (no recovery codes)"

    code_count = len(config.codes_hashes)

    if code_count == 0:
        return "Unrecoverable (recovery enabled but no codes)"
    elif config.use_count >= code_count:
        return "Unrecoverable (all recovery codes used)"
    else:
        remaining = code_count - config.use_count
        return f"Recoverable ({remaining} codes remaining)"
