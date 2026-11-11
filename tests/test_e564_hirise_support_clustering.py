import numpy as np
import pytest

from experiments.e563_three_way_common_support import summarize_support_spatial_clustering


def _fixture():
    observed = np.ones((3, 3), dtype=bool)
    ctx_valid = np.ones((3, 3), dtype=bool)
    hirise_inside = np.ones((3, 3), dtype=bool)
    hirise_inside[0, 0] = False
    hirise_inside[0, 1] = False
    hirise_inside[2, 2] = False
    hirise_valid = hirise_inside.copy()
    hirise_valid[1, 1] = False
    return observed, ctx_valid, hirise_inside, hirise_valid


def test_outside_and_inside_nodata_are_separate_four_connected_classes():
    result = summarize_support_spatial_clustering(*_fixture(), permutations=199, seed=7)
    outside = result["categories"]["hirise_outside_bounds"]
    nodata = result["categories"]["hirise_inside_nodata"]

    assert result["observed_mola_nodes"] == 9
    assert result["cardinal_adjacency_edges_among_observed_bins"] == 12
    assert outside["count"] == 3
    assert outside["four_connected_component_sizes_desc"] == [2, 1]
    assert outside["same_category_cardinal_adjacency_edges"] == 1
    assert nodata["count"] == 1
    assert nodata["four_connected_component_sizes_desc"] == [1]
    assert nodata["same_category_cardinal_adjacency_edges"] == 0


def test_fixed_count_reference_is_deterministic_and_preserves_category_counts():
    first = summarize_support_spatial_clustering(*_fixture(), permutations=499, seed=20261112)
    second = summarize_support_spatial_clustering(*_fixture(), permutations=499, seed=20261112)

    assert first == second
    for category in first["categories"].values():
        assert category["reference_permutations"] in (0, 499)
        value = category["reference_upper_tail_fraction"]
        assert value is None or 0 <= value <= 1
    assert "coordinates" not in str(first["categories"]).lower()
    assert first["raw_pixels_retained"] is False
    assert first["point_coordinates_retained"] is False


def test_empty_category_does_not_claim_a_randomization_result():
    observed = np.ones((2, 2), dtype=bool)
    result = summarize_support_spatial_clustering(
        observed, observed, observed, observed, permutations=99
    )
    outside = result["categories"]["hirise_outside_bounds"]
    assert outside["count"] == 0
    assert outside["reference_permutations"] == 0
    assert outside["reference_upper_tail_fraction"] is None


def test_valid_hirise_points_outside_bounds_are_rejected():
    observed = np.ones((2, 2), dtype=bool)
    inside = observed.copy()
    inside[0, 0] = False
    with pytest.raises(ValueError, match="cannot be outside"):
        summarize_support_spatial_clustering(observed, observed, inside, observed, permutations=99)


def test_mask_shape_mismatch_and_zero_observed_bins_fail_closed():
    observed, ctx_valid, inside, valid = _fixture()
    with pytest.raises(ValueError, match="identical shapes"):
        summarize_support_spatial_clustering(observed, ctx_valid[:, :2], inside, valid, permutations=99)
    empty = np.zeros((2, 2), dtype=bool)
    full = np.ones((2, 2), dtype=bool)
    with pytest.raises(ValueError, match="no MOLA observed-shot bins"):
        summarize_support_spatial_clustering(empty, full, full, full, permutations=99)
