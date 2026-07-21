# Echotome Security Model

Status: **Experimental design baseline**  
Applies to: Echotome 3.1.x and the planned 3.2 security-format revision

## 1. Product security boundary

Echotome is a standalone encrypted-artifact system with optional audio-derived ritual factors. Its security must remain valid when all AAL integrations and external adapters are absent.

Echotome does **not** claim that audio, timing, visual sigils, or device identity are independently secret. These inputs may add binding, ceremony, context, or an additional possession factor, but the confidentiality of user data must rest on standard authenticated encryption and a well-defined key-management design.

## 2. Assurance labels

- **PROVIDED** — directly implemented and covered by automated tests.
- **DESIGNED** — specified, but not yet fully implemented or validated.
- **EXPERIMENTAL** — research feature with bounded, non-production claims.
- **NOT PROVIDED** — outside the supported security contract.

No security claim may use words such as "prevents," "cannot," "unforgeable," or "plausibly deniable" unless supported by a documented threat model and adversarial validation.

## 3. Protected assets

- Plaintext user files
- Data-encryption keys (DEKs)
- Key-encryption keys (KEKs)
- Identity private keys
- Recovery material
- Artifact manifests and provenance records
- Vault metadata that may reveal user activity

## 4. Adversaries

### A1 — Opportunistic file thief
Obtains encrypted artifacts but not the passphrase, recovery material, or protected device keys.

### A2 — Offline password attacker
Obtains artifacts and performs repeated KDF attempts using commodity or specialized hardware.

### A3 — Local account attacker
Can read user-accessible files and configuration but does not control the operating-system kernel or hardware-backed keystore.

### A4 — Compromised application runtime
Can inspect process memory while Echotome is unlocked. Confidentiality after successful runtime compromise is **NOT PROVIDED**.

### A5 — Device-cloning attacker
Copies exportable identity keys and application files. Software-stored device identity alone does not distinguish a clone.

### A6 — Coercive or state-level adversary
Resistance to compelled disclosure, endpoint implants, invasive hardware attacks, or forensic laboratory analysis is **NOT PROVIDED**.

## 5. Cryptographic design requirements for 3.2

### 5.1 Envelope encryption

1. Generate a random 256-bit DEK using the operating system CSPRNG.
2. Encrypt plaintext with an explicit, versioned AEAD suite.
3. Derive a KEK from the passphrase and optional ritual transcript using Argon2id.
4. Wrap the DEK with the KEK.
5. Store the wrapped DEK, KDF parameters, random KDF salt, AEAD nonce, suite identifiers, and authenticated manifest in the artifact.

Changing a passphrase should re-wrap the DEK rather than re-encrypt the payload.

### 5.2 Approved baseline suites

The initial interoperable suite is:

- Payload AEAD: `AES-256-GCM`
- Password KDF: `Argon2id`
- Identity signatures: `Ed25519`
- General hashing: `SHA-256`
- Key separation/expansion: `HKDF-SHA-256` only where a documented domain-separation purpose exists
- Randomness: operating-system CSPRNG

XChaCha20-Poly1305 may be added only through a library that actually implements the XChaCha construction and after cross-platform test vectors are committed. The current `cryptography` `ChaCha20Poly1305` class must not be described as XChaCha20-Poly1305.

### 5.3 Random salts and nonces

- Every password-derived KEK receives a fresh random salt.
- Salts are stored in the artifact and are not secret.
- AES-GCM nonces are 96 bits, randomly generated, and must never repeat for the same key.
- Algorithms are selected by an explicit `cipher_suite` field, never inferred from nonce length and never selected by catching a broad exception.

### 5.4 Ritual input role

Audio and timing data are treated as **public or reproducible context by default**. They may be included in a transcript hash used as Argon2id associated input or in a domain-separated KEK derivation, but they must not reduce passphrase entropy or replace random salts.

Ritual verification may gate an unlock attempt as an application policy. It is not described as proof of liveness, anti-replay protection, or device attestation until those claims are demonstrated against a documented adversary.

### 5.5 Device identity

Software-stored Ed25519 keys provide artifact signing and continuity of identity, not hardware attestation. A copied private key produces an indistinguishable clone. Hardware-backed keys may strengthen non-exportability on supported platforms, but this is a separate capability with separate assurance.

## 6. Artifact requirements

Every 3.2 artifact must include and authenticate:

- Magic value and format version
- Cipher-suite identifier
- KDF identifier and complete parameters
- Random KDF salt
- Wrapped DEK
- Payload nonce
- Payload ciphertext and authentication tag
- Manifest schema version
- Optional signer key identifier and signature
- Optional ritual transcript hash and policy identifier
- Creation tool version

Parsers must reject unknown mandatory fields, unsupported suites, invalid lengths, duplicate fields, malformed encodings, authentication failures, and version downgrades.

## 7. Feature classification

| Feature | Classification | Supported claim |
|---|---|---|
| AES-GCM payload encryption | DESIGNED baseline | Confidentiality and integrity when keys and nonces are managed correctly |
| Argon2id passphrase hardening | DESIGNED baseline | Raises offline guessing cost according to recorded parameters |
| Ed25519 certificates | EXPERIMENTAL/PARTIAL | Detects modification and identifies the signing key |
| Temporal Salt Chain | EXPERIMENTAL | Deterministic ordering transcript; no anti-replay claim |
| Audio fingerprint/RIV | EXPERIMENTAL | Matching and contextual binding; not a secret |
| PNG LSB steganography | EXPERIMENTAL | Concealment convenience; not cryptographic confidentiality |
| Decoy headers | EXPERIMENTAL | Cosmetic obfuscation; no plausible-deniability claim |
| Microphone ritual | EXPERIMENTAL | User-interaction gate; no liveness or anti-synthesis claim |
| Abraxas bridge | OPTIONAL ADAPTER | Must not receive secret key material |

## 8. Recovery and lifecycle

Production readiness requires tested procedures for:

- Passphrase change
- DEK re-wrapping
- Identity-key rotation
- Compromise response and revocation metadata
- Recovery bundle creation and verification
- Device migration
- Lost ritual input
- Corrupt artifact restoration from backup
- Secure deletion limitations
- Version and algorithm migration

Unrecoverable-by-default profiles are prohibited for the 1.0 general release. Expert-only irreversible modes, if retained, require explicit acknowledgement and independent recovery testing.

## 9. Required validation gates

- Known-answer tests for every suite
- Wrong-passphrase and tamper rejection
- Nonce-uniqueness tests
- Deterministic canonical-manifest tests
- Malformed artifact and parser fuzzing
- Cross-version compatibility fixtures
- Clock manipulation and replay experiments for ritual features
- Key rotation and recovery drills
- Clean-environment package installation
- Dependency and static analysis
- Signed release manifest and SBOM
- Independent cryptographic review before claims of production security

## 10. Standards basis

This design follows the principles of NIST SP 800-218 SSDF, NIST cryptographic and key-management guidance, RFC 9106 for Argon2, RFC 8032 for Ed25519, and OWASP cryptographic-storage and key-management guidance. Standards alignment does not imply certification, validation, or formal compliance.
