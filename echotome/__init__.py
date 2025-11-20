"""
Echotome v3.0 — Ritual Cryptography Engine

A modular privacy instrument combining:
- Active Region Detection: Audio activity analysis
- Temporal Salt Chain (TSC): Time-bound cryptographic hash chain
- Device Identity: Ed25519 keypair management
- Ritual Ownership Certificates (ROC): Signed ritual metadata
- Steganography: PNG LSB payload embedding
- Ritual Imprint Vector (RIV): 256-bit ritual fingerprint
- AF-KDF: Audio-Field Key Derivation Function
- Privacy Profiles: QuickLock, RitualLock, BlackVault
- AEAD Encryption: XChaCha20-Poly1305 / AES-GCM
- Vault Management: Secure encrypted storage with ROC binding
- Sigil Generation: Deterministic visual crypto-art with visual hash
- Abraxas Bridge: Metadata export for symbolic visualization

Designed for Claude Code, ABX-Core style:
modular, deterministic, and pipeline-friendly.
"""

# Core configuration (v0.2.0 legacy)
from .config import EchotomeConfig, EchotomeResult

# Privacy profiles
from .privacy_profiles import (
    PrivacyProfile,
    get_profile,
    list_profiles,
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

# V3.0: Ritual certificates
from .ritual_certificates import (
    RitualCertificate,
    RitualCertificatePayload,
    create_ritual_certificate,
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

__version__ = "3.0.0"

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
    # V3.0: Ritual certificates
    "RitualCertificate",
    "RitualCertificatePayload",
    "create_ritual_certificate",
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
]
