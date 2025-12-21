from __future__ import annotations

import numpy as np

from echotome.audio_layer import (
    DEFAULT_FRAME_SIZE,
    DEFAULT_HOP_SIZE,
    compute_spectral_map,
    extract_audio_features_from_samples,
    frame_audio,
)


def test_frame_audio_pads_short_inputs():
    samples = np.ones(1000, dtype=np.float32)

    frames = frame_audio(samples, frame_size=DEFAULT_FRAME_SIZE, hop_size=DEFAULT_HOP_SIZE)

    assert frames.shape == (1, DEFAULT_FRAME_SIZE)
    np.testing.assert_allclose(frames[0, : len(samples)], 1.0)
    np.testing.assert_array_equal(frames[0, len(samples) :], 0.0)


def test_compute_spectral_map_accepts_precomputed_frames_without_mutation():
    rng = np.random.default_rng(0)
    samples = rng.standard_normal(DEFAULT_FRAME_SIZE * 2, dtype=np.float32)

    frames = frame_audio(samples, frame_size=DEFAULT_FRAME_SIZE, hop_size=DEFAULT_FRAME_SIZE // 2)
    frames_copy = frames.copy()

    spec_a = compute_spectral_map(
        samples,
        frame_size=DEFAULT_FRAME_SIZE,
        hop_size=DEFAULT_FRAME_SIZE // 2,
    )
    spec_b = compute_spectral_map(
        samples,
        frame_size=DEFAULT_FRAME_SIZE,
        hop_size=DEFAULT_FRAME_SIZE // 2,
        frames=frames,
    )

    np.testing.assert_allclose(spec_a, spec_b)
    np.testing.assert_array_equal(frames, frames_copy)


def test_extract_audio_features_from_samples_is_deterministic_with_precomputed_maps():
    samples = np.linspace(-1.0, 1.0, DEFAULT_FRAME_SIZE * 3, dtype=np.float32)
    frames = frame_audio(samples, frame_size=DEFAULT_FRAME_SIZE, hop_size=DEFAULT_HOP_SIZE)
    spectral_map = compute_spectral_map(
        samples,
        frame_size=DEFAULT_FRAME_SIZE,
        hop_size=DEFAULT_HOP_SIZE,
        frames=frames,
    )

    features = extract_audio_features_from_samples(
        samples,
        frame_size=DEFAULT_FRAME_SIZE,
        hop_size=DEFAULT_HOP_SIZE,
        frames=frames,
        spectral_map=spectral_map,
    )

    assert features.shape == (256,)
    assert features.dtype == np.float32
    assert np.isfinite(features).all()
