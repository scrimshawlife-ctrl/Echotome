# Echotome

**Echotome** is a cryptographic audio key system:
- Upload an audio file → converts to MIDI → derives an AES key.
- Renders the key as a unique **song** with selectable style, motif, and scale.
- Generated key-songs can encrypt/decrypt files or secret messages.
- Signed WAV + rune watermark ensures authenticity.

## Features
- Multiple music styles (ambient, trance, lo-fi, etc).
- Seed motif + custom scales.
- Medleys (chain multiple styles).
- Export MIDI + stems.
- Proprietary derivation layer (PDL) in WASM.
- Built-in integrity & tamper checks.
- Animated splash screen + app icons.

## Run
```bash
npm install
npm run dev
