from __future__ import annotations

import argparse
import hashlib
import json
import math
import tempfile
from pathlib import Path

import numpy as np
import rasterio
import requests
from rasterio.windows import Window

EXPERIMENT = "E573 Lonar SRTM terrain sample"
TILE_NAME = "N19E076.tif"
TILE_URL = (
    "https://opentopography.s3.sdsc.edu/raster/"
    "SRTM_GL1/SRTM_GL1_srtm/N19E076.tif"
)
MAX_TILE_BYTES = 40_000_000
WINDOW_SIZE = 81
NASA_PRODUCT = "SRTMGL1 v003"
NASA_DOI = "10.5067/MEaSUREs/SRTM/SRTMGL1.003"

# Lonar's published location is approximately 19°58'N, 76°31'E.
# The two regional windows are analyst-selected terrain controls only:
# they are not independently classified as non-analogues or as a different lithology.
SITES = {
    "lonar_candidate": {
        "latitude": 19 + 58 / 60,
        "longitude": 76 + 31 / 60,
        "role": "published impact-crater candidate",
        "label_state": "candidate_site; not a recovered analogue",
    },
    "regional_control_west": {
        "latitude": 19.90,
        "longitude": 76.30,
        "role": "analyst-selected regional terrain control",
        "label_state": "unclassified_control; not a verified non-analogue",
    },
    "regional_control_east": {
        "latitude": 19.90,
        "longitude": 76.75,
        "role": "analyst-selected regional terrain control",
        "label_state": "unclassified_control; not a verified non-analogue",
    },
}


class E573Error(RuntimeError):
    pass


def download_tile(destination: Path) -> dict:
    digest = hashlib.sha256()
    total = 0
    with requests.get(TILE_URL, stream=True, timeout=(20, 90)) as response:
        if response.status_code != 200:
            raise E573Error("SRTM_TILE_HTTP_STATUS_" + str(response.status_code))
        content_length = response.headers.get("Content-Length")
        if content_length and int(content_length) > MAX_TILE_BYTES:
            raise E573Error("SRTM_TILE_CONTENT_LENGTH_EXCEEDS_CAP")
        with destination.open("wb") as handle:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                total += len(chunk)
                if total > MAX_TILE_BYTES:
                    raise E573Error("SRTM_TILE_STREAM_EXCEEDS_CAP")
                digest.update(chunk)
                handle.write(chunk)
    if total == 0:
        raise E573Error("SRTM_TILE_EMPTY")
    if content_length and total != int(content_length):
        raise E573Error("SRTM_TILE_LENGTH_MISMATCH")
    return {
        "http_status": 200,
        "content_type": response.headers.get("Content-Type"),
        "content_length_header": int(content_length) if content_length else None,
        "downloaded_bytes": total,
        "sha256": digest.hexdigest(),
        "max_bytes": MAX_TILE_BYTES,
    }


def _median(values: np.ndarray) -> float | None:
    values = np.asarray(values, dtype=np.float64)
    values = values[np.isfinite(values)]
    return float(np.median(values)) if values.size else None


def terrain_descriptors(
    elevation: np.ndarray,
    valid: np.ndarray,
    pixel_x_m: float,
    pixel_y_m: float,
) -> dict:
    elevation = np.asarray(elevation, dtype=np.float64)
    valid = np.asarray(valid, dtype=bool)
    if elevation.ndim != 2 or elevation.shape != valid.shape:
        raise ValueError("elevation and validity arrays must be matching 2-D arrays")
    if min(pixel_x_m, pixel_y_m) <= 0 or not math.isfinite(pixel_x_m + pixel_y_m):
        raise ValueError("pixel dimensions must be finite and positive")
    values = elevation[valid & np.isfinite(elevation)]
    if values.size < 25:
        raise ValueError("too few valid pixels for terrain descriptors")

    median = float(np.median(values))
    p05, p50, p95 = (float(x) for x in np.percentile(values, [5, 50, 95]))
    mad = float(np.median(np.abs(values - median)))

    safe = np.where(valid & np.isfinite(elevation), elevation, median)
    dz_dy, dz_dx = np.gradient(safe, pixel_y_m, pixel_x_m)
    slope = np.degrees(np.arctan(np.hypot(dz_dx, dz_dy)))
    slope_valid = valid.copy()
    slope_valid[1:-1, 1:-1] &= (
        valid[:-2, 1:-1]
        & valid[2:, 1:-1]
        & valid[1:-1, :-2]
        & valid[1:-1, 2:]
    )
    slope_values = slope[slope_valid & np.isfinite(slope)]

    rows, cols = np.indices(elevation.shape)
    center_row = (elevation.shape[0] - 1) / 2
    center_col = (elevation.shape[1] - 1) / 2
    radius_m = np.sqrt(
        ((cols - center_col) * pixel_x_m) ** 2
        + ((rows - center_row) * pixel_y_m) ** 2
    )
    center_mask = (radius_m <= 250) & valid
    rim_mask = (radius_m >= 700) & (radius_m <= 1050) & valid
    center_median = _median(elevation[center_mask])
    rim_median = _median(elevation[rim_mask])

    return {
        "window_shape": [int(elevation.shape[0]), int(elevation.shape[1])],
        "valid_pixel_count": int(values.size),
        "valid_fraction": float(values.size / elevation.size),
        "elevation_unit": "m",
        "elevation_p05_m": p05,
        "elevation_median_m": p50,
        "elevation_p95_m": p95,
        "relief_p95_minus_p05_m": float(p95 - p05),
        "elevation_mad_m": mad,
        "slope_median_deg": float(np.median(slope_values)) if slope_values.size else None,
        "slope_p90_deg": float(np.percentile(slope_values, 90)) if slope_values.size else None,
        "center_radius_m": 250,
        "rim_annulus_inner_m": 700,
        "rim_annulus_outer_m": 1050,
        "center_median_m": center_median,
        "rim_annulus_median_m": rim_median,
        "rim_minus_center_m": (
            float(rim_median - center_median)
            if center_median is not None and rim_median is not None
            else None
        ),
        "slope_valid_pixel_count": int(slope_values.size),
    }


def sample_site(dataset, site_name: str, site: dict) -> dict:
    row, col = dataset.index(site["longitude"], site["latitude"])
    half = WINDOW_SIZE // 2
    row_off, col_off = row - half, col - half
    if (
        row_off < 0
        or col_off < 0
        or row_off + WINDOW_SIZE > dataset.height
        or col_off + WINDOW_SIZE > dataset.width
    ):
        raise E573Error("SITE_WINDOW_OUTSIDE_PINNED_TILE_" + site_name)

    window = Window(col_off, row_off, WINDOW_SIZE, WINDOW_SIZE)
    sample = dataset.read(1, window=window, masked=True)
    elevation = np.asarray(sample.data, dtype=np.float64)
    mask = np.ma.getmaskarray(sample)
    valid = (~mask) & np.isfinite(elevation)
    latitude_scale = 111_320.0
    pixel_x_m = abs(dataset.transform.a) * latitude_scale * math.cos(math.radians(site["latitude"]))
    pixel_y_m = abs(dataset.transform.e) * latitude_scale
    result = terrain_descriptors(elevation, valid, pixel_x_m, pixel_y_m)
    result.update({
        "site_id": site_name,
        "role": site["role"],
        "label_state": site["label_state"],
        "latitude": site["latitude"],
        "longitude": site["longitude"],
        "pixel_row": int(row),
        "pixel_col": int(col),
        "pixel_size_x_m_at_site": float(pixel_x_m),
        "pixel_size_y_m": float(pixel_y_m),
    })
    return result


def run() -> dict:
    with tempfile.TemporaryDirectory(prefix="e573-srtm-") as temp_dir:
        tile_path = Path(temp_dir) / TILE_NAME
        transport = download_tile(tile_path)
        with rasterio.open(tile_path) as dataset:
            if dataset.crs is None or dataset.crs.to_epsg() != 4326:
                raise E573Error("SRTM_TILE_CRS_NOT_EPSG4326")
            if dataset.width != 3601 or dataset.height != 3601:
                raise E573Error("SRTM_TILE_DIMENSIONS_UNEXPECTED")
            if dataset.count != 1 or dataset.dtypes[0] != "int16":
                raise E573Error("SRTM_TILE_BAND_OR_DTYPE_UNEXPECTED")
            if not (
                math.isclose(abs(dataset.transform.a), 1 / 3600, rel_tol=0, abs_tol=1e-10)
                and math.isclose(abs(dataset.transform.e), 1 / 3600, rel_tol=0, abs_tol=1e-10)
            ):
                raise E573Error("SRTM_TILE_RESOLUTION_UNEXPECTED")
            if dataset.nodata is None:
                raise E573Error("SRTM_TILE_NODATA_SEMANTICS_MISSING")

            sites = [
                sample_site(dataset, name, site)
                for name, site in SITES.items()
            ]
            metadata = {
                "product": NASA_PRODUCT,
                "doi": NASA_DOI,
                "tile": TILE_NAME,
                "source_provider": "OpenTopography public S3-compatible mirror",
                "source_url": TILE_URL,
                "source_access": "anonymous/no-sign-request; no API key or account used",
                "width": int(dataset.width),
                "height": int(dataset.height),
                "bands": int(dataset.count),
                "dtype": dataset.dtypes[0],
                "crs": dataset.crs.to_string(),
                "transform": [float(value) for value in dataset.transform[:6]],
                "bounds": [float(value) for value in dataset.bounds],
                "resolution_degrees": [float(dataset.transform.a), float(dataset.transform.e)],
                "approx_resolution_m_at_19_9N": [
                    float(abs(dataset.transform.a) * 111_320.0 * math.cos(math.radians(19.9))),
                    float(abs(dataset.transform.e) * 111_320.0),
                ],
                "nodata": float(dataset.nodata),
                "unit": "m (SRTM elevation product convention; GeoTIFF band unit metadata: " + str(dataset.units[0]) + ")",
                "acquisition_epoch": "SRTM mission, February 2000",
                "transport": transport,
            }

    candidate = next(row for row in sites if row["site_id"] == "lonar_candidate")
    controls = [row for row in sites if row["site_id"].startswith("regional_control")]
    control_rim = float(np.median([row["rim_minus_center_m"] for row in controls]))
    control_relief = float(np.median([row["relief_p95_minus_p05_m"] for row in controls]))
    return {
        "experiment": EXPERIMENT,
        "outcome": "LONAR_TERRAIN_SAMPLE_ACQUIRED",
        "source": metadata,
        "sampling": {
            "window_pixels": WINDOW_SIZE,
            "window_extent_approx_km": [
                round(WINDOW_SIZE * metadata["approx_resolution_m_at_19_9N"][0] / 1000, 3),
                round(WINDOW_SIZE * metadata["approx_resolution_m_at_19_9N"][1] / 1000, 3),
            ],
            "sites": sites,
            "candidate_minus_control_median": {
                "rim_minus_center_m": float(candidate["rim_minus_center_m"] - control_rim),
                "relief_p95_minus_p05_m": float(candidate["relief_p95_minus_p05_m"] - control_relief),
                "control_count": len(controls),
                "control_label_boundary": "two analyst-selected regional terrain controls; not independently verified non-analogues",
            },
        },
        "claim_state": {
            "NASA_SRTMGL1_tile_ingestion": "SUPPORTED_FOR_THIS_PINNED_TILE",
            "Lonar_crater_morphology_in_SRTM": "MEASURED_FOR_THIS_WINDOW_IF_RIM_CONTRAST_IS_POSITIVE",
            "local_terrain_contrast": "DESCRIPTIVE_ONLY_TWO_UNCLASSIFIED_CONTROLS",
            "Earth_terrain_feature_availability": "SUPPORTED_FOR_THIS_PRODUCT_AND_TILE",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery_E001": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "local_validation_advantage": "NOT YET PROVEN",
            "challenge_selection_superiority": "NOT YET PROVEN",
        },
        "limitations": [
            "The SRTM tile is a surface-elevation product acquired in February 2000, not a current field measurement.",
            "The two regional controls are analyst-selected and are not verified geological negative controls.",
            "The site coordinates are published approximate coordinates; the crater center is not a surveyed control point.",
            "The 30 m SRTM descriptors are not directly comparable to the approximately 1.895 km/px equatorial LOLA grid or the 1 m HiRISE DTM; support-matched aggregation is required before cross-body comparisons.",
            "SRTM topographic morphology alone cannot establish mineralogy, impact ejecta composition, water chemistry, or analogue validity.",
            "No field visit, field measurement, protected-area access, or destructive sampling was performed.",
            "No raw DEM tile or per-pixel elevation array is committed; only aggregate descriptors and provenance are retained.",
        ],
        "next_gate": "Only after adding a second independently sourced Earth product and a genuinely labeled non-analogue control should this feature enter a frozen Earth/planetary E001 matrix. First align spatial support and physical descriptors across instruments; do not score cross-body similarity from these raw summaries.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run()
        code = 0
    except Exception as error:
        result = {
            "experiment": EXPERIMENT,
            "outcome": "ACQUISITION_OR_VALIDATION_FAILURE",
            "error_type": type(error).__name__,
            "message": str(error)[:240],
            "claim_state": {
                "NASA_SRTMGL1_tile_ingestion": "NOT YET SUPPORTED",
                "cross_body_similarity": "NOT YET PROVEN",
                "known_site_recovery_E001": "NOT YET MEASURED",
                "novel_analogue_discovery": "NOT YET PROVEN",
            },
            "raw_tile_retained": False,
        }
        code = 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "outcome": result.get("outcome"),
        "downloaded_bytes": result.get("source", {}).get("transport", {}).get("downloaded_bytes"),
        "site_count": len(result.get("sampling", {}).get("sites", [])),
        "claim_state": result.get("claim_state", {}),
    }, sort_keys=True))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
