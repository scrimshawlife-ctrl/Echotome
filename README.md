# Echotome v2.0

**Audio-Field Key Derivation & Crypto-Sigil Engine**

Echotome is a modular privacy instrument that combines audio biometrics with cryptography to create a unique encryption system. It uses **AF-KDF** (Audio-Field Key Derivation Function) to derive cryptographic keys from the combination of:
- Your secret passphrase
- Audio file characteristics
- Privacy profile settings

---

## Features

### 🔐 AF-KDF (Audio-Field Key Derivation)
Derives cryptographic keys from passphrase + audio features using:
- Argon2id memory-hard KDF (with scrypt fallback)
- SHA-256 audio feature hashing
- HKDF for input mixing

### 🛡️ Privacy Profiles
Three security modes for different use cases:

| Profile | Memory | Time | Audio Weight | Deniable |
|---------|--------|------|--------------|----------|
| **QuickLock** | 64 MB | 2 iter | 0.0 (passphrase only) | No |
| **RitualLock** | 256 MB | 4 iter | 0.7 (strong audio binding) | No |
| **BlackVault** | 512 MB | 8 iter | 1.0 (full audio dependence) | Yes |

### 🔒 AEAD Encryption
- **XChaCha20-Poly1305** (preferred)
- **AES-GCM** (fallback)
- Authenticated encryption with associated data

### 🎨 Crypto-Sigils
Deterministic visual art generated from audio + key:
- Spectral feature mapping
- Key-seeded randomness
- 512x512 PNG output

### 📦 Vault System
JSON-backed encrypted storage:
- Multiple vaults with different profiles
- File encryption/decryption
- Metadata tracking
- Stored in `~/.echotome/`

### 🌉 Abraxas Bridge
Safe metadata export (NO secrets):
- Rune IDs
- Entropy scores
- Profile statistics
- Vault constellations

---

## Installation

```bash
pip install -e .
```

### Dependencies
- numpy
- soundfile
- Pillow
- cryptography (Argon2id, XChaCha20-Poly1305)
- fastapi, uvicorn (for API server)

---

## Quick Start

### Encrypt a File

```bash
python -c "
from pathlib import Path
from echotome import encrypt_with_echotome

encrypt_with_echotome(
    audio_path=Path('audio.wav'),
    passphrase='my-secret-phrase',
    profile_name='RitualLock',
    in_file=Path('secret.txt'),
    out_file=Path('secret.enc'),
    sigil_path=Path('sigil.png'),
)
"
```

### Decrypt a File

```bash
python -c "
from pathlib import Path
from echotome import decrypt_with_echotome

decrypt_with_echotome(
    audio_path=Path('audio.wav'),
    passphrase='my-secret-phrase',
    blob_file=Path('secret.enc'),
    out_file=Path('decrypted.txt'),
)
"
```

---

## Privacy Profiles Explained

### QuickLock 🔓
- **Use case**: Fast encryption, low-resource devices
- **Audio**: Not used (passphrase only)
- **Speed**: ~100ms encryption
- **Security**: Standard passphrase-based

### RitualLock 🔮
- **Use case**: Important files, symbolic audio binding
- **Audio**: 70% influence on key derivation
- **Speed**: ~500ms encryption
- **Security**: Audio acts as secondary factor
- **Note**: Requires same audio file to decrypt

### BlackVault 🖤
- **Use case**: Maximum paranoia, plausible deniability
- **Audio**: 100% audio dependence
- **Speed**: ~1s encryption
- **Security**: Cannot decrypt without exact audio file
- **Deniability**: Encrypted data includes decoy headers

---

## Vault Management

### Create a Vault

```python
from pathlib import Path
from echotome import create_vault, extract_audio_features, derive_final_key, get_profile, rune_id_from_key

audio_features = extract_audio_features(Path('audio.wav'))
profile = get_profile('RitualLock')
key = derive_final_key('my-passphrase', audio_features, profile)
rune = rune_id_from_key(key)

vault = create_vault('MySecrets', 'RitualLock', rune)
print(f"Created vault: {vault.id}")
```

### List Vaults

```python
from echotome import list_vaults

vaults = list_vaults()
for v in vaults:
    print(f"{v.name}: {v.rune_id} ({v.file_count} files)")
```

---

## API Server

Start the REST API:

```bash
echotome-api
# or
python -m echotome.api
```

### Endpoints

- `GET /health` - Health check
- `GET /profiles` - List privacy profiles
- `POST /create_vault` - Create new vault
- `POST /encrypt` - Encrypt file
- `POST /decrypt` - Decrypt file
- `GET /vaults` - List all vaults
- `DELETE /vaults/{id}` - Delete vault

---

## How AF-KDF Works

```
┌─────────────┐
│ Passphrase  │
└──────┬──────┘
       │
       ├──────────────┐
       │              │
┌──────▼──────┐  ┌───▼────────┐
│ Audio File  │  │  Profile   │
│  Features   │  │  Settings  │
└──────┬──────┘  └───┬────────┘
       │             │
       │   SHA-256   │
       └──────┬──────┘
              │
       ┌──────▼──────┐
       │    HKDF     │
       │   Mixing    │
       └──────┬──────┘
              │
       ┌──────▼──────┐
       │  Argon2id   │
       │  (or scrypt)│
       └──────┬──────┘
              │
       ┌──────▼──────┐
       │  Final Key  │
       │  (32 bytes) │
       └─────────────┘
```

---

## Security Considerations

### ✅ What Echotome Provides
- Memory-hard key derivation (Argon2id)
- Authenticated encryption (AEAD)
- Deterministic key generation
- Audio as a second factor

### ⚠️ What Echotome Does NOT Provide
- **NOT a replacement for standard encryption** (use for symbolic/artistic purposes)
- **Audio is NOT secret** - Anyone can access your audio file
- **Audio dependence is a feature AND risk** - Lose the audio, lose the data
- **Plausible deniability is experimental** - Not legally tested

### 🔒 Best Practices
1. Use strong passphrases (20+ characters)
2. Keep backup copies of audio files used with BlackVault
3. Use RitualLock for important data (balance security/usability)
4. Use QuickLock for non-sensitive data
5. Never commit vault data or audio files to public repos

---

## Abraxas Integration

Export metadata for Abraxas visualization:

```python
from echotome import export_for_abraxas

data = export_for_abraxas()
print(data['stats'])
print(data['constellation'])
```

**Abraxas receives**:
- Rune IDs
- Entropy scores
- Profile distribution
- Vault age/usage stats

**Abraxas NEVER receives**:
- Encryption keys
- Passphrases
- Plaintext data
- Audio file paths

---

## CLI (Legacy v0.2.0)

The original sigil-only CLI is still available:

```bash
echotome input.wav output.png --key "secret" --json-out meta.json
```

---

## Development

### Run Tests
```bash
pip install -e ".[dev]"
pytest
```

### Format Code
```bash
black echotome/
ruff check echotome/
```

---

## Architecture (ABX-Core Style)

Echotome follows modular ABX-Core principles:

```
echotome/
├── audio_layer.py      # Audio I/O and feature extraction
├── crypto_core.py      # AF-KDF and AEAD encryption
├── privacy_profiles.py # Profile definitions
├── sigil_layer.py      # Visual crypto-art generation
├── vaults.py           # Vault management
├── pipeline.py         # High-level orchestration
├── api.py              # REST API server
└── abraxas_bridge.py   # Metadata export
```

Each module is standalone and can be used independently.

---

## License

See LICENSE file.

---

## Support

For issues, questions, or contributions:
- GitHub: [scrimshawlife-ctrl/Echotome](https://github.com/scrimshawlife-ctrl/Echotome)

---

**Echotome v2.0** — Where audio meets cryptography.
