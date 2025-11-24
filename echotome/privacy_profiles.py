from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass
class PrivacyProfile:
    """
    Privacy profile defining KDF parameters, audio weighting, and threat model.

    v3.1: Extended with explicit threat models, security flags, and operational constraints.
    v3.2: Added session management and locality enforcement.

    Attributes:
        name: Profile name
        kdf_time: Iteration count for KDF (Argon2 iterations)
        kdf_memory: Memory cost in KB for KDF
        kdf_parallelism: Parallelism degree for Argon2
        audio_weight: How much audio influences key (0.0 to 1.0)
        deniable: Whether to use deniability features
        requires_mic: Microphone-only unlock required
        requires_timing: Timing enforcement enabled
        hardware_recommended: Hardware keystore recommended
        unrecoverable_default: Default to no recovery codes
        threat_model_id: Short threat model identifier
        threat_model_description: One-line threat model summary
        threat_model_assumptions: Security assumptions
        threat_model_protects_against: What this profile protects against
        threat_model_does_not_protect_against: Known limitations
        allows_visual_ritual: Whether visual/text ritual mode is allowed
        session_ttl_seconds: Default session TTL in seconds (v3.2)
        allow_plaintext_disk: Whether decrypted files can be written to disk (v3.2)
    """
    name: str
    kdf_time: int
    kdf_memory: int
    kdf_parallelism: int
    audio_weight: float
    deniable: bool
    requires_mic: bool
    requires_timing: bool
    hardware_recommended: bool
    unrecoverable_default: bool
    threat_model_id: str
    threat_model_description: str
    threat_model_assumptions: str
    threat_model_protects_against: str
    threat_model_does_not_protect_against: str
    allows_visual_ritual: bool
    session_ttl_seconds: int = 900  # v3.2: Default 15 minutes
    allow_plaintext_disk: bool = True  # v3.2: Allow disk-based decryption

    def __str__(self) -> str:
        return (
            f"PrivacyProfile({self.name}, "
            f"threat_model={self.threat_model_id}, "
            f"audio_weight={self.audio_weight}, "
            f"requires_mic={self.requires_mic})"
        )


# Define the three core privacy profiles with v3.1 threat models

QUICK_LOCK = PrivacyProfile(
    name="Quick Lock",
    kdf_time=2,
    kdf_memory=65536,  # 64 MB
    kdf_parallelism=2,
    audio_weight=0.0,
    deniable=False,
    requires_mic=False,
    requires_timing=False,
    hardware_recommended=False,
    unrecoverable_default=False,
    threat_model_id="casual",
    threat_model_description=(
        "Protects against casual snooping and opportunistic access to unlocked/unattended devices."
    ),
    threat_model_assumptions=(
        "User has a strong passphrase. Device is not compromised. "
        "Attacker has physical access but limited time and no technical expertise."
    ),
    threat_model_protects_against=(
        "Casual device access, family/roommate snooping, lost device with screen lock bypass. "
        "Non-targeted attacks without access to encryption keys or passphrases."
    ),
    threat_model_does_not_protect_against=(
        "Targeted attacks with cryptanalysis capability. File copies analyzed offline. "
        "Attackers with both device and ritual audio track. State-level adversaries."
    ),
    allows_visual_ritual=True,
    session_ttl_seconds=3600,  # v3.2: 1 hour
    allow_plaintext_disk=True,  # v3.2: Disk decryption allowed
)
"""
Quick Lock: Fast, passphrase-only encryption.
- Low memory/time requirements
- No audio involvement (audio_weight = 0.0)
- No deniability features
- Threat model: casual (protects against opportunistic access)
- Good for: Rapid encryption, low-resource devices, everyday use
"""

RITUAL_LOCK = PrivacyProfile(
    name="Ritual Lock",
    kdf_time=4,
    kdf_memory=131072,  # 128 MB
    kdf_parallelism=4,
    audio_weight=0.7,
    deniable=False,
    requires_mic=False,
    requires_timing=True,
    hardware_recommended=True,
    unrecoverable_default=False,
    threat_model_id="focused",
    threat_model_description=(
        "Protects against technically capable attackers with access to encrypted files "
        "and ritual audio tracks, but not your device identity keys."
    ),
    threat_model_assumptions=(
        "User has both strong passphrase and ritual audio. Device identity is secure. "
        "Attacker may have file copies and know the ritual track, but cannot spoof identity or timing."
    ),
    threat_model_protects_against=(
        "File theft with known ritual track. Offline brute force with audio but no device identity. "
        "Timing acceleration attacks. Track substitution attacks. Cloud backup compromise."
    ),
    threat_model_does_not_protect_against=(
        "Device compromise with identity key extraction. State-level adversaries with custom hardware. "
        "Attackers who can both steal identity keys and obtain ritual audio with perfect timing."
    ),
    allows_visual_ritual=True,
    session_ttl_seconds=1200,  # v3.2: 20 minutes
    allow_plaintext_disk=True,  # v3.2: Disk decryption allowed
)
"""
Ritual Lock: Balanced audio-enhanced encryption with timing enforcement.
- Medium memory/time requirements
- Strong audio influence (audio_weight = 0.7)
- Timing enforcement enabled
- Threat model: focused (protects against file theft with known track)
- Good for: Important files, symbolic binding to audio, cloud-synced vaults
"""

BLACK_VAULT = PrivacyProfile(
    name="Black Vault",
    kdf_time=8,
    kdf_memory=262144,  # 256 MB
    kdf_parallelism=8,
    audio_weight=1.0,
    deniable=True,
    requires_mic=True,
    requires_timing=True,
    hardware_recommended=True,
    unrecoverable_default=True,
    threat_model_id="targeted",
    threat_model_description=(
        "Designed for high-sensitivity data where targeted attacks and file copies are assumed. "
        "Requires live microphone ritual with timing enforcement."
    ),
    threat_model_assumptions=(
        "User is under active surveillance or targeted attack. Encrypted files may be copied multiple times. "
        "Attacker has significant resources. User must perform live ritual to prove possession."
    ),
    threat_model_protects_against=(
        "File theft without live ritual capability. Offline attacks with all file artifacts. "
        "Coercion scenarios (can deny vault exists or claim data is destroyed). "
        "Advanced timing attacks and audio synthesis. File copy analysis over extended time."
    ),
    threat_model_does_not_protect_against=(
        "Live device compromise during unlock. Rubber-hose cryptanalysis (physical coercion during ritual). "
        "State-level adversaries with quantum computing (future threat). "
        "Attacks after successful unlock while vault is open."
    ),
    allows_visual_ritual=False,  # Audio ritual strictly required
    session_ttl_seconds=300,  # v3.2: 5 minutes (strict)
    allow_plaintext_disk=False,  # v3.2: Memory-only recommended
)
"""
Black Vault: Maximum security with deniability and microphone-only ritual.
- High memory/time requirements
- Full audio dependence (audio_weight = 1.0)
- Deniability features enabled (decoy headers)
- Microphone ritual strictly required
- Threat model: targeted (protects against sophisticated adversaries)
- Good for: Highly sensitive data, maximum paranoia, targeted threat scenarios
"""


# Profile registry (v3.1: normalized names)
_PROFILES: Dict[str, PrivacyProfile] = {
    "quicklock": QUICK_LOCK,
    "quick lock": QUICK_LOCK,
    "quick": QUICK_LOCK,
    "q": QUICK_LOCK,
    "rituallock": RITUAL_LOCK,
    "ritual lock": RITUAL_LOCK,
    "ritual": RITUAL_LOCK,
    "r": RITUAL_LOCK,
    "blackvault": BLACK_VAULT,
    "black vault": BLACK_VAULT,
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
        >>> get_profile("Quick Lock")
        >>> get_profile("ritual")
        >>> get_profile("b")  # Black Vault
    """
    normalized = name.lower().replace("_", "").replace("-", "")
    if normalized in _PROFILES:
        return _PROFILES[normalized]
    raise ValueError(
        f"Unknown profile: {name}. "
        f"Available: Quick Lock, Ritual Lock, Black Vault"
    )


def list_profiles() -> list[PrivacyProfile]:
    """
    Get all available privacy profiles.

    Returns:
        List of PrivacyProfile instances
    """
    return [QUICK_LOCK, RITUAL_LOCK, BLACK_VAULT]


def describe_profile(name: str) -> dict:
    """
    Get comprehensive description of profile for API/UI display.

    v3.1: Returns full threat model and security parameters.
    v3.2: Includes session management parameters.

    Args:
        name: Profile name

    Returns:
        Dictionary with profile metadata, threat model, and security parameters
    """
    profile = get_profile(name)

    return {
        "name": profile.name,
        "threat_model_id": profile.threat_model_id,
        "threat_model_description": profile.threat_model_description,
        "threat_model_assumptions": profile.threat_model_assumptions,
        "threat_model_protects_against": profile.threat_model_protects_against,
        "threat_model_does_not_protect_against": profile.threat_model_does_not_protect_against,

        # Security parameters
        "audio_weight": profile.audio_weight,
        "requires_mic": profile.requires_mic,
        "requires_timing": profile.requires_timing,
        "deniable": profile.deniable,
        "hardware_recommended": profile.hardware_recommended,
        "unrecoverable_default": profile.unrecoverable_default,
        "allows_visual_ritual": profile.allows_visual_ritual,

        # Session parameters (v3.2)
        "session_ttl_seconds": profile.session_ttl_seconds,
        "allow_plaintext_disk": profile.allow_plaintext_disk,

        # KDF parameters
        "kdf_time": profile.kdf_time,
        "kdf_memory": profile.kdf_memory,
        "kdf_parallelism": profile.kdf_parallelism,
    }


def get_kdf_params(profile_name: str) -> tuple[int, int, int]:
    """
    Get KDF parameters for a profile (time, memory, parallelism).

    v3.1: Includes parallelism parameter for Argon2id.

    Args:
        profile_name: Profile name

    Returns:
        Tuple of (time_cost, memory_cost, parallelism)
    """
    profile = get_profile(profile_name)
    return (profile.kdf_time, profile.kdf_memory, profile.kdf_parallelism)


def validate_ritual_mode(profile_name: str, ritual_mode: str) -> bool:
    """
    Validate if a ritual mode is allowed for this profile.

    v3.1: Supports file, mic, and visual ritual modes.

    Args:
        profile_name: Profile name
        ritual_mode: Ritual mode ("file", "mic", or "visual")

    Returns:
        True if mode is allowed for this profile

    Raises:
        ValueError: If ritual_mode is not recognized
    """
    profile = get_profile(profile_name)

    if ritual_mode == "mic":
        # Mic mode always allowed
        return True
    elif ritual_mode == "file":
        # File mode not allowed if profile requires mic
        return not profile.requires_mic
    elif ritual_mode == "visual":
        # Visual mode only if profile allows it
        return profile.allows_visual_ritual
    else:
        raise ValueError(f"Unknown ritual mode: {ritual_mode}")


def profile_info() -> str:
    """
    Get human-readable information about all profiles.

    v3.1: Includes threat model information.

    Returns:
        Formatted string describing all profiles
    """
    info = ["Available Privacy Profiles (v3.1):", ""]
    for profile in list_profiles():
        info.append(f"  {profile.name}:")
        info.append(f"    Threat Model: {profile.threat_model_id}")
        info.append(f"    {profile.threat_model_description}")
        info.append(f"    KDF: {profile.kdf_time} iterations, {profile.kdf_memory // 1024} MB, {profile.kdf_parallelism}x parallel")
        info.append(f"    Audio Weight: {profile.audio_weight}")
        info.append(f"    Requires Mic: {profile.requires_mic}")
        info.append(f"    Timing Enforced: {profile.requires_timing}")
        info.append(f"    Deniable: {profile.deniable}")
        info.append("")
    return "\n".join(info)
