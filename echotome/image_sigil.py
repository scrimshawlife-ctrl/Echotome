from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

import numpy as np
from PIL import Image


@dataclass
class SigilParams:
    width: int = 512
    height: int = 512
    contrast_boost: float = 1.5


def features_to_sigil(
    features: np.ndarray,
    seed: int,
    params: SigilParams,
) -> Image.Image:
    """
    Convert a feature map into a deterministic 'crypto-sigil' image.

    Process:
    - Normalize features to 0–1
    - Apply random-but-deterministic permutations and textures via RNG(seed)
    - Map to 3-channel image (fake colorization)
    """
    rng = np.random.default_rng(seed)

    # Normalize features
    f = features.copy()
    if f.size == 0:
        raise ValueError("Empty feature map passed to features_to_sigil")
    f -= f.min()
    max_val = f.max()
    if max_val > 0:
        f /= max_val

    # Resize to target aspect using simple interpolation
    img_array = _resize_feature_map(
        f,
        (params.height, params.width),
    )

    # Contrast
    img_array = np.clip(
        (img_array - 0.5) * params.contrast_boost + 0.5,
        0.0,
        1.0,
    )

    # Build RGB channels using deterministic mixing
    # Channel permutations based on RNG
    perm = rng.permutation(3)
    base = img_array
    ch_r = np.clip(base + 0.15 * rng.standard_normal(base.shape), 0.0, 1.0)
    ch_g = np.clip(base + 0.15 * rng.standard_normal(base.shape), 0.0, 1.0)
    ch_b = np.clip(base + 0.15 * rng.standard_normal(base.shape), 0.0, 1.0)

    channels = [ch_r, ch_g, ch_b]
    rgb = np.stack([channels[i] for i in perm], axis=-1)

    # Convert to uint8 image
    rgb_uint8 = (rgb * 255.0).astype("uint8")
    image = Image.fromarray(rgb_uint8, mode="RGB")
    return image


def _resize_feature_map(
    f: np.ndarray,
    target_hw: Tuple[int, int],
) -> np.ndarray:
    """
    Resize 2D feature map (frames, bins) to (height, width) via bilinear interpolation.
    """
    h_t, w_t = target_hw
    h_s, w_s = f.shape

    # Map target grid into source index space
    y = np.linspace(0, h_s - 1, h_t)
    x = np.linspace(0, w_s - 1, w_t)
    yy, xx = np.meshgrid(y, x, indexing="ij")

    y0 = np.floor(yy).astype(int)
    x0 = np.floor(xx).astype(int)
    y1 = np.clip(y0 + 1, 0, h_s - 1)
    x1 = np.clip(x0 + 1, 0, w_s - 1)

    wy = yy - y0
    wx = xx - x0

    top = (1 - wx) * f[y0, x0] + wx * f[y0, x1]
    bottom = (1 - wx) * f[y1, x0] + wx * f[y1, x1]
    out = (1 - wy) * top + wy * bottom

    return out.astype("float32")
