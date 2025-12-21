"""
Compatibility shim re-exporting audio helpers.

Prefer :mod:`echotome.audio_layer` for new development; this module
exists to keep legacy imports working while sharing the same
implementations and optimizations.
"""

from __future__ import annotations

from .audio_layer import (
    DEFAULT_FRAME_SIZE,
    DEFAULT_HOP_SIZE,
    DEFAULT_SAMPLE_RATE,
    _resample_linear,  # noqa: F401 — kept for backward compatibility
    compute_spectral_map,
    extract_audio_features,
    extract_audio_features_from_samples,
    frame_audio,
    load_audio_mono,
)

__all__ = [
    "DEFAULT_FRAME_SIZE",
    "DEFAULT_HOP_SIZE",
    "DEFAULT_SAMPLE_RATE",
    "compute_spectral_map",
    "extract_audio_features",
    "extract_audio_features_from_samples",
    "frame_audio",
    "load_audio_mono",
]
