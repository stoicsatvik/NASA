"""E563: three-way MOLA / CTX / HiRISE common-point-support audit at Jezero.

This experiment tests spatial support only. It does not compare vertical values,
fit a registration correction, infer route safety, or claim analogue recovery.
Raw raster samples are transient; only counts, hashes, metadata and provenance
are written to the receipt.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
import pyproj
import rasterio
import requests
import tifffile
from rasterio.io import MemoryFile

from experiments.e545_mola_observed_support import (
    COUNT_IMG,
    COUNT_LABEL,
    COUNT_NAME,
    COUNT_RECORD_BYTES,
    FILE_RECORDS,
    LINE_SAMPLES,
    PIXELS_PER_DEGREE,
    TOPO_IMG,
    TOPO_LABEL,
    TOPO_NAME,
    TOPO_RECORD_BYTES,
    byte_range,
    extract_window,
    fetch_exact_range,
    fetch_label,
    make_window,
    pixel_index,
    validate_label,
)
from experiments.e548_hirise_pixel_window import (
    TIFF_URL,
    RangeReader,
    ProbeError,
    _first_float,
    _geo_summary,
    _read_small_label,
    _resolve_nodata,
    parse_pds3_label,
)
from experiments.e549_ctx_hirise_matched_support import (
    CTX_DOI,
    HI_DOI,
    _read_ctx,
    _read_hirise_array,
)

MOLA_RADIUS_FALLBACK_M = 3_396_000.0
MOLA_MAX_LATITUDE_DEG = 44.0
MOLA_WEST_LONGITUDE_DEG = 0.0
MOLA_WINDOW_SIZE = 33
MAX_HIRISE_TRANSFER_BYTES = 2_500_000
USER_AGENT = "Unified-Parallel-Foundry-E563/1.0"


class E563Error(RuntimeError):
    def __init__(self, outcome: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.outcome = outcome
        self.details = details or {}


def mola_pixel_centers(window: dict) -> tuple[np.ndarray, np.ndarray]:
    """Return planetocentric latitude and positive-east longitude at pixel centers."""
    rows = np.arange(window["row_start"], window["row_end"] + 1, dtype="float64")
    cols = np.arange(window["col_start"], window["col_end"] + 1, dtype="float64")
    lat = MOLA_MAX_LATITUDE_DEG - (rows[:, None] - 0.5) / PIXELS_PER_DEGREE
    lon = MOLA_WEST_LONGITUDE_DEG + (cols[None, :] - 0.5) / PIXELS_PER_DEGREE
    return np.broadcast_arrays(lat, lon)


def build_hirise_crs(label: dict[str, str]) -> tuple[pyproj.CRS, dict]:
    radius_a_km = _first_float(label.get("A_AXIS_RADIUS"))
    radius_c_km = _first_float(label.get("C_AXIS_RADIUS"))
    center_lat = _first_float(label.get("CENTER_LATITUDE"))
    center_lon = _first_float(label.get("CENTER_LONGITUDE"))
    resolution = _first_float(label.get("MAP_RESOLUTION"))
    projection = (label.get("MAP_PROJECTION_TYPE") or "").upper()
    if None in (radius_a_km, center_lat, center_lon, resolution) or projection != "EQUIRECTANGULAR":
        raise E563Error(
            "HIRISE_PROJECTION_INCOMPLETE",
            "HiRISE PDS3 label lacks the frozen equirectangular CRS parameters",
        )
    radius_m = radius_a_km * 1000.0
    pixel_size_m = 2.0 * math.pi * radius_m / (360.0 * resolution)
    if not math.isclose(pixel_size_m, 1.0, rel_tol=1e-6):
        raise E563Error(
            "HIRISE_SCALE_MISMATCH",
            "PDS3 MAP_RESOLUTION does not imply the expected 1 m HiRISE pixels",
            {"derived_pixel_size_m": pixel_size_m},
        )
    if radius_c_km is not None and not math.isclose(radius_a_km, radius_c_km, rel_tol=1e-9):
        raise E563Error(
            "HIRISE_ELLIPSOID_NOT_SPHERICAL",
            "The pinned CTX/HiRISE transformation assumes equal A/C radii",
        )
    crs = pyproj.CRS.from_proj4(
        f"+proj=eqc +lat_ts={center_lat} +lat_0={center_lat} "
        f"+lon_0={center_lon} +x_0=0 +y_0=0 +a={radius_m} +b={radius_m} "
        "+units=m +no_defs +type=crs"
    )
    return crs, {
        "reference_radius_a_m": radius_m,
        "reference_radius_c_m": radius_c_km * 1000.0 if radius_c_km is not None else None,
        "center_latitude_deg": center_lat,
        "center_longitude_deg": center_lon,
        "map_resolution_pixels_per_degree": resolution,
        "derived_pixel_size_m": pixel_size_m,
        "projection": projection,
    }


def point_indices(
    x: np.ndarray,
    y: np.ndarray,
    *,
    xmin: float,
    ymax: float,
    pixel_width: float,
    pixel_height: float,
    width: int,
    height: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Map projected coordinates to containing raster pixels and an in-bounds mask."""
    if pixel_width <= 0 or pixel_height <= 0:
        raise ValueError("pixel dimensions must be positive")
    cols = np.floor((x - xmin) / pixel_width).astype("int64")
    rows = np.floor((ymax - y) / pixel_height).astype("int64")
    inside = (cols >= 0) & (cols < width) & (rows >= 0) & (rows < height)
    return rows, cols, inside


def summarize_common_support(
    mola_observed: np.ndarray,
    ctx_valid: np.ndarray,
    hirise_valid: np.ndarray,
) -> dict:
    if mola_observed.shape != ctx_valid.shape or mola_observed.shape != hirise_valid.shape:
        raise ValueError("MOLA, CTX and HiRISE masks must have identical shapes")
    observed = np.asarray(mola_observed, dtype=bool)
    ctx = np.asarray(ctx_valid, dtype=bool)
    hi = np.asarray(hirise_valid, dtype=bool)
    denominator = int(observed.sum())
    if denominator == 0:
        raise ValueError("no MOLA observed-shot bins in the frozen window")
    ctx_count = int((observed & ctx).sum())
    hi_count = int((observed & hi).sum())
    common = int((observed & ctx & hi).sum())
    return {
        "mola_observed_bins": denominator,
        "mola_observed_within_ctx_valid_pixels": ctx_count,
        "mola_observed_within_hirise_valid_pixels": hi_count,
        "three_way_common_valid_point_support": common,
        "ctx_fraction_of_observed_mola_bins": ctx_count / denominator,
        "hirise_fraction_of_observed_mola_bins": hi_count / denominator,
        "three_way_fraction_of_observed_mola_bins": common / denominator,
        "support_is_point_center_not_area_fraction": True,
    }


def _grid_cardinal_edges(observed: np.ndarray) -> tuple[int, np.ndarray]:
    """Build 4-neighbor edges among observed MOLA bins, without retaining coordinates."""
    coords = np.argwhere(np.asarray(observed, dtype=bool))
    lookup = {(int(row), int(col)): index for index, (row, col) in enumerate(coords)}
    edges: list[tuple[int, int]] = []
    for index, (row, col) in enumerate(coords):
        for neighbor in ((int(row) + 1, int(col)), (int(row), int(col) + 1)):
            other = lookup.get(neighbor)
            if other is not None:
                edges.append((index, other))
    return len(coords), np.asarray(edges, dtype=np.int64).reshape((-1, 2))


def _component_sizes_4(mask: np.ndarray) -> list[int]:
    """Return descending 4-connected component sizes for a boolean grid."""
    values = np.asarray(mask, dtype=bool)
    visited = np.zeros(values.shape, dtype=bool)
    sizes: list[int] = []
    for row, col in zip(*np.where(values)):
        if visited[row, col]:
            continue
        visited[row, col] = True
        stack = [(int(row), int(col))]
        size = 0
        while stack:
            current_row, current_col = stack.pop()
            size += 1
            for next_row, next_col in (
                (current_row - 1, current_col),
                (current_row + 1, current_col),
                (current_row, current_col - 1),
                (current_row, current_col + 1),
            ):
                if (
                    0 <= next_row < values.shape[0]
                    and 0 <= next_col < values.shape[1]
                    and values[next_row, next_col]
                    and not visited[next_row, next_col]
                ):
                    visited[next_row, next_col] = True
                    stack.append((next_row, next_col))
        sizes.append(size)
    return sorted(sizes, reverse=True)


def _conditional_adjacency_reference(
    membership: np.ndarray,
    edges: np.ndarray,
    *,
    permutations: int,
    rng: np.random.Generator,
) -> dict:
    """Compare same-class edges with a fixed-count random-label reference.

    This is a descriptive reference only. It is not an inferential p-value:
    raster footprint geometry and nodata generation are not exchangeable under
    the uniform-label reference.
    """
    members = np.asarray(membership, dtype=bool)
    observed_edges = (
        int(np.count_nonzero(members[edges[:, 0]] & members[edges[:, 1]]))
        if edges.size
        else 0
    )
    count = int(members.sum())
    node_count = int(members.size)
    if count in (0, node_count) or edges.size == 0:
        return {
            "same_category_cardinal_adjacency_edges": observed_edges,
            "reference_mean_adjacency_edges": None,
            "reference_95th_percentile_adjacency_edges": None,
            "reference_upper_tail_fraction": None,
            "reference_permutations": 0,
        }

    null_edges = np.empty(permutations, dtype=np.int32)
    for index in range(permutations):
        selected = np.zeros(node_count, dtype=bool)
        selected[rng.choice(node_count, size=count, replace=False)] = True
        null_edges[index] = int(
            np.count_nonzero(selected[edges[:, 0]] & selected[edges[:, 1]])
        )
    ordered = np.sort(null_edges)
    q95_index = max(0, min(permutations - 1, math.ceil(0.95 * permutations) - 1))
    exceedances = int(np.count_nonzero(null_edges >= observed_edges))
    return {
        "same_category_cardinal_adjacency_edges": observed_edges,
        "reference_mean_adjacency_edges": float(null_edges.mean()),
        "reference_95th_percentile_adjacency_edges": int(ordered[q95_index]),
        "reference_upper_tail_fraction": float((exceedances + 1) / (permutations + 1)),
        "reference_permutations": permutations,
    }


def summarize_support_spatial_clustering(
    mola_observed: np.ndarray,
    ctx_valid: np.ndarray,
    hirise_inside: np.ndarray,
    hirise_valid: np.ndarray,
    *,
    permutations: int = 9_999,
    seed: int = 20_261_112,
) -> dict:
    """Summarize unsupported-point clustering using masks already held by E563.

    Only component sizes, adjacency counts and fixed-count random-label
    reference summaries are returned. No pixel values or point coordinates
    are persisted.
    """
    arrays = [
        np.asarray(mola_observed, dtype=bool),
        np.asarray(ctx_valid, dtype=bool),
        np.asarray(hirise_inside, dtype=bool),
        np.asarray(hirise_valid, dtype=bool),
    ]
    if any(array.shape != arrays[0].shape for array in arrays[1:]):
        raise ValueError("MOLA and support masks must have identical shapes")
    observed, ctx, inside, valid = arrays
    if not observed.any():
        raise ValueError("no MOLA observed-shot bins in the frozen window")
    if np.any(valid & ~inside):
        raise ValueError("HiRISE valid pixels cannot be outside the raster bounds")
    if permutations < 1:
        raise ValueError("permutations must be positive")

    node_count, edges = _grid_cardinal_edges(observed)
    category_masks = {
        "ctx_invalid": observed & ~ctx,
        "hirise_outside_bounds": observed & ~inside,
        "hirise_inside_nodata": observed & inside & ~valid,
    }
    rng = np.random.default_rng(seed)
    categories = {}
    for name, grid_mask in category_masks.items():
        membership = grid_mask[observed]
        component_sizes = _component_sizes_4(grid_mask)
        reference = _conditional_adjacency_reference(
            membership,
            edges,
            permutations=permutations,
            rng=rng,
        )
        count = int(membership.sum())
        categories[name] = {
            "count": count,
            "fraction_of_observed_mola_bins": count / node_count,
            "four_connected_component_count": len(component_sizes),
            "four_connected_component_sizes_desc": component_sizes,
            **reference,
        }

    return {
        "method": "4-neighbor cardinal adjacency on the fixed MOLA grid; observed bins only",
        "observed_mola_nodes": node_count,
        "cardinal_adjacency_edges_among_observed_bins": int(edges.shape[0]),
        "reference_design": (
            "uniformly reassign each category to the same number of observed MOLA bins; "
            "the fixed observed-shot mask is preserved"
        ),
        "reference_interpretation": (
            "descriptive only, not an inferential p-value; the uniform-label reference "
            "does not model raster footprint geometry, geology or nodata generation"
        ),
        "permutation_seed": seed,
        "categories": categories,
        "raw_pixels_retained": False,
        "point_coordinates_retained": False,
    }


def _sample_hirise_observed_points(
    session: requests.Session,
    lat: np.ndarray,
    lon: np.ndarray,
    observed: np.ndarray,
    hi_crs: pyproj.CRS,
    hi_page,
    hi_geo: dict,
    nodata: float | None,
    object_size: int,
) -> tuple[np.ndarray, dict]:
    radius_m = MOLA_RADIUS_FALLBACK_M
    mola_geographic = pyproj.CRS.from_proj4(
        f"+proj=longlat +a={radius_m} +b={radius_m} +no_defs +type=crs"
    )
    transformer = pyproj.Transformer.from_crs(mola_geographic, hi_crs, always_xy=True)
    inverse = pyproj.Transformer.from_crs(hi_crs, mola_geographic, always_xy=True)
    x, y = transformer.transform(lon, lat, errcheck=True)
    lon_back, lat_back = inverse.transform(x, y, errcheck=True)
    max_roundtrip_m = float(
        max(
            np.max(np.abs(lat_back - lat)) * math.pi / 180.0 * radius_m,
            np.max(np.abs(lon_back - lon)) * math.pi / 180.0 * radius_m,
        )
    )

    bounds = hi_geo["raster_bounds_map_units"]
    sx, sy = map(float, hi_geo["model_pixel_scale"])
    rows, cols, inside = point_indices(
        np.asarray(x),
        np.asarray(y),
        xmin=float(bounds["xmin"]),
        ymax=float(bounds["ymax"]),
        pixel_width=sx,
        pixel_height=sy,
        width=int(hi_page.imagewidth),
        height=int(hi_page.imagelength),
    )
    inside_observed = observed & inside
    valid = np.zeros(observed.shape, dtype=bool)
    grouped: dict[int, list[tuple[int, int, int]]] = {}
    for i, j in zip(*np.where(inside_observed)):
        grouped.setdefault(int(rows[i, j]), []).append((int(i), int(j), int(cols[i, j])))

    reader = RangeReader(
        session,
        TIFF_URL,
        object_size,
        max_bytes=MAX_HIRISE_TRANSFER_BYTES,
    )
    for raster_row, points in sorted(grouped.items()):
        col_start = min(p[2] for p in points)
        col_end = max(p[2] for p in points) + 1
        window = {
            "col_off": col_start,
            "row_off": raster_row,
            "width": col_end - col_start,
            "height": 1,
        }
        values, _ = _read_hirise_array(reader, hi_page, window)
        for i, j, col in points:
            value = float(values[0, col - col_start])
            valid[i, j] = math.isfinite(value) and (nodata is None or value != nodata)

    return valid, {
        "inside_raster_observed_bins": int(inside_observed.sum()),
        "sampled_observed_bins": int(sum(len(v) for v in grouped.values())),
        "unique_raster_rows_read": len(grouped),
        "range_requests": len(reader.ranges),
        "bytes_transferred": reader.transferred,
        "transfer_cap_bytes": MAX_HIRISE_TRANSFER_BYTES,
        "max_coordinate_roundtrip_error_m": max_roundtrip_m,
        "raw_pixels_retained": False,
    }


def run() -> dict:
    session = requests.Session()
    receipt = {
        "experiment": "E563_THREE_WAY_MOLA_CTX_HIRISE_COMMON_POINT_SUPPORT",
        "area": "Jezero crater, Mars",
        "outcome": "NOT_RUN",
        "claim_state": {
            "bounded_mola_observed_shot_support": "NOT YET MEASURED",
            "ctx_hirise_crs_parameter_equivalence": "NOT YET MEASURED",
            "mola_ctx_hirise_common_point_support": "NOT YET MEASURED",
            "local_horizontal_registration_residual": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "The result measures point-center support for MOLA bins with count > 0; it is not an area-coverage fraction.",
            "MOLA IAU2000 and Mars 2015 CTX/HiRISE coordinate references are not independently tied by control points in this experiment.",
            "The transformation preserves planetocentric latitude/longitude and applies the target HiRISE projection; it does not estimate a datum shift.",
            "MOLA topography is not compared numerically with CTX/HiRISE elevations because their vertical reference/processing definitions are not reconciled here.",
            "No fitted horizontal or vertical correction, imputation, route-risk score, analogue similarity score or E001 recovery is performed.",
            "No raw raster samples are persisted; only masks, counts, hashes and source metadata are retained.",
        ],
    }
    try:
        topo_label_text, topo_label_receipt = fetch_label(session, TOPO_LABEL, TOPO_NAME)
        count_label_text, count_label_receipt = fetch_label(session, COUNT_LABEL, COUNT_NAME)
        topo_fields = validate_label(topo_label_text, "topography")
        count_fields = validate_label(count_label_text, "counts")

        center_row, center_col = pixel_index(18.3995, 77.27025)
        window = make_window(center_row, center_col, MOLA_WINDOW_SIZE)
        topo_start, topo_end = byte_range(window["row_start"], window["row_end"], TOPO_RECORD_BYTES)
        count_start, count_end = byte_range(window["row_start"], window["row_end"], COUNT_RECORD_BYTES)
        topo_total = FILE_RECORDS * TOPO_RECORD_BYTES
        count_total = FILE_RECORDS * COUNT_RECORD_BYTES
        topo_raw, topo_range = fetch_exact_range(
            session, TOPO_IMG, TOPO_NAME, topo_start, topo_end, topo_total
        )
        count_raw, count_range = fetch_exact_range(
            session, COUNT_IMG, COUNT_NAME, count_start, count_end, count_total
        )
        topography = extract_window(
            topo_raw, record_bytes=TOPO_RECORD_BYTES, line_samples=LINE_SAMPLES,
            window=window, kind="topography"
        )
        counts = extract_window(
            count_raw, record_bytes=COUNT_RECORD_BYTES, line_samples=LINE_SAMPLES,
            window=window, kind="counts"
        )
        if topography.shape != (MOLA_WINDOW_SIZE, MOLA_WINDOW_SIZE):
            raise E563Error("MOLA_WINDOW_SHAPE_MISMATCH", "MOLA topography window has unexpected shape")
        observed = counts > 0
        if not observed.any():
            raise E563Error("MOLA_ZERO_OBSERVATION_WINDOW", "Frozen MOLA window has no observed-shot bins")

        lat, lon = mola_pixel_centers(window)
        hi_label_text, hi_label_receipt = _read_small_label(session)
        hi_label = parse_pds3_label(hi_label_text)
        hi_crs, hi_projection = build_hirise_crs(hi_label)

        ctx_bytes, ctx_transport = _read_ctx(session)
        with MemoryFile(ctx_bytes) as memory_file:
            with memory_file.open() as ctx_ds:
                if ctx_ds.driver != "GTiff" or ctx_ds.count < 1:
                    raise E563Error("CTX_RASTER_CONTRACT_MISMATCH", "Pinned CTX object is not a readable GeoTIFF")
                ctx_crs = pyproj.CRS.from_wkt(ctx_ds.crs.to_wkt())
                crs_equal = ctx_crs.equals(hi_crs, ignore_axis_order=True)
                if not crs_equal:
                    raise E563Error(
                        "CTX_HIRISE_CRS_NOT_EQUIVALENT",
                        "PDS3-derived HiRISE CRS differs from the pinned CTX raster CRS",
                        {"ctx_crs": ctx_crs.to_string(), "hirise_crs": hi_crs.to_string()},
                    )
                ctx_values = ctx_ds.read(1)
                ctx_mask = (ctx_ds.read_masks(1) > 0) & np.isfinite(ctx_values)
                if ctx_ds.nodata is not None:
                    ctx_mask &= ctx_values != ctx_ds.nodata
                ctx_rows = np.zeros(observed.shape, dtype="int64")
                ctx_cols = np.zeros(observed.shape, dtype="int64")
                ctx_inside = np.zeros(observed.shape, dtype=bool)
                ctx_valid = np.zeros(observed.shape, dtype=bool)
                to_ctx = pyproj.Transformer.from_crs(
                    pyproj.CRS.from_proj4(
                        f"+proj=longlat +a={MOLA_RADIUS_FALLBACK_M} "
                        f"+b={MOLA_RADIUS_FALLBACK_M} +no_defs +type=crs"
                    ),
                    ctx_crs,
                    always_xy=True,
                )
                x, y = to_ctx.transform(lon, lat, errcheck=True)
                for i, j in zip(*np.where(observed)):
                    row, col = ctx_ds.index(float(x[i, j]), float(y[i, j]))
                    ctx_rows[i, j], ctx_cols[i, j] = row, col
                    inside = 0 <= row < ctx_ds.height and 0 <= col < ctx_ds.width
                    ctx_inside[i, j] = inside
                    if inside:
                        ctx_valid[i, j] = bool(ctx_mask[row, col])

                hi_head = session.head(
                    TIFF_URL,
                    headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
                    timeout=(15, 45),
                    allow_redirects=False,
                )
                try:
                    if int(hi_head.status_code) != 200:
                        raise E563Error(
                            f"HIRISE_HEAD_HTTP_{hi_head.status_code}",
                            "Pinned HiRISE TIFF HEAD failed",
                        )
                    raw_size = hi_head.headers.get("Content-Length", "")
                    if not raw_size.isdigit() or int(raw_size) <= 0:
                        raise E563Error("HIRISE_SIZE_UNKNOWN", "Pinned HiRISE TIFF has no positive Content-Length")
                    hi_size = int(raw_size)
                    if hi_head.headers.get("Accept-Ranges", "").lower() != "bytes":
                        raise E563Error("HIRISE_RANGE_UNAVAILABLE", "Pinned HiRISE TIFF does not advertise byte ranges")
                finally:
                    hi_head.close()

                reader = RangeReader(
                    session, TIFF_URL, hi_size, max_bytes=MAX_HIRISE_TRANSFER_BYTES
                )
                with tifffile.TiffFile(reader) as tif:
                    if not tif.pages:
                        raise E563Error("HIRISE_TIFF_NO_PAGES", "Pinned HiRISE TIFF has no image pages")
                    hi_page = tif.pages[0]
                    if int(hi_page.imagewidth) != 21400 or int(hi_page.imagelength) != 21488:
                        raise E563Error("HIRISE_DIMENSION_MISMATCH", "HiRISE dimensions differ from E548 contract")
                    nodata, nodata_source = _resolve_nodata(hi_page, hi_label)
                    hi_geo = _geo_summary(hi_page)
                    hi_valid, hi_transport = _sample_hirise_observed_points(
                        session, lat, lon, observed, hi_crs, hi_page, hi_geo, nodata, hi_size
                    )
                    hi_inside = np.zeros(observed.shape, dtype=bool)
                    bounds = hi_geo["raster_bounds_map_units"]
                    sx, sy = map(float, hi_geo["model_pixel_scale"])
                    hi_rows, hi_cols, hi_inside = point_indices(
                        np.asarray(x), np.asarray(y),
                        xmin=float(bounds["xmin"]), ymax=float(bounds["ymax"]),
                        pixel_width=sx, pixel_height=sy,
                        width=int(hi_page.imagewidth), height=int(hi_page.imagelength),
                    )
                    hi_inside &= observed

                spatial_clustering = summarize_support_spatial_clustering(
                    observed,
                    ctx_valid,
                    hi_inside,
                    hi_valid,
                    permutations=9_999,
                    seed=20_261_112,
                )
                common = summarize_common_support(observed, ctx_valid, hi_valid)
                receipt.update({
                    "outcome": "THREE_WAY_POINT_SUPPORT_MEASURED",
                    "sources": {
                        "mola": {
                            "topography_image": TOPO_IMG,
                            "counts_image": COUNT_IMG,
                            "coordinate_reference": "IAU2000; 3396.0 km sphere; simple cylindrical; planetocentric latitude; positive-east longitude",
                            "topography_label": topo_label_receipt,
                            "counts_label": count_label_receipt,
                            "topography_range": topo_range,
                            "counts_range": count_range,
                            "doi_or_bundle": "PDS Geosciences Node MGS MOLA MEGDR v2.0",
                        },
                        "ctx": {"doi": CTX_DOI, **ctx_transport},
                        "hirise": {
                            "doi": HI_DOI,
                            "label": hi_label_receipt,
                            "object_size_bytes": hi_size,
                            "nodata_value": nodata,
                            "nodata_source": nodata_source,
                            "projection": hi_projection,
                            "geotiff_bounds_map_units": hi_geo["raster_bounds_map_units"],
                            "model_pixel_scale": hi_geo["model_pixel_scale"],
                            **hi_transport,
                        },
                    },
                    "mola_window": {
                        "center_row_1_based": center_row,
                        "center_col_1_based": center_col,
                        **window,
                        "observed_shot_bins": int(observed.sum()),
                        "total_bins": int(observed.size),
                        "observed_shot_fraction": float(observed.mean()),
                        "center_pixel_latitude_deg": float(lat[MOLA_WINDOW_SIZE // 2, MOLA_WINDOW_SIZE // 2]),
                        "center_pixel_longitude_deg": float(lon[MOLA_WINDOW_SIZE // 2, MOLA_WINDOW_SIZE // 2]),
                        "nominal_local_east_west_spacing_m": 463.0 * math.cos(math.radians(18.3995)),
                        "nominal_north_south_spacing_m": 463.0,
                    },
                    "crs_audit": {
                        "ctx_hirise_pyproj_equivalent": crs_equal,
                        "mola_reference_radius_m": MOLA_RADIUS_FALLBACK_M,
                        "hirise_reference_radius_m": hi_projection["reference_radius_a_m"],
                        "radius_difference_m": hi_projection["reference_radius_a_m"] - MOLA_RADIUS_FALLBACK_M,
                        "mola_to_target_projection": "planetocentric lon/lat transformed to HiRISE PDS3-derived equirectangular CRS",
                        "coordinate_roundtrip_error_m": hi_transport["max_coordinate_roundtrip_error_m"],
                        "independent_horizontal_control_residual": "NOT MEASURED",
                    },
                    "common_point_support": common,
                    "spatial_support_clustering": spatial_clustering,
                    "geometry_support": {
                        "mola_observed_bins_inside_ctx_raster": int((observed & ctx_inside).sum()),
                        "mola_observed_bins_inside_hirise_raster": int((observed & hi_inside).sum()),
                        "mola_observed_bins_with_valid_ctx_pixels": int((observed & ctx_valid).sum()),
                        "mola_observed_bins_with_valid_hirise_pixels": int((observed & hi_valid).sum()),
                    },
                    "claim_state": {
                        "bounded_mola_observed_shot_support": "SUPPORTED",
                        "ctx_hirise_crs_parameter_equivalence": "SUPPORTED",
                        "mola_ctx_hirise_common_point_support": (
                            "SUPPORTED FOR THIS BOUNDED WINDOW"
                            if common["three_way_common_valid_point_support"] == common["mola_observed_bins"]
                            else "PARTIAL FOR THIS BOUNDED WINDOW"
                        ),
                        "local_horizontal_registration_residual": "NOT YET MEASURED",
                        "cross_body_similarity": "NOT YET PROVEN",
                        "known_site_recovery": "NOT YET MEASURED",
                        "novel_analogue_discovery": "NOT YET PROVEN",
                        "route_safety": "NOT CLAIMED",
                    },
                    "raw_pixels_retained": False,
                })
                receipt["transport_summary"] = {
                    "ctx_bytes": ctx_transport["bytes"],
                    "hirise_range_requests": hi_transport["range_requests"],
                    "hirise_bytes": hi_transport["bytes_transferred"],
                    "hirise_transfer_cap_bytes": hi_transport["transfer_cap_bytes"],
                }
        return receipt
    except (E563Error, ProbeError) as exc:
        receipt["outcome"] = getattr(exc, "outcome", "ERROR")
        receipt["error"] = {
            "kind": type(exc).__name__,
            "message": str(exc),
            **getattr(exc, "details", {}),
        }
        return receipt
    except Exception as exc:
        receipt["outcome"] = "ERROR"
        receipt["error"] = {"kind": type(exc).__name__, "message": str(exc)}
        return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    summary = {
        "experiment": result["experiment"],
        "outcome": result["outcome"],
        "mola_observed_bins": result.get("common_point_support", {}).get("mola_observed_bins"),
        "three_way_common_points": result.get("common_point_support", {}).get("three_way_common_valid_point_support"),
        "three_way_fraction": result.get("common_point_support", {}).get("three_way_fraction_of_observed_mola_bins"),
        "hirise_bytes": result.get("transport_summary", {}).get("hirise_bytes"),
    }
    print(json.dumps(summary, sort_keys=True))
    return 0 if result["outcome"] == "THREE_WAY_POINT_SUPPORT_MEASURED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
