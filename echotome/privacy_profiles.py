from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PrivacyProfile:
    """
    Privacy profile defining KDF parameters and audio weighting.

    Attributes:
        name: Profile name
        kdf_time: Iteration count for KDF (Argon2 iterations)
        kdf_memory: Memory cost in KB for KDF
        audio_weight: How much audio influences key (0.0 to 1.0)
        deniable: Whether to use deniability features
    """
    name: str
    kdf_time: int
    kdf_memory: int
    audio_weight: float
    deniable: bool

    def __str__(self) -> str:
        return (
            f"PrivacyProfile({self.name}, "
            f"time={self.kdf_time}, "
            f"memory={self.kdf_memory}KB, "
            f"audio_weight={self.audio_weight}, "
            f"deniable={self.deniable})"
        )


# Define the three core privacy profiles

QUICK_LOCK = PrivacyProfile(
    name="QuickLock",
    kdf_time=2,
    kdf_memory=65536,  # 64 MB
    audio_weight=0.0,
    deniable=False,
)
"""
Quick Lock: Fast, passphrase-only encryption.
- Low memory/time requirements
- No audio involvement (audio_weight = 0.0)
- No deniability features
- Good for: Rapid encryption, low-resource devices
"""

RITUAL_LOCK = PrivacyProfile(
    name="RitualLock",
    kdf_time=4,
    kdf_memory=262144,  # 256 MB
    audio_weight=0.7,
    deniable=False,
)
"""
Ritual Lock: Balanced audio-enhanced encryption.
- Medium memory/time requirements
- Strong audio influence (audio_weight = 0.7)
- No deniability features
- Good for: Important files, symbolic binding to audio
"""

BLACK_VAULT = PrivacyProfile(
    name="BlackVault",
    kdf_time=8,
    kdf_memory=524288,  # 512 MB
    audio_weight=1.0,
    deniable=True,
)
"""
Black Vault: Maximum security with deniability.
- High memory/time requirements
- Full audio dependence (audio_weight = 1.0)
- Deniability features enabled (decoy headers)
- Good for: Highly sensitive data, maximum paranoia
"""


# Profile registry
_PROFILES: Dict[str, PrivacyProfile] = {
    "quicklock": QUICK_LOCK,
    "quick": QUICK_LOCK,
    "q": QUICK_LOCK,
    "rituallock": RITUAL_LOCK,
    "ritual": RITUAL_LOCK,
    "r": RITUAL_LOCK,
    "blackvault": BLACK_VAULT,
    "black": BLACK_VAULT,
    "b": BLACK_VAULT,
}


def get_profile(name: str) -> PrivacyProfile:
    """
    Get a privacy profile by name (case-insensitive).

    Args:
        name: Profile name (supports aliases like 'q', 'r', 'b')

    Returns:
        PrivacyProfile instance

    Raises:
        ValueError: If profile name not found

    Examples:
        >>> get_profile("quick")
        >>> get_profile("RitualLock")
        >>> get_profile("b")  # BlackVault
    """
    normalized = name.lower().replace("_", "").replace("-", "")
    if normalized in _PROFILES:
        return _PROFILES[normalized]
    raise ValueError(
        f"Unknown profile: {name}. "
        f"Available: QuickLock, RitualLock, BlackVault"
    )


def list_profiles() -> list[PrivacyProfile]:
    """
    Get all available privacy profiles.

    Returns:
        List of PrivacyProfile instances
    """
    return [QUICK_LOCK, RITUAL_LOCK, BLACK_VAULT]


def profile_info() -> str:
    """
    Get human-readable information about all profiles.

    Returns:
        Formatted string describing all profiles
    """
    info = ["Available Privacy Profiles:", ""]
    for profile in list_profiles():
        info.append(f"  {profile.name}:")
        info.append(f"    KDF Time: {profile.kdf_time} iterations")
        info.append(f"    KDF Memory: {profile.kdf_memory // 1024} MB")
        info.append(f"    Audio Weight: {profile.audio_weight}")
        info.append(f"    Deniable: {profile.deniable}")
        info.append("")
    return "\n".join(info)
