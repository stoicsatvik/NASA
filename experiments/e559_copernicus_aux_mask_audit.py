from __future__ import annotations

import argparse
import hashlib
import json
import math
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import parse_qs, quote, urlsplit

import numpy as np
import rasterio
import requests
from rasterio.windows import Window
from rasterio.warp import transform as reproject_xy

from experiments.e557_copernicus_glo30_lonar_sample import (
    BASE_URL,
    BUCKET_HOST,
    SITES,
    USER_AGENT,
    tile_stem,
)

MAX_LISTING_BYTES = 2_000_000
MAX_LISTING_KEYS = 100
MAX_OBJECT_BYTES = 100_000_000
HEADER_RANGE_BYTES = 16_384
MAX_KML_BYTES = 1_000_000
WINDOW = 17
MAX_BLOCK_UNCOMPRESSED_BYTES = 8_000_000
AUXFILES = "AUXFILES"
PREVIEW = "PREVIEW"

# DGED product-handbook naming convention: DSM_10_N19_00_E076_00_<layer>.
LAYER_SUFFIXES = {
    "EDM": "_EDM.tif",
    "FLM": "_FLM.tif",
    "WBM": "_WBM.tif",
    "HEM": "_HEM.tif",
    "ACM": "_ACM.kml",
    "SRC": "_SRC.kml",
}
MASK_CLASSES = {
    "EDM": {
        0: "void", 1: "not_edited", 2: "external_elevation_infill",
        3: "interpolated", 4: "smoothed", 5: "airport",
        6: "raised_negative_elevation", 7: "flattened",
        8: "ocean", 9: "lake", 10: "river", 11: "shoreline",
        12: "morphed", 13: "shifted",
    },
    "FLM": {
        0: "void", 1: "edited_except_filled", 2: "not_edited_not_filled",
        3: "ASTER", 4: "SRTM90", 5: "SRTM30", 6: "GMTED2010",
        7: "SRTM30plus", 8: "TerraSAR_X", 9: "AW3D30",
        100: "Norway_DEM", 101: "Spain_DSM05",
    },
    "WBM": {0: "no_water", 1: "ocean", 2: "lake", 3: "river"},
}
EXPECTED_FILENAME_PREFIX = "Copernicus_DSM_10_N19_00_E076_00"


class E559Error(RuntimeError):
    def __init__(self, outcome: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.outcome = outcome
        self.details = details or {}


def expected_key(prefix: str, layer: str) -> str:
    if layer not in LAYER_SUFFIXES:
        raise ValueError(f"unsupported layer: {layer}")
    folder = AUXFILES if layer in {"EDM", "FLM", "WBM", "HEM", "ACM"} else PREVIEW
    return f"{prefix}{folder}/{EXPECTED_FILENAME_PREFIX}{LAYER_SUFFIXES[layer]}"


def validate_key(key: str, prefix: str) -> str:
    if not key.startswith(prefix) or key.startswith("/") or ".." in key.split("/"):
        raise E559Error("OBJECT_KEY_OUTSIDE_PREFIX", "S3 object key is outside the exact frozen tile prefix", {"key": key})
    return key


def object_url(key: str, prefix: str) -> str:
    validate_key(key, prefix)
    return f"{BASE_URL}{quote(key, safe='/')}"


def parse_listing(body: bytes, expected_prefix: str) -> dict:
    if len(body) > MAX_LISTING_BYTES:
        raise E559Error("LISTING_BODY_BUDGET_EXCEEDED", "S3 listing XML exceeds the 2 MB response budget")
    try:
        root = ET.fromstring(body)
    except ET.ParseError as error:
        raise E559Error("LISTING_XML_INVALID", "S3 ListObjectsV2 response is not valid XML") from error
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    bucket = root.findtext("s3:Name", default="", namespaces=ns)
    prefix = root.findtext("s3:Prefix", default="", namespaces=ns)
    truncated = root.findtext("s3:IsTruncated", default="true", namespaces=ns).lower() == "true"
    if bucket != "copernicus-dem-30m" or prefix != expected_prefix:
        raise E559Error(
            "LISTING_SCOPE_MISMATCH",
            "S3 response bucket or prefix differs from the frozen public tile scope",
            {"bucket": bucket, "prefix": prefix, "expected_prefix": expected_prefix},
        )
    objects = []
    for node in root.findall("s3:Contents", ns):
        key = node.findtext("s3:Key", default="", namespaces=ns)
        size_text = node.findtext("s3:Size", default="", namespaces=ns)
        if not key or not size_text.isdigit():
            raise E559Error("LISTING_OBJECT_INVALID", "S3 object entry lacks a key or numeric size")
        validate_key(key, expected_prefix)
        objects.append({
            "key": key,
            "size_bytes": int(size_text),
            "etag": node.findtext("s3:ETag", default="", namespaces=ns).strip('"'),
            "last_modified": node.findtext("s3:LastModified", default="", namespaces=ns),
        })
    if len(objects) > MAX_LISTING_KEYS:
        raise E559Error("LISTING_KEY_BUDGET_EXCEEDED", "S3 returned more than the frozen 100-object limit")
    return {
        "bucket": bucket,
        "prefix": prefix,
        "key_count_reported": int(root.findtext("s3:KeyCount", default=str(len(objects)), namespaces=ns)),
        "is_truncated": truncated,
        "objects": objects,
    }


def list_prefix(session: requests.Session, prefix: str) -> dict:
    response = session.get(
        BASE_URL,
        params={"list-type": "2", "prefix": prefix, "max-keys": str(MAX_LISTING_KEYS)},
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        timeout=(15, 45),
        allow_redirects=False,
        stream=True,
    )
    try:
        if response.status_code in (301, 302, 303, 307, 308):
            raise E559Error("LISTING_REDIRECT_REFUSED", "S3 listing redirected; redirects are not followed")
        if response.status_code == 403:
            raise E559Error("LISTING_FORBIDDEN", "The exact anonymous S3 prefix listing returned HTTP 403")
        if response.status_code == 404:
            raise E559Error("BUCKET_OR_PREFIX_NOT_FOUND", "The exact public S3 listing returned HTTP 404")
        if response.status_code != 200:
            raise E559Error(f"LISTING_HTTP_{response.status_code}", "S3 ListObjectsV2 did not return HTTP 200")
        parsed = urlsplit(response.url)
        query = parse_qs(parsed.query)
        if parsed.scheme != "https" or parsed.hostname != BUCKET_HOST or parsed.path != "/":
            raise E559Error("LISTING_URL_OUTSIDE_ALLOWLIST", "S3 listing response left the exact bucket endpoint")
        if query.get("prefix") != [prefix] or query.get("list-type") != ["2"] or query.get("max-keys") != [str(MAX_LISTING_KEYS)]:
            raise E559Error("LISTING_QUERY_CHANGED", "S3 listing query differs from the frozen prefix/limit")
        body = response.raw.read(MAX_LISTING_BYTES + 1, decode_content=True)
        result = parse_listing(body, prefix)
        result["http_status"] = response.status_code
        result["response_bytes"] = len(body)
        result["response_sha256"] = hashlib.sha256(body).hexdigest()
        result["full_prefix_enumerated"] = not result["is_truncated"]
        return result
    finally:
        response.close()


def head_object(session: requests.Session, url: str, expected_size: int) -> dict:
    response = session.head(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        timeout=(15, 45),
        allow_redirects=False,
    )
    if response.status_code in (301, 302, 303, 307, 308):
        raise E559Error("OBJECT_REDIRECT_REFUSED", "Mask object HEAD redirected; redirects are not followed")
    if response.status_code == 403:
        raise E559Error("OBJECT_FORBIDDEN", "Listed object returned HTTP 403")
    if response.status_code != 200:
        raise E559Error(f"OBJECT_HEAD_HTTP_{response.status_code}", "Listed object HEAD did not return HTTP 200")
    if response.url != url:
        raise E559Error("OBJECT_HEAD_URL_CHANGED", "Object HEAD URL changed")
    length = response.headers.get("Content-Length")
    if not length or not length.isdigit() or int(length) != expected_size:
        raise E559Error("OBJECT_LENGTH_MISMATCH", "HEAD length differs from the listing receipt")
    if expected_size <= 0 or expected_size > MAX_OBJECT_BYTES:
        raise E559Error("OBJECT_SIZE_OUTSIDE_BUDGET", "Object size is outside the 100 MB bound")
    if response.headers.get("Accept-Ranges", "").lower() != "bytes":
        raise E559Error("OBJECT_RANGE_NOT_ADVERTISED", "Object does not advertise byte-range access")
    return {
        "http_status": response.status_code,
        "content_length_bytes": int(length),
        "content_type": response.headers.get("Content-Type"),
        "accept_ranges": response.headers.get("Accept-Ranges"),
        "etag": response.headers.get("ETag"),
        "last_modified": response.headers.get("Last-Modified"),
    }


def read_tiff_header(session: requests.Session, url: str, expected_size: int) -> dict:
    response = session.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "identity",
            "Range": f"bytes=0-{HEADER_RANGE_BYTES - 1}",
        },
        timeout=(15, 45),
        allow_redirects=False,
        stream=True,
    )
    try:
        if response.status_code in (301, 302, 303, 307, 308):
            raise E559Error("OBJECT_RANGE_REDIRECT_REFUSED", "Object range redirected; redirects are not followed")
        if response.status_code == 200:
            raise E559Error("OBJECT_RANGE_IGNORED", "Object server ignored Range; response body was not consumed")
        if response.status_code != 206:
            raise E559Error(f"OBJECT_RANGE_HTTP_{response.status_code}", "Object header range did not return HTTP 206")
        start, end, total = response.headers.get("Content-Range", "").replace("bytes ", "").split("/", 1)[0].split("-") + [expected_size]
        if (int(start), int(end), int(total)) != (0, HEADER_RANGE_BYTES - 1, expected_size):
            raise E559Error("OBJECT_CONTENT_RANGE_MISMATCH", "Object header range does not match the frozen request")
        body = response.raw.read(HEADER_RANGE_BYTES + 1, decode_content=False)
        if len(body) != HEADER_RANGE_BYTES or body[:4] not in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"):
            raise E559Error("OBJECT_TIFF_HEADER_INVALID", "Object prefix is not a bounded TIFF/BigTIFF header")
        return {
            "http_status": 206,
            "content_range": response.headers.get("Content-Range"),
            "bytes_read": len(body),
            "prefix_sha256": hashlib.sha256(body).hexdigest(),
            "tiff_signature": body[:4].hex(),
        }
    finally:
        response.close()


def _sample_xy(dataset, latitude: float, longitude: float) -> tuple[float, float]:
    if dataset.crs is None:
        raise E559Error("MASK_CRS_MISSING", "Mask GeoTIFF has no CRS")
    if dataset.crs.is_geographic:
        return longitude, latitude
    xs, ys = reproject_xy("EPSG:4326", dataset.crs, [longitude], [latitude])
    return xs[0], ys[0]


def summarize_mask_window(values, layer: str, nodata) -> dict:
    arr = np.ma.asarray(values)
    data = np.asarray(arr.data)
    invalid = np.ma.getmaskarray(arr) | ~np.isfinite(data.astype(np.float64))
    if layer == "HEM":
        invalid |= data == -32767
    valid = data[~invalid]
    counts = {}
    if valid.size:
        unique, frequencies = np.unique(valid, return_counts=True)
        counts = {str(int(value)) if float(value).is_integer() else str(float(value)): int(count) for value, count in zip(unique, frequencies)}
    result = {
        "window_shape": [int(arr.shape[0]), int(arr.shape[1])],
        "valid_samples": int(valid.size),
        "masked_or_sentinel_samples": int(arr.size - valid.size),
        "nodata_metadata": None if nodata is None else float(nodata),
        "value_counts": counts,
        "raw_window_retained": False,
    }
    if valid.size:
        if layer in MASK_CLASSES:
            mapping = MASK_CLASSES[layer]
            result["class_counts"] = {
                mapping[int(value)]: count for value, count in counts.items()
                if int(float(value)) in mapping
            }
            result["unknown_values"] = sorted({
                int(float(value)) for value in counts if int(float(value)) not in mapping
            })
        else:
            numeric = valid.astype(np.float64)
            result.update({
                "height_error_min_m": float(np.min(numeric)),
                "height_error_median_m": float(np.median(numeric)),
                "height_error_max_m": float(np.max(numeric)),
            })
    center = arr[arr.shape[0] // 2, arr.shape[1] // 2]
    result["center_value"] = None if np.ma.is_masked(center) or not np.isfinite(float(center)) or (layer == "HEM" and float(center) == -32767) else float(center)
    return result


def sample_mask(dataset, layer: str, site: dict) -> dict:
    x, y = _sample_xy(dataset, float(site["latitude"]), float(site["longitude"]))
    row, col = dataset.index(x, y)
    half = WINDOW // 2
    row0, col0 = row - half, col - half
    row1, col1 = row + half + 1, col + half + 1
    if row0 < 0 or col0 < 0 or row1 > dataset.height or col1 > dataset.width:
        raise E559Error("MASK_WINDOW_OUTSIDE_TILE", "Frozen mask sample window crosses raster boundary")
    if not dataset.is_tiled:
        raise E559Error("MASK_NOT_TILED", "Mask is not tiled; a bounded raster window cannot be guaranteed")
    block_h, block_w = dataset.block_shapes[0]
    row_blocks = len(set(range(row0 // block_h, (row1 - 1) // block_h + 1)))
    col_blocks = len(set(range(col0 // block_w, (col1 - 1) // block_w + 1)))
    block_bytes = block_h * block_w * np.dtype(dataset.dtypes[0]).itemsize
    blocks = row_blocks * col_blocks
    estimated = blocks * block_bytes
    if estimated > MAX_BLOCK_UNCOMPRESSED_BYTES:
        raise E559Error(
            "MASK_BLOCK_BUDGET_EXCEEDED",
            "Required mask blocks exceed the 8 MB uncompressed read budget",
            {"blocks": blocks, "block_uncompressed_bytes": block_bytes, "estimated_bytes": estimated},
        )
    values = dataset.read(1, window=Window(col0, row0, WINDOW, WINDOW), masked=True)
    result = summarize_mask_window(values, layer, dataset.nodata)
    result.update({
        "site_id": site["site_id"],
        "site_role": site["role"],
        "latitude": float(site["latitude"]),
        "longitude": float(site["longitude"]),
        "pixel_row": int(row),
        "pixel_column": int(col),
        "blocks_touched": blocks,
        "block_shape": [int(block_h), int(block_w)],
        "estimated_uncompressed_block_bytes": int(estimated),
    })
    return result


def summarize_kml(body: bytes) -> dict:
    try:
        root = ET.fromstring(body)
    except ET.ParseError as error:
        raise E559Error("KML_XML_INVALID", "Public KML object is not valid XML") from error
    placemarks = [node for node in root.iter() if node.tag.rsplit("}", 1)[-1] == "Placemark"]
    features = []
    all_fields = set()
    for placemark in placemarks:
        name = ""
        fields = {}
        for node in placemark.iter():
            local = node.tag.rsplit("}", 1)[-1]
            if local == "name" and not name:
                name = (node.text or "").strip()
            if local in {"Data", "SimpleData"}:
                field_name = node.attrib.get("name")
                value_node = next((child for child in node if child.tag.rsplit("}", 1)[-1] == "value"), None)
                value = (value_node.text or "").strip() if value_node is not None else (node.text or "").strip()
                if field_name:
                    fields[field_name] = value
                    all_fields.add(field_name)
        features.append({"name": name, "fields": fields})
    return {
        "placemark_count": len(placemarks),
        "field_names": sorted(all_fields),
        "sample_features": features[:10],
        "raw_kml_retained": False,
    }


def read_small_kml(session: requests.Session, url: str, expected_size: int) -> dict:
    if expected_size > MAX_KML_BYTES:
        return {"outcome": "KML_EXCEEDS_1MB_BUDGET", "size_bytes": expected_size}
    response = session.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        timeout=(15, 45),
        allow_redirects=False,
    )
    if response.status_code in (301, 302, 303, 307, 308):
        raise E559Error("KML_REDIRECT_REFUSED", "KML object redirected; redirects are not followed")
    if response.status_code != 200 or response.url != url:
        raise E559Error(f"KML_HTTP_{response.status_code}", "KML object did not return exact HTTP 200")
    if len(response.content) != expected_size or len(response.content) > MAX_KML_BYTES:
        raise E559Error("KML_BODY_SIZE_MISMATCH", "KML response length differs from the S3 listing")
    result = summarize_kml(response.content)
    result["size_bytes"] = len(response.content)
    result["sha256"] = hashlib.sha256(response.content).hexdigest()
    return result


def run() -> dict:
    stem = tile_stem(float(SITES[0]["latitude"]), float(SITES[0]["longitude"]))
    tile_folder = stem
    session = requests.Session()
    prefix_results = {}
    all_objects = []
    for folder in (AUXFILES, PREVIEW):
        prefix = f"{tile_folder}/{folder}/"
        try:
            listing = list_prefix(session, prefix)
            prefix_results[folder] = listing
            all_objects.extend(listing["objects"])
        except E559Error as error:
            prefix_results[folder] = {
                "outcome": error.outcome,
                "message": str(error),
                "details": error.details,
                "full_prefix_enumerated": False,
            }
    expected = {layer: expected_key(f"{tile_folder}/", layer) for layer in LAYER_SUFFIXES}
    objects_by_key = {item["key"]: item for item in all_objects}
    exact_presence = {layer: key in objects_by_key for layer, key in expected.items()}
    samples = {}
    object_receipts = {}
    for layer in ("EDM", "FLM", "WBM", "HEM"):
        key = expected[layer]
        if key not in objects_by_key:
            continue
        entry = objects_by_key[key]
        url = object_url(key, f"{tile_folder}/{AUXFILES}/")
        head = head_object(session, url, int(entry["size_bytes"]))
        header = read_tiff_header(session, url, int(entry["size_bytes"]))
        object_receipts[layer] = {"key": key, "head": head, "header_range": header}
        with rasterio.Env(
            GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR",
            CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif",
            CPL_VSIL_CURL_USE_HEAD="YES",
            CPL_VSIL_CURL_CACHE_SIZE="0",
            CPL_VSIL_CURL_CHUNK_SIZE="16384",
            GDAL_HTTP_MAX_RETRY="0",
        ):
            with rasterio.open(f"/vsicurl/{url}") as dataset:
                if not dataset.is_tiled:
                    object_receipts[layer]["raster_metadata"] = {
                        "is_tiled": False,
                        "width": int(dataset.width),
                        "height": int(dataset.height),
                        "crs": str(dataset.crs),
                        "dtype": dataset.dtypes[0],
                    }
                    object_receipts[layer]["sample_outcome"] = "MASK_NOT_TILED"
                    continue
                object_receipts[layer]["raster_metadata"] = {
                    "is_tiled": True,
                    "width": int(dataset.width),
                    "height": int(dataset.height),
                    "crs": str(dataset.crs),
                    "epsg": dataset.crs.to_epsg() if dataset.crs else None,
                    "transform": [float(v) for v in dataset.transform[:6]],
                    "dtype": dataset.dtypes[0],
                    "nodata": dataset.nodata,
                    "block_shapes": [[int(a), int(b)] for a, b in dataset.block_shapes],
                }
                samples[layer] = [sample_mask(dataset, layer, site) for site in SITES]
    kml_receipts = {}
    for layer in ("ACM", "SRC"):
        key = expected[layer]
        if key not in objects_by_key:
            continue
        entry = objects_by_key[key]
        folder = AUXFILES if layer == "ACM" else PREVIEW
        url = object_url(key, f"{tile_folder}/{folder}/")
        head = head_object(session, url, int(entry["size_bytes"]))
        kml_receipts[layer] = {
            "key": key,
            "head": head,
            "summary": read_small_kml(session, url, int(entry["size_bytes"])),
        }
    found_masks = any(exact_presence[layer] for layer in ("EDM", "FLM", "WBM", "HEM"))
    found_lineage = any(exact_presence[layer] for layer in ("ACM", "SRC"))
    if found_masks and samples:
        outcome = "PUBLIC_QUALITY_MASKS_ACQUIRED_AND_SAMPLED"
    elif found_masks:
        outcome = "PUBLIC_QUALITY_MASK_OBJECTS_FOUND_METADATA_ONLY"
    elif found_lineage:
        outcome = "PUBLIC_LINEAGE_OBJECTS_FOUND"
    elif all(prefix_results.get(folder, {}).get("full_prefix_enumerated") for folder in (AUXFILES, PREVIEW)):
        outcome = "NO_EXPECTED_AUX_MASK_OR_LINEAGE_OBJECTS_IN_PUBLIC_PREFIX"
    else:
        outcome = "AUX_MASK_DISCOVERY_INCOMPLETE"
    return {
        "experiment": "E559 Copernicus GLO-30 AUXFILES quality-mask and source-lineage audit",
        "outcome": outcome,
        "source": {
            "product": "Copernicus DEM GLO-30 Public COG / DGED ancillary-layer naming convention",
            "publisher": "European Union / ESA Copernicus; DEM processing by Airbus Defence and Space",
            "bucket": "copernicus-dem-30m",
            "region": "eu-central-1",
            "tile_stem": stem,
            "tile_folder": tile_folder,
            "license": "Copernicus Licence; attribution required",
            "reference_handbook": "Copernicus DEM Product Handbook v5.0, 29 November 2022, section 1.2.8.1",
            "reference_handbook_url": "https://dataspace.copernicus.eu/sites/default/files/media/files/2024-06/geo1988-copernicusdem-spe-002_producthandbook_i5.0.pdf",
            "reference_dataset_band_definitions": "Google Earth Engine COPERNICUS/DEM/GLO30_2024_1 catalogue",
            "reference_dataset_url": "https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_DEM_GLO30_2024_1",
        },
        "frozen_listing_scope": {
            "prefixes": [f"{tile_folder}/{AUXFILES}/", f"{tile_folder}/{PREVIEW}/"],
            "max_keys_per_prefix": MAX_LISTING_KEYS,
            "max_listing_bytes": MAX_LISTING_BYTES,
            "redirects_followed": False,
            "credentials_used": False,
            "pagination_followed": False,
        },
        "prefix_listings": prefix_results,
        "expected_keys_from_handbook": expected,
        "exact_expected_key_presence": exact_presence,
        "object_receipts": object_receipts,
        "mask_samples": samples,
        "lineage_kml": kml_receipts,
        "raw_mask_pixels_retained": False,
        "raw_kml_retained": False,
        "raw_dem_retained": False,
        "actual_network_bytes": "NOT EXACTLY MEASURED",
        "interpretation": {
            "WBM": "0=no water, 1=ocean, 2=lake, 3=river; WBM identifies pixels edited as water bodies.",
            "FLM": "0=void, 1=edited except filled, 2=not edited/not filled, 3–9 and 100–101 identify fill-source classes.",
            "EDM": "0=void, 1=not edited, 2=external infill, 3=interpolated, 4=smoothed, 5=airport, 6=raised negative, 7=flattened, 8–10=water, 11=shoreline, 12=morphed, 13=shifted.",
            "HEM": "Height-error standard deviation; edited regions may use -32767 and must be interpreted with EDM/FLM.",
            "SRC": "Source Data Layer KML; source scene IDs, acquisition dates/times and height-of-ambiguity metadata may be present.",
            "ACM": "Accuracy-layer KML; global/geocell accuracy metadata is not a site-specific field validation.",
        },
        "claim_boundary": {
            "public_DSM_tile": "SUPPORTED by E557",
            "public_quality_mask_availability": (
                "SUPPORTED" if found_masks else
                "NOT FOUND IN COMPLETE PREFIX LISTING" if all(prefix_results.get(folder, {}).get("full_prefix_enumerated") for folder in (AUXFILES, PREVIEW))
                else "NOT YET MEASURED"
            ),
            "Lonar_water_or_fill_status": "MEASURED ONLY IF WBM/FLM/EDM samples are present; otherwise NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "local_validation_advantage": "NOT YET PROVEN",
        },
        "limitations": [
            "The DGED product handbook's folder/file structure is being checked against the actual legacy public COG bucket; product documentation does not guarantee that every ancillary object is exposed in that bucket.",
            "Only the exact N19/E076 tile's AUXFILES and PREVIEW prefixes are listed; no alternative filenames or paths are guessed.",
            "Only small 17×17 windows are read from tiled masks; non-tiled masks are not sampled.",
            "The two locations remain a literature lead and a nearby comparison point, not positive/negative analogue labels.",
            "Copernicus GLO-30 is a DSM, not a bare-earth DTM; water editing, fill sources, and local quality must remain explicit.",
            "The product handbook reports global accuracy statistics; they do not establish local Lonar accuracy.",
            "No raw DEM, mask pixels, or complete KML files are retained.",
        ],
        "next_gate": (
            "If WBM/EDM confirms the flat Lonar centre is water-edited and FLM/HEM/SRC expose the source lineage, reclassify the E557 centre sample as an edited-water DSM observation and run the coordinate-uncertainty-aware annulus on unedited terrain. "
            "If masks are absent from the exact public prefixes, stop guessing AWS paths and seek an independently documented product endpoint or another public terrain source."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": result["experiment"],
        "outcome": result["outcome"],
        "tile": result["source"]["tile_stem"],
        "expected_mask_keys_found": {
            key: value for key, value in result["exact_expected_key_presence"].items()
        },
        "sampled_layers": sorted(result["mask_samples"]),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
