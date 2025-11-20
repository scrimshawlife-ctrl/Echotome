# Echotome Changelog

## v3.1.0 - Hardened Edition (2025)

### 🔒 Security Hardening

#### Threat Models per Profile
- **NEW**: Each privacy profile now has explicit threat model documentation
- Quick Lock: `casual` threat model (protects against opportunistic access)
- Ritual Lock: `focused` threat model (protects against file theft with known track)
- Black Vault: `targeted` threat model (protects against sophisticated adversaries)
- All profiles include detailed assumptions, protections, and limitations

#### Recovery & Loss Handling
- **NEW**: Optional recovery codes system
  - Generate 5 cryptographically secure recovery codes on vault creation
  - SHA-256 hashed storage (plaintext shown once)
  - Recovery events are logged
  - Can disable recovery entirely for maximum security
- **NEW**: Explicit `unrecoverable` flag per vault
  - Black Vault defaults to unrecoverable=true
  - User can override if they accept reduced security posture

#### Multi-Part / Chained Rituals
- **NEW**: Support for multiple audio tracks in sequence
  - Bind 2+ tracks to a single vault
  - Unlock requires all tracks in exact order
  - Temporal Salt Chain folds across all tracks
  - Supports both file and mic modes for multi-track
- **NEW**: `RitualTrack` data structure
- Backward compatible: single-track ROCs still supported

### 🛡️ Privacy & Compliance

#### Privacy Posture Guardrails
- **NEW**: Strict privacy enforcement module (`privacy.py`)
  - No external network calls except API handling
  - No telemetry or analytics by default
  - Automatic redaction of sensitive fields in logs
  - Three privacy levels: STRICT (default), NORMAL, VERBOSE
- **NEW**: Privacy-aware logger with field sanitization
- **NEW**: Privacy posture documentation with locality guarantees
- **NEW**: Session semantics section documenting ephemeral plaintext model

#### Session Management (Ritual Windows)
- **NEW**: Time-limited "ritual windows" where decrypted content exists (`sessions.py`)
  - `SessionManager`: Tracks active decryption sessions
  - `Session`: Dataclass with session_id, vault_id, expiry, master_key (in-memory only)
  - `SessionConfig`: Profile-specific session parameters
  - Session directories: `~/.echotome/sessions/<session_id>/` (700 permissions)
  - Profile-based TTLs:
    - Quick Lock: 30 min default (max 2 hours)
    - Ritual Lock: 15 min default (max 1 hour)
    - Black Vault: 5 min default (max 15 min, auto-lock on background)
- **NEW**: Automatic session cleanup on expiry
  - Master keys zeroized from memory
  - Session directories securely wiped (files overwritten then deleted)
  - Auto-lock timer visible in UI
- **NEW**: Session extension support with max TTL enforcement
- **NEW**: Cleanup of stale session directories on startup

#### Versioning & Migration
- **NEW**: Comprehensive version tracking
  - All artifacts include `echotome_version`, `kdf_version`, `tsc_version`, etc.
  - Automatic detection of version compatibility
  - Migration system for v3.0 → v3.1 vaults
  - Forward-compatible data structures
- **NEW**: `migration.py` module with `migrate_vault()` function

### 🧪 Testing & Quality

#### Comprehensive Test Suite
- **NEW**: pytest-based test suite in `tests/` directory
  - `test_privacy_profiles.py`: Threat models and profile validation
  - `test_recovery.py`: Recovery code generation and verification
  - `test_migration.py`: Version compatibility and data migration
  - ~40 test cases covering critical functionality

### 🔧 Backend Improvements

#### Enhanced Privacy Profiles
- Added `kdf_parallelism` parameter for Argon2id
- Added `requires_mic`, `requires_timing`, `hardware_recommended` flags
- Added `unrecoverable_default` flag
- Added `allows_visual_ritual` flag (placeholder for future feature)

#### Updated Data Structures
- `RitualCertificatePayload` now supports both single and multi-track formats
- `RecoveryConfig` dataclass for recovery management
- `VersionInfo` dataclass for artifact versioning

#### New Modules
- `privacy_profiles.py`: Extended with v3.1 fields (threat models, etc.)
- `recovery.py`: Recovery code generation, hashing, verification
- `privacy.py`: Privacy posture enforcement and logging
- `migration.py`: Version compatibility and data migration

### 📱 Mobile Client Preparation

#### Hardware-Backed Identity (Planned)
- Abstraction for OS keystore integration
- Concept of "hardware" vs "filesystem" backend_type in identity_keys
- Mobile clients should use react-native-keychain or platform keystores

#### Accessibility (Planned)
- Visual/text ritual mode for non-audio access
- Clearly labeled as lower entropy than audio ritual
- Disabled by default for Black Vault

### 📊 API Changes (Backward Compatible)

- All v3.0 endpoints remain functional
- New endpoints can expose threat model descriptions
- Recovery code generation integrated into vault creation flow
- Multi-track ritual binding supported alongside single-track

### 🔄 Migration Notes

**Upgrading from v3.0:**
- Existing v3.0 vaults will be automatically migrated on first load
- Migration adds: recovery config (disabled), unrecoverable flag, version_info
- Single-track ROCs are converted to tracks=[single_track] format
- No data loss, fully backward compatible

**Version Compatibility:**
- v3.1 can read v3.0 vaults
- v3.0 can read v3.1 single-track vaults (ignores new fields)
- v3.0 cannot read v3.1 multi-track vaults

### 📝 Documentation

- Updated `pyproject.toml` to v3.1.0
- Added this CHANGELOG.md
- Updated README.md with v3.1 features (see below)
- Privacy posture statement in `privacy.py`

---

## v3.0.0 - Ritual Cryptography Engine (2024)

### Core Features

- **Temporal Salt Chain (TSC)**: Time-bound cryptographic hash chain
- **Active Region Detection**: Multi-metric audio activity analysis
- **Device Identity**: Ed25519 keypairs for device-bound encryption
- **Ritual Ownership Certificates (ROC)**: Signed metadata proving ritual binding
- **Steganography**: PNG LSB embedding of encrypted master keys
- **Ritual Imprint Vector (RIV)**: 256-bit audio fingerprint
- **Privacy Profiles**: Quick Lock, Ritual Lock, Black Vault
- **FastAPI Backend**: REST API for vault operations
- **React Native Mobile**: Android-first mobile client

### Security

- XChaCha20-Poly1305 AEAD encryption
- Argon2id key derivation
- Ed25519 signatures
- SHA-256 hashing throughout
- Plausible deniability (Black Vault)

---

## v2.0.0 - Audio-Enhanced Encryption (2023)

- Audio-field key derivation (AF-KDF)
- Basic vault management
- Passphrase + audio binding

---

## v0.2.0 - Initial Release (2022)

- Basic encryption with audio binding
- Proof of concept
