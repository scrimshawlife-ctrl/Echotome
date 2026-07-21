# Echotome Security Policy

## Current status

Echotome 3.1 is **experimental security software**. Do not use the current release as the sole protection for irreplaceable, regulated, safety-critical, or high-value data.

The canonical security boundary is documented in [`docs/SECURITY_MODEL.md`](docs/SECURITY_MODEL.md). The accepted redesign is recorded in [`docs/ADR-001-CRYPTOGRAPHIC-BASELINE.md`](docs/ADR-001-CRYPTOGRAPHIC-BASELINE.md).

## Important implementation notice

The current 3.1 cryptographic core contains a documented/runtime suite mismatch: it attempts to use the `cryptography` package's `ChaCha20Poly1305` class with a 24-byte nonce while describing the operation as XChaCha20-Poly1305. That class is not an XChaCha implementation. The broad exception path then falls back to AES-GCM.

Until the 3.2 format migration is complete:

- Treat 3.1 artifact writing as legacy and experimental.
- Do not infer assurance from the README's XChaCha wording.
- Preserve independent backups of plaintext and recovery material.
- Do not rely on ritual audio, timing, steganography, or decoy headers as substitutes for standard authenticated encryption and sound key management.

## Supported claims

- Ed25519 signatures can identify the signing key and detect signed-content modification when verification is correctly performed.
- Authenticated encryption can provide confidentiality and integrity when the selected algorithm, keys, nonces, and authenticated metadata are managed correctly.
- Argon2id can increase the cost of offline passphrase guessing according to its recorded parameters.

## Unsupported claims

Echotome does not currently claim:

- Hardware device attestation
- Guaranteed anti-replay or liveness
- Resistance to compromised endpoints
- Plausible deniability or coercion resistance
- Protection against state-level adversaries
- Formal verification, FIPS validation, or independent cryptographic certification

## Reporting vulnerabilities

Do not publish suspected vulnerabilities, exploit details, private artifacts, keys, passphrases, or recovery data in a public issue.

Until a private disclosure channel is configured, open a minimal GitHub issue stating that a private security report is available, without including exploitation details. Maintainers should then establish a private channel before requesting technical evidence.

## Release gate

A production-ready release requires:

1. Explicit versioned cipher and KDF suites
2. Fresh random KDF salts and per-artifact DEKs
3. Envelope encryption and authenticated manifests
4. Known-answer, tamper, recovery, migration, and fuzz tests
5. Clean-environment CI and signed release provenance
6. Independent cryptographic and application-security review
