# Echotome v3.2 Security Hardening Guide

**Version**: 3.2.0
**Edition**: Session & Locality Enforcement
**Threat Models**: Casual, Focused, Targeted

## Table of Contents

1. [Security Architecture](#security-architecture)
2. [Threat Models](#threat-models)
3. [Locality Enforcement](#locality-enforcement)
4. [Session Security](#session-security)
5. [Cryptographic Operations](#cryptographic-operations)
6. [Privacy Guardrails](#privacy-guardrails)
7. [Attack Surface Analysis](#attack-surface-analysis)
8. [Security Audit Checklist](#security-audit-checklist)

---

## Security Architecture

### Defense in Depth

Echotome v3.2 implements multiple security layers:

```
┌─────────────────────────────────────────────┐
│  Layer 1: Locality Enforcement (v3.2)       │
│  - No network calls                         │
│  - No telemetry                             │
│  - Local-only operation                     │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  Layer 2: Audio-Field KDF                   │
│  - Multi-factor key derivation              │
│  - Audio features + passphrase              │
│  - Profile-based hardness                   │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  Layer 3: Time-Limited Sessions (v3.2)      │
│  - Profile-based TTLs                       │
│  - Auto-expiration                          │
│  - Secure deletion                          │
└─────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────┐
│  Layer 4: Privacy-Aware Logging (v3.2)      │
│  - Sensitive data redaction                 │
│  - No audio in logs                         │
│  - No passphrases in logs                   │
└─────────────────────────────────────────────┘
```

---

## Threat Models

### Quick Lock (Casual Adversary)

**Assumptions**:
- Casual attacker (no forensics)
- Physical access unlikely
- Convenience prioritized

**Protections**:
- KDF: 2 iterations, 64 GB RAM
- Session TTL: 1 hour
- Audio weight: 0% (passphrase-only)
- Secure delete: Disabled

**Does NOT Protect Against**:
- Determined attackers with forensics
- Memory dumps
- Targeted attacks

**Use Cases**:
- Personal documents
- Non-sensitive data
- Convenience prioritized

### Ritual Lock (Focused Adversary)

**Assumptions**:
- Motivated attacker with tools
- Some forensic capability
- Balanced security/usability

**Protections**:
- KDF: 4 iterations, 128 GB RAM
- Session TTL: 20 minutes
- Audio weight: 70% (hybrid)
- Secure delete: Enabled (3-pass)

**Does NOT Protect Against**:
- State-level actors
- Hardware implants
- Advanced persistent threats

**Use Cases**:
- Business documents
- Sensitive personal data
- Compliance requirements

### Black Vault (Targeted Adversary)

**Assumptions**:
- State-level actor or equivalent
- Advanced forensics
- Hardware attacks possible
- Maximum paranoia

**Protections**:
- KDF: 8 iterations, 256 GB RAM
- Session TTL: 5 minutes (strict)
- Audio weight: 100% (audio required)
- Secure delete: Enabled (3-pass + memory zeroing)
- Memory-only mode: No plaintext disk
- Auto-lock on background
- Deniable encryption support

**Does NOT Protect Against**:
- Physical torture/coercion
- Compromised hardware
- Quantum computers (future threat)

**Use Cases**:
- Whistleblowing
- Investigative journalism
- High-risk activism
- Classified data

---

## Locality Enforcement

### v3.2 Locality Constants

**Location**: `echotome/privacy.py`

```python
# Enforced at code level
PRIVACY_STRICT = True              # Strict privacy mode
ALLOW_THIRD_PARTY_UPLOADS = False  # No external uploads
ALLOW_EXTERNAL_TELEMETRY = False   # No telemetry
NETWORK_ISOLATED = True            # Local-only operation
```

### Verification

```python
# Check locality enforcement
from echotome.privacy import (
    PRIVACY_STRICT,
    ALLOW_THIRD_PARTY_UPLOADS,
    ALLOW_EXTERNAL_TELEMETRY,
    NETWORK_ISOLATED,
)

assert PRIVACY_STRICT == True
assert ALLOW_THIRD_PARTY_UPLOADS == False
assert ALLOW_EXTERNAL_TELEMETRY == False
assert NETWORK_ISOLATED == True
```

### Network Isolation

**Firewall rules** (iptables):

```bash
# Block outbound from Echotome service
iptables -A OUTPUT -m owner --uid-owner echotome -j REJECT

# Allow local loopback only
iptables -A OUTPUT -m owner --uid-owner echotome -d 127.0.0.1 -j ACCEPT
```

**SELinux policy**:

```
# echotome.te
policy_module(echotome, 1.0.0)

type echotome_t;
type echotome_exec_t;

# Allow local socket only
allow echotome_t self:tcp_socket { bind connect listen };
allow echotome_t self:unix_stream_socket { bind connect listen };

# Deny all network
dontaudit echotome_t kernel_t:tcp_socket *;
```

---

## Session Security

### v3.2 Session Architecture

**Session directory**:
```
~/.echotome/sessions/<session_id>/
├── decrypted_file_1
├── decrypted_file_2
└── .session_metadata
```

**Permissions**:
```bash
chmod 700 ~/.echotome/sessions        # rwx------
chmod 700 ~/.echotome/sessions/*      # rwx------
chown -R echotome:echotome ~/.echotome
```

### Secure Deletion (3-Pass)

**Implementation**: `echotome/sessions.py`

```python
def secure_delete_file(path: Path) -> None:
    """
    3-pass secure deletion:
    1. Overwrite with zeros
    2. Overwrite with ones
    3. Overwrite with random data
    """
    size = path.stat().st_size

    with open(path, 'r+b') as f:
        # Pass 1: Zeros
        f.seek(0)
        f.write(b'\x00' * size)
        f.flush()
        os.fsync(f.fileno())

        # Pass 2: Ones
        f.seek(0)
        f.write(b'\xff' * size)
        f.flush()
        os.fsync(f.fileno())

        # Pass 3: Random
        f.seek(0)
        f.write(os.urandom(size))
        f.flush()
        os.fsync(f.fileno())

    # Finally, unlink
    path.unlink()
```

### Memory Zeroing

```python
def zero_memory(key: bytes) -> None:
    """Zero out key material before deallocation."""
    if isinstance(key, bytes):
        # Overwrite with zeros
        key_buffer = ctypes.create_string_buffer(len(key))
        ctypes.memset(ctypes.addressof(key_buffer), 0, len(key))
```

### Session Expiration

**Auto-expiration** (enforced at API level):

```python
def is_session_valid(session: Session) -> bool:
    """Check if session is still valid."""
    if time.time() > session.expires_at:
        # Session expired
        cleanup_session(session.session_id)
        return False
    return True
```

**Background cleanup** (cron):

```bash
# Every 5 minutes
*/5 * * * * /opt/echotome/venv/bin/python -c "from echotome.sessions import get_session_manager; get_session_manager().cleanup_expired_sessions()"
```

---

## Cryptographic Operations

### Audio-Field Key Derivation (AF-KDF)

**Algorithm**: PBKDF2-HMAC-SHA256 + Audio Features

```python
def derive_final_key(
    passphrase: str,
    audio_features: np.ndarray,
    profile: PrivacyProfile
) -> bytes:
    """
    Derive master key from passphrase + audio.

    Args:
        passphrase: User passphrase
        audio_features: Extracted audio features (numpy array)
        profile: Privacy profile (KDF parameters)

    Returns:
        32-byte master key
    """
    # Extract audio salt
    audio_salt = hash_audio_features(audio_features)

    # PBKDF2 with profile-specific parameters
    key = PBKDF2(
        password=passphrase.encode('utf-8'),
        salt=audio_salt,
        iterations=profile.kdf_time * 100000,  # Scaled
        dkLen=32,
        hmac_hash_module=SHA256
    )

    # Mix in audio features (weighted by profile.audio_weight)
    if profile.audio_weight > 0:
        audio_key = derive_from_features(audio_features)
        key = weighted_mix(key, audio_key, profile.audio_weight)

    return key
```

### Encryption Scheme

**Algorithm**: AES-256-GCM

```python
def encrypt_data(plaintext: bytes, key: bytes) -> dict:
    """
    Encrypt plaintext with AES-256-GCM.

    Args:
        plaintext: Data to encrypt
        key: 32-byte master key

    Returns:
        {
            "ciphertext": base64,
            "nonce": base64,
            "tag": base64
        }
    """
    cipher = Cipher(algorithms.AES(key), modes.GCM(nonce), backend=default_backend())
    encryptor = cipher.encryptor()

    ciphertext = encryptor.update(plaintext) + encryptor.finalize()

    return {
        "ciphertext": base64.b64encode(ciphertext).decode(),
        "nonce": base64.b64encode(nonce).decode(),
        "tag": base64.b64encode(encryptor.tag).decode()
    }
```

### Rune ID (Key Fingerprint)

```python
def rune_id_from_key(key: bytes) -> str:
    """Generate human-readable key fingerprint."""
    digest = hashlib.sha256(key).digest()
    return base64.b32encode(digest[:20]).decode().lower()
```

---

## Privacy Guardrails

### Privacy-Aware Logging

**Implementation**: `echotome/privacy.py`

```python
class PrivacyAwareLogger:
    """Logger that redacts sensitive data."""

    SENSITIVE_KEYS = [
        'passphrase', 'password', 'key', 'secret',
        'audio', 'audio_data', 'audio_features',
        'recovery_code', 'master_key'
    ]

    def sanitize(self, data: dict) -> dict:
        """Redact sensitive keys."""
        sanitized = {}
        for k, v in data.items():
            if any(s in k.lower() for s in self.SENSITIVE_KEYS):
                sanitized[k] = '[REDACTED]'
            else:
                sanitized[k] = v
        return sanitized

    def log_operation(self, operation: str, details: dict) -> None:
        """Log operation with sanitization."""
        sanitized = self.sanitize(details)
        logger.info(f"{operation}: {sanitized}")
```

### Example Logs

**✅ GOOD (privacy-aware)**:
```
[INFO] Decrypt operation started: vault_id=abc123, profile=Ritual Lock, rune_id=xyz789
[INFO] Audio features extracted: duration=5.2s, sample_rate=44100
[INFO] KDF completed: iterations=400000, memory=128MB, time=12.3s
[INFO] Session created: session_id=def456, ttl=1200s
[INFO] Decrypt operation completed: session_id=def456, time=13.1s
```

**❌ BAD (privacy violations)**:
```
[ERROR] Decrypt failed: passphrase=hunter2, audio=/path/to/recording.wav
[DEBUG] Master key: 0x3a7f2e1b...
[DEBUG] Decrypted plaintext: <binary data>
```

### Filename Redaction

```python
def redact_path(path: Path) -> str:
    """Redact filename, keep directory structure."""
    return str(path.parent / '[FILENAME_REDACTED]')

# Example
logger.info(f"File encrypted: {redact_path(input_file)}")
# Output: File encrypted: /home/user/documents/[FILENAME_REDACTED]
```

---

## Attack Surface Analysis

### Attack Vectors

| Vector | Risk | Mitigation |
|--------|------|------------|
| **Weak passphrase** | High | Enforce minimum entropy, recovery codes |
| **Audio reuse** | Medium | Warn users, support multi-track rituals |
| **Memory dumps** | High | Memory zeroing, Black Vault memory-only mode |
| **Session hijacking** | Low | Sessions local-only, no network exposure |
| **Path traversal** | Low | Strict path validation, resolve() checks |
| **Timing attacks** | Medium | Constant-time comparisons for sensitive ops |
| **Side-channel** | Medium | KDF randomness, no predictable delays |
| **Forensic recovery** | High | 3-pass secure delete, SSD may leak |

### Mitigations

**1. Passphrase Entropy**:
```python
def check_passphrase_strength(passphrase: str) -> bool:
    """Enforce minimum entropy."""
    if len(passphrase) < 12:
        return False
    if not any(c.isupper() for c in passphrase):
        return False
    if not any(c.islower() for c in passphrase):
        return False
    if not any(c.isdigit() for c in passphrase):
        return False
    return True
```

**2. Constant-Time Comparison**:
```python
import hmac

def verify_rune_id(expected: str, provided: str) -> bool:
    """Compare rune IDs in constant time."""
    return hmac.compare_digest(expected, provided)
```

**3. SSD Wear Leveling** (secure delete limitation):
```bash
# For SSDs, consider cryptographic erasure instead
# Encrypt storage, then discard keys
```

**4. Recovery Code Protection**:
```python
def hash_recovery_code(code: str) -> str:
    """Hash recovery codes (never store plaintext)."""
    return bcrypt.hashpw(code.encode(), bcrypt.gensalt())
```

---

## Security Audit Checklist

### Pre-Deployment

- [ ] **Locality verification**: No outbound network calls
- [ ] **Logging audit**: No sensitive data in logs
- [ ] **Session permissions**: 700 for session directories
- [ ] **Secure delete enabled**: For Ritual Lock and Black Vault
- [ ] **HTTPS enforced**: Certificate valid, no HTTP fallback
- [ ] **Rate limiting**: Configured on reverse proxy
- [ ] **Firewall rules**: Echotome user network-isolated
- [ ] **Memory limits**: OOM killer configured
- [ ] **Session cleanup**: Cron job active
- [ ] **Recovery codes**: Hashed, never plaintext
- [ ] **API authentication**: Token/key-based auth configured
- [ ] **Error messages**: Generic, no sensitive data leaks

### Runtime Monitoring

- [ ] **Active sessions**: Monitor count, detect anomalies
- [ ] **Failed decrypt attempts**: Rate limit, log for audit
- [ ] **Session expiration**: Verify auto-cleanup works
- [ ] **Disk usage**: Session directories cleaned up
- [ ] **Memory usage**: No leaks, Black Vault memory-only
- [ ] **API latency**: KDF operations within expected range
- [ ] **Log review**: Daily review for security events

### Incident Response

1. **Session compromise detected**:
   ```bash
   # Emergency lock all sessions
   curl -X DELETE http://localhost:8000/sessions?secure_delete=true
   ```

2. **Suspected key leak**:
   ```bash
   # Regenerate recovery codes
   echotome recovery --count 10
   ```

3. **Unauthorized access**:
   ```bash
   # Review logs
   grep "Decrypt failed" /var/log/echotome/api.log
   # Check for brute force patterns
   ```

---

## Compliance

### GDPR Considerations

- **Right to erasure**: Secure deletion support
- **Data minimization**: No unnecessary data collected
- **Privacy by design**: Locality enforcement, no telemetry

### HIPAA Considerations

- **Encryption at rest**: AES-256-GCM
- **Access controls**: Session-based, time-limited
- **Audit logs**: Privacy-aware logging

---

## Security Contacts

**Security vulnerabilities**: security@echotome.example.com

**PGP Key**: [Include PGP public key]

**Responsible Disclosure**: 90-day disclosure window

---

**End of Security Guide**
