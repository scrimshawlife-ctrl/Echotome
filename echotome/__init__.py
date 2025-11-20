"""
Echotome v2.0 — Audio-Field Key Derivation & Crypto-Sigil Engine

A modular privacy instrument combining:
- AF-KDF: Audio-Field Key Derivation Function
- Privacy Profiles: QuickLock, RitualLock, BlackVault
- AEAD Encryption: XChaCha20-Poly1305 / AES-GCM
- Vault Management: Secure encrypted storage
- Sigil Generation: Deterministic visual crypto-art
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

__version__ = "2.0.0"

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
]
