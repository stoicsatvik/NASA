from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import struct
from pathlib import Path
from urllib.parse import urlsplit

import requests

CMR_ENDPOINT = "https://cmr.earthdata.nasa.gov/search/granules.umm_json"
COLLECTION_CONCEPT_ID = "C2763264762-LPCLOUD"
EXPECTED_TILE_BYTES = 3601 * 3601 * 2
TILE_SAMPLES = 3601
WINDOW = 17
VOID_SENTINEL = -32768
MAX_CMR_BYTES = 2_000_000
MAX_TOTAL_BODY_BYTES = 100_000
USER_AGENT = "Unified-Parallel-Foundry-E556/1.0"
DATA_HOST = "data.lpdaac.earthdatacloud.nasa.gov"
DATA_PREFIX = "/lp-prod-public/MEASURES/NASADEM_HGT.001/"

SITES = (
    {
        "site_id": "lonar_literature_lead",
        "latitude": 19.9750,
        "longitude": 76.5090,
        "role": "literature_lead_not_validated_positive",
    },
    {
        "site_id": "nearby_local_comparison_point",
        "latitude": 19.8000,
        "longitude": 76.3000,
        "role": "nearby_comparison_not_negative_label",
    },
)


class E556Error(RuntimeError):
    def __init__(self, outcome: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.outcome = outcome
        self.details = details or {}


def tile_name(latitude: float, longitude: float) -> str:
    if not (-56 <= latitude < 60) or not (-180 <= longitude < 180):
        raise ValueError("coordinate outside NASADEM HGT stated spatial extent")
    south = math.floor(latitude)
    west = math.floor(longitude)
    ns = "N" if south >= 0 else "S"
    ew = "E" if west >= 0 else "W"
    return f"{ns}{abs(south):02d}{ew}{abs(west):03d}"


def _bounded_body(response, cap: int) -> bytes:
    declared = response.headers.get("Content-Length")
    if declared:
        if not declared.isdigit() or int(declared) > cap:
            raise E556Error("CMR_RESPONSE_TOO_LARGE", "Declared CMR response exceeds the byte cap")
    body = response.raw.read(cap + 1, decode_content=False)
    if len(body) > cap:
        raise E556Error("CMR_RESPONSE_TOO_LARGE", "CMR response exceeded the byte cap")
    if declared and len(body) != int(declared):
        raise E556Error("CMR_LENGTH_MISMATCH", "CMR response length differs from Content-Length")
    return body


def _related_data_urls(umm: dict) -> list[str]:
    urls = []
    for item in umm.get("RelatedUrls", []) or []:
        kind = str(item.get("Type", "")).strip().lower()
        subtype = str(item.get("Subtype", "")).strip().lower()
        if kind in {"get data", "download data"} or "direct download" in subtype:
            url = item.get("URL")
            if isinstance(url, str):
                urls.append(url)
    return urls


def parse_cmr_tile(payload: dict, expected_tile: str) -> dict:
    items = payload.get("items")
    if not isinstance(items, list):
        raise E556Error("CMR_SCHEMA_INVALID", "CMR UMM response has no items list")
    matches = []
    for item in items:
        if not isinstance(item, dict):
            continue
        umm = item.get("umm") or {}
        granule_ur = str(umm.get("GranuleUR", ""))
        identifiers = (umm.get("DataGranule") or {}).get("Identifiers") or []
        if isinstance(identifiers, dict):
            identifiers = [identifiers]
        producer_id = str(identifiers[0].get("Identifier", "")) if identifiers and isinstance(identifiers[0], dict) else ""
        candidates = _related_data_urls(umm)
        identity = f"{granule_ur} {producer_id} " + " ".join(candidates)
        if expected_tile.lower() in identity.lower():
            matches.append({
                "granule_ur": granule_ur,
                "producer_granule_id": producer_id or None,
                "data_urls": candidates,
                "collection_concept_id": (item.get("meta") or {}).get("collection-concept-id"),
            })
    if not matches:
        raise E556Error(
            "CMR_TILE_NOT_FOUND",
            "CMR returned no NASADEM HGT granule matching the coordinate-derived tile",
            {"expected_tile": expected_tile, "returned_item_count": len(items)},
        )
    if len(matches) > 1:
        unique = {m["granule_ur"] for m in matches}
        if len(unique) > 1:
            raise E556Error(
                "CMR_TILE_AMBIGUOUS",
                "CMR returned multiple distinct granules for one coordinate-derived tile",
                {"expected_tile": expected_tile, "granule_urs": sorted(unique)},
            )
    return matches[0]


def validate_data_url(url: str, expected_tile: str) -> str:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != DATA_HOST
        or parsed.port not in (None, 443)
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise E556Error("DATA_URL_OUTSIDE_ALLOWLIST", "CMR data URL is outside the exact HTTPS host allowlist")
    if parsed.path.startswith("/lp-prod-protected/"):
        raise E556Error("EARTHDATA_AUTH_REQUIRED", "CMR returned a protected NASADEM path; no credentials will be used")
    if not parsed.path.startswith(DATA_PREFIX):
        raise E556Error("DATA_URL_PATH_UNSUPPORTED", "CMR data URL is not in the public NASADEM HGT collection path")
    basename = parsed.path.rsplit("/", 1)[-1]
    if expected_tile.lower() not in basename.lower() or not basename.lower().endswith(".hgt"):
        raise E556Error("DATA_URL_TILE_MISMATCH", "CMR direct URL does not identify the expected HGT tile")
    return url


def parse_content_range(value: str | None) -> tuple[int, int, int]:
    if not value or not value.startswith("bytes "):
        raise E556Error("CONTENT_RANGE_MISSING", "Range response omitted a valid Content-Range")
    try:
        span, total = value[6:].split("/", 1)
        start, end = span.split("-", 1)
        parsed = (int(start), int(end), int(total))
    except (ValueError, TypeError) as error:
        raise E556Error("CONTENT_RANGE_INVALID", "Content-Range is malformed") from error
    if min(parsed) < 0 or parsed[1] < parsed[0] or parsed[2] <= parsed[1]:
        raise E556Error("CONTENT_RANGE_INVALID", "Content-Range bounds are inconsistent")
    return parsed


def _read_range(session, url: str, start: int, end: int, expected_total: int, budget: dict) -> bytes:
    if start < 0 or end < start:
        raise E556Error("RANGE_INVALID", "Requested byte range is invalid")
    expected_length = end - start + 1
    if budget["body_bytes"] + expected_length > MAX_TOTAL_BODY_BYTES:
        raise E556Error("TRANSFER_BUDGET_EXCEEDED", "E556 transfer budget would be exceeded")
    response = session.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "identity",
            "Range": f"bytes={start}-{end}",
        },
        timeout=(15, 45),
        allow_redirects=False,
        stream=True,
    )
    try:
        if response.status_code in (301, 302, 303, 307, 308):
            raise E556Error("EARTHDATA_AUTH_REQUIRED", "NASADEM request redirected; redirects and login flows are not followed")
        if response.status_code in (401, 403):
            raise E556Error("EARTHDATA_AUTH_REQUIRED", f"NASADEM request returned HTTP {response.status_code}; no credentials will be used")
        if response.status_code == 200:
            raise E556Error("RANGE_IGNORED", "Server ignored the Range header; response body was not consumed")
        if response.status_code != 206:
            raise E556Error(f"DATA_HTTP_{response.status_code}", "NASADEM range request did not return HTTP 206")
        if response.url != url:
            raise E556Error("DATA_FINAL_URL_CHANGED", "NASADEM response URL differs from the pinned CMR URL")
        start_got, end_got, total_got = parse_content_range(response.headers.get("Content-Range"))
        if (start_got, end_got, total_got) != (start, end, expected_total):
            raise E556Error(
                "CONTENT_RANGE_MISMATCH",
                "NASADEM Content-Range differs from the exact requested span or expected HGT tile size",
                {"expected": [start, end, expected_total], "actual": [start_got, end_got, total_got]},
            )
        declared = response.headers.get("Content-Length")
        if declared and (not declared.isdigit() or int(declared) != expected_length):
            raise E556Error("RANGE_LENGTH_MISMATCH", "Range Content-Length differs from the requested byte count")
        body = response.raw.read(expected_length + 1, decode_content=False)
        if len(body) != expected_length:
            raise E556Error("RANGE_BODY_LENGTH_MISMATCH", "Range body length differs from the requested byte count")
        budget["body_bytes"] += len(body)
        budget["requests"] += 1
        return body
    finally:
        response.close()


def _pixel_spacing(latitude: float) -> tuple[float, float]:
    lat = math.radians(latitude)
    metres_per_degree_lat = 111132.92 - 559.82 * math.cos(2 * lat) + 1.175 * math.cos(4 * lat)
    metres_per_degree_lon = 111412.84 * math.cos(lat) - 93.5 * math.cos(3 * lat)
    return metres_per_degree_lon / 3600.0, metres_per_degree_lat / 3600.0


def _summarize_patch(rows: list[list[int]], latitude: float, longitude: float, row0: int, col0: int, patch_digest: str) -> dict:
    values = [value for row in rows for value in row]
    void_count = sum(value == VOID_SENTINEL for value in values)
    valid = [value for value in values if value != VOID_SENTINEL]
    dx, dy = _pixel_spacing(latitude)
    mid = len(rows) // 2
    slope_deg = None
    if len(rows) >= 3 and all(rows[r][c] != VOID_SENTINEL for r in range(mid - 1, mid + 2) for c in range(mid - 1, mid + 2)):
        a, b, c = rows[mid - 1][mid - 1:mid + 2]
        d, _, f = rows[mid][mid - 1:mid + 2]
        g, h, i = rows[mid + 1][mid - 1:mid + 2]
        dzdx = ((c + 2 * f + i) - (a + 2 * d + g)) / (8.0 * dx)
        dzdy = ((g + 2 * h + i) - (a + 2 * b + c)) / (8.0 * dy)
        slope_deg = math.degrees(math.atan(math.hypot(dzdx, dzdy)))
    result = {
        "site_id": None,
        "latitude": latitude,
        "longitude": longitude,
        "tile": tile_name(latitude, longitude),
        "pixel_row": row0,
        "pixel_column": col0,
        "window_samples": len(rows),
        "pixel_spacing_approx_m": {"east_west": dx, "north_south": dy},
        "window_extent_approx_m": {"east_west": (len(rows[0]) - 1) * dx, "north_south": (len(rows) - 1) * dy},
        "void_sentinel": VOID_SENTINEL,
        "void_sentinel_count": void_count,
        "valid_sample_count": len(valid),
        "patch_sha256": patch_digest,
        "raw_patch_retained": False,
    }
    if valid:
        result.update({
            "elevation_min_m": min(valid),
            "elevation_median_m": statistics.median(valid),
            "elevation_mean_m": statistics.fmean(valid),
            "elevation_population_sd_m": statistics.pstdev(valid),
            "elevation_max_m": max(valid),
            "local_relief_m": max(valid) - min(valid),
            "central_horn_slope_deg": slope_deg,
        })
    else:
        result["outcome"] = "ALL_VOID_SENTINEL"
    return result


def sample_patch(session, url: str, site: dict, budget: dict) -> dict:
    latitude = float(site["latitude"])
    longitude = float(site["longitude"])
    tile = tile_name(latitude, longitude)
    south = math.floor(latitude)
    west = math.floor(longitude)
    row0 = round((south + 1 - latitude) * 3600)
    col0 = round((longitude - west) * 3600)
    half = WINDOW // 2
    r0, r1 = row0 - half, row0 + half
    c0, c1 = col0 - half, col0 + half
    if r0 < 0 or c0 < 0 or r1 >= TILE_SAMPLES or c1 >= TILE_SAMPLES:
        raise E556Error("PATCH_OUTSIDE_TILE", "Requested patch crosses the HGT tile boundary")
    rows = []
    digest = hashlib.sha256()
    for row_index in range(r0, r1 + 1):
        start = (row_index * TILE_SAMPLES + c0) * 2
        end = (row_index * TILE_SAMPLES + c1 + 1) * 2 - 1
        body = _read_range(session, url, start, end, EXPECTED_TILE_BYTES, budget)
        digest.update(body)
        rows.append(list(struct.unpack(">" + "h" * WINDOW, body)))
    summary = _summarize_patch(rows, latitude, longitude, row0, col0, digest.hexdigest())
    summary["site_id"] = site["site_id"]
    summary["site_role"] = site["role"]
    return summary


def query_site(session, site: dict) -> dict:
    tile = tile_name(float(site["latitude"]), float(site["longitude"]))
    response = session.get(
        CMR_ENDPOINT,
        params={
            "collection_concept_id": COLLECTION_CONCEPT_ID,
            "point": f'{site["longitude"]:.6f},{site["latitude"]:.6f}',
            "page_size": 10,
        },
        headers={"User-Agent": USER_AGENT, "Accept": "application/vnd.nasa.cmr.umm_results+json"},
        timeout=(15, 45),
        allow_redirects=False,
        stream=True,
    )
    try:
        if response.status_code in (301, 302, 303, 307, 308):
            raise E556Error("CMR_REDIRECT", "CMR metadata request redirected unexpectedly")
        if response.status_code != 200:
            raise E556Error(f"CMR_HTTP_{response.status_code}", "CMR metadata request did not return HTTP 200")
        body = _bounded_body(response, MAX_CMR_BYTES)
        payload = json.loads(body.decode("utf-8"))
        granule = parse_cmr_tile(payload, tile)
        granule["cmr_response_bytes"] = len(body)
        granule["cmr_response_sha256"] = hashlib.sha256(body).hexdigest()
        return {"site_id": site["site_id"], "tile": tile, "granule": granule}
    finally:
        response.close()


def run() -> dict:
    session = requests.Session()
    budget = {"body_bytes": 0, "requests": 0}
    site_metadata = []
    try:
        for site in SITES:
            site_metadata.append(query_site(session, site))
        urls = {}
        protected_paths = []
        for item in site_metadata:
            tile = item["tile"]
            if tile in urls:
                continue
            candidates = item["granule"]["data_urls"]
            safe = []
            failures = []
            for candidate in candidates:
                parsed = urlsplit(candidate)
                if (
                    parsed.scheme == "https"
                    and parsed.hostname == DATA_HOST
                    and parsed.path.startswith("/lp-prod-protected/")
                    and tile.lower() in parsed.path.lower()
                ):
                    protected_paths.append({
                        "tile": tile,
                        "host": parsed.hostname,
                        "path": parsed.path,
                        "query_present": bool(parsed.query),
                    })
                try:
                    safe.append(validate_data_url(candidate, tile))
                except E556Error as error:
                    failures.append(error.outcome)
            if safe:
                urls[tile] = safe[0]
            elif "EARTHDATA_AUTH_REQUIRED" in failures:
                raise E556Error(
                    "EARTHDATA_AUTH_REQUIRED",
                    "CMR exposes only a protected NASADEM HGT path; no credentials will be used",
                    {
                        "cmr_sites": [
                            {
                                "site_id": record["site_id"],
                                "tile": record["tile"],
                                "granule_ur": record["granule"]["granule_ur"],
                                "cmr_response_bytes": record["granule"]["cmr_response_bytes"],
                                "cmr_response_sha256": record["granule"]["cmr_response_sha256"],
                            }
                            for record in site_metadata
                        ],
                        "protected_paths": protected_paths,
                    },
                )
        if not urls:
            raise E556Error(
                "NO_ALLOWLISTED_PUBLIC_DATA_URL",
                "CMR identified the tile but did not expose an allowlisted public direct HGT URL",
                {"tiles": sorted({item["tile"] for item in site_metadata})},
            )
        tile = site_metadata[0]["tile"]
        url = urls.get(tile)
        if not url:
            raise E556Error("NO_ALLOWLISTED_PUBLIC_DATA_URL", "No allowlisted public URL exists for the candidate tile")
        url = validate_data_url(url, tile)
        probe = _read_range(session, url, 0, 1, EXPECTED_TILE_BYTES, budget)
        if len(probe) != 2:
            raise E556Error("PROBE_INVALID", "HGT header probe did not return exactly two bytes")
        samples = [sample_patch(session, url, site, budget) for site in SITES]
        return {
            "experiment": "E556 NASADEM HGT candidate/control-point access and bounded elevation sample",
            "outcome": "PUBLIC_TILE_RANGE_ACCESS_AND_PATCH_SAMPLE_SUPPORTED",
            "source": {
                "collection": "NASADEM Merged DEM Global 1 arc second V001",
                "doi": "10.5067/MEASURES/NASADEM/NASADEM_HGT.001",
                "collection_concept_id": COLLECTION_CONCEPT_ID,
                "provider": "NASA LP DAAC",
                "nominal_spacing": "1 arc-second; approximately 30 m at the equator",
                "tile_grid": "1 degree × 1 degree; 3601 × 3601 signed 16-bit HGT samples",
                "elevation_units": "metres",
                "vertical_reference": "EGM96 geoid, subject to product guide verification",
                "source_sensor_period": "SRTM mission, 11–21 February 2000",
                "provenance_note": "NASADEM is a reprocessed/merged elevation product using SRTM telemetry and auxiliary control/elevation sources; it is not a raw single-instrument measurement.",
                "public_data_host": DATA_HOST,
                "public_data_path": urlsplit(url).path,
            },
            "cmr": site_metadata,
            "range_probe": {
                "http_status": 206,
                "content_range_expected_total_bytes": EXPECTED_TILE_BYTES,
                "first_two_bytes_sha256": hashlib.sha256(probe).hexdigest(),
            },
            "samples": samples,
            "transfer": {
                "range_requests": budget["requests"],
                "response_body_bytes": budget["body_bytes"],
                "hard_body_byte_budget": MAX_TOTAL_BODY_BYTES,
                "raw_raster_retained": False,
                "raw_cmr_metadata_retained": False,
                "credentials_used": False,
                "redirects_followed": False,
            },
            "claim_boundary": {
                "nasadem_tile_access": "SUPPORTED for this public product/tile if exact range validation passes",
                "lonar_literature_lead": "NOT A VALIDATED POSITIVE LABEL",
                "nearby_deccan_comparison": "NOT A VALIDATED NEGATIVE LABEL",
                "earth_site_terrain_descriptors": "MEASURED DESCRIPTIVE SAMPLES ONLY",
                "cross_body_similarity": "NOT YET PROVEN",
                "known_site_recovery": "NOT YET MEASURED",
                "novel_analogue_discovery": "NOT YET PROVEN",
                "local_validation_advantage": "NOT YET PROVEN",
            },
            "limitations": [
                "Two local terrain samples do not form an independently labelled analogue/control dataset.",
                "A single 17×17 patch is descriptive and cannot establish site-level terrain distributions.",
                "The two points are a literature lead and nearby comparison, not positive/negative ground truth.",
                "No MOLA/CTX/HiRISE common-support registration or E001 ranking is performed.",
                "The conventional -32768 HGT void sentinel is counted separately; product-specific fill semantics must be checked against the current user guide before broader use.",
            ],
            "next_gate": "Use the NASADEM NUM/source-count layer and independently sourced Earth-site labels/controls; then aggregate DEM and planetary data to matched physical footprints before E001.",
        }
    except E556Error as error:
        return {
            "experiment": "E556 NASADEM HGT candidate/control-point access and bounded elevation sample",
            "outcome": error.outcome,
            "message": str(error),
            "details": error.details,
            "transfer": {
                "range_requests": budget["requests"],
                "response_body_bytes": budget["body_bytes"],
                "hard_body_byte_budget": MAX_TOTAL_BODY_BYTES,
                "raw_raster_retained": False,
                "raw_cmr_metadata_retained": False,
                "credentials_used": False,
                "redirects_followed": False,
            },
            "claim_boundary": {
                "cross_body_similarity": "NOT YET PROVEN",
                "known_site_recovery": "NOT YET MEASURED",
                "novel_analogue_discovery": "NOT YET PROVEN",
                "local_validation_advantage": "NOT YET PROVEN",
            },
            "next_gate": "Preserve the exact access failure; do not use credentials or substitute unverified data.",
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
        "site_count": len(result.get("samples", [])),
        "range_requests": result.get("transfer", {}).get("range_requests", 0),
        "response_body_bytes": result.get("transfer", {}).get("response_body_bytes", 0),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
