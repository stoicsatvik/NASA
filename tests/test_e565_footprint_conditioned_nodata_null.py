"""E565: condition HiRISE nodata clustering reference on the raster footprint."""

import numpy as np

from experiments.e563_three_way_common_support import summarize_support_spatial_clustering


def _footprint_fixture():
    observed = np.ones((3, 3), dtype=bool)
    ctx_valid = np.ones((3, 3), dtype=bool)
    hirise_inside = np.ones((3, 3), dtype=bool)
    hirise_inside[0, 0] = False
    hirise_inside[0, 1] = False
    hirise_inside[2, 2] = False
    hirise_valid = hirise_inside.copy()
    hirise_valid[1, 1] = False
    hirise_valid[1, 2] = False
    return observed, ctx_valid, hirise_inside, hirise_valid


def test_nodata_reference_conditions_on_fixed_hirise_footprint():
    result = summarize_support_spatial_clustering(
        *_footprint_fixture(),
        permutations=9_999,
        seed=20261112,
    )
    nodata = result["categories"]["hirise_inside_nodata"]
    reference = nodata["footprint_conditioned_reference"]

    assert nodata["count"] == 2
    assert nodata["same_category_cardinal_adjacency_edges"] == 1
    assert reference["eligible_in_bounds_observed_bins"] == 6
    assert reference["in_bounds_cardinal_adjacency_edges"] == 6
    assert reference["same_category_cardinal_adjacency_edges"] == 1
    assert reference["reference_permutations"] == 9_999
    # Six possible adjacent pairs among C(6, 2) equally likely pairs.
    assert abs(reference["reference_mean_adjacency_edges"] - 0.4) < 0.02
    assert reference["reference_95th_percentile_adjacency_edges"] == 1
    assert 0.35 < reference["reference_upper_tail_fraction"] < 0.45
    assert "not an inferential p-value" in reference["reference_interpretation"]


def test_footprint_conditioned_reference_is_deterministic():
    first = summarize_support_spatial_clustering(
        *_footprint_fixture(), permutations=999, seed=17
    )
    second = summarize_support_spatial_clustering(
        *_footprint_fixture(), permutations=999, seed=17
    )
    assert (
        first["categories"]["hirise_inside_nodata"]["footprint_conditioned_reference"]
        == second["categories"]["hirise_inside_nodata"]["footprint_conditioned_reference"]
    )
    assert first["raw_pixels_retained"] is False
    assert first["point_coordinates_retained"] is False
