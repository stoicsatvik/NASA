"""Deterministic tests for E554; no live source or raw data required."""
import numpy as np
import pytest

from experiments.e554_hirise_nodata_neighborhood import (
    BLOCK_SIZE,
    WINDOW_SIZE,
    summarize_mask,
)


def test_all_nodata_neighborhood_is_not_mislabeled_as_a_measurement():
    values = np.full((WINDOW_SIZE, WINDOW_SIZE), -9999.0, dtype=np.float32)
    result = summarize_mask(values, -9999.0)
    assert result["usable_pixels"] == 0
    assert result["center_64x64_usable_pixels"] == 0
    assert result["classification"] == "ALL_NODATA_WITHIN_128M"
    assert result["raw_pixels_retained"] is False


def test_center_gap_with_valid_pixels_nearby_is_detected():
    values = np.full((WINDOW_SIZE, WINDOW_SIZE), -9999.0, dtype=np.float32)
    values[:16, :] = 12.0
    result = summarize_mask(values, -9999.0)
    assert result["usable_pixels"] == 16 * WINDOW_SIZE
    assert result["center_64x64_usable_pixels"] == 0
    assert result["classification"] == "NODATA_CORE_WITH_NEARBY_SUPPORT"


def test_support_reaching_center_is_distinguished_from_edge_only_support():
    values = np.full((WINDOW_SIZE, WINDOW_SIZE), -9999.0, dtype=np.float32)
    values[32:96, 32:96] = 3.0
    result = summarize_mask(values, -9999.0)
    assert result["center_64x64_usable_pixels"] == 64 * 64
    assert result["classification"] == "VALID_SUPPORT_REACHES_CENTER"


def test_block_grid_preserves_exact_16_by_16_counts():
    values = np.full((WINDOW_SIZE, WINDOW_SIZE), -9999.0, dtype=np.float32)
    values[:BLOCK_SIZE, :BLOCK_SIZE] = 1.0
    result = summarize_mask(values, -9999.0)
    assert len(result["block_valid_pixel_counts"]) == 8
    assert len(result["block_valid_pixel_counts"][0]) == 8
    assert result["block_valid_pixel_counts"][0][0] == 256
    assert sum(map(sum, result["block_valid_pixel_counts"])) == 256


def test_nonfinite_values_are_not_counted_as_valid():
    values = np.ones((WINDOW_SIZE, WINDOW_SIZE), dtype=np.float32)
    values[:8, :8] = np.nan
    result = summarize_mask(values, None)
    assert result["nonfinite_pixels"] == 64
    assert result["usable_pixels"] == WINDOW_SIZE * WINDOW_SIZE - 64


def test_invalid_shape_and_block_size_fail_closed():
    with pytest.raises(ValueError, match="128x128"):
        summarize_mask(np.zeros((64, 64)), None)
    with pytest.raises(ValueError, match="divide"):
        summarize_mask(np.zeros((128, 128)), None, block_size=15)
