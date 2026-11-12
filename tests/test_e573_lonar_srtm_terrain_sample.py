import numpy as np
import pytest

from experiments.e573_lonar_srtm_terrain_sample import (
    SITES,
    WINDOW_SIZE,
    terrain_descriptors,
)


def make_crater_window(pixel_x_m=30.0, pixel_y_m=30.0):
    rows, cols = np.indices((WINDOW_SIZE, WINDOW_SIZE))
    center = (WINDOW_SIZE - 1) / 2
    radius = np.sqrt(
        ((cols - center) * pixel_x_m) ** 2
        + ((rows - center) * pixel_y_m) ** 2
    )
    elevation = np.full((WINDOW_SIZE, WINDOW_SIZE), 500.0)
    elevation[radius <= 250] = 400.0
    elevation[(radius >= 700) & (radius <= 1050)] = 530.0
    return elevation


def test_lonar_crater_window_has_positive_rim_minus_center_contrast():
    elevation = make_crater_window()
    result = terrain_descriptors(
        elevation,
        np.ones_like(elevation, dtype=bool),
        30.0,
        30.0,
    )
    assert result["rim_minus_center_m"] == pytest.approx(130.0)
    assert result["relief_p95_minus_p05_m"] > 0
    assert result["valid_fraction"] == 1.0


def test_flat_control_window_has_zero_relief_and_zero_slope():
    elevation = np.full((WINDOW_SIZE, WINDOW_SIZE), 500.0)
    result = terrain_descriptors(
        elevation,
        np.ones_like(elevation, dtype=bool),
        30.0,
        30.0,
    )
    assert result["relief_p95_minus_p05_m"] == pytest.approx(0.0)
    assert result["slope_median_deg"] == pytest.approx(0.0)
    assert result["slope_p90_deg"] == pytest.approx(0.0)
    assert result["rim_minus_center_m"] == pytest.approx(0.0)


def test_nodata_is_excluded_from_elevation_and_slope_statistics():
    elevation = make_crater_window()
    valid = np.ones_like(elevation, dtype=bool)
    valid[:20, :20] = False
    result = terrain_descriptors(elevation, valid, 30.0, 30.0)
    assert result["valid_fraction"] == pytest.approx(1 - 400 / elevation.size)
    assert result["valid_pixel_count"] == elevation.size - 400
    assert np.isfinite(result["elevation_median_m"])
    assert np.isfinite(result["slope_p90_deg"])


def test_invalid_array_shapes_are_rejected():
    with pytest.raises(ValueError, match="matching 2-D arrays"):
        terrain_descriptors(
            np.zeros((10, 10)),
            np.ones((9, 10), dtype=bool),
            30.0,
            30.0,
        )


def test_nonpositive_pixel_size_is_rejected():
    with pytest.raises(ValueError, match="finite and positive"):
        terrain_descriptors(
            np.zeros((WINDOW_SIZE, WINDOW_SIZE)),
            np.ones((WINDOW_SIZE, WINDOW_SIZE), dtype=bool),
            0.0,
            30.0,
        )


def test_site_roles_do_not_claim_verified_negative_controls():
    assert SITES["lonar_candidate"]["label_state"] == "candidate_site; not a recovered analogue"
    assert "not a verified non-analogue" in SITES["regional_control_west"]["label_state"]
    assert "not a verified non-analogue" in SITES["regional_control_east"]["label_state"]
