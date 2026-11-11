from __future__ import annotations

import numpy as np
import pyproj
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin, rowcol

from experiments.e567_fom_confidence_point_support import (
    MOLA_RADIUS_FALLBACK_M,
    sample_confidence,
    summarize_values,
)


def test_value_summary_keeps_observed_and_valid_denominators_separate():
    summary = summarize_values([2.0, 2.0, 5.0], inside_count=4, observed_count=6)
    assert summary["observed_mola_point_centers"] == 6
    assert summary["inside_confidence_raster_bounds"] == 4
    assert summary["valid_unmasked_confidence_samples"] == 3
    assert summary["inside_fraction_of_observed"] == 4 / 6
    assert summary["valid_fraction_of_observed"] == 3 / 6
    assert summary["valid_fraction_of_inside"] == 3 / 4
    assert summary["values_are_interpreted_as_calibrated_uncertainty"] is False


def test_confidence_sampler_excludes_nodata_and_out_of_bounds_points():
    crs = pyproj.CRS.from_proj4(
        "+proj=longlat +a=" + str(MOLA_RADIUS_FALLBACK_M)
        + " +b=" + str(MOLA_RADIUS_FALLBACK_M)
        + " +no_defs +type=crs"
    )
    data = np.arange(40 * 40, dtype=np.uint16).reshape((40, 40))
    transform = from_origin(77.15, 18.6, 0.01, 0.01)
    nodata_row, nodata_col = rowcol(transform, 77.2, 18.4)
    data[nodata_row, nodata_col] = 65535
    with MemoryFile() as memory_file:
        with memory_file.open(
            driver="GTiff",
            width=40,
            height=40,
            count=1,
            dtype="uint16",
            crs=crs,
            transform=transform,
            nodata=65535,
        ) as dataset:
            dataset.write(data, 1)
            lat = np.asarray([[18.4, 18.4, 18.4], [18.4, 18.4, 18.4]])
            lon = np.asarray([[77.2, 77.3, 77.4], [77.5, 77.6, 77.7]])
            observed = np.ones((2, 3), dtype=bool)
            summary = sample_confidence(dataset, lat, lon, observed)

    samples = summary["sample_summary"]
    assert samples["observed_mola_point_centers"] == 6
    assert samples["inside_confidence_raster_bounds"] == 4
    assert samples["valid_unmasked_confidence_samples"] == 3
    assert samples["valid_fraction_of_observed"] == 0.5
    assert summary["raw_pixel_values_retained"] is False
    assert summary["point_coordinates_retained"] is False


def test_empty_sample_summary_does_not_invent_values():
    summary = summarize_values([], inside_count=0, observed_count=5)
    assert summary["valid_unmasked_confidence_samples"] == 0
    assert summary["sample_min"] is None
    assert summary["sample_median"] is None
    assert summary["sample_max"] is None
