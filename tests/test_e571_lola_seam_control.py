from __future__ import annotations

import pytest

from experiments.e570_lola_gdr_sample import latitude_band_diagnostic
from experiments.e571_lola_seam_control import CENTERS, compare_windows, overlap_rows


def _window(identifier, rows, relief, mad, median_slope, p90_slope):
    return {
        "id": identifier,
        "window_rows_zero_based": rows,
        "descriptor": {
            "radial_height_relief_p95_p05_m": relief,
            "radial_height_mad_m": mad,
            "median_local_slope_deg": median_slope,
            "p90_local_slope_deg": p90_slope,
        },
    }


def test_three_centers_share_longitude_and_straddle_documented_seam():
    assert {center["longitude_deg_east"] for center in CENTERS} == {90.0}
    assert [center["latitude_deg"] for center in CENTERS] == [-45.0, -44.5, -45.5]
    assert latitude_band_diagnostic(-45.0)["crosses_documented_45_degree_band_boundary"]
    assert not latitude_band_diagnostic(-44.5)["crosses_documented_45_degree_band_boundary"]
    assert not latitude_band_diagnostic(-45.5)["crosses_documented_45_degree_band_boundary"]


def test_adjacent_windows_overlap_by_three_rows_and_not_independent():
    seam = _window("seam_baseline", [2155, 2165], 100, 10, 2, 4)
    north = _window("north_control", [2147, 2157], 20, 2, 1, 2)
    south = _window("south_control", [2163, 2173], 30, 3, 1.5, 3)
    assert overlap_rows(seam, north) == 3
    assert overlap_rows(seam, south) == 3


def test_comparison_reports_effect_sizes_without_claiming_causation():
    windows = [
        _window("seam_baseline", [2155, 2165], 100, 10, 2, 4),
        _window("north_control", [2147, 2157], 20, 2, 1, 2),
        _window("south_control", [2163, 2173], 30, 3, 1.5, 3),
    ]
    result = compare_windows(windows)
    relief = result["metrics"]["radial_height_relief_p95_p05_m"]
    assert relief["control_mean"] == pytest.approx(25)
    assert relief["seam_minus_control_mean"] == pytest.approx(75)
    assert relief["seam_to_control_mean_ratio"] == pytest.approx(4)
    assert relief["seam_exceeds_both_controls"] is True
    assert result["north_seam_shared_rows"] == 3
    assert result["south_seam_shared_rows"] == 3


def test_comparison_handles_missing_slope_descriptor_without_imputation():
    windows = [
        _window("seam_baseline", [2155, 2165], 100, 10, None, 4),
        _window("north_control", [2147, 2157], 20, 2, 1, 2),
        _window("south_control", [2163, 2173], 30, 3, 1.5, 3),
    ]
    result = compare_windows(windows)
    assert result["metrics"]["median_local_slope_deg"]["comparison"] == "NOT_COMPUTABLE"
    assert result["metrics"]["median_local_slope_deg"]["seam"] is None


def test_comparison_rejects_missing_or_extra_window_ids():
    with pytest.raises(ValueError, match="expected exactly"):
        compare_windows([_window("seam_baseline", [1, 11], 1, 1, 1, 1)])


def test_seam_reference_is_rounded_and_not_independent_evidence():
    windows = [
        _window("seam_baseline", [2155, 2165], 1662.64, 10, 2, 4),
        _window("north_control", [2147, 2157], 20, 2, 1, 2),
        _window("south_control", [2163, 2173], 30, 3, 1.5, 3),
    ]
    check = compare_windows(windows)["e570_reacquisition_check"]
    assert check["absolute_difference_from_rounded_e570_report_m"] == pytest.approx(0)
    assert "not an independent sample" in check["comparison_note"]
