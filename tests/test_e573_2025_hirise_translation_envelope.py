import math

import numpy as np
import pyproj
import pytest

from experiments.e573_2025_hirise_translation_envelope import (
    INNER_RADIUS_M,
    OUTER_RADIUS_M,
    MAX_2020_RANGE_BYTES,
    OFFSETS_M,
    offset_key,
    summarize_tabs,
    sample_2025_at_offset,
    MOLA_RADIUS_FALLBACK_M,
)


def test_2020_range_budget_is_explicitly_bounded():
    assert MAX_2020_RANGE_BYTES == 32 * 1024 * 1024


def test_translation_grid_is_unique_and_within_published_radial_envelope():
    assert len(OFFSETS_M) == 13
    assert len(set(OFFSETS_M)) == 13
    assert (0.0, 0.0) in OFFSETS_M
    assert all(math.hypot(dx, dy) <= OUTER_RADIUS_M + 1e-9 for dx, dy in OFFSETS_M)
    assert (INNER_RADIUS_M, 0.0) in OFFSETS_M
    assert (OUTER_RADIUS_M, 0.0) in OFFSETS_M
    diagonal = OUTER_RADIUS_M / math.sqrt(2)
    assert any(math.isclose(dx, diagonal, abs_tol=1e-8) and math.isclose(dy, diagonal, abs_tol=1e-8) for dx, dy in OFFSETS_M)


def test_offset_keys_are_stable_and_collision_free():
    keys = [offset_key(dx, dy) for dx, dy in OFFSETS_M]
    assert len(keys) == len(set(keys))
    assert offset_key(0.0, 0.0) == "dx_p0_000000_dy_p0_000000_m"


def test_summary_reports_worst_case_margin_without_inferential_language():
    tabs = {
        "zero": {"2020_valid": 164, "2025_valid": 259, "net_valid_support_change_2025_minus_2020": 95},
        "shift_a": {"2020_valid": 160, "2025_valid": 250, "net_valid_support_change_2025_minus_2020": 90},
        "shift_b": {"2020_valid": 166, "2025_valid": 165, "net_valid_support_change_2025_minus_2020": -1},
    }
    result = summarize_tabs(tabs)
    assert result["offset_count"] == 3
    assert result["min_2020_valid"] == 160
    assert result["max_2020_valid"] == 166
    assert result["min_2025_valid"] == 165
    assert result["max_2025_valid"] == 259
    assert result["min_2025_minus_2020"] == -1
    assert result["max_2025_minus_2020"] == 95
    assert result["2025_support_advantage_at_every_tested_offset"] is False


def test_summary_rejects_empty_input():
    with pytest.raises(ValueError, match="at least one"):
        summarize_tabs({})

class _SinglePixelDataset:
    driver = "GTiff"
    count = 1
    width = 1
    height = 1
    crs = pyproj.CRS.from_proj4(
        f"+proj=longlat +a={MOLA_RADIUS_FALLBACK_M} +b={MOLA_RADIUS_FALLBACK_M} +no_defs +type=crs"
    )

    def index(self, x, y):
        return 0, 0

    def read(self, *args, **kwargs):
        return np.ma.array([[42.0]], mask=False)


def test_2025_masks_are_flattened_to_the_same_observed_point_order_as_2020():
    observed = np.asarray([[True, False], [False, True]])
    lat = np.zeros((2, 2), dtype=float)
    lon = np.zeros((2, 2), dtype=float)

    inside, valid = sample_2025_at_offset(
        _SinglePixelDataset(), lat, lon, observed, 0.0, 0.0
    )

    assert inside.shape == (int(observed.sum()),)
    assert valid.shape == (int(observed.sum()),)
    assert inside.tolist() == [True, True]
    assert valid.tolist() == [True, True]

