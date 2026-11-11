import numpy as np
import pytest
import rasterio
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from experiments.e544_ctx_raster_ingestion import (
    AcquisitionError,
    SOURCE_URL,
    fetch_raster_bytes,
    inspect_raster,
    is_tiff,
    validate_source_url,
)


class FakeResponse:
    def __init__(self, payload, content_type="image/tiff", status=200, url=SOURCE_URL):
        self.payload = payload
        self.status = status
        self.headers = {
            "Content-Type": content_type,
            "Content-Length": str(len(payload)),
        }
        self.url = url

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def getcode(self):
        return self.status

    def read(self, limit=-1):
        return self.payload if limit < 0 else self.payload[:limit]


def synthetic_geotiff():
    values = np.arange(128 * 128, dtype=np.float32).reshape(128, 128)
    values[:64, :64] = -9999.0
    with MemoryFile() as memory_file:
        with memory_file.open(
            driver="GTiff",
            width=128,
            height=128,
            count=1,
            dtype="float32",
            crs="EPSG:4326",
            transform=from_origin(77.0, 18.0, 0.0001, 0.0001),
            nodata=-9999.0,
        ) as dataset:
            dataset.write(values, 1)
            dataset.update_tags(AREA_OR_POINT="Point")
        return memory_file.read()


def test_source_url_is_pinned_to_exact_public_usgs_product():
    validate_source_url(SOURCE_URL)
    with pytest.raises(ValueError):
        validate_source_url("https://example.com/data.tif")
    with pytest.raises(ValueError):
        validate_source_url(SOURCE_URL + "?download=1")


@pytest.mark.parametrize("magic", [b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"])
def test_tiff_magic_accepts_classic_and_bigtiff(magic):
    assert is_tiff(magic + b"payload")


def test_tiff_magic_rejects_html_and_zip():
    assert not is_tiff(b"<!DOCTYPE html>")
    assert not is_tiff(b"PK\\x03\\x04")


def test_fetch_records_transport_without_exposing_payload():
    payload = synthetic_geotiff()

    def opener(request, timeout):
        assert request.full_url == SOURCE_URL
        assert timeout == 90
        return FakeResponse(payload)

    data, receipt = fetch_raster_bytes(opener=opener)
    assert data == payload
    assert receipt["http_status"] == 200
    assert receipt["bytes"] == len(payload)
    assert receipt["content_type"] == "image/tiff"


def test_fetch_classifies_html_preview_as_negative_not_as_raster():
    payload = b"<!DOCTYPE html><html>preview</html>"

    def opener(request, timeout):
        return FakeResponse(payload, content_type="text/html")

    with pytest.raises(AcquisitionError) as caught:
        fetch_raster_bytes(opener=opener)
    assert caught.value.kind == "NON_TIFF_RESPONSE"
    assert caught.value.result_class == "NEGATIVE_RESULT"


def test_geotiff_inspection_reports_crs_nodata_and_bounded_valid_samples():
    receipt = inspect_raster(synthetic_geotiff())
    assert receipt["driver"] == "GTiff"
    assert receipt["width"] == 128
    assert receipt["height"] == 128
    assert receipt["crs"] == "EPSG:4326"
    assert receipt["nodata_band_1"] == -9999.0
    assert receipt["sample_valid_pixels"] > 0
    assert len(receipt["sample_windows"]) == 5
    assert receipt["raw_pixels_retained"] is False


def test_geotiff_inspection_rejects_non_tiff_bytes():
    with pytest.raises(AcquisitionError) as caught:
        inspect_raster(b"not a TIFF")
    assert caught.value.kind == "NON_TIFF_BYTES"
