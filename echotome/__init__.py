"""
Echotome v3.1 — Ritual Cryptography Engine (Hardened)

A modular privacy instrument combining:

V3.1 Hardening Features:
- Threat Models: Explicit security posture per privacy profile
- Recovery Codes: Optional recovery with cryptographic code generation
- Multi-Part Rituals: Chain multiple tracks in sequence for higher entropy
- Privacy Guardrails: Strict telemetry controls and PII redaction
- Versioning: Forward-compatible data structures with migration support

V3.0 Core Features:
- Active Region Detection: Audio activity analysis
- Temporal Salt Chain (TSC): Time-bound cryptographic hash chain
- Device Identity: Ed25519 keypair management
- Ritual Ownership Certificates (ROC): Signed ritual metadata
- Steganography: PNG LSB payload embedding
- Ritual Imprint Vector (RIV): 256-bit ritual fingerprint
- AF-KDF: Audio-Field Key Derivation Function
- Privacy Profiles: Quick Lock, Ritual Lock, Black Vault
- AEAD Encryption: XChaCha20-Poly1305 / AES-GCM
- Vault Management: Secure encrypted storage with ROC binding
- Sigil Generation: Deterministic visual crypto-art with visual hash
- Abraxas Bridge: Metadata export for symbolic visualization

Designed for Claude Code, ABX-Core style:
modular, deterministic, and pipeline-friendly.
"""

# Core configuration (v0.2.0 legacy)
from .config import EchotomeConfig, EchotomeResult

# Privacy profiles (v3.1: extended with threat models)
from .privacy_profiles import (
    PrivacyProfile,
    get_profile,
    list_profiles,
    describe_profile,
    validate_ritual_mode,
    get_kdf_params,
    QUICK_LOCK,
    RITUAL_LOCK,
    BLACK_VAULT,
)

# Audio processing
from .audio_layer import (
    extract_audio_features,
    load_audio_mono,
    compute_spectral_map,
)

# Cryptography
from .crypto_core import (
    derive_final_key,
    encrypt_bytes,
    decrypt_bytes,
    EncryptedBlob,
    rune_id_from_key,
)

# Sigil generation
from .sigil_layer import (
    generate_sigil,
    features_to_sigil,
    SigilParams,
)

# High-level pipeline
from .pipeline import (
    encrypt_with_echotome,
    decrypt_with_echotome,
    run_echotome,  # Legacy v0.2.0
)

# Vault management
from .vaults import (
    Vault,
    create_vault,
    get_vault,
    list_vaults,
    delete_vault,
    encrypt_file_to_vault,
    decrypt_file_from_vault,
    get_vault_stats,
)

# Abraxas bridge
from .abraxas_bridge import (
    export_metadata,
    export_aggregated_stats,
    export_for_abraxas,
)

# V3.0: Active region detection
from .active_region import (
    detect_active_region,
    get_active_region_info,
)

# V3.0: Temporal salt chain
from .temporal_salt_chain import (
    compute_temporal_hash,
    compute_temporal_hash_streaming,
    TemporalHashStreamer,
    verify_temporal_consistency,
)

# V3.0: Identity keys
from .identity_keys import (
    IdentityKeypair,
    ensure_identity_keypair,
    generate_identity_keypair,
    load_identity_keypair,
    get_identity_fingerprint,
    sign_data,
    verify_signature,
)

# V3.0: Ritual certificates (v3.1: extended with multi-track support)
from .ritual_certificates import (
    RitualCertificate,
    RitualCertificatePayload,
    RitualTrack,
    create_ritual_certificate,
    create_multi_track_ritual_certificate,
    verify_ritual_certificate,
    save_ritual_certificate,
    load_certificate_by_rune_id,
    load_certificate_by_audio_hash,
    list_all_certificates,
    compute_audio_hash,
    compute_roc_hash,
)

# V3.0: Steganography
from .stego import (
    embed_payload_in_png,
    extract_payload_from_png,
    verify_stego_integrity,
    estimate_stego_capacity,
)

# V3.0: Ritual Imprint Vector
from .imprint import (
    compute_riv,
    riv_to_hex,
    riv_from_hex,
    compare_rivs,
    riv_distance,
    verify_riv_consistency,
)

# V3.1: Recovery codes
from .recovery import (
    RecoveryConfig,
    generate_recovery_codes,
    hash_recovery_codes,
    verify_recovery_code,
    create_recovery_config,
    validate_and_mark_used,
    disable_recovery,
    get_recovery_strength,
    format_codes_for_display,
)

# V3.1: Privacy posture
from .privacy import (
    PrivacyLevel,
    get_logger,
    set_privacy_level,
    get_privacy_level,
    sanitize_log_data,
    get_privacy_posture,
)

# V3.1: Versioning & migration
from .migration import (
    VersionInfo,
    ECHOTOME_VERSION,
    is_compatible,
    needs_migration,
    migrate_vault,
    validate_version_compatibility,
)

# V3.1: Session management
from .sessions import (
    Session,
    SessionConfig,
    SessionManager,
    get_session_manager,
    create_session,
    get_session,
    end_session,
    cleanup_expired_sessions,
)

__version__ = "3.1.0"

__all__ = [
    # Version
    "__version__",
    # Legacy v0.2.0
    "EchotomeConfig",
    "EchotomeResult",
    "run_echotome",
    # Privacy profiles
    "PrivacyProfile",
    "get_profile",
    "list_profiles",
    "describe_profile",
    "validate_ritual_mode",
    "get_kdf_params",
    "QUICK_LOCK",
    "RITUAL_LOCK",
    "BLACK_VAULT",
    # Audio
    "extract_audio_features",
    "load_audio_mono",
    "compute_spectral_map",
    # Crypto
    "derive_final_key",
    "encrypt_bytes",
    "decrypt_bytes",
    "EncryptedBlob",
    "rune_id_from_key",
    # Sigils
    "generate_sigil",
    "features_to_sigil",
    "SigilParams",
    # Pipeline
    "encrypt_with_echotome",
    "decrypt_with_echotome",
    # Vaults
    "Vault",
    "create_vault",
    "get_vault",
    "list_vaults",
    "delete_vault",
    "encrypt_file_to_vault",
    "decrypt_file_from_vault",
    "get_vault_stats",
    # Abraxas
    "export_metadata",
    "export_aggregated_stats",
    "export_for_abraxas",
    # V3.0: Active region
    "detect_active_region",
    "get_active_region_info",
    # V3.0: Temporal salt chain
    "compute_temporal_hash",
    "compute_temporal_hash_streaming",
    "TemporalHashStreamer",
    "verify_temporal_consistency",
    # V3.0: Identity
    "IdentityKeypair",
    "ensure_identity_keypair",
    "generate_identity_keypair",
    "load_identity_keypair",
    "get_identity_fingerprint",
    "sign_data",
    "verify_signature",
    # V3.0: Ritual certificates (v3.1: multi-track)
    "RitualCertificate",
    "RitualCertificatePayload",
    "RitualTrack",
    "create_ritual_certificate",
    "create_multi_track_ritual_certificate",
    "verify_ritual_certificate",
    "save_ritual_certificate",
    "load_certificate_by_rune_id",
    "load_certificate_by_audio_hash",
    "list_all_certificates",
    "compute_audio_hash",
    "compute_roc_hash",
    # V3.0: Steganography
    "embed_payload_in_png",
    "extract_payload_from_png",
    "verify_stego_integrity",
    "estimate_stego_capacity",
    # V3.0: RIV
    "compute_riv",
    "riv_to_hex",
    "riv_from_hex",
    "compare_rivs",
    "riv_distance",
    "verify_riv_consistency",
    # V3.1: Recovery codes
    "RecoveryConfig",
    "generate_recovery_codes",
    "hash_recovery_codes",
    "verify_recovery_code",
    "create_recovery_config",
    "validate_and_mark_used",
    "disable_recovery",
    "get_recovery_strength",
    "format_codes_for_display",
    # V3.1: Privacy posture
    "PrivacyLevel",
    "get_logger",
    "set_privacy_level",
    "get_privacy_level",
    "sanitize_log_data",
    "get_privacy_posture",
    # V3.1: Versioning & migration
    "VersionInfo",
    "ECHOTOME_VERSION",
    "is_compatible",
    "needs_migration",
    "migrate_vault",
    "validate_version_compatibility",
    # V3.1: Session management
    "Session",
    "SessionConfig",
    "SessionManager",
    "get_session_manager",
    "create_session",
    "get_session",
    "end_session",
    "cleanup_expired_sessions",
]
