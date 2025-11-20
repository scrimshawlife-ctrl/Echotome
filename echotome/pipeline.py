from __future__ import annotations

from pathlib import Path
from typing import Optional

from .audio_layer import load_audio_mono, compute_spectral_map, extract_audio_features
from .config import EchotomeConfig, EchotomeResult
from .crypto_core import derive_final_key, encrypt_bytes, decrypt_bytes, EncryptedBlob, rune_id_from_key
from .privacy_profiles import get_profile
from .sigil_layer import generate_sigil, features_to_sigil, SigilParams


def encrypt_with_echotome(
    audio_path: Path,
    passphrase: str,
    profile_name: str,
    in_file: Path,
    out_file: Path,
    sigil_path: Optional[Path] = None,
) -> dict:
    """
    High-level encryption pipeline using Echotome AF-KDF.

    Steps:
    1. Load audio and extract features
    2. Derive key via AF-KDF (passphrase + audio + profile)
    3. Generate sigil from audio features and key
    4. Encrypt input file using AEAD
    5. Save encrypted blob to output file
    6. Optionally save sigil image

    Args:
        audio_path: Path to audio file
        passphrase: User's secret passphrase
        profile_name: Privacy profile (QuickLock, RitualLock, BlackVault)
        in_file: Path to file to encrypt
        out_file: Path for encrypted output
        sigil_path: Optional path to save sigil image

    Returns:
        Metadata dictionary with rune_id, profile, etc.
    """
    # Load profile
    profile = get_profile(profile_name)

    # Extract audio features
    audio_features = extract_audio_features(audio_path)

    # Derive final key using AF-KDF
    key = derive_final_key(passphrase, audio_features, profile)

    # Generate rune ID
    rune_id = rune_id_from_key(key)

    # Encrypt file
    with open(in_file, "rb") as f:
        plaintext = f.read()

    context = {
        "profile_name": profile.name,
        "rune_id": rune_id,
        "filename": in_file.name,
    }
    if profile.deniable:
        context["deniable"] = True

    blob = encrypt_bytes(plaintext, key, context)

    # Save encrypted file
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w") as f:
        f.write(blob.to_json())

    # Generate and save sigil if requested
    if sigil_path:
        spectral_map = compute_spectral_map(
            load_audio_mono(audio_path, 16000)[0],
            frame_size=2048,
            hop_size=512,
        )
        sigil = generate_sigil(spectral_map, key, size=(512, 512))
        sigil_path.parent.mkdir(parents=True, exist_ok=True)
        sigil.save(str(sigil_path), format="PNG")

    # Return metadata
    return {
        "rune_id": rune_id,
        "profile": profile.name,
        "audio_path": str(audio_path),
        "encrypted_file": str(out_file),
        "sigil_path": str(sigil_path) if sigil_path else None,
        "original_filename": in_file.name,
    }


def decrypt_with_echotome(
    audio_path: Path,
    passphrase: str,
    blob_file: Path,
    out_file: Path,
) -> dict:
    """
    High-level decryption pipeline using Echotome AF-KDF.

    Steps:
    1. Load encrypted blob
    2. Extract audio features
    3. Derive key via AF-KDF using blob's profile
    4. Decrypt and verify
    5. Save plaintext to output file

    Args:
        audio_path: Path to audio file (same as used for encryption)
        passphrase: User's secret passphrase (same as used for encryption)
        blob_file: Path to encrypted blob file
        out_file: Path for decrypted output

    Returns:
        Metadata dictionary

    Raises:
        ValueError: If decryption fails (wrong key, corrupted data, etc.)
    """
    # Load encrypted blob
    with open(blob_file, "r") as f:
        blob = EncryptedBlob.from_json(f.read())

    # Load profile from blob
    profile = get_profile(blob.profile_name)

    # Extract audio features
    audio_features = extract_audio_features(audio_path)

    # Derive final key using AF-KDF
    key = derive_final_key(passphrase, audio_features, profile)

    # Verify rune ID matches
    expected_rune_id = rune_id_from_key(key)
    if expected_rune_id != blob.rune_id:
        raise ValueError(
            f"Rune ID mismatch! Expected {expected_rune_id}, got {blob.rune_id}. "
            "Wrong passphrase, audio file, or corrupted blob."
        )

    # Decrypt
    plaintext = decrypt_bytes(blob, key)

    # Save decrypted file
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "wb") as f:
        f.write(plaintext)

    return {
        "rune_id": blob.rune_id,
        "profile": profile.name,
        "decrypted_file": str(out_file),
        "blob_version": blob.version,
    }


# Legacy v0.2.0 interface (kept for backward compatibility)
def run_echotome(config: EchotomeConfig) -> EchotomeResult:
    """
    Legacy Echotome v0.2.0 pipeline (sigil generation only).

    This function is kept for backward compatibility.
    New code should use encrypt_with_echotome() and decrypt_with_echotome().

    Pipeline:
    - Load audio
    - Compute feature map
    - Derive hash + seed
    - Generate sigil image
    - Save image and return metadata
    """
    from .crypto import derive_feature_hash, build_rune_id

    input_path = Path(config.input_audio)
    output_path = Path(config.output_image)

    # 1) Load audio
    samples, sr = load_audio_mono(
        input_path,
        target_sample_rate=config.target_sample_rate,
    )

    # 2) Features
    features = compute_spectral_map(
        samples,
        frame_size=config.frame_size,
        hop_size=config.hop_size,
    )

    # 3) Hash / seed
    digest, seed = derive_feature_hash(features, config.secret_key)
    rune_id = build_rune_id(digest, prefix=config.rune_prefix)

    # 4) Sigil image
    sigil_params = SigilParams(
        width=config.image_width,
        height=config.image_height,
        contrast_boost=config.contrast_boost,
    )
    image = features_to_sigil(features, seed=seed, params=sigil_params)

    # 5) Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(str(output_path), format="PNG")

    checksum = digest
    result = EchotomeResult(
        rune_id=rune_id,
        checksum=checksum,
        config=config.to_dict(),
    )
    return result
