import hashlib

import numpy as np
import pytest

from experiments.e557_copernicus_glo30_lonar_sample import (
    BUCKET_HOST,
    HEADER_RANGE_BYTES,
    tile_stem,
    tile_url,
    validate_tile_url,
    parse_content_range,
    summarize_window,
    E557Error,
)


def test_lonar_coordinates_map_to_expected_public_tile():
    stem = "Copernicus_DSM_COG_10_N19_00_E076_00_DEM"
    assert tile_stem(19.975, 76.509) == stem
    assert tile_url(19.975, 76.509) == (
        f"https://{BUCKET_HOST}/{stem}/{stem}.tif"
    )


def test_tile_stem_uses_floor_for_southern_and_western_coordinates():
    assert tile_stem(-12.4, -45.2) == "Copernicus_DSM_COG_10_S13_00_W046_00_DEM"


def test_tile_url_allowlist_rejects_other_hosts_and_queries():
    stem = tile_stem(19.975, 76.509)
    url = tile_url(19.975, 76.509)
    assert validate_tile_url(url, stem) == url
    with pytest.raises(E557Error) as caught:
        validate_tile_url(url.replace(BUCKET_HOST, "example.com"), stem)
    assert caught.value.outcome == "URL_OUTSIDE_ALLOWLIST"
    with pytest.raises(E557Error):
        validate_tile_url(url + "?signed=true", stem)


def test_content_range_requires_exact_nonnegative_bounds():
    assert parse_content_range("bytes 0-16383/1000000") == (0, 16383, 1000000)
    with pytest.raises(E557Error):
        parse_content_range("bytes 0-16384/16384")
    with pytest.raises(E557Error):
        parse_content_range("bytes 2-1/100")


def test_summary_reports_descriptive_metrics_and_masked_count():
    values = np.fromfunction(lambda r, c: 100.0 + r + 2.0 * c, (17, 17), dtype=float)
    masked = np.ma.array(values, mask=np.zeros((17, 17), dtype=bool))
    masked.mask[0, 0] = True
    result = summarize_window(masked, 19.975, (29.0, 31.0))
    assert result["valid_samples"] == 288
    assert result["masked_or_nonfinite_samples"] == 1
    assert result["elevation_min_m"] == pytest.approx(102.0)
    assert result["elevation_max_m"] == pytest.approx(148.0)
    assert result["local_relief_m"] == pytest.approx(46.0)
    assert result["central_slope_deg"] is not None
    assert result["raw_window_retained"] is False


def test_summary_fails_closed_on_all_masked_window():
    values = np.ma.masked_all((17, 17), dtype=float)
    result = summarize_window(values, 19.975, (29.0, 31.0))
    assert result["valid_samples"] == 0
    assert result["outcome"] == "NO_VALID_SAMPLES"


def test_header_range_constant_is_small_and_deterministic():
    assert HEADER_RANGE_BYTES == 16_384
    assert len(hashlib.sha256(b"fixture").hexdigest()) == 64
