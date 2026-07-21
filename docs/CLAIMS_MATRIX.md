# Echotome Claims Matrix

This matrix is the source of truth for README, UI, API, and release language.

| Claim area | Allowed wording | Prohibited wording before validation | Evidence required to upgrade |
|---|---|---|---|
| Payload encryption | “Uses a versioned authenticated-encryption suite.” | “Unbreakable,” “military-grade,” “cannot be decrypted.” | Known-answer vectors, nonce tests, tamper tests, independent review |
| Password hardening | “Argon2id raises the cost of offline guessing according to recorded parameters.” | “Prevents brute force.” | Parameter benchmarks, password policy, attack-cost analysis |
| Audio ritual | “Adds contextual binding or an optional unlock policy.” | “Audio is a secret key,” “cannot be synthesized or copied.” | False-accept/reject characterization and adversarial audio testing |
| Timing ritual | “Records and checks a timing transcript under defined tolerances.” | “Cannot be replayed or accelerated.” | Trusted-clock model, replay harness, acceleration/pausing tests |
| Device identity | “Signs artifacts with an Ed25519 identity key.” | “Proves the physical device,” “cannot be cloned.” | Hardware-backed non-exportability and platform attestation evidence |
| ROC certificates | “Signed metadata associated with an artifact or ritual.” | “Proves legal ownership.” | Explicit legal framework and independent review; cryptography alone is insufficient |
| Steganography | “Embeds data in an image for concealment or transport.” | “Makes the artifact undetectable.” | Steganalysis evaluation with bounded detection claims |
| Decoy headers | “Adds cosmetic obfuscation.” | “Provides plausible deniability or coercion resistance.” | Separately reviewed deniable-encryption construction and threat model |
| Recovery | “Supports tested recovery workflows where configured.” | “Data can always be recovered.” | Recovery drills across corruption, loss, migration, and rotation scenarios |
| Standards | “Designed with reference to NIST, RFC, and OWASP guidance.” | “NIST certified,” “FIPS compliant,” “formally verified.” | Relevant external validation or certification |

## Release-language rule

Every public security statement must identify one of these statuses:

- `PROVIDED`
- `DESIGNED`
- `EXPERIMENTAL`
- `NOT PROVIDED`

Marketing language must not exceed the corresponding engineering status.
