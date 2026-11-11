from __future__ import annotations

import hashlib
import io
import zipfile

import numpy as np
import pyproj
import rasterio
import pytest
from rasterio.io import MemoryFile
from rasterio.transform import from_origin, rowcol

from experiments.e568_2025_hirise_dtm_observed_point_support import (
    MOLA_RADIUS_FALLBACK_M,
    sample_raster,
    build_support_cross_tab,
    stream_member,
)


def test_stream_member_checks_size_and_emits_only_a_compact_receipt(tmp_path):
    payload = b"bounded-fixture-" * 1000
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mosaic/test_DTM.tif", payload)
    with zipfile.ZipFile(io.BytesIO(buffer.getvalue()), "r") as archive:
        info = archive.infolist()[0]
        destination = tmp_path / "test.tif"
        receipt = stream_member(
            archive,
            info,
            destination,
            expected_compressed=info.compress_size,
            expected_uncompressed=info.file_size,
        )
    assert destination.read_bytes() == payload
    assert receipt["uncompressed_sha256"] == hashlib.sha256(payload).hexdigest()
    assert receipt["uncompressed_bytes"] == len(payload)
    assert receipt["temporary_file_deleted_after_sampling"] is True


def test_stream_member_rejects_changed_size(tmp_path):
    payload = b"not the pinned product"
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("mosaic/test_DTM.tif", payload)
    with zipfile.ZipFile(io.BytesIO(buffer.getvalue()), "r") as archive:
        info = archive.infolist()[0]
        with pytest.raises(ValueError, match="compressed size changed"):
            stream_member(
                archive,
                info,
                tmp_path / "test.tif",
                expected_compressed=info.compress_size + 1,
                expected_uncompressed=info.file_size,
            )


def test_raster_sampler_preserves_observed_inside_and_valid_denominators():
    crs = pyproj.CRS.from_proj4(
        "+proj=longlat +a=" + str(MOLA_RADIUS_FALLBACK_M)
        + " +b=" + str(MOLA_RADIUS_FALLBACK_M)
        + " +no_defs +type=crs"
    )
    transform = from_origin(77.15, 18.6, 0.01, 0.01)
    data = np.arange(40 * 40, dtype=np.int16).reshape((40, 40))
    nodata_row, nodata_col = rowcol(transform, 77.2, 18.4)
    data[nodata_row, nodata_col] = -32768
    with MemoryFile() as memory_file:
        with memory_file.open(
            driver="GTiff",
            width=40,
            height=40,
            count=1,
            dtype="int16",
            crs=crs,
            transform=transform,
            nodata=-32768,
        ) as dataset:
            dataset.write(data, 1)
            dataset.scales = (0.1,)
            dataset.offsets = (100.0,)
            lat = np.asarray([[18.4, 18.4, 18.4], [18.4, 18.4, 18.4]])
            lon = np.asarray([[77.2, 77.3, 77.4], [77.5, 77.6, 77.7]])
            observed = np.ones((2, 3), dtype=bool)
            result = sample_raster(dataset, lat, lon, observed)

    summary = result["summary"]
    assert summary["observed_mola_point_centers"] == 6
    assert summary["inside_raster_bounds"] == 4
    assert summary["valid_unmasked_samples"] == 3
    assert summary["valid_fraction_of_observed"] == 0.5
    assert result["_valid_mask"] == [False, True, True, True, False, False]
    assert summary["scaled_sample_min"] is not None
    assert result["metadata"]["scale"] == 0.1
    assert result["metadata"]["offset"] == 100.0


def test_cross_tab_separates_outside_points_from_in_bounds_nodata():
    dtm = {
        "_inside_mask": [True, True, True, False, False],
        "_valid_mask": [True, False, False, False, False],
    }
    confidence = {
        "_inside_mask": [True, True, False, False, True],
        "_valid_mask": [True, False, False, False, True],
    }
    result = build_support_cross_tab(dtm, confidence)

    assert result["observed_mola_point_centers"] == 5
    assert result["both_inside_bounds"] == 2
    assert result["both_outside_bounds"] == 1
    assert result["dtm_inside_confidence_outside"] == 1
    assert result["confidence_inside_dtm_outside"] == 1
    assert result["both_valid_within_both_bounds"] == 1
    assert result["both_nodata_within_both_bounds"] == 1
    assert result["confidence_valid_but_dtm_invalid_within_both_bounds"] == 0
    assert result["dtm_valid_but_confidence_invalid_within_both_bounds"] == 0
    assert result["validity_masks_identical_at_observed_points"] is False
    assert result["validity_masks_identical_within_both_bounds"] is True


def test_cross_tab_rejects_valid_samples_outside_raster_bounds():
    dtm = {"_inside_mask": [False], "_valid_mask": [True]}
    confidence = {"_inside_mask": [False], "_valid_mask": [False]}
    with pytest.raises(ValueError, match="out-of-bounds point"):
        build_support_cross_tab(dtm, confidence)
