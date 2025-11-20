from __future__ import annotations

from pathlib import Path

from .audio_features import load_audio_mono, compute_spectral_map
from .config import EchotomeConfig, EchotomeResult
from .crypto import derive_feature_hash, build_rune_id
from .image_sigil import SigilParams, features_to_sigil


def run_echotome(config: EchotomeConfig) -> EchotomeResult:
    """
    Full Echotome pipeline:
    - Load audio
    - Compute feature map
    - Derive hash + seed
    - Generate sigil image
    - Save image and return metadata
    """
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

    checksum = digest  # exposed directly; could later compress/encode if needed
    result = EchotomeResult(
        rune_id=rune_id,
        checksum=checksum,
        config=config.to_dict(),
    )
    return result
