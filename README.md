# Echotome v0.2.0

Audio → Crypto-Sigil Engine (AAL / ABX-Core)

Echotome takes an audio file, a secret key, and produces a deterministic
"crypto-sigil" PNG plus metadata (rune id + checksum).

## Installation

```bash
pip install -e .
```

## Usage

```bash
echotome input.wav output.png --key "your-secret-key" --json-out meta.json
```

All steps are deterministic for a given (audio, key, config).

## How to use this inside Claude Code

1. Create a new Claude Code project.
2. Add the files exactly as above.
3. Run in the integrated terminal:

```bash
pip install -e .
echotome path/to/input.wav out/sigil.png --key "my-secret"
```
