# ADR-001 — Cryptographic Baseline and Claim Discipline

- Status: Accepted for design migration
- Date: 2026-07-20
- Decision scope: Echotome 3.2 artifact and key architecture

## Context

Echotome 3.1 mixes conventional encryption with audio-derived ritual inputs. The current implementation and documentation contain material mismatches:

1. `ChaCha20Poly1305` is invoked with a 24-byte nonce and described as XChaCha20-Poly1305, although that implementation is not XChaCha.
2. A broad exception silently switches the payload cipher to AES-GCM.
3. The artifact does not explicitly record the cipher suite.
4. The passphrase KDF salt is deterministic rather than unique per artifact.
5. Claims about replay prevention, forgery resistance, device binding, advanced attackers, and plausible deniability exceed the demonstrated evidence.
6. Audio and timing inputs are treated ambiguously as both symbolic factors and cryptographic secrets.

## Decision

### 1. Use a versioned envelope-encryption design

- Generate a fresh 256-bit DEK for each artifact.
- Encrypt payload data with AES-256-GCM as the initial baseline.
- Derive a KEK with Argon2id using a fresh random salt stored in the artifact.
- Bind optional ritual context through a canonical transcript hash and explicit domain separation.
- Wrap the DEK with the KEK.
- Authenticate all security-relevant manifest fields.

### 2. Eliminate implicit algorithm fallback

Encryption and decryption must select algorithms from an explicit `cipher_suite` identifier. Unsupported suites fail closed. Runtime exceptions must not change algorithms.

### 3. Treat audio and timing as non-secret by default

Ritual factors may provide policy gating, contextual binding, ceremony, or a possession signal. They are not counted as password entropy and are not claimed to provide liveness, anti-replay, or anti-synthesis protection without dedicated validation.

### 4. Separate identity signatures from device attestation

Ed25519 signatures prove possession of a signing key. Exportable software keys do not prove that an operation occurred on one physical device. Hardware-backed attestation is a future independent capability.

### 5. Remove unsupported deniability claims

LSB steganography and decoy headers are classified as experimental concealment or obfuscation. Echotome will not claim plausible deniability or coercion resistance without a separately reviewed construction and threat model.

### 6. Adopt assurance labels

All security features and documentation use `PROVIDED`, `DESIGNED`, `EXPERIMENTAL`, or `NOT PROVIDED` labels.

## Consequences

### Positive

- Cipher behavior becomes inspectable and interoperable.
- Password rotation becomes a DEK re-wrapping operation.
- Random salts prevent identical passphrase/profile inputs from producing the same KEK across artifacts.
- Existing experimental ritual features can remain without carrying unsupported security claims.
- Standalone operation is preserved.

### Negative

- The 3.2 artifact format is a breaking security-format revision.
- Existing 2.x/3.1 artifacts require a legacy reader and explicit migration.
- Tests and documentation must be rewritten around explicit suites and manifests.
- Some existing profile names and marketing language require deprecation.

## Migration requirements

1. Freeze legacy writers; retain read-only compatibility.
2. Add a 3.2 artifact schema and canonical serializer.
3. Add explicit suite, KDF, salt, wrapped-DEK, and manifest fields.
4. Add known-answer and corruption fixtures.
5. Add a migration command that decrypts legacy artifacts and writes 3.2 artifacts after verification.
6. Never rewrite an artifact in place; preserve the source until the migrated artifact verifies.
7. Record migration provenance without storing secrets.

## Rejected alternatives

### Continue inferring the algorithm from nonce length
Rejected because format interpretation becomes implicit and downgrade-prone.

### Keep broad cipher fallback for portability
Rejected because silent fallback makes assurance and interoperability unknowable.

### Use deterministic KDF salts for reproducibility
Rejected because password KDF salts should be unique; reproducibility belongs in test vectors, not production key derivation.

### Count audio fingerprints as secret entropy
Rejected because audio is commonly copyable, observable, reproducible, or synthesizable.

### Replace conventional encryption with ritual cryptography
Rejected. Ritual mechanisms remain an optional layer around standard authenticated encryption.
