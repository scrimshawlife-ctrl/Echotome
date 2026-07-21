# Echotome Security Upgrade Roadmap

## Objective

Move Echotome from experimental technical alpha to a standalone, reviewable encrypted-artifact product without discarding its ritual interaction model.

## P0 — Claim and format correction

### Deliverables

- [x] Bounded security model
- [x] Cryptographic baseline ADR
- [ ] Replace README absolute claims with assurance labels
- [ ] Rename security profiles to capability profiles or add explicit experimental labels
- [ ] Remove claims of plausible deniability, coercion resistance, state-level protection, and anti-replay prevention
- [ ] Declare 3.1 artifact writing experimental and legacy
- [ ] Specify the complete 3.2 artifact schema

### Exit gate

No public documentation makes a stronger claim than the threat model and automated evidence support.

## P0 — Cryptographic core 3.2

### Deliverables

- [ ] Introduce `cipher_suite` and `kdf_suite` enums
- [ ] Make AES-256-GCM the explicit baseline payload suite
- [ ] Remove broad exception-based cipher fallback
- [ ] Generate one random DEK per artifact
- [ ] Generate a fresh random Argon2id salt per wrapping operation
- [ ] Wrap the DEK with a passphrase/ritual-derived KEK
- [ ] Authenticate the complete canonical manifest as AAD
- [ ] Record all KDF parameters in the artifact
- [ ] Add explicit schema and format versions
- [ ] Reject unsupported or malformed suites and lengths
- [ ] Zero or shorten the lifetime of plaintext key buffers where Python permits

### Exit gate

Known-answer vectors, tamper tests, wrong-passphrase tests, nonce tests, and clean package tests pass in CI.

## P0 — Standalone lifecycle

### Deliverables

- [ ] One canonical CLI flow for `enroll`, `encrypt`, `inspect`, `verify`, `decrypt`, `rewrap`, `recover`, and `migrate`
- [ ] No dependency on Abraxas or any AAL service
- [ ] Optional adapters isolated behind package extras
- [ ] Atomic artifact writes and crash-safe replacement
- [ ] Explicit overwrite policy
- [ ] Recovery bundle creation and verification
- [ ] Passphrase-change workflow using DEK re-wrapping

### Exit gate

A scrubbed machine can install the package and complete the entire lifecycle offline using only documented commands.

## P1 — Legacy migration

### Deliverables

- [ ] Read-only 2.x/3.1 parser
- [ ] Fixture corpus for every supported legacy format
- [ ] `echotome migrate` command
- [ ] Source artifact preserved until destination verification succeeds
- [ ] Migration receipt with source hash, destination hash, tool version, and suite transition
- [ ] Refuse ambiguous or unauthenticated legacy input unless the user explicitly accepts a bounded recovery mode

### Exit gate

Every supported legacy fixture either migrates deterministically or fails with a stable, documented error.

## P1 — Adversarial validation

### Deliverables

- [ ] Property-based tests for serialization and parser invariants
- [ ] Artifact parser fuzzing
- [ ] Clock skew, pause, acceleration, replay, and frame-reordering experiments
- [ ] Audio substitution, re-encoding, synthesis, and noise robustness characterization
- [ ] Device-key cloning demonstration
- [ ] API authentication, body-size limits, rate limits, and path handling tests
- [ ] Concurrent vault and interrupted-write tests
- [ ] Dependency audit and SBOM

### Exit gate

Experimental ritual claims are rewritten from measured results, including false-accept and false-reject boundaries.

## P1 — CI and release engineering

### Deliverables

- [ ] Python-version and operating-system matrix
- [ ] Locked development and release dependencies
- [ ] Lint, type check, test, coverage, package build, and package install gates
- [ ] Static security analysis
- [ ] Signed source and wheel releases
- [ ] SBOM and provenance attestation
- [ ] Compatibility manifest
- [ ] Vulnerability disclosure policy

### Exit gate

A release candidate can be reproduced and validated from a clean checkout with a single command.

## P2 — Hardware-backed identity

### Deliverables

- [ ] Define a provider interface for software and hardware-backed identities
- [ ] Platform-specific non-exportable key storage where supported
- [ ] Clear UI distinction between software identity and hardware-backed identity
- [ ] Rotation, loss, and migration semantics
- [ ] No generic claim of hardware attestation unless platform evidence is verified

### Exit gate

Each provider has a separately documented threat model and conformance test suite.

## P2 — Independent review

### Deliverables

- [ ] External cryptographic design review
- [ ] Application security assessment
- [ ] Resolution of all critical and high findings
- [ ] Public review summary and limitations
- [ ] Specification freeze for 1.0

### Exit gate

Echotome may describe itself as production-ready only after independent review and completion of the standalone recovery and migration drills.

## Revised readiness trajectory

| Gate | Estimated readiness |
|---|---:|
| Current experimental baseline | 38% |
| Claim correction + 3.2 format specification | 48% |
| 3.2 crypto core + standalone lifecycle | 62% |
| Migration + adversarial validation | 76% |
| Release engineering + recovery drills | 86% |
| Independent review + resolved findings | 92%+ |

These percentages are planning indicators, not security certifications.
