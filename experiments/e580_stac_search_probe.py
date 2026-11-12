"""E580: one bounded public STAC item search and DTM byte-range probe.

No credentials are used. Raw item JSON and raster bytes are never persisted.
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

API_URL = "https://stac.astrogeology.usgs.gov/api/search"
COLLECTION = "mro_ctx_controlled_usgs_dtms"
BBOX = [76.69, 17.41, 78.69, 19.41]
LIMIT = 1
MAX_SEARCH_BYTES = 1_000_000
MAX_RANGE_BYTES = 4096
TIMEOUT_SECONDS = 20
USER_AGENT = "UnifiedParallelFoundry-E580-public-STAC-probe/1.0"
ALLOWED_HOSTS = {
    "stac.astrogeology.usgs.gov",
    "astrogeo-ard.s3-us-west-2.amazonaws.com",
    "astrogeo-ard.s3.amazonaws.com",
    "astrogeo-ard.s3.us-west-2.amazonaws.com",
    "s3.us-west-2.amazonaws.com",
}


class ProbeError(RuntimeError):
    pass


def build_search_payload() -> dict:
    return {"collections": [COLLECTION], "bbox": BBOX, "limit": LIMIT}


def safe_url_summary(url: str) -> dict:
    parsed = urllib.parse.urlsplit(url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "path": parsed.path,
        "query_key_names": sorted({
            key.lower()
            for key, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        }),
        "query_values_stored": False,
    }


def validate_public_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username
        or parsed.password
    ):
        raise ProbeError("URL outside pinned public HTTPS host allowlist")


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_bounded(
    url: str,
    *,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict | None = None,
    max_bytes: int = MAX_SEARCH_BYTES,
) -> dict:
    validate_public_url(url)
    request_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json,application/json",
    }
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    opener = urllib.request.build_opener(SafeRedirectHandler())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read(max_bytes + 1)
            bytes_read = len(payload)
            too_large = bytes_read > max_bytes
            if too_large:
                payload = b""
            final_url = response.geturl()
            validate_public_url(final_url)
            return {
                "status": response.status,
                "headers": response.headers,
                "payload": payload,
                "bytes_read": bytes_read,
                "final_url": final_url,
                "too_large": too_large,
            }
    except urllib.error.HTTPError as error:
        return {
            "status": error.code,
            "headers": error.headers,
            "payload": b"",
            "bytes_read": 0,
            "final_url": error.geturl(),
            "too_large": False,
        }


def parse_feature_collection(payload: bytes) -> dict:
    try:
        document = json.loads(payload.decode("utf-8"))
    except Exception as error:
        raise ProbeError("search response is not valid UTF-8 JSON") from error
    if (
        not isinstance(document, dict)
        or document.get("type") != "FeatureCollection"
        or not isinstance(document.get("features"), list)
    ):
        raise ProbeError("search response is not a STAC FeatureCollection")

    features = document["features"]
    if not features:
        return {"decision": "NO_ITEMS_MATCHED", "matched": 0, "items": []}

    summaries = []
    for feature in features[:LIMIT]:
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        geometry = feature.get("geometry")
        if not isinstance(geometry, dict):
            geometry = {}
        assets = feature.get("assets")
        if not isinstance(assets, dict):
            assets = {}
        dtm = assets.get("dtm")
        href = dtm.get("href") if isinstance(dtm, dict) else None
        usable = False
        if isinstance(href, str):
            try:
                validate_public_url(href)
                usable = True
            except ProbeError:
                usable = False

        summaries.append({
            "id": feature.get("id"),
            "collection": feature.get("collection"),
            "geometry_type": geometry.get("type"),
            "bbox": feature.get("bbox"),
            "datetime": properties.get("datetime"),
            "proj_epsg": properties.get("proj:epsg"),
            "proj_shape": properties.get("proj:shape"),
            "proj_transform": properties.get("proj:transform"),
            "proj_wkt2_present": bool(properties.get("proj:wkt2")),
            "asset_keys": sorted(assets.keys()),
            "dtm_href": safe_url_summary(href) if usable else None,
            "dtm_href_usable": usable,
        })
    return {
        "decision": "ITEM_METADATA_ACQUIRED",
        "matched": len(features),
        "items": summaries,
    }


def range_probe(url: str) -> dict:
    response = fetch_bounded(
        url,
        method="GET",
        headers={"Range": f"bytes=0-{MAX_RANGE_BYTES - 1}"},
        max_bytes=MAX_RANGE_BYTES,
    )
    content_range = response["headers"].get("Content-Range")
    match = re.fullmatch(r"bytes 0-(\d+)/(\d+|\*)", content_range.strip()) if content_range else None
    range_verified = (
        response["status"] == 206
        and match is not None
        and int(match.group(1)) < MAX_RANGE_BYTES
    )
    return {
        "status": response["status"],
        "content_range": content_range,
        "content_type": response["headers"].get("Content-Type"),
        "bytes_read": response["bytes_read"],
        "first_bytes_sha256": (
            hashlib.sha256(response["payload"]).hexdigest()
            if response["payload"] else None
        ),
        "range_verified": range_verified,
        "url": safe_url_summary(response["final_url"]),
    }


def audit() -> dict:
    receipt = {
        "experiment": "E580",
        "collection": COLLECTION,
        "search_url": safe_url_summary(API_URL),
        "search_payload": build_search_payload(),
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_raster_stored": False,
        "sample_pixels_acquired": False,
        "decision": "ACQUISITION_NOT_ATTEMPTED",
    }
    response = fetch_bounded(
        API_URL,
        method="POST",
        data=json.dumps(build_search_payload()).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        max_bytes=MAX_SEARCH_BYTES,
    )
    receipt.update({
        "http_status": response["status"],
        "content_type": response["headers"].get("Content-Type"),
        "response_bytes_read": response["bytes_read"],
        "final_search_url": safe_url_summary(response["final_url"]),
    })
    if response["status"] != 200:
        receipt["decision"] = "HTTP_SEARCH_FAILURE"
        return receipt
    if response["too_large"]:
        receipt["decision"] = "SEARCH_RESPONSE_EXCEEDS_1MB_CAP"
        return receipt

    parsed = parse_feature_collection(response["payload"])
    receipt.update(parsed)
    if parsed["decision"] == "NO_ITEMS_MATCHED":
        return receipt

    document = json.loads(response["payload"].decode("utf-8"))
    first = document["features"][0]
    assets = first.get("assets") if isinstance(first.get("assets"), dict) else {}
    dtm = assets.get("dtm") if isinstance(assets.get("dtm"), dict) else {}
    href = dtm.get("href")
    if not isinstance(href, str):
        receipt["decision"] = "ITEM_ACQUIRED_WITHOUT_DTM_ASSET"
        return receipt
    try:
        validate_public_url(href)
    except ProbeError:
        receipt["decision"] = "ITEM_ACQUIRED_DTM_HOST_NOT_ALLOWLISTED"
        return receipt

    try:
        receipt["dtm_range"] = range_probe(href)
    except Exception as error:
        receipt["dtm_range"] = {
            "decision": "RANGE_PROBE_ERROR",
            "error_type": type(error).__name__,
            "error_message": str(error)[:240],
            "range_verified": False,
        }
    receipt["decision"] = (
        "ITEM_AND_DTM_RANGE_ACQUIRED"
        if receipt["dtm_range"].get("range_verified")
        else "ITEM_ACQUIRED_DTM_RANGE_NOT_VERIFIED"
    )
    return receipt


def summarize_receipt(receipt: dict) -> dict:
    items = receipt.get("items") or []
    item = items[0] if items else {}
    range_result = receipt.get("dtm_range")
    if not isinstance(range_result, dict):
        range_result = {}
    return {
        "experiment": receipt.get("experiment", "E580"),
        "decision": receipt.get("decision"),
        "http_status": receipt.get("http_status"),
        "matched": receipt.get("matched"),
        "item_id": item.get("id"),
        "geometry_type": item.get("geometry_type"),
        "asset_keys": item.get("asset_keys", []),
        "dtm_range_status": range_result.get("status"),
        "dtm_range_verified": bool(range_result.get("range_verified")),
        "sample_pixels_acquired": False,
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_raster_stored": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e580/stac-summary.json"))
    args = parser.parse_args()
    try:
        receipt = audit()
    except Exception as error:
        receipt = {
            "experiment": "E580",
            "decision": "ACQUISITION_ERROR",
            "error_type": type(error).__name__,
            "error_message": str(error)[:300],
            "credentials_used": False,
            "raw_item_json_stored": False,
            "raw_raster_stored": False,
            "sample_pixels_acquired": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summarize_receipt(receipt), sort_keys=True))


if __name__ == "__main__":
    main()
