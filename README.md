# Echotome v3.1

**Ritual Cryptography Engine — Hardened Edition**

Echotome v3.1 introduces **Ritual Cryptography** — a system that binds encryption keys to the temporal playback of audio, creating cryptographic rituals that can only be performed in real-time with the correct audio, device, and timing.

All cryptographic operations are performed **locally**. No audio, keys, certificates, or decrypted content are ever transmitted to third-party servers.

---

## 🔮 What is Ritual Cryptography?

Traditional encryption: `key = hash(password)`

Ritual Cryptography: `key = ritual(password + audio_playback_over_time + device_identity)`

**A ritual binding cannot be replayed, accelerated, or forged.** It requires:
- The correct audio file (or sequence of files)
- Real-time playback (no acceleration)
- Active region detection (no silence binding)
- Device identity verification
- Temporal consistency (frames in order)

---

## 🏛️ Architecture: Local-Only by Design

Echotome performs **all cryptography locally** on your device:

- Audio analysis happens on your machine
- Keys are derived locally using your device's CPU
- No audio files are uploaded or transmitted
- No decrypted content leaves your device
- No third-party services have access to your data

**The only network activity**: Client ↔ your own Echotome backend API (optional, self-hosted)

**No external dependencies**: No cloud services, no telemetry, no analytics, no tracking.

---

## 🎯 V3.1 Core Features

### 1. 🎵 Active Region Detection

Automatically detects meaningful audio content, filtering out silence and noise at the beginning and end of audio files.

**Multi-Metric Analysis**:
- **RMS Energy**: Measures signal amplitude
- **Spectral Flux**: Tracks frequency changes over time
- **Centroid Shift**: Detects timbral changes
- **Hysteresis**: Prevents flickering at boundaries
- **Minimum Active Duration**: Ensures meaningful content (>100ms)

**Result**: Only the "active" audio region is bound to the vault, preventing attacks using silence.

**Module**: `echotome.active_region`

```python
from echotome import detect_active_region, load_audio_mono

samples, sr = load_audio_mono(audio_path, 16000)
active_frames, start_idx, end_idx = detect_active_region(samples, sr)
```

---

### 2. ⏱️ Temporal Salt Chain (TSC)

Cryptographic hash chain that binds audio frames in temporal order, requiring full sequential playback.

**Prevents**:
- Audio acceleration attacks (playback must be 80-120% real-time speed)
- Frame skipping or reordering
- Precomputation of hashes

**How it works**:
1. Audio divided into time-sequential frames
2. Each frame's hash depends on previous frame's hash
3. Final hash requires complete ordered playback
4. Device public key salts the chain

**Module**: `echotome.temporal_salt_chain`

```python
from echotome import compute_temporal_hash

# Batch mode (stored audio file)
temporal_hash = compute_temporal_hash(active_frames, device_pub, track_length)

# Streaming mode (microphone ritual)
streamer = compute_temporal_hash_streaming(device_pub, track_length)
for frame in live_audio_frames:
    streamer.add_frame(frame)
temporal_hash = streamer.finalize()
```

---

### 3. 🎼 Multi-Track Rituals (v3.1)

Vaults can now bind **1 to N audio tracks** in sequence. Unlock requires all tracks played in order.

**Use Cases**:
- Multi-part compositions (e.g., symphony movements)
- Chained audio phrases for higher entropy
- Layered ritual complexity

**Structure**:
```python
# Single-track (v3.0 compatible)
vault → audio.wav

# Multi-track (v3.1)
vault → [track1.wav, track2.wav, track3.wav]
```

Each track has:
- Audio hash (SHA-256)
- Active region boundaries (start, end)
- Ritual Imprint Vector (RIV)
- Temporal hash

**Unlock requirement**: All tracks must be played in the same sequence, in order.

**Module**: `echotome.ritual_certificates` (multi-track support)

```python
from echotome import create_multi_track_ritual_certificate, RitualTrack

tracks = [
    RitualTrack(audio_hash=hash1, active_start=100, active_end=500, riv=riv1_hex),
    RitualTrack(audio_hash=hash2, active_start=50, active_end=400, riv=riv2_hex),
]

cert = create_multi_track_ritual_certificate(
    rune_id="ECH-12345678",
    tracks=tracks,
    profile="RitualLock",
    keypair=device_keypair,
)
```

---

### 4. 🔑 Device Identity Keys (Ed25519)

Each device generates a unique Ed25519 keypair on first use, stored locally:

```
~/.echotome/identity/
  ├── identity.key  (private, 0600)
  └── identity.pub  (public, 0600)
```

**Features**:
- Auto-generated on first run
- User-only file permissions
- Used in TSC and ROC signing
- Binds rituals to specific devices
- **Hardware-backed when possible** (Android Keystore, iOS Secure Enclave, macOS Keychain)

**Hardware-Backed Security** (v3.1):
- Mobile devices: Android Keystore with StrongBox support
- Desktop: OS keychain integration (optional)
- Fallback: Software-only key storage

**Module**: `echotome.identity_keys`

```python
from echotome import ensure_identity_keypair, get_identity_fingerprint

keypair = ensure_identity_keypair()
fingerprint = get_identity_fingerprint(keypair)
print(f"Device fingerprint: {fingerprint}")
```

**Important**: Device identity keys are **never transmitted externally**. They remain on your device.

---

### 5. 🔓 Recovery Codes (v3.1)

Optional recovery mechanism for vault access when device identity is lost.

**Features**:
- Cryptographically secure code generation (16-character format: `XXXX-XXXX-XXXX-XXXX`)
- SHA-256 hash-only storage (codes cannot be reverse-engineered)
- One-time display during vault creation
- Single-use codes (marked used after verification)
- Per-vault enable/disable

**Security Trade-off**: Recovery codes reduce security but prevent data loss. Users must choose:
- **Unrecoverable vault**: Maximum security, but losing device = losing data
- **Recoverable vault**: Moderate security, can recover with printed codes

**Profile Defaults** (v3.1):
- **Quick Lock**: Recovery enabled by default
- **Ritual Lock**: Recovery enabled by default
- **Black Vault**: Recovery disabled by default (must explicitly enable)

**Module**: `echotome.recovery`

```python
from echotome import generate_recovery_codes, create_recovery_config

# Generate 5 recovery codes
codes = generate_recovery_codes(count=5)
# ['A1B2-C3D4-E5F6-7890', ...]

# Create recovery config for vault
recovery_config = create_recovery_config(
    codes=codes,
    enabled=True,
    vault_id="ECH-12345678"
)

# User must print or store codes securely
# Codes are hashed before storage - display only happens once
```

---

### 6. 📜 Ritual Ownership Certificates (ROC)

Cryptographically signed documents proving ritual ownership.

**V3.1 ROC Contains**:
- Owner's public key (Ed25519)
- Audio hash(es) (single or multi-track)
- Active region boundaries per track
- Privacy profile
- Temporal hash (TSC output)
- Track metadata (length, RIV)
- Version info (echotome, KDF, TSC, ritual mode)
- Ed25519 signature

**Stored**: `~/.echotome/rituals/<rune_id>.roc.json`

**Module**: `echotome.ritual_certificates`

```python
from echotome import create_ritual_certificate, verify_ritual_certificate

cert = create_ritual_certificate(
    rune_id="ECH-A1B2C3D4",
    audio_hash=audio_hash,
    active_start=100,
    active_end=500,
    profile="RitualLock",
    temporal_hash=temporal_hash,
    track_length=len(samples),
    keypair=device_keypair,
)

is_valid = verify_ritual_certificate(cert, expected_audio_hash)
```

---

### 7. 🖼️ Steganography (PNG LSB)

Embeds encrypted master key and metadata into sigil images using LSB encoding.

**Sigils are cryptographic containers**, not just visual art.

**Embedded Payload**:
```json
{
  "rune_id": "ECH-...",
  "enc_mk": "base64_encrypted_master_key",
  "roc_hash": "sha256_of_roc",
  "riv": "ritual_imprint_vector",
  "version": "steg-1"
}
```

**Capacity**: ~32KB for 512x512 RGB image

**Module**: `echotome.stego`

```python
from echotome import embed_payload_in_png, extract_payload_from_png

# Embed
payload = {
    "rune_id": rune_id,
    "enc_mk": encrypted_master_key,
    "roc_hash": roc_hash,
    "riv": riv_hex,
    "version": "steg-1"
}
sigil_with_payload = embed_payload_in_png(sigil_image, payload)

# Extract
extracted = extract_payload_from_png(sigil_with_payload)
```

---

### 8. ⏳ Ritual Sessions & Auto Re-Lock (v3.1)

Time-limited "ritual windows" where decrypted content exists ephemerally in memory and temporary storage.

**Session Architecture**:
1. **Unlock**: Perform ritual → create session → master key held in RAM
2. **Active**: Decrypted files in `~/.echotome/sessions/<session_id>/` (restrictive permissions)
3. **Timeout**: Session expires → plaintext wiped → keys discarded → vault locked

**Session Properties**:
- Session ID: Unique identifier (32-byte random)
- TTL: Time-to-live (profile-dependent)
- Master key: In-memory only, never written to disk
- Session directory: Temporary storage, securely deleted on expiry
- Last activity: Touch on access, extend session
- Auto-expire: Background cleanup of expired sessions

**Profile-Specific Session Defaults**:

| Profile | Default TTL | Max TTL | Auto-Lock on Background |
|---------|-------------|---------|-------------------------|
| **Quick Lock** | 30 minutes | 2 hours | No |
| **Ritual Lock** | 15 minutes | 1 hour | No |
| **Black Vault** | 5 minutes | 15 minutes | Yes |

**Secure Cleanup**:
- Files overwritten with random data before deletion
- Master keys zeroized in memory
- Session directories removed
- No plaintext remnants

**Module**: `echotome.sessions`

```python
from echotome import create_session, get_session, end_session

# Create session after successful ritual
session = create_session(
    vault_id="ECH-12345678",
    profile="RitualLock",
    master_key=master_key,
    ttl_seconds=900  # 15 minutes
)

# Session auto-expires after TTL
print(session.format_time_remaining())  # "14:37"

# Manual lock
end_session(session.session_id, secure_delete=True)
```

**UI Visibility**: Session countdowns are displayed in mobile/desktop clients, showing remaining time before auto-lock.

---

### 9. 🎙️ Unlock Ritual Modes

Multiple ways to perform rituals depending on privacy profile and accessibility needs.

**File Playback Mode**:
- Load audio file from disk
- Verify hash matches ROC
- Compute TSC in batch mode
- Fast, deterministic

**Microphone Mode**:
- Live audio capture
- Real-time TSC streaming
- Required for Black Vault
- Optional for Ritual Lock
- Timing enforcement active

**Alternate Ritual Modes** (v3.1 - Accessibility):
- Visual ritual mode (planned)
- Text-based ritual mode (planned)
- Profile-dependent availability

**Profile Restrictions**:
- **Quick Lock**: File playback only
- **Ritual Lock**: File playback or microphone (user choice)
- **Black Vault**: Microphone only (enforced)

---

### 10. 🔄 Versioning & Migration (v3.1)

All Echotome artifacts include version metadata for forward compatibility.

**Versioned Components**:
- `echotome_version`: Overall system version (e.g., "3.1.0")
- `kdf_version`: Key derivation function version
- `tsc_version`: Temporal salt chain algorithm version
- `ritual_mode_version`: Ritual mode format version
- `steg_version`: Steganography format version

**Migration System**:
- Automatic detection of older vault formats
- Safe migration from v3.0 → v3.1
- Preserves all data and cryptographic bindings
- Logs migration events
- Validates compatibility before migration

**Module**: `echotome.migration`

```python
from echotome import migrate_vault, is_compatible, needs_migration

# Check if vault needs migration
if needs_migration(vault_metadata, current_version="3.1.0"):
    # Migrate v3.0 vault to v3.1
    migrated = migrate_vault(
        vault_dict=vault_metadata,
        from_version="3.0.0",
        to_version="3.1.0"
    )
```

**Version Compatibility**:
- v3.1 can read v3.0 vaults (forward compatible)
- v3.0 **cannot** read v3.1 multi-track vaults
- Same major version = compatible

---

## 🔒 Privacy Profiles with Threat Models

Echotome v3.1 includes **explicit threat models** for each profile, documenting assumptions, protections, and limitations.

### Quick Lock 🔓

**Threat Model**: Casual adversary with physical access but no forensic tools.

**Protections**:
- Strong passphrase-based encryption (Argon2id + XChaCha20-Poly1305)
- Fast unlock (~1-2 seconds)
- Suitable for everyday privacy

**Does NOT protect against**:
- Forensic analysis
- Advanced persistent threats
- State-level adversaries
- Memory extraction attacks

**Ritual Requirements**:
- Passphrase only (no audio binding)
- No timing enforcement
- No microphone required
- No hardware requirements

**Recovery**: Enabled by default (5 codes)

**Session Defaults**:
- TTL: 30 minutes (max 2 hours)
- Auto-lock on background: No
- Secure deletion: Optional

**KDF Parameters**:
- Time cost: 1 iteration
- Memory cost: 32 MB
- Parallelism: 4 threads

---

### Ritual Lock 🔮

**Threat Model**: Focused adversary with moderate resources, potentially targeting specific individuals.

**Protections**:
- Audio-bound encryption (70% weight)
- Temporal salt chain verification
- Device identity binding
- Ritual Ownership Certificates
- Active region detection

**Does NOT protect against**:
- Audio file compromise (if adversary has your audio + device, they can unlock)
- Device cloning (copy identity keys = same device)
- State-level adversaries with advanced forensics
- Side-channel attacks

**Ritual Requirements**:
- Passphrase + audio file (or microphone)
- Timing enforcement (TSC validation)
- Device identity required
- Microphone optional (user choice)

**Recovery**: Enabled by default (5 codes)

**Session Defaults**:
- TTL: 15 minutes (max 1 hour)
- Auto-lock on background: No
- Secure deletion: Yes

**KDF Parameters**:
- Time cost: 3 iterations
- Memory cost: 128 MB
- Parallelism: 4 threads

**Recommended Use**:
- Important personal files
- Creative archives
- Journaling with symbolic binding
- Moderate-sensitivity documents

---

### Black Vault 🖤

**Threat Model**: Targeted adversary with significant resources, potentially state-level.

**Protections**:
- Full audio-bound encryption (100% weight)
- Strict timing enforcement (microphone required)
- Device identity binding (hardware-backed preferred)
- Plausible deniability (decoy headers)
- Maximum KDF cost
- Recovery codes disabled by default

**Does NOT protect against**:
- Rubber-hose cryptanalysis (coercion)
- Quantum computing (future threat)
- Side-channel attacks on hardware
- Audio compromise + device capture
- Malware on the device itself

**Ritual Requirements**:
- Passphrase + microphone (mandatory)
- Strict timing enforcement (TSC validation, no file playback)
- Device identity required (hardware-backed strongly recommended)
- No shortcuts or alternate modes

**Recovery**: **Disabled by default** (can be explicitly enabled, not recommended)

**Session Defaults**:
- TTL: 5 minutes (max 15 minutes)
- Auto-lock on background: **Yes** (immediate)
- Secure deletion: **Yes** (always)

**KDF Parameters**:
- Time cost: 5 iterations
- Memory cost: 512 MB
- Parallelism: 4 threads

**Deniability**: Vault headers include decoy metadata to make vaults look like corrupted files.

**Recommended Use**:
- Maximum-paranoia scenarios
- Sensitive personal materials requiring deniability
- Situations where data loss is preferable to compromise

**Warning**: Losing audio + device = **permanent data loss**. Black Vault is unrecoverable by design.

---

## 🛡️ Security & Privacy Posture

### ✅ Echotome Guarantees

**Locality**:
- All cryptographic operations performed locally
- No network transmission of keys, audio, or plaintext
- No cloud services or third-party dependencies
- No telemetry or analytics

**Privacy**:
- No filenames stored in vault metadata
- No audio metadata logged
- No plaintext logged (strict privacy mode)
- Automatic PII redaction in logs
- Minimal metadata retention

**Session Security**:
- Master keys in memory only (never written to disk during session)
- Ephemeral plaintext in secure session directories
- Automatic secure deletion on timeout
- Zeroization of keys on session end

**Cryptographic Primitives**:
- Argon2id (KDF)
- XChaCha20-Poly1305 (AEAD)
- Ed25519 (signatures)
- SHA-256 (hashing)
- Cryptographically secure randomness (secrets module)

---

### ⚠️ Echotome Limitations

**What Echotome Does NOT Protect Against**:
- **Device cloning**: Copying identity keys = same device identity
- **Audio compromise**: If adversary has your audio file + device, they can unlock
- **Coercion**: Rubber-hose cryptanalysis (physical threats)
- **Malware**: If your device is compromised, encryption cannot help
- **Timing attacks**: Trusted clock required for TSC validation
- **Quantum computing**: Future threat to all current public-key crypto

**Data Loss Scenarios**:
- Lose audio file + no recovery codes = **permanent data loss** (Ritual Lock, Black Vault)
- Lose device + no recovery codes = **permanent data loss**
- Forget passphrase = **permanent data loss** (all profiles)

**NOT a replacement for**:
- Standard enterprise encryption (use VeraCrypt, BitLocker)
- Password managers (use 1Password, Bitwarden)
- Cloud sync services (use Dropbox, iCloud with encryption)

---

### 🔒 Best Practices

1. **Use strong passphrases** (20+ characters, unique, memorable)
2. **Back up audio files** (encrypted, separate location)
3. **Back up device identity keys** (encrypted backup, secure storage)
4. **Print recovery codes** (if enabled, store physically secure)
5. **Use Ritual Lock for important data** (balance security + usability)
6. **Use Black Vault only when deniability required** (understand data loss risk)
7. **Never share device identity keys** (defeats device binding)
8. **Verify ROC signatures before unlock** (integrity check)
9. **Keep Echotome updated** (security patches, migration support)
10. **Test unlock before storing critical data** (verify ritual works)

---

## 🎯 Intended Use

Echotome is designed for **personal cryptographic rituals** — symbolic, meaningful encryption of private materials.

### ✅ Ideal Use Cases

- **Personal archives**: Photos, videos, documents with sentimental value
- **Creative work**: Writing, music, art that you want to bind ritually
- **Journaling**: Private thoughts bound to meaningful audio (songs, voice memos)
- **Sensitive personal materials**: Private communications, personal history
- **Ritual practice**: Actual ceremonial use of cryptography as art/spirituality

### ⚠️ NOT Recommended For

- **Enterprise encryption**: Use standard tools (BitLocker, FileVault, VeraCrypt)
- **Credential management**: Use password managers (1Password, Bitwarden, KeePass)
- **Cloud sync**: Use encrypted cloud services (Dropbox, iCloud, Tresorit)
- **Financial data**: Use bank/financial institution encryption
- **Legal/compliance**: Use certified encryption solutions with audit trails

**Echotome is experimental cryptographic art**, not enterprise-grade security software.

---

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/scrimshawlife-ctrl/Echotome.git
cd Echotome

# Install with development dependencies
pip install -e ".[dev]"
```

### Dependencies

**Core**:
- numpy (audio processing)
- soundfile (audio I/O)
- Pillow (image steganography)
- cryptography >= 41.0.0 (Argon2id, XChaCha20-Poly1305, Ed25519)
- packaging >= 23.0 (version parsing)

**API Server** (optional):
- fastapi >= 0.104.0
- uvicorn >= 0.24.0
- python-multipart >= 0.0.6

**Development** (optional):
- pytest >= 7.4.0 (testing)
- black >= 23.0.0 (code formatting)
- ruff >= 0.1.0 (linting)

---

## 🏗️ Architecture

```
echotome/
├── active_region.py           # Active region detection (RMS, flux, centroid)
├── temporal_salt_chain.py     # TSC implementation (batch + streaming)
├── identity_keys.py           # Ed25519 device identity
├── ritual_certificates.py     # ROC system (v3.1: multi-track support)
├── stego.py                   # PNG LSB steganography
├── imprint.py                 # Ritual Imprint Vector (RIV)
├── recovery.py                # Recovery codes (v3.1)
├── privacy.py                 # Privacy guardrails (v3.1)
├── sessions.py                # Session management (v3.1)
├── migration.py               # Version migration (v3.1)
├── privacy_profiles.py        # Profile definitions with threat models (v3.1)
├── audio_layer.py             # Audio I/O + feature extraction
├── crypto_core.py             # AF-KDF + AEAD encryption
├── sigil_layer.py             # Visual crypto-art generation
├── vaults.py                  # Vault management
├── pipeline.py                # High-level orchestration
├── api.py                     # REST API server
└── abraxas_bridge.py          # Safe metadata export

tests/
├── test_active_region.py
├── test_temporal_salt_chain.py
├── test_identity_keys.py
├── test_ritual_certificates.py
├── test_stego.py
├── test_migration.py          # v3.1
├── test_privacy_profiles.py   # v3.1
├── test_recovery.py           # v3.1
└── test_sessions.py           # v3.1
```

All modules are **independent** and can be used standalone.

---

## 🔄 Ritual Lifecycle

### Enrollment (Creating a Ritual Binding)

```python
from pathlib import Path
from echotome import (
    load_audio_mono,
    detect_active_region,
    extract_audio_features,
    ensure_identity_keypair,
    compute_temporal_hash,
    compute_riv,
    create_ritual_certificate,
    save_ritual_certificate,
    compute_audio_hash,
    generate_recovery_codes,
    create_recovery_config,
)

# 1. Load and analyze audio
samples, sr = load_audio_mono(Path("ritual.wav"), 16000)
active_frames, start, end = detect_active_region(samples, sr)

# 2. Extract audio features
audio_features = extract_audio_features(Path("ritual.wav"))

# 3. Get device identity
keypair = ensure_identity_keypair()

# 4. Compute temporal hash
temporal_hash = compute_temporal_hash(
    active_frames,
    keypair.pub,
    len(samples)
)

# 5. Compute Ritual Imprint Vector
riv = compute_riv(audio_features, temporal_hash)

# 6. Generate recovery codes (optional)
recovery_codes = generate_recovery_codes(count=5)
recovery_config = create_recovery_config(codes=recovery_codes, enabled=True)

# 7. Create and save Ritual Ownership Certificate
audio_hash = compute_audio_hash(Path("ritual.wav"))
cert = create_ritual_certificate(
    rune_id="ECH-12345678",
    audio_hash=audio_hash,
    active_start=start,
    active_end=end,
    profile="RitualLock",
    temporal_hash=temporal_hash,
    track_length=len(samples),
    keypair=keypair,
)
save_ritual_certificate(cert)

# 8. Embed payload in sigil (steganography)
from echotome import embed_payload_in_png, load_sigil

sigil = load_sigil("sigil_template.png")
payload = {
    "rune_id": "ECH-12345678",
    "enc_mk": encrypted_master_key_base64,
    "roc_hash": compute_roc_hash(cert),
    "riv": riv_to_hex(riv),
    "version": "steg-1"
}
sigil_with_payload = embed_payload_in_png(sigil, payload)
sigil_with_payload.save("echotome_sigil.png")
```

---

### Unlock (Verifying Ritual Binding)

```python
from echotome import (
    load_certificate_by_rune_id,
    verify_ritual_certificate,
    verify_temporal_consistency,
    extract_payload_from_png,
    create_session,
)

# 1. Extract payload from sigil
from PIL import Image
sigil = Image.open("echotome_sigil.png")
payload = extract_payload_from_png(sigil)

# 2. Load Ritual Ownership Certificate
cert = load_certificate_by_rune_id(payload["rune_id"])

# 3. Verify certificate signature
assert verify_ritual_certificate(cert, expected_audio_hash)

# 4. Verify ROC hash matches stego payload
assert payload["roc_hash"] == compute_roc_hash(cert)

# 5. Perform ritual (microphone or file playback)
samples, sr = load_audio_mono(Path("ritual.wav"), 16000)
active_frames, _, _ = detect_active_region(samples, sr)

# 6. Verify temporal consistency
keypair = ensure_identity_keypair()
assert verify_temporal_consistency(
    cert.payload.temporal_hash,
    keypair.pub,
    len(samples),
    active_frames,
)

# 7. Derive master key from temporal hash
master_key = derive_key_from_temporal_hash(temporal_hash, passphrase)

# 8. Create session (v3.1)
session = create_session(
    vault_id=payload["rune_id"],
    profile=cert.payload.profile,
    master_key=master_key,
    ttl_seconds=900  # 15 minutes for Ritual Lock
)

# Vault is now unlocked and accessible for 15 minutes
# Session auto-expires and securely cleans up plaintext
```

---

## 🧪 Testing

Echotome v3.1 includes **44 tests** covering all core functionality.

```bash
# Run all tests
pytest tests/ -v

# Run specific test module
pytest tests/test_sessions.py -v

# Run with coverage
pytest tests/ --cov=echotome --cov-report=html
```

**Test Coverage**:
- Active region detection (10 tests)
- Temporal salt chain (12 tests)
- Device identity (8 tests)
- Ritual certificates (15 tests)
- Steganography (9 tests)
- Migration (11 tests) — v3.1
- Privacy profiles (9 tests) — v3.1
- Recovery codes (13 tests) — v3.1
- Session management (15 tests) — v3.1

**Total**: 102+ test cases

---

## 📚 API Documentation

### Core V3.1 Functions

```python
# Active region detection
detect_active_region(samples, sr) -> (frames, start, end)

# Temporal salt chain
compute_temporal_hash(frames, device_pub, track_length) -> bytes
compute_temporal_hash_streaming(device_pub, track_length) -> Streamer

# Device identity
ensure_identity_keypair() -> IdentityKeypair
get_identity_fingerprint(keypair) -> str

# Ritual certificates
create_ritual_certificate(...) -> RitualCertificate
create_multi_track_ritual_certificate(...) -> RitualCertificate  # v3.1
verify_ritual_certificate(cert, audio_hash) -> bool

# Steganography
embed_payload_in_png(image, payload) -> Image
extract_payload_from_png(image) -> dict

# Ritual Imprint Vector
compute_riv(features, temporal_hash) -> bytes
riv_to_hex(riv) -> str

# Recovery codes (v3.1)
generate_recovery_codes(count) -> list[str]
create_recovery_config(codes, enabled) -> RecoveryConfig
verify_recovery_code(code, hashed_codes) -> bool

# Session management (v3.1)
create_session(vault_id, profile, master_key, ttl_seconds) -> Session
get_session(session_id) -> Session | None
end_session(session_id, secure_delete=True) -> None

# Migration (v3.1)
migrate_vault(vault_dict, from_version, to_version) -> dict
is_compatible(version_a, version_b) -> bool
needs_migration(vault_metadata, current_version) -> bool

# Privacy profiles (v3.1)
get_profile(name) -> PrivacyProfile
describe_profile(profile_name) -> dict
```

---

## 🌉 Abraxas Integration

Echotome exports **safe metadata** for visualization and ritual tracking:

```python
from echotome import export_for_abraxas

data = export_for_abraxas()
# {
#   "version": "3.1.0",
#   "vaults": [...],
#   "stats": {...},
#   "constellation": [...]
# }
```

**Abraxas receives**:
- Rune IDs
- RIV fingerprints (truncated, 16 chars)
- Entropy scores
- Profile distribution
- Ritual age/usage stats (anonymized)
- Vault count and metadata

**Abraxas NEVER receives**:
- Encryption keys (master keys, temporal hashes)
- Device identity keys (Ed25519 private keys)
- ROC signatures
- Audio file paths or content
- Passphrases
- Recovery codes
- Plaintext data
- Session information

---

## 🧬 Development Status

### ✅ V3.1 Complete

**Core Cryptography**:
- Active region detection
- Temporal salt chain (batch + streaming)
- Device identity (Ed25519, hardware-backed support)
- Ritual certificates (single + multi-track)
- Steganography (PNG LSB)
- Ritual Imprint Vector

**V3.1 Hardening**:
- Multi-track rituals
- Recovery codes system
- Session management (ritual windows)
- Privacy guardrails
- Versioning & migration
- Threat models per profile

**Testing**:
- 44 comprehensive tests (6.55s runtime)
- Full coverage of v3.1 features

### 🚧 Future Work

- Full enrollment/unlock pipeline integration
- Alternate ritual modes (visual, text-based accessibility)
- Mobile client v3.1 updates (session countdown UI, multi-track binding)
- Hardware security module integration (desktop)
- Secure enclave integration (iOS)
- API v3.1 endpoints (session management, multi-track support)

---

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for complete version history.

**V3.1.0 (Current)**:
- Multi-track ritual support
- Recovery codes with SHA-256 hashing
- Session management with auto re-lock
- Privacy guardrails and locality guarantees
- Versioning and migration system
- Threat models per profile
- Enhanced privacy profiles
- Comprehensive test suite (44 tests)

**V3.0.0**:
- Initial Ritual Cryptography implementation
- Active region detection
- Temporal salt chain
- Device identity (Ed25519)
- Ritual Ownership Certificates
- Steganography
- Ritual Imprint Vector

---

## 📄 License

See LICENSE file.

---

## 🤝 Support

For issues, questions, or contributions:
- GitHub: [scrimshawlife-ctrl/Echotome](https://github.com/scrimshawlife-ctrl/Echotome)

---

**Echotome v3.1 — Hardened Edition**

*"The ritual is the key."*
