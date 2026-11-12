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
from pathlib import Path
from urllib.parse import urlsplit

MAX_BYTES = 256 * 1024
TIMEOUT_SECONDS = 25
ALLOWED_HOST = "firms.modaps.eosdis.nasa.gov"
SOURCES = {
    "MODIS_C61": {
        "platform": "Terra/Aqua",
        "nominal_product_resolution": "about 1 km",
        "url": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/MODIS_C6_1_Global_7d.csv",
    },
    "VIIRS_NOAA20": {
        "platform": "NOAA-20",
        "nominal_product_resolution": "375 m",
        "url": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/viirs-noaa20-1/csv/VIIRS_NOAA20_NRT_Global_7d.csv",
    },
    "VIIRS_NOAA21": {
        "platform": "NOAA-21",
        "nominal_product_resolution": "375 m",
        "url": "https://firms.modaps.eosdis.nasa.gov/data/active_fire/viirs-noaa21-1/csv/VIIRS_NOAA21_NRT_Global_7d.csv",
    },
}
COMMON_FIELDS = {
    "latitude", "longitude", "acq_date", "acq_time", "satellite",
    "instrument", "confidence", "version", "frp", "daynight",
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
                "etag_present": bool(headers.get("ETag")),
                "last_modified_present": bool(headers.get("Last-Modified")),
                "final_host": urlsplit(final_url).hostname,
                "prefix_bytes": min(len(payload), MAX_BYTES),
                "prefix_sha256": hashlib.sha256(payload[:MAX_BYTES]).hexdigest(),
                "prefix_truncated_by_probe": len(payload) > MAX_BYTES or (
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


def run_probe() -> dict:
    results = [probe_source(name, config) for name, config in SOURCES.items()]
    modis_ok = any(
        item["source"].startswith("MODIS_") and item["access_state"] == "ACCESSIBLE_BOUNDED_CSV_PREFIX"
        for item in results
    )
    viirs_ok = any(
        item["source"].startswith("VIIRS_") and item["access_state"] == "ACCESSIBLE_BOUNDED_CSV_PREFIX"
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
        "source_page_claim": "official FIRMS page advertises 24 h, 48 h and 7 day products; its two-month daily HTTPS text folder requires Earthdata Login",
        "request_policy": {
            "max_prefix_bytes_per_product": MAX_BYTES,
            "range_request": True,
            "credentials_sent": False,
            "earthdata_login_used": False,
            "map_key_used": False,
            "raw_observations_retained": False,
            "raw_coordinates_retained": False,
        },
        "products": results,
        "recent_modis_access_supported": modis_ok,
        "recent_viirs_access_supported": viirs_ok,
        "both_sensor_families_accessible": modis_ok and viirs_ok,
        "common_fields_across_successful_products": sorted(common),
        "interpretation": (
            "Recent keyless sample access is supported for the exact successful product endpoints only. "
            "This does not establish archive access, complete seven-day coverage, detection equivalence, "
            "cross-sensor bias correction or a validated harmonization model."
            if modis_ok and viirs_ok else
            "At least one sensor-family endpoint did not yield an admissible bounded CSV sample. "
            "Preserve endpoint-specific access results; do not infer that all FIRMS products are unavailable."
        ),
        "claim_state": {
            "recent_modis_keyless_access": "SUPPORTED" if modis_ok else "NOT_YET_ESTABLISHED",
            "recent_viirs_keyless_access": "SUPPORTED" if viirs_ok else "NOT_YET_ESTABLISHED",
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
