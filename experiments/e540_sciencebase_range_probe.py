"""E540: bounded anonymous Range probe of one metadata-provided ScienceBase DEM URL.

Only the exact file record's downloadUri is considered. The probe refuses
signed/tokenized URLs, reads at most 32 response bytes (33 to detect over-read),
and never stores raw URL query values or response bytes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from experiments.e539_public_cloud_url_metadata_audit import (
    ITEM_ID,
    _fetch_sciencebase_items,
)

DEM_NAME = "GFDF_Ripples_2023_04_18_DEM.tif"
EXPECTED_BYTES = 619_492
RANGE_END = 31
MAX_READ_BYTES = RANGE_END + 2
TIMEOUT_SECONDS = 20
OUT = Path(".artifacts/e540")
USER_AGENT = "NASA-E540-ScienceBase-anonymous-range-probe/1.0"
SCIENCEBASE_HOSTS = {"www.sciencebase.gov", "sciencebase.gov", "sciencebase.usgs.gov"}
TOKEN_QUERY_KEYS = {
    "token", "access_token", "auth", "authorization", "key", "api_key",
    "signature", "sig", "x-amz-signature", "x-amz-credential",
    "x-amz-security-token", "x-amz-algorithm", "x-amz-date",
    "x-amz-expires", "x-amz-signedheaders", "expires", "se", "sp", "sv",
}


def _query_keys(url: str) -> list[str]:
    return sorted({
        key.lower()
        for key, _ in urllib.parse.parse_qsl(
            urllib.parse.urlsplit(url).query, keep_blank_values=True
        )
    })


def is_allowed_download_url(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").lower()
    is_sciencebase = (
        host in SCIENCEBASE_HOSTS
        and parsed.path.startswith("/catalog/file/get/")
    )
    is_s3 = (
        host == "s3.amazonaws.com"
        or host.endswith(".s3.amazonaws.com")
        or host == "s3.us-west-2.amazonaws.com"
        or host.endswith(".s3.us-west-2.amazonaws.com")
    )
    return (
        parsed.scheme == "https"
        and (is_sciencebase or is_s3)
        and not parsed.username
        and not parsed.password
        and not parsed.fragment
        and not TOKEN_QUERY_KEYS.intersection(_query_keys(url))
    )


def sanitize_url(url: str) -> dict:
    parsed = urllib.parse.urlsplit(url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "path": parsed.path,
        "query_key_names": _query_keys(url),
        "token_like_query_present": bool(TOKEN_QUERY_KEYS.intersection(_query_keys(url))),
    }


def locate_dem_download_uri(items: list[dict]) -> dict:
    matches = []
    for item in items:
        item_id = str(item.get("id") or item.get("itemId") or "")
        files = item.get("files", [])
        if not isinstance(files, list):
            continue
        for entry in files:
            if not isinstance(entry, dict):
                continue
            name = entry.get("name") or entry.get("fileName") or entry.get("filename")
            if name != DEM_NAME:
                continue
            raw_size = entry.get("size")
            try:
                size = int(raw_size) if raw_size is not None else None
            except (TypeError, ValueError):
                size = None
            matches.append({
                "item_id": item_id,
                "filename": DEM_NAME,
                "size_bytes": size,
                "download_uri": entry.get("downloadUri"),
            })
    if not matches:
        return {"status": "FILE_RECORD_NOT_FOUND", "match_count": 0}
    if len(matches) != 1:
        return {"status": "AMBIGUOUS_FILE_RECORD", "match_count": len(matches)}
    match = matches[0]
    if not isinstance(match["download_uri"], str) or not match["download_uri"].strip():
        return {
            "status": "DOWNLOAD_URI_MISSING",
            "match_count": 1,
            "item_id": match["item_id"],
            "filename": match["filename"],
            "size_bytes": match["size_bytes"],
        }
    url = match.pop("download_uri").strip()
    if match["size_bytes"] is None:
        return {
            "status": "FILE_SIZE_MISSING",
            "match_count": 1,
            "item_id": match["item_id"],
            "filename": match["filename"],
            "download_url": sanitize_url(url),
        }
    if match["size_bytes"] != EXPECTED_BYTES:
        return {
            "status": "METADATA_SIZE_MISMATCH",
            "match_count": 1,
            "item_id": match["item_id"],
            "filename": match["filename"],
            "size_bytes": match["size_bytes"],
            "expected_bytes": EXPECTED_BYTES,
            "download_url": sanitize_url(url),
        }
    safe = sanitize_url(url)
    if TOKEN_QUERY_KEYS.intersection(safe["query_key_names"]):
        return {
            "status": "TOKENIZED_URL_NOT_ANONYMOUS",
            "match_count": 1,
            **{k: v for k, v in match.items() if k != "download_uri"},
            "download_url": safe,
        }
    if not is_allowed_download_url(url):
        return {
            "status": "URL_OUTSIDE_ALLOWLIST",
            "match_count": 1,
            **{k: v for k, v in match.items() if k != "download_uri"},
            "download_url": safe,
        }
    return {
        "status": "READY_FOR_ANONYMOUS_RANGE_PROBE",
        "match_count": 1,
        **{k: v for k, v in match.items() if k != "download_uri"},
        "download_url": safe,
        "_request_url": url,
    }


class AllowlistedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        target = urllib.parse.urljoin(req.full_url, newurl)
        if not is_allowed_download_url(target):
            raise urllib.error.URLError("redirect target outside anonymous ScienceBase/S3 allowlist")
        return super().redirect_request(req, fp, code, msg, headers, target)


def probe_range(url: str, expected_size: int = EXPECTED_BYTES, opener=None) -> dict:
    if not is_allowed_download_url(url):
        return {"outcome": "URL_REJECTED", "download_url": sanitize_url(url)}
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/octet-stream, image/tiff",
            "Accept-Encoding": "identity",
            "Range": f"bytes=0-{RANGE_END}",
        },
    )
    client = opener or urllib.request.build_opener(AllowlistedRedirectHandler())
    try:
        with client.open(request, timeout=TIMEOUT_SECONDS) as response:
            final_url = response.geturl()
            if not is_allowed_download_url(final_url):
                return {
                    "outcome": "REDIRECT_OUTSIDE_ALLOWLIST",
                    "http_status": response.status,
                    "final_url": sanitize_url(final_url),
                }
            status = response.status
            headers = response.headers
            prefix = response.read(MAX_READ_BYTES)
    except urllib.error.HTTPError as exc:
        return {
            "outcome": "HTTP_ERROR",
            "http_status": exc.code,
            "final_url": sanitize_url(exc.geturl()),
        }
    except urllib.error.URLError as exc:
        return {
            "outcome": "NETWORK_ERROR",
            "error_type": type(exc.reason).__name__,
        }

    content_range = headers.get("Content-Range")
    receipt = {
        "http_status": status,
        "final_url": sanitize_url(final_url),
        "requested_range": f"bytes=0-{RANGE_END}",
        "content_range": content_range,
        "content_length_header": headers.get("Content-Length"),
        "response_bytes_read": len(prefix),
        "response_bytes_stored": False,
        "prefix_sha256": hashlib.sha256(prefix[:RANGE_END + 1]).hexdigest(),
        "tiff_magic": prefix[:4] in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"),
    }
    if status != 206:
        receipt["outcome"] = "RANGE_NOT_HONORED"
    elif len(prefix) > RANGE_END + 1:
        receipt["outcome"] = "RANGE_OVERREAD"
    elif len(prefix) != RANGE_END + 1:
        receipt["outcome"] = "RANGE_LENGTH_MISMATCH"
    elif content_range != f"bytes 0-{RANGE_END}/{expected_size}":
        receipt["outcome"] = "CONTENT_RANGE_MISMATCH"
    elif not receipt["tiff_magic"]:
        receipt["outcome"] = "PREFIX_NOT_TIFF"
    else:
        receipt["outcome"] = "RANGE_PREFIX_VALID"
    return receipt


def run_probe(items: list[dict] | None = None, opener=None) -> dict:
    metadata_errors = []
    if items is None:
        try:
            items, metadata_errors = _fetch_sciencebase_items()
        except Exception as exc:
            return {
                "experiment": "E540",
                "item_id": ITEM_ID,
                "filename": DEM_NAME,
                "outcome": "METADATA_FETCH_ERROR",
                "error_type": type(exc).__name__,
                "raw_metadata_stored": False,
                "query_values_stored": False,
                "response_bytes_stored": False,
                "binary_file_downloaded": False,
            }
    selection = locate_dem_download_uri(items)
    result = {
        "experiment": "E540",
        "item_id": ITEM_ID,
        "filename": DEM_NAME,
        "metadata_errors": [
            {
                "source": error.get("source"),
                "http_status": error.get("http_status"),
                "final_host": error.get("final_host"),
                "final_path": error.get("final_path"),
            }
            for error in metadata_errors
        ],
        "file_record": {k: v for k, v in selection.items() if k != "_request_url"},
        "range_request_sent": False,
        "raw_metadata_stored": False,
        "query_values_stored": False,
        "response_bytes_stored": False,
        "binary_file_downloaded": False,
        "claim_boundary": (
            "A valid 32-byte TIFF prefix proves only bounded range access to the first bytes. "
            "It does not establish full DEM acquisition, CRS, resolution, nodata, vertical datum, "
            "physical calibration, or planetary-analogue recovery."
        ),
    }
    if selection["status"] != "READY_FOR_ANONYMOUS_RANGE_PROBE":
        result["outcome"] = selection["status"]
        return result
    result["range_request_sent"] = True
    probe = probe_range(selection["_request_url"], opener=opener)
    result["range_probe"] = probe
    result["outcome"] = probe["outcome"]
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT / "receipt.json")
    args = parser.parse_args()
    result = run_probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    if result["outcome"] in {"METADATA_FETCH_ERROR", "NETWORK_ERROR"}:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
