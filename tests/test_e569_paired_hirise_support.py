from __future__ import annotations

import numpy as np
import pytest

from experiments.e569_paired_hirise_support import (
    TRANSLATION_OFFSETS_M,
    build_paired_cross_tab,
    build_row_range_plan,
    point_indices,
    valid_sample,
)


def test_paired_cross_tab_reports_gains_losses_and_footprint_separately():
    result = build_paired_cross_tab(
        old_inside=[1, 1, 0, 1, 0, 1],
        old_valid=[1, 0, 0, 1, 0, 0],
        new_inside=[1, 1, 1, 1, 1, 0],
        new_valid=[1, 1, 0, 0, 1, 0],
    )

    assert result["observed_points"] == 6
    assert result["both_inside_bounds"] == 3
    assert result["2020_only_footprint"] == 1
    assert result["2025_only_footprint"] == 2
    assert result["both_outside_bounds"] == 1
    assert result["both_valid"] == 1
    assert result["2020_valid_only"] == 1
    assert result["2025_valid_only"] == 2
    assert result["both_invalid"] == 2
    assert result["net_valid_support_change_2025_minus_2020"] == 1
    assert result["paired_gain_minus_loss"] == 1
    assert result["validity_jaccard"] == pytest.approx(1 / 4)


def test_paired_cross_tab_rejects_valid_samples_outside_own_raster():
    with pytest.raises(ValueError, match="out-of-bounds"):
        build_paired_cross_tab(
            old_inside=[False],
            old_valid=[True],
            new_inside=[True],
            new_valid=[False],
        )


def test_paired_cross_tab_handles_empty_valid_union():
    result = build_paired_cross_tab(
        old_inside=[True, False],
        old_valid=[False, False],
        new_inside=[True, False],
        new_valid=[False, False],
    )
    assert result["validity_jaccard"] is None
    assert result["both_nodata_within_shared_footprint"] == 1


def test_row_range_plan_coalesces_columns_for_each_strip():
    plan = build_row_range_plan([
        (
            np.asarray([4, 4, 7, 9]),
            np.asarray([8, 3, 5, 100]),
            np.asarray([True, True, True, False]),
        ),
        (
            np.asarray([4, 7]),
            np.asarray([12, 2]),
            np.asarray([True, True]),
        ),
    ])
    assert plan == {4: (3, 12), 7: (2, 5)}


def test_row_range_plan_ignores_out_of_bounds_points():
    plan = build_row_range_plan([
        (
            np.asarray([-1, 4]),
            np.asarray([3, 5]),
            np.asarray([False, True]),
        )
    ])
    assert plan == {4: (5, 5)}


def test_translation_grid_is_fixed_and_contains_zero():
    assert len(TRANSLATION_OFFSETS_M) == 9
    assert len(set(TRANSLATION_OFFSETS_M)) == 9
    assert (0.0, 0.0) in TRANSLATION_OFFSETS_M
    assert set(TRANSLATION_OFFSETS_M) == {
        (x, y) for x in (-6.0, 0.0, 6.0) for y in (-6.0, 0.0, 6.0)
    }


def test_point_indices_preserve_half_open_raster_bounds():
    rows, cols, inside = point_indices(
        np.asarray([0.5, 9.5, 10.0, -0.1]),
        np.asarray([9.5, 0.5, 0.5, 9.5]),
        xmin=0.0,
        ymax=10.0,
        pixel_width=1.0,
        pixel_height=1.0,
        width=10,
        height=10,
    )
    assert rows.tolist() == [0, 9, 9, 0]
    assert cols.tolist() == [0, 9, 10, -1]
    assert inside.tolist() == [True, True, False, False]


def test_nodata_and_nonfinite_values_are_not_valid():
    assert valid_sample(12.0, -9999.0)
    assert not valid_sample(-9999.0, -9999.0)
    assert not valid_sample(float("nan"), -9999.0)
    assert not valid_sample(float("inf"), None)
