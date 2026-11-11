"""E544: bounded acquisition and metadata/sample audit of the official Jezero CTX TRN DTM."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

SOURCE_URL = (
    "https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/"
    "JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif"
)
SOURCE_PAGE = "https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_ctx_dtm_mosaic"
SOURCE_DOI = "10.5066/P906QQT8"
ALLOWED_HOST = "planetarymaps.usgs.gov"
ALLOWED_PATH = (
    "/mosaic/mars2020_trn/CTX/"
    "JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif"
)
MAX_BYTES = 20_000_000
SAMPLE_SIZE = 64
TIFF_MAGICS = (b"II*\\x00", b"MM\\x00*", b"II+\\x00", b"MM\\x00+")


class AcquisitionError(RuntimeError):
    def __init__(self, kind: str, message: str, *, result_class: str = "ERROR", details: dict | None = None):
        super().__init__(message)
        self.kind = kind
        self.result_class = result_class
        self.details = details or {}


def validate_source_url(url: str, *, exact_path: bool = True) -> None:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname != ALLOWED_HOST or parsed.port not in (None, 443):
        raise ValueError("source URL is outside the pinned HTTPS USGS host")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("source URL contains credentials, query parameters or a fragment")
    if exact_path and parsed.path != ALLOWED_PATH:
        raise ValueError("source URL path does not match the pinned CTX product")


def is_tiff(data: bytes) -> bool:
    return any(data.startswith(magic) for magic in TIFF_MAGICS)


def fetch_raster_bytes(url: str = SOURCE_URL, opener=urlopen) -> tuple[bytes, dict]:
    validate_source_url(url)
    request = Request(
        url,
        headers={
            "User-Agent": "Unified-Parallel-Foundry-E544/1.0",
            "Accept": "image/tiff,application/octet-stream;q=0.9,*/*;q=0.1",
        },
    )
    try:
        response = opener(request, timeout=90)
    except HTTPError as exc:
        result_class = "NEGATIVE_RESULT" if exc.code in (403, 404, 410) else "ERROR"
        raise AcquisitionError(
            f"HTTP_{exc.code}",
            "Pinned public CTX source returned an HTTP error",
            result_class=result_class,
            details={"http_status": int(exc.code)},
        ) from exc
    except URLError as exc:
        raise AcquisitionError(
            "NETWORK_ERROR",
            "Pinned public CTX source could not be reached",
            details={"reason_type": type(exc.reason).__name__},
        ) from exc

    with response:
        status = getattr(response, "status", None)
        if status is None:
            status = response.getcode()
        final_url = response.geturl()
        try:
            validate_source_url(final_url, exact_path=False)
        except ValueError as exc:
            raise AcquisitionError(
                "REDIRECT_OUTSIDE_ALLOWLIST",
                "The official URL redirected outside the pinned USGS host",
                result_class="NEGATIVE_RESULT",
                details={"final_host": urlsplit(final_url).hostname},
            ) from exc

        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        content_length_raw = response.headers.get("Content-Length")
        content_length = int(content_length_raw) if content_length_raw and content_length_raw.isdigit() else None
        data = response.read(MAX_BYTES + 1)

    if status != 200:
        raise AcquisitionError(
            "UNEXPECTED_HTTP_STATUS",
            "Pinned CTX source did not return a complete HTTP 200 response",
            result_class="NEGATIVE_RESULT" if status in (403, 404, 410) else "ERROR",
            details={"http_status": int(status), "content_type": content_type},
        )
    if len(data) > MAX_BYTES:
        raise AcquisitionError(
            "RESPONSE_TOO_LARGE",
            "Response exceeded the bounded 20 MB acquisition limit",
            details={"bytes_read": len(data), "max_bytes": MAX_BYTES},
        )
    if content_length is not None and content_length != len(data):
        raise AcquisitionError(
            "CONTENT_LENGTH_MISMATCH",
            "Received byte count differs from the HTTP Content-Length",
            details={"content_length": content_length, "bytes_read": len(data)},
        )
    if not is_tiff(data):
        raise AcquisitionError(
            "NON_TIFF_RESPONSE",
            "The pinned USGS endpoint did not return TIFF bytes",
            result_class="NEGATIVE_RESULT",
            details={
                "http_status": int(status),
                "content_type": content_type,
                "bytes_read": len(data),
                "prefix_hex": data[:16].hex(),
            },
        )
    return data, {
        "http_status": int(status),
        "content_type": content_type,
        "content_length": content_length,
        "bytes": len(data),
        "final_host": urlsplit(final_url).hostname,
    }


def _window_stats(dataset, label: str, col: int, row: int, size: int) -> dict:
    import numpy as np
    from rasterio.windows import Window

    width = min(size, dataset.width - col)
    height = min(size, dataset.height - row)
    window = Window(col, row, width, height)
    values = dataset.read(1, window=window)
    valid_mask = dataset.read_masks(1, window=window) > 0
    valid_mask &= np.isfinite(values)
    if dataset.nodata is not None:
        valid_mask &= values != dataset.nodata
    valid = values[valid_mask].astype("float64", copy=False)
    result = {
        "label": label,
        "window": {"col_off": int(col), "row_off": int(row), "width": int(width), "height": int(height)},
        "valid_pixels": int(valid.size),
        "total_pixels": int(values.size),
    }
    if valid.size:
        result.update({
            "min": float(np.min(valid)),
            "max": float(np.max(valid)),
            "mean": float(np.mean(valid)),
            "std": float(np.std(valid, ddof=0)),
        })
    return result


def inspect_raster(data: bytes) -> dict:
    import rasterio
    import numpy as np
    from rasterio.io import MemoryFile

    if not is_tiff(data):
        raise AcquisitionError("NON_TIFF_BYTES", "Raster inspection requires TIFF magic", result_class="NEGATIVE_RESULT")
    try:
        with MemoryFile(data) as memory_file:
            with memory_file.open() as dataset:
                if dataset.driver != "GTiff" or dataset.count < 1 or dataset.width < 2 or dataset.height < 2:
                    raise AcquisitionError("INVALID_RASTER_STRUCTURE", "TIFF is not a usable GeoTIFF raster")
                size = min(SAMPLE_SIZE, dataset.width, dataset.height)
                windows = [
                    ("upper_left", 0, 0),
                    ("upper_right", dataset.width - size, 0),
                    ("center", (dataset.width - size) // 2, (dataset.height - size) // 2),
                    ("lower_left", 0, dataset.height - size),
                    ("lower_right", dataset.width - size, dataset.height - size),
                ]
                samples = [_window_stats(dataset, label, col, row, size) for label, col, row in windows]
                units = dataset.units[0] if dataset.units and dataset.units[0] else None
                tags = dataset.tags()
                band_tags = dataset.tags(1)
                allowed_tag_keys = {
                    "AREA_OR_POINT", "TIFFTAG_DATETIME", "TIFFTAG_SOFTWARE",
                    "TIFFTAG_IMAGEDESCRIPTION", "TIFFTAG_DOCUMENTNAME",
                }
                safe_tags = {k: str(v)[:500] for k, v in tags.items() if k in allowed_tag_keys}
                safe_band_tags = {
                    k: str(v)[:500] for k, v in band_tags.items()
                    if k.upper() in {"UNIT", "UNITS", "DESCRIPTION", "STATISTICS_MINIMUM", "STATISTICS_MAXIMUM"}
                }
                total_valid = sum(item["valid_pixels"] for item in samples)
                return {
                    "driver": dataset.driver,
                    "width": int(dataset.width),
                    "height": int(dataset.height),
                    "band_count": int(dataset.count),
                    "dtype_band_1": str(dataset.dtypes[0]),
                    "crs": dataset.crs.to_string() if dataset.crs else None,
                    "transform": [float(v) for v in tuple(dataset.transform)[:6]],
                    "bounds": [
                        float(dataset.bounds.left), float(dataset.bounds.bottom),
                        float(dataset.bounds.right), float(dataset.bounds.top),
                    ],
                    "resolution_crs_units": [float(v) for v in dataset.res],
                    "nodata_band_1": float(dataset.nodata) if dataset.nodata is not None else None,
                    "unit_band_1": units,
                    "band_1_scale": float(dataset.scales[0]) if dataset.scales else None,
                    "band_1_offset": float(dataset.offsets[0]) if dataset.offsets else None,
                    "area_or_point": safe_tags.get("AREA_OR_POINT"),
                    "dataset_tags": safe_tags,
                    "band_tags": safe_band_tags,
                    "sample_windows": samples,
                    "sample_valid_pixels": int(total_valid),
                    "sample_policy": "five deterministic 64x64 windows; only summary statistics retained",
                    "raw_pixels_retained": False,
                    "rasterio_version": rasterio.__version__,
                    "numpy_version": np.__version__,
                }
    except AcquisitionError:
        raise
    except Exception as exc:
        raise AcquisitionError(
            "GEOTIFF_PARSE_ERROR",
            "TIFF bytes could not be opened and sampled as a GeoTIFF",
            details={"exception_type": type(exc).__name__},
        ) from exc


def run() -> dict:
    data, transport = fetch_raster_bytes()
    raster = inspect_raster(data)
    return {
        "experiment": "E544 bounded official Jezero CTX TRN DTM acquisition and sample audit",
        "status": "COMPLETE",
        "source": {"url": SOURCE_URL, "page": SOURCE_PAGE, "doi": SOURCE_DOI, "publisher": "USGS Astrogeology Science Center"},
        "transport": transport,
        "sha256": hashlib.sha256(data).hexdigest(),
        "raster": raster,
        "claim_boundary": {
            "raw_ctx_raster_acquired": True,
            "ctx_geotiff_metadata_inspected": True,
            "bounded_pixel_samples_inspected": raster["sample_valid_pixels"] > 0,
            "mars_reference_transform_validated": False,
            "ctx_hirise_raster_coregistration_measured": False,
            "mola_local_observed_count_mask_measured": False,
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "One CTX product is not a cross-body descriptor set or known-site recovery experiment.",
            "Raster CRS, units, nodata and values are reported as encoded; no unverified vertical or body-reference transformation is applied.",
            "The five sample windows are not a full-raster quality assessment.",
            "No HiRISE or MOLA raster pixels are acquired by this experiment.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run()
    except AcquisitionError as exc:
        result = {
            "experiment": "E544 bounded official Jezero CTX TRN DTM acquisition and sample audit",
            "status": exc.result_class,
            "error_kind": exc.kind,
            "message": str(exc),
            "details": exc.details,
            "source": {"url": SOURCE_URL, "page": SOURCE_PAGE, "doi": SOURCE_DOI, "publisher": "USGS Astrogeology Science Center"},
            "claim_boundary": {
                "raw_ctx_raster_acquired": False,
                "cross_body_similarity": "NOT YET PROVEN",
                "known_site_recovery": "NOT YET MEASURED",
            },
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"],
        "error_kind": result.get("error_kind"),
        "sha256": result.get("sha256"),
        "raw_ctx_raster_acquired": result.get("claim_boundary", {}).get("raw_ctx_raster_acquired"),
        "sample_valid_pixels": result.get("raster", {}).get("sample_valid_pixels"),
    }, sort_keys=True))
    if result["status"] == "ERROR":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
