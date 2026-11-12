"""E594: bounded, credentialless NASA FIRMS MODIS/VIIRS recent-file probe."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import urllib.error
import urllib.request
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit

MAX_BYTES = 256 * 1024
TIMEOUT_SECONDS = 25
ROOT_LISTING_URL = "https://firms.modaps.eosdis.nasa.gov/data/active_fire/"
ALLOWED_HOST = "firms.modaps.eosdis.nasa.gov"
SOURCES = {
    "MODIS_C61": {
        "platform": "Terra/Aqua",
        "nominal_product_resolution": "about 1 km",
        "url": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_7d.csv",
    },
    "VIIRS_SNPP": {
        "platform": "Suomi-NPP",
        "nominal_product_resolution": "375 m",
        "product_coverage_end": "2026-11-02",
        "url": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/viirs-npp-1/csv/VIIRS_SNPP_NRT_Global_7d.csv",
    },
}
COMMON_FIELDS = {
    "latitude", "longitude", "acq_date", "acq_time", "satellite",
    "confidence", "version", "frp", "daynight",
}


class StrictRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def validate_url(url: str) -> None:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_HOST
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.port not in (None, 443)
        or not parsed.path.startswith("/data/active_fire/")
    ):
        raise ValueError("URL outside the fixed public FIRMS download boundary")


def summarize_csv_prefix(payload: bytes) -> dict:
    text = payload.decode("utf-8-sig", errors="replace")
    stream = io.StringIO(text)
    reader = csv.reader(stream)
    try:
        header = [name.strip().lower() for name in next(reader)]
    except StopIteration:
        return {"is_csv": False, "reason": "empty_payload"}
    if len(header) < 8 or len(set(header)) != len(header):
        return {"is_csv": False, "reason": "invalid_header", "header": header[:40]}

    rows = []
    incomplete = 0
    for row in reader:
        if not row or all(not value.strip() for value in row):
            continue
        if len(row) != len(header):
            incomplete += 1
            continue
        rows.append(dict(zip(header, (value.strip() for value in row))))

    lat_values, lon_values, dates, frp_values = [], [], [], []
    valid_coordinates = valid_date_time = 0
    confidence = {}
    satellite = set()
    instrument = set()
    for row in rows:
        try:
            lat = float(row.get("latitude", ""))
            lon = float(row.get("longitude", ""))
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                valid_coordinates += 1
                lat_values.append(lat)
                lon_values.append(lon)
        except (TypeError, ValueError):
            pass
        raw_date = row.get("acq_date", "")
        raw_time = row.get("acq_time", "")
        try:
            date.fromisoformat(raw_date)
            if re.fullmatch(r"\d{1,4}", raw_time) and int(raw_time) <= 2359:
                valid_date_time += 1
                dates.append(raw_date)
        except ValueError:
            pass
        value = row.get("frp", "")
        try:
            number = float(value)
            if number >= 0:
                frp_values.append(number)
        except (TypeError, ValueError):
            pass
        if row.get("confidence"):
            confidence[row["confidence"]] = confidence.get(row["confidence"], 0) + 1
        if row.get("satellite"):
            satellite.add(row["satellite"])
        if row.get("instrument"):
            instrument.add(row["instrument"])

    return {
        "is_csv": True,
        "header": header,
        "row_count_in_prefix": len(rows),
        "incomplete_rows_dropped": incomplete,
        "common_field_coverage": sorted(COMMON_FIELDS.intersection(header)),
        "missing_common_fields": sorted(COMMON_FIELDS.difference(header)),
        "brightness_fields": sorted(
            field for field in header
            if field in {"brightness", "bright_t31", "bright_ti4", "bright_ti5"}
        ),
        "valid_coordinate_rows": valid_coordinates,
        "latitude_bounds_in_prefix": (
            [round(min(lat_values), 6), round(max(lat_values), 6)] if lat_values else None
        ),
        "longitude_bounds_in_prefix": (
            [round(min(lon_values), 6), round(max(lon_values), 6)] if lon_values else None
        ),
        "valid_date_time_rows": valid_date_time,
        "acquisition_date_bounds_in_prefix": [min(dates), max(dates)] if dates else None,
        "satellite_values": sorted(satellite),
        "instrument_values": sorted(instrument),
        "confidence_value_counts": dict(sorted(confidence.items())),
        "frp_nonnegative_rows": len(frp_values),
        "frp_bounds_in_prefix": (
            [round(min(frp_values), 6), round(max(frp_values), 6)] if frp_values else None
        ),
        "raw_observations_retained": False,
        "raw_coordinates_retained": False,
    }


def probe_source(name: str, config: dict) -> dict:
    url = config["url"]
    validate_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Foundry-E594/1.0 (bounded public-data provenance probe)",
            "Accept": "text/csv,text/plain,*/*",
            "Range": f"bytes=0-{MAX_BYTES - 1}",
        },
    )
    result = {
        "source": name,
        "platform": config["platform"],
        "nominal_product_resolution": config["nominal_product_resolution"],
        "source_url": url,
        "credentials_sent": False,
        "earthdata_login_used": False,
        "map_key_used": False,
        "access_state": "NOT_ACQUIRED",
    }
    opener = urllib.request.build_opener(StrictRedirectHandler())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            final_url = response.geturl()
            validate_url(final_url)
            payload = response.read(MAX_BYTES + 1)
            headers = response.headers
            result.update({
                "http_status": response.status,
                "content_type": headers.get_content_type(),
                "content_length_header": headers.get("Content-Length"),
                "content_range_header": headers.get("Content-Range"),
                "last_modified_header": headers.get("Last-Modified"),
                "etag_present": bool(headers.get("ETag")),
                "last_modified_present": bool(headers.get("Last-Modified")),
                "final_host": urlsplit(final_url).hostname,
                "prefix_bytes": min(len(payload), MAX_BYTES),
                "prefix_sha256": hashlib.sha256(payload[:MAX_BYTES]).hexdigest(),
                "prefix_truncated_by_probe": len(payload) > MAX_BYTES or (
                    headers.get("Content-Range") is not None
                    and headers.get("Content-Range").rsplit("/", 1)[-1].isdigit()
                    and int(headers.get("Content-Range").rsplit("/", 1)[-1]) > min(len(payload), MAX_BYTES)
                ) or (
                    headers.get("Content-Length") is not None
                    and int(headers.get("Content-Length")) > MAX_BYTES
                ),
            })
            parsed = summarize_csv_prefix(payload[:MAX_BYTES])
            result["sample"] = parsed
            if response.status in (200, 206) and result["content_type"] in {
                "text/csv", "text/plain", "application/octet-stream"
            } and parsed.get("is_csv") and not parsed.get("missing_common_fields"):
                result["access_state"] = "ACCESSIBLE_BOUNDED_CSV_PREFIX"
            else:
                result["access_state"] = "HTTP_RESPONSE_BUT_SAMPLE_NOT_ADMISSIBLE"
    except urllib.error.HTTPError as error:
        result.update({
            "http_status": error.code,
            "access_state": "HTTP_ERROR",
            "content_type": error.headers.get_content_type() if error.headers else None,
            "final_host": urlsplit(error.geturl()).hostname,
        })
        error.close()
    except Exception as error:
        result.update({
            "access_state": "TRANSPORT_OR_POLICY_ERROR",
            "error_type": type(error).__name__,
        })
    return result



class _HrefCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            for key, value in attrs:
                if key.lower() == "href" and value:
                    self.hrefs.append(value)


def probe_directory_listing(url: str) -> dict:
    validate_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Foundry-E594/1.0 (bounded public-directory discovery)",
            "Accept": "text/html,*/*",
            "Range": f"bytes=0-{MAX_BYTES - 1}",
        },
    )
    result = {"url": url, "status": None, "content_type": None, "links": []}
    opener = urllib.request.build_opener(StrictRedirectHandler())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read(MAX_BYTES + 1)
            result.update({
                "status": response.status,
                "content_type": response.headers.get_content_type(),
                "prefix_bytes": min(len(payload), MAX_BYTES),
                "last_modified": response.headers.get("Last-Modified"),
            })
            if result["content_type"] != "text/html":
                return result
            parser = _HrefCollector()
            parser.feed(payload[:MAX_BYTES].decode("utf-8", errors="replace"))
            links = []
            for href in parser.hrefs:
                try:
                    candidate = urljoin(url, href)
                    validate_url(candidate)
                    if candidate not in links:
                        links.append(candidate)
                except ValueError:
                    continue
            result["links"] = sorted(links)[:100]
    except urllib.error.HTTPError as error:
        result.update({
            "status": error.code,
            "content_type": error.headers.get_content_type() if error.headers else None,
        })
        error.close()
    except Exception as error:
        result["error_type"] = type(error).__name__
    return result


def discover_viirs_csv_candidates() -> dict:
    root = probe_directory_listing(ROOT_LISTING_URL)
    listings = []
    candidates = []
    viirs_dirs = [
        url for url in root.get("links", [])
        if url.endswith("/") and "viirs" in urlsplit(url).path.lower()
    ][:3]
    for directory in viirs_dirs:
        first = probe_directory_listing(directory)
        listings.append(first)
        direct = first.get("links", [])
        child_dirs = [
            url for url in direct
            if url.endswith("/") and urlsplit(url).path.rstrip("/").split("/")[-1].lower() in {"csv", "text", "global"}
        ][:2]
        for child in child_dirs:
            second = probe_directory_listing(child)
            listings.append(second)
            direct.extend(second.get("links", []))
        for url in direct:
            name = urlsplit(url).path.rsplit("/", 1)[-1]
            if (
                "viirs" in name.lower()
                and name.lower().endswith(".csv")
                and ("global_7d" in name.lower() or "global_24h" in name.lower())
                and url not in candidates
            ):
                candidates.append(url)
    return {
        "root_listing": {k: v for k, v in root.items() if k != "links"} | {
            "viirs_directories": viirs_dirs
        },
        "directory_listings": [
            {k: v for k, v in item.items() if k != "links"} | {
                "viirs_subdirectories": [
                    url for url in item.get("links", [])
                    if url.endswith("/") and urlsplit(url).path.rstrip("/").split("/")[-1].lower() in {"csv", "text", "global"}
                ],
                "csv_candidates": [
                    url for url in item.get("links", [])
                    if url.lower().endswith(".csv") and "viirs" in url.lower()
                ],
            }
            for item in listings
        ],
        "candidate_urls": sorted(candidates)[:6],
    }

def run_probe() -> dict:
    results = [probe_source(name, config) for name, config in SOURCES.items()]
    directory_discovery = discover_viirs_csv_candidates()
    for index, url in enumerate(directory_discovery["candidate_urls"]):
        filename = urlsplit(url).path.rsplit("/", 1)[-1]
        platform = "NOAA-20" if "NOAA20" in filename.upper() else (
            "NOAA-21" if "NOAA21" in filename.upper() else "Suomi-NPP"
        )
        name = "VIIRS_DISCOVERED_" + str(index + 1)
        results.append(probe_source(name, {
            "platform": platform,
            "nominal_product_resolution": "375 m",
            "url": url,
        }))
    modis_ok = any(
        item["source"].startswith("MODIS_") and item["access_state"] == "ACCESSIBLE_BOUNDED_CSV_PREFIX"
        for item in results
    )
    viirs_ok = any(
        item["source"].startswith("VIIRS_") and item["access_state"] == "ACCESSIBLE_BOUNDED_CSV_PREFIX"
        for item in results
    )
    current_viirs_ok = any(
        item["source"].startswith("VIIRS_")
        and item["platform"] in {"NOAA-20", "NOAA-21"}
        and item["access_state"] == "ACCESSIBLE_BOUNDED_CSV_PREFIX"
        for item in results
    )
    successful = [
        item for item in results
        if item["access_state"] == "ACCESSIBLE_BOUNDED_CSV_PREFIX"
    ]
    common = set.intersection(*[
        set(item["sample"]["header"]) for item in successful
    ]) if len(successful) >= 2 else set()
    return {
        "experiment": "E594",
        "date": "2026-11-12",
        "source_page": "https://firms.modaps.eosdis.nasa.gov/content/active_fire/",
        "source_page_claim": "official FIRMS page advertises 24 h, 48 h and 7 day products; the two-month daily HTTPS text folder requires Earthdata Login; S-NPP product coverage ends 2026-11-02",
        "request_policy": {
            "max_prefix_bytes_per_product": MAX_BYTES,
            "range_request": True,
            "credentials_sent": False,
            "earthdata_login_used": False,
            "map_key_used": False,
            "raw_observations_retained": False,
            "raw_coordinates_retained": False,
        },
        "directory_discovery": directory_discovery,
        "products": results,
        "recent_modis_access_supported": modis_ok,
        "viirs_keyless_7d_file_access_supported": viirs_ok,
        "viirs_current_coverage_available": current_viirs_ok,
        "both_sensor_families_keyless_7d_file_access": modis_ok and viirs_ok,
        "common_fields_across_successful_products": sorted(common),
        "interpretation": (
            "Keyless 7-day file access is supported for MODIS and at least one VIIRS endpoint. "
            "Current VIIRS coverage is supported only if a NOAA-20/NOAA-21 endpoint was discovered and sampled. "
            "This does not establish archive access, complete seven-day coverage, detection equivalence, "
            "cross-sensor bias correction or a validated harmonization model."
            if modis_ok and viirs_ok else
            "Preserve endpoint-specific access results. MODIS access can be supported independently; "
            "failed S-NPP or NOAA candidate paths do not prove that all VIIRS products are unavailable."
        ),
        "claim_state": {
            "recent_modis_keyless_access": "SUPPORTED" if modis_ok else "NOT_YET_ESTABLISHED",
            "viirs_snpp_keyless_7d_file_access": "SUPPORTED" if any(item["source"] == "VIIRS_SNPP" and item["access_state"] == "ACCESSIBLE_BOUNDED_CSV_PREFIX" for item in results) else "NOT_YET_ESTABLISHED",
            "viirs_noaa20_21_keyless_recent_file_access": "SUPPORTED" if current_viirs_ok else "NOT_YET_ESTABLISHED",
            "current_viirs_product_coverage": "SUPPORTED_FOR_NOAA20_21" if current_viirs_ok else "ENDED_2026-11-02_FOR_SNPP; NOAA20_21_NOT_YET_ESTABLISHED",
            "cross_sensor_harmonization": "NOT_YET_PROVEN",
            "historical_archive_keyless_access": "NOT_YET_PROVEN",
            "challenge_selection_superiority": "NOT_YET_PROVEN",
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    payload = json.dumps(run_probe(), indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
