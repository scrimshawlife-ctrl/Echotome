# Echotome v3.0

**Ritual Cryptography Engine**

Echotome v3.0 introduces **Ritual Cryptography** — a system that binds encryption keys to the temporal playback of audio, creating cryptographic rituals that can only be performed in real-time with the correct audio, device, and timing.

---

## 🔮 What is Ritual Cryptography?

Traditional encryption: `key = hash(password)`

Ritual Cryptography: `key = ritual(password + audio_playback_over_time + device_identity)`

**A ritual binding cannot be replayed, accelerated, or forged.** It requires:
- The correct audio file
- Real-time playback (no acceleration)
- Active region detection (no silence binding)
- Device identity verification
- Temporal consistency (frames in order)

---

## 🎯 V3.0 Core Features

### 1. 🎵 Active Region Detection
Automatically detects meaningful audio content, filtering out:
- Silence and background noise
- Lead-in/lead-out periods
- Dead space

**Algorithm**: Multi-metric analysis using RMS energy, spectral flux, and centroid shift

**Module**: `echotome.active_region`

```python
from echotome import detect_active_region, load_audio_mono

samples, sr = load_audio_mono(audio_path, 16000)
active_frames, start, end = detect_active_region(samples, sr)
```

### 2. ⏱️ Temporal Salt Chain (TSC)
Cryptographic hash chain that binds audio frames in temporal order.

**Prevents**:
- Audio acceleration attacks
- Frame skipping
- Precomputation

**Requires**: Real-time playback within 80-120% speed tolerance

**Module**: `echotome.temporal_salt_chain`

```python
from echotome import compute_temporal_hash

# Batch mode (stored audio)
temporal_hash = compute_temporal_hash(active_frames, device_pub, track_length)

# Streaming mode (microphone)
streamer = compute_temporal_hash_streaming(device_pub, track_length)
for frame in live_audio_frames:
    streamer.add_frame(frame)
temporal_hash = streamer.finalize()
```

### 3. 🔑 Device Identity (Ed25519)
Each device has a unique Ed25519 keypair stored in:
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

**Module**: `echotome.identity_keys`

```python
from echotome import ensure_identity_keypair, get_identity_fingerprint

keypair = ensure_identity_keypair()
fingerprint = get_identity_fingerprint(keypair)
print(f"Device fingerprint: {fingerprint}")
```

### 4. 📜 Ritual Ownership Certificates (ROC)
Cryptographically signed documents proving ritual ownership.

**Contains**:
- Owner's public key
- Audio hash
- Active region boundaries
- Privacy profile
- Temporal hash
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
    track_length=len(samples)
)

is_valid = verify_ritual_certificate(cert, expected_audio_hash)
```

### 5. 🖼️ Steganography (PNG LSB)
Embeds encrypted master key and metadata into sigil PNG using LSB encoding.

**Payload**:
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
payload = {"rune_id": rune, "enc_mk": enc_key, "roc_hash": roc_hash, "riv": riv_hex}
sigil_with_payload = embed_payload_in_png(sigil_image, payload)

# Extract
extracted = extract_payload_from_png(sigil_with_payload)
```

### 6. 🧬 Ritual Imprint Vector (RIV)
256-bit fingerprint combining audio characteristics with temporal hash.

**Components**:
- Spectral signature (frequency domain)
- Rhythm signature (temporal patterns)
- Temporal hash (TSC output)

**Uses**:
- Stego payload verification
- ROC cross-validation
- Ritual matching

**Module**: `echotome.imprint`

```python
from echotome import compute_riv, riv_to_hex

riv = compute_riv(audio_features, temporal_hash)
riv_hex = riv_to_hex(riv)  # 64-char hex string
```

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
)

# 1. Load and analyze audio
samples, sr = load_audio_mono(Path("audio.wav"), 16000)
active_frames, start, end = detect_active_region(samples, sr)

# 2. Extract features
audio_features = extract_audio_features(Path("audio.wav"))

# 3. Get device identity
keypair = ensure_identity_keypair()

# 4. Compute temporal hash
temporal_hash = compute_temporal_hash(
    active_frames,
    keypair.pub,
    len(samples)
)

# 5. Compute RIV
riv = compute_riv(audio_features, temporal_hash)

# 6. Create and save ROC
audio_hash = compute_audio_hash(Path("audio.wav"))
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

# 7. Generate sigil with embedded payload
# (Next: integrate with sigil_layer + stego)
```

### Unlock (Verifying Ritual Binding)

```python
from echotome import (
    load_certificate_by_rune_id,
    verify_ritual_certificate,
    verify_temporal_consistency,
    extract_payload_from_png,
)

# 1. Load ROC
cert = load_certificate_by_rune_id("ECH-12345678")

# 2. Verify certificate
assert verify_ritual_certificate(cert, expected_audio_hash)

# 3. Replay audio and verify temporal consistency
active_frames, _, _ = detect_active_region(samples, sr)
assert verify_temporal_consistency(
    cert.payload.temporal_hash,
    keypair.pub,
    len(samples),
    active_frames,
)

# 4. Extract and verify stego payload
payload = extract_payload_from_png(sigil_image)
assert payload["rune_id"] == cert.payload.rune_id
assert payload["roc_hash"] == compute_roc_hash(cert)

# 5. Decrypt master key using temporal hash
# (Next: integrate with crypto_core)
```

---

## 📦 Installation

```bash
pip install -e .
```

### Dependencies
- numpy
- soundfile
- Pillow
- cryptography (Ed25519, Argon2id, XChaCha20-Poly1305)
- fastapi, uvicorn (for API server)

---

## 🔒 Privacy Profiles

### QuickLock 🔓
- **Audio dependence**: None (passphrase only)
- **Timing enforcement**: No
- **Microphone mode**: No
- **Use case**: Fast encryption, low-resource devices

### RitualLock 🔮
- **Audio dependence**: 70%
- **Timing enforcement**: Yes (TSC validation)
- **Microphone mode**: Optional
- **Use case**: Important files, symbolic binding

### BlackVault 🖤
- **Audio dependence**: 100%
- **Timing enforcement**: Yes (strict)
- **Microphone mode**: Required
- **Deniability**: Decoy headers
- **Use case**: Maximum paranoia, plausible deniability

---

## 🏗️ Architecture (ABX-Core)

```
echotome/
├── active_region.py         # Active region detection
├── temporal_salt_chain.py   # TSC implementation
├── identity_keys.py         # Ed25519 device identity
├── ritual_certificates.py   # ROC system
├── stego.py                 # PNG LSB steganography
├── imprint.py               # RIV computation
├── audio_layer.py           # Audio I/O + feature extraction
├── crypto_core.py           # AF-KDF + AEAD encryption
├── privacy_profiles.py      # Profile definitions
├── sigil_layer.py           # Visual crypto-art
├── vaults.py                # Vault management
├── pipeline.py              # High-level orchestration
├── api.py                   # REST API server
└── abraxas_bridge.py        # Metadata export
```

All modules are independent and can be used standalone.

---

## ⚠️ Security Considerations

### ✅ V3.0 Provides
- Time-bound cryptographic rituals
- Device-specific bindings
- Real-time playback verification
- Signed ownership certificates
- Active region filtering
- Temporal consistency checks

### ⚠️ V3.0 Does NOT Provide
- **NOT secure against device cloning** (copy identity keys = same device)
- **Audio is NOT secret** (anyone can access your audio file)
- **Lose audio = lose data** (with RitualLock/BlackVault)
- **NOT a replacement for standard encryption** (use for symbolic/artistic purposes)
- **Timing validation requires trusted clock**

### 🔒 Best Practices
1. Use strong passphrases (20+ characters)
2. Back up audio files AND identity keys
3. Use RitualLock for important data
4. Use BlackVault only when deniability needed
5. Never share device identity keys
6. Verify ROC signatures before unlock

---

## 🌉 Abraxas Integration

V3.0 exports safe ritual metadata:

```python
from echotome import export_for_abraxas

data = export_for_abraxas()
# {
#   "version": "3.0",
#   "vaults": [...],
#   "stats": {...},
#   "constellation": [...]
# }
```

**Abraxas receives**:
- Rune IDs
- RIV fingerprints (truncated)
- Entropy scores
- Profile distribution
- Ritual age/usage stats

**Abraxas NEVER receives**:
- Encryption keys
- Temporal hashes
- Device identity keys
- ROC signatures
- Audio file paths

---

## 🧪 Development Status

### ✅ V3.0 Core Complete
- Active region detection
- Temporal salt chain
- Device identity (Ed25519)
- Ritual certificates (ROC)
- Steganography (PNG LSB)
- Ritual Imprint Vector (RIV)

### 🚧 V3.0 Integration In Progress
- Enrollment/unlock pipeline
- Crypto-core temporal KDF
- Sigil visual hash
- Vault ROC binding
- API v3.0 endpoints
- Full microphone mode

---

## 📚 API Documentation

### Core V3.0 Functions

```python
# Active region
detect_active_region(samples, sr) -> (frames, start, end)

# Temporal salt chain
compute_temporal_hash(frames, device_pub, track_length) -> bytes

# Device identity
ensure_identity_keypair() -> IdentityKeypair

# Ritual certificates
create_ritual_certificate(...) -> RitualCertificate
verify_ritual_certificate(cert, audio_hash) -> bool

# Steganography
embed_payload_in_png(image, payload) -> Image
extract_payload_from_png(image) -> dict

# Ritual Imprint Vector
compute_riv(features, temporal_hash) -> bytes
```

---

## 🎮 Legacy Compatibility

V3.0 maintains full backward compatibility with v2.0 and v0.2.0:

```bash
# V0.2.0 CLI (sigil generation)
echotome input.wav output.png --key "secret"

# V2.0 API
from echotome import encrypt_with_echotome, decrypt_with_echotome
```

## 🛰️ Edge Deployment (Jetson Orin Nano Prep)

- Reuse precomputed buffers to avoid extra FFT/resampling passes on constrained ARM SOCs:

```python
from echotome import (
    DEFAULT_FRAME_SIZE,
    DEFAULT_HOP_SIZE,
    DEFAULT_SAMPLE_RATE,
    compute_spectral_map,
    extract_audio_features_from_samples,
    frame_audio,
    load_audio_mono,
)

samples, sr = load_audio_mono(audio_path, DEFAULT_SAMPLE_RATE)
frames = frame_audio(samples, frame_size=DEFAULT_FRAME_SIZE, hop_size=DEFAULT_HOP_SIZE)
spectral_map = compute_spectral_map(samples, DEFAULT_FRAME_SIZE, DEFAULT_HOP_SIZE, frames=frames)
features = extract_audio_features_from_samples(
    samples,
    sr=sr,
    frame_size=DEFAULT_FRAME_SIZE,
    hop_size=DEFAULT_HOP_SIZE,
    frames=frames,
    spectral_map=spectral_map,
)
```

- Keep the 16 kHz default sample rate unless you need full-fidelity analysis; it reduces CPU load for realtime work on the Orin Nano.
- Ensure system deps are present on the kit (`sudo apt-get install libsndfile1`), and pin BLAS threads for predictable thermals (`export OPENBLAS_NUM_THREADS=2`).
- If using OpenBLAS wheels, setting `OPENBLAS_CORETYPE=ARMV8` avoids generic kernels and speeds up numpy on Jetson-class boards.

---

## 📄 License

See LICENSE file.

---

## 🤝 Support

For issues, questions, or contributions:
- GitHub: [scrimshawlife-ctrl/Echotome](https://github.com/scrimshawlife-ctrl/Echotome)

---

**Echotome v3.0** — Where ritual meets cryptography.

*"The ritual is the key."*
