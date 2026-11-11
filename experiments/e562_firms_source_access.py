"""E562: bounded, credential-free NASA FIRMS data-access audit.

This experiment separates a public static VIIRS sample from the live/historical
FIRMS paths. It never creates, reads, or transmits credentials and stores only
a compact provenance receipt, never the downloaded sample rows.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SAMPLE_URL = (
    "https://firms.modaps.eosdis.nasa.gov/content/notebooks/"
    "sample_viirs_snpp_071223.csv"
)
DAILY_URL = (
    "https://nrt3.modaps.eosdis.nasa.gov/archive/FIRMS/noaa-20-viirs-c2/"
    "South_Asia/J1_VIIRS_C2_South_Asia_VJ114IMGTDL_NRT_2026312.txt"
)
NO_KEY_API_URL = (
    "https://firms.modaps.eosdis.nasa.gov/api/area/csv/NO_KEY/"
    "VIIRS_NOAA20_NRT/0,0,1,1/1"
)
ALLOWED_HOSTS = {
    "firms.modaps.eosdis.nasa.gov",
    "nrt3.modaps.eosdis.nasa.gov",
}
MAX_SAMPLE_BYTES = 8_000_000
MAX_PROBE_BYTES = 2_048
EXPECTED_SAMPLE_ROWS = 74_605
EXPECTED_FIELDS = {
    "latitude", "longitude", "bright_ti4", "scan", "track", "acq_date",
    "acq_time", "satellite", "instrument", "confidence", "version",
    "bright_ti5", "frp", "daynight",
}


@dataclass(frozen=True)
class FetchResult:
    status: int | None
    content_type: str | None
    body: bytes
    bytes_read: int
    truncated: bool
    redirect_seen: bool
    error: str | None = None


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def validate_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        raise ValueError("URL is outside the pinned HTTPS source allowlist")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("credentials, query strings and fragments are forbidden")


def fetch_url(url: str, max_bytes: int) -> FetchResult:
    validate_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Unified-Foundry-E562/1.0",
            "Accept": "text/csv,text/plain,application/octet-stream,*/*",
        },
        method="GET",
    )
    opener = urllib.request.build_opener(NoRedirectHandler())
    try:
        response = opener.open(request, timeout=25)
        with response:
            status = int(response.status)
            content_type = response.headers.get("Content-Type")
            data = response.read(max_bytes + 1)
            truncated = len(data) > max_bytes
            if truncated:
                data = data[:max_bytes]
            return FetchResult(
                status=status,
                content_type=content_type,
                body=data,
                bytes_read=len(data),
                truncated=truncated,
                redirect_seen=False,
            )
    except urllib.error.HTTPError as exc:
        data = exc.read(max_bytes + 1)
        truncated = len(data) > max_bytes
        if truncated:
            data = data[:max_bytes]
        return FetchResult(
            status=int(exc.code),
            content_type=exc.headers.get("Content-Type") if exc.headers else None,
            body=data,
            bytes_read=len(data),
            truncated=truncated,
            redirect_seen=300 <= int(exc.code) < 400,
        )
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return FetchResult(
            status=None,
            content_type=None,
            body=b"",
            bytes_read=0,
            truncated=False,
            redirect_seen=False,
            error=type(exc).__name__,
        )


def _text(result: FetchResult) -> str:
    return result.body.decode("utf-8-sig", errors="replace")


def parse_sample_summary(result: FetchResult) -> dict[str, Any]:
    if result.status != 200 or result.truncated:
        return {
            "outcome": "SAMPLE_NOT_FULLY_RETRIEVED",
            "http_status": result.status,
            "bytes_read": result.bytes_read,
            "truncated": result.truncated,
            "error": result.error,
        }
    text = _text(result)
    reader = csv.DictReader(io.StringIO(text))
    fields = reader.fieldnames or []
    if not fields:
        return {
            "outcome": "SAMPLE_HAS_NO_CSV_HEADER",
            "http_status": result.status,
            "content_type": result.content_type,
            "bytes_read": result.bytes_read,
            "sha256": hashlib.sha256(result.body).hexdigest(),
        }
    row_count = 0
    missing_by_field = {field: 0 for field in fields}
    dates: list[str] = []
    instruments: set[str] = set()
    satellites: set[str] = set()
    versions: set[str] = set()
    for row in reader:
        row_count += 1
        for field in fields:
            if row.get(field) in (None, ""):
                missing_by_field[field] += 1
        if row.get("acq_date"):
            dates.append(row["acq_date"])
        if row.get("instrument"):
            instruments.add(row["instrument"])
        if row.get("satellite"):
            satellites.add(row["satellite"])
        if row.get("version"):
            versions.add(row["version"])
    return {
        "outcome": "SAMPLE_PARSED",
        "http_status": result.status,
        "content_type": result.content_type,
        "bytes_read": result.bytes_read,
        "sha256": hashlib.sha256(result.body).hexdigest(),
        "row_count": row_count,
        "field_count": len(fields),
        "fields": fields,
        "required_fields_present": EXPECTED_FIELDS.issubset(set(fields)),
        "matches_official_tutorial_row_count": row_count == EXPECTED_SAMPLE_ROWS,
        "date_min": min(dates) if dates else None,
        "date_max": max(dates) if dates else None,
        "instruments": sorted(instruments),
        "satellites": sorted(satellites),
        "versions": sorted(versions),
        "missing_counts": missing_by_field,
    }


def classify_protected_probe(result: FetchResult, *, api: bool) -> str:
    body = _text(result).lower()
    if result.status in (401, 403) or result.redirect_seen:
        return "AUTHENTICATION_REQUIRED"
    if api and result.status in (400, 401) and (
        "invalid map_key" in body or "map_key" in body
    ):
        return "MAP_KEY_REQUIRED"
    if result.status == 200 and body.lstrip().startswith(("<!doctype html", "<html")):
        return "HTML_OR_LOGIN_PAGE_NOT_DATA"
    if result.status == 200:
        return "HTTP_200_REQUIRES_SCHEMA_CHECK"
    if result.status == 404:
        return "PINNED_FILE_NOT_FOUND_OR_ROTATED"
    if result.status is None:
        return "NETWORK_UNAVAILABLE"
    return f"HTTP_{result.status}_UNRESOLVED"


def run_audit() -> dict[str, Any]:
    sample = fetch_url(SAMPLE_URL, MAX_SAMPLE_BYTES)
    daily = fetch_url(DAILY_URL, MAX_PROBE_BYTES)
    api = fetch_url(NO_KEY_API_URL, MAX_PROBE_BYTES)
    sample_summary = parse_sample_summary(sample)
    return {
        "experiment": "E562",
        "title": "NASA FIRMS credential-free sample and live-data access audit",
        "protocol": {
            "credentials_used": False,
            "credentials_created": False,
            "redirects_followed": False,
            "max_sample_bytes": MAX_SAMPLE_BYTES,
            "max_probe_bytes": MAX_PROBE_BYTES,
            "sample_url": SAMPLE_URL,
            "daily_file_url": DAILY_URL,
            "no_key_api_url": NO_KEY_API_URL,
            "raw_rows_retained": False,
        },
        "sample": sample_summary,
        "daily_file_probe": {
            "http_status": daily.status,
            "content_type": daily.content_type,
            "bytes_read": daily.bytes_read,
            "truncated": daily.truncated,
            "redirect_seen": daily.redirect_seen,
            "error": daily.error,
            "outcome": classify_protected_probe(daily, api=False),
        },
        "no_key_api_probe": {
            "http_status": api.status,
            "content_type": api.content_type,
            "bytes_read": api.bytes_read,
            "truncated": api.truncated,
            "redirect_seen": api.redirect_seen,
            "error": api.error,
            "outcome": classify_protected_probe(api, api=True),
        },
        "claim_boundary": {
            "public_viirs_sample_ingestion": (
                "SUPPORTED" if sample_summary["outcome"] == "SAMPLE_PARSED"
                and sample_summary.get("required_fields_present") else "NOT_VERIFIED"
            ),
            "current_or_historical_modis_viirs_access_without_credentials": "NOT_YET_PROVEN",
            "cross_sensor_harmonization": "NOT_YET_MEASURED",
            "global_or_regional_fire_calendar": "NOT_YET_MEASURED",
        },
        "limitations": [
            "The official sample is a static VIIRS SNPP sample from 2023-07-12, not a current or historical paired MODIS/VIIRS cohort.",
            "A public sample file does not establish anonymous access to current daily files or the area API.",
            "No MAP_KEY or Earthdata token was requested, created, read, or used.",
            "A successful HTTP response is not by itself a validated sensor-harmonization result.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e562/receipt.json"))
    args = parser.parse_args()
    receipt = run_audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": receipt["experiment"],
        "sample_outcome": receipt["sample"]["outcome"],
        "sample_rows": receipt["sample"].get("row_count"),
        "daily_outcome": receipt["daily_file_probe"]["outcome"],
        "api_outcome": receipt["no_key_api_probe"]["outcome"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
