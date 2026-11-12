"""E582: bounded audit of the pinned CTX item's QA and MOLA-control assets.

Only aggregate metrics, schema, counts, hashes and safe URL summaries are stored.
Raw asset bytes, CSV rows, coordinates and signed query values are never persisted.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API_URL = "https://stac.astrogeology.usgs.gov/api/search"
COLLECTION = "mro_ctx_controlled_usgs_dtms"
ITEM_ID = "P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W"
MAX_SEARCH_BYTES = 1_000_000
MAX_QA_BYTES = 1_000_000
MAX_CSV_BYTES = 5_000_000
MAX_CSV_ROWS = 100_000
TIMEOUT_SECONDS = 30
USER_AGENT = "UnifiedParallelFoundry-E582-CTX-QA-MOLA-audit/1.0"
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
    return {"collections": [COLLECTION], "ids": [ITEM_ID], "limit": 1}


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
    try:
        port = parsed.port
    except ValueError as error:
        raise ProbeError("invalid URL port") from error
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username
        or parsed.password
        or port not in (None, 443)
        or parsed.fragment
    ):
        raise ProbeError("URL outside pinned public HTTPS host allowlist")


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_bounded(
    url: str,
    *,
    max_bytes: int,
    method: str = "GET",
    data: bytes | None = None,
    headers: dict | None = None,
) -> dict:
    validate_public_url(url)
    request_headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json,application/json,text/plain,text/csv,*/*",
    }
    if headers:
        request_headers.update(headers)
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    opener = urllib.request.build_opener(SafeRedirectHandler())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            declared_header = response.headers.get("Content-Length")
            try:
                declared = int(declared_header) if declared_header else None
            except (TypeError, ValueError):
                declared = None
            final_url = response.geturl()
            validate_public_url(final_url)
            if declared is not None and declared > max_bytes:
                return {
                    "status": response.status,
                    "headers": response.headers,
                    "payload": b"",
                    "bytes_read": 0,
                    "declared_bytes": declared,
                    "final_url": final_url,
                    "too_large": True,
                }
            payload = response.read(max_bytes + 1)
            bytes_read = len(payload)
            too_large = bytes_read > max_bytes
            if too_large:
                payload = b""
            return {
                "status": response.status,
                "headers": response.headers,
                "payload": payload,
                "bytes_read": bytes_read,
                "declared_bytes": declared,
                "final_url": final_url,
                "too_large": too_large,
            }
    except urllib.error.HTTPError as error:
        return {
            "status": error.code,
            "headers": error.headers,
            "payload": b"",
            "bytes_read": 0,
            "declared_bytes": None,
            "final_url": error.geturl(),
            "too_large": False,
        }


def parse_item(document: dict) -> tuple[dict, dict]:
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ProbeError("pinned search did not return a STAC FeatureCollection")
    features = document.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise ProbeError("pinned search must return exactly one feature")
    feature = features[0]
    if not isinstance(feature, dict):
        raise ProbeError("STAC feature is not an object")
    if feature.get("id") != ITEM_ID or feature.get("collection") != COLLECTION:
        raise ProbeError("STAC search returned a different item or collection")
    assets = feature.get("assets")
    if not isinstance(assets, dict):
        raise ProbeError("pinned item has no asset object")
    properties = feature.get("properties")
    if not isinstance(properties, dict):
        properties = {}
    summary = {
        "id": feature.get("id"),
        "collection": feature.get("collection"),
        "datetime": properties.get("datetime"),
        "asset_keys": sorted(str(key) for key in assets.keys()),
    }
    return summary, assets


def parse_qa_metrics(payload: bytes) -> dict:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return {
            "decision": "QA_NOT_UTF8_TEXT",
            "raw_text_stored": False,
            "metric_count": 0,
        }

    pattern = re.compile(
        r"^\s*([A-Za-z][A-Za-z0-9 _./()\-]{0,79})\s*[:=]\s*"
        r"([-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)\s*(.*?)\s*$"
    )
    known_units = {"m", "meter", "meters", "metre", "metres", "km", "px", "pixel", "pixels", "%", "deg", "degree", "degrees"}
    metrics = []
    unparsed_lines = 0
    for line in text.splitlines():
        match = pattern.match(line)
        if not match:
            if line.strip():
                unparsed_lines += 1
            continue
        key = " ".join(match.group(1).split())[:80]
        try:
            value = float(match.group(2))
        except ValueError:
            unparsed_lines += 1
            continue
        if not math.isfinite(value):
            unparsed_lines += 1
            continue
        tail = match.group(3).strip()
        unit = tail if tail.lower() in known_units else None
        metrics.append({"key": key, "value": value, "unit": unit})
        if len(metrics) >= 200:
            break

    return {
        "decision": "QA_KEY_VALUE_SUMMARY",
        "line_count": len(text.splitlines()),
        "metric_count": len(metrics),
        "unparsed_nonempty_lines": unparsed_lines,
        "metrics": metrics,
        "raw_text_stored": False,
    }


def parse_mola_csv(payload: bytes, *, max_rows: int = MAX_CSV_ROWS) -> dict:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return {
            "decision": "MOLA_CSV_NOT_UTF8_TEXT",
            "row_count": 0,
            "columns": [],
            "numeric_summaries": {},
            "raw_rows_stored": False,
        }
    if not text.strip():
        return {
            "decision": "MOLA_CSV_EMPTY",
            "row_count": 0,
            "columns": [],
            "numeric_summaries": {},
            "raw_rows_stored": False,
        }

    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    fieldnames = reader.fieldnames or []
    if not fieldnames:
        return {
            "decision": "MOLA_CSV_NO_HEADER",
            "row_count": 0,
            "columns": [],
            "numeric_summaries": {},
            "raw_rows_stored": False,
        }

    columns = [str(name).strip()[:80] for name in fieldnames if name is not None]
    accumulators: dict[str, dict] = {}
    row_count = 0
    truncated = False
    for row in reader:
        if row_count >= max_rows:
            truncated = True
            break
        row_count += 1
        for name in columns:
            raw = row.get(name)
            if raw is None or not str(raw).strip():
                continue
            try:
                value = float(str(raw).strip())
            except ValueError:
                continue
            if not math.isfinite(value):
                continue
            stats = accumulators.setdefault(name, {
                "count": 0,
                "missing_or_non_numeric": 0,
                "min": value,
                "max": value,
                "sum": 0.0,
            })
            stats["count"] += 1
            stats["min"] = min(stats["min"], value)
            stats["max"] = max(stats["max"], value)
            stats["sum"] += value

    summaries = {}
    for name, stats in accumulators.items():
        count = stats["count"]
        summaries[name] = {
            "numeric_count": count,
            "min": stats["min"],
            "max": stats["max"],
            "mean": stats["sum"] / count if count else None,
        }

    return {
        "decision": "MOLA_CSV_SCHEMA_AND_AGGREGATES",
        "row_count": row_count,
        "truncated_at_row_cap": truncated,
        "columns": columns[:64],
        "numeric_summaries": summaries,
        "raw_rows_stored": False,
    }


def audit_asset(name: str, asset: dict, max_bytes: int, parser) -> dict:
    if not isinstance(asset, dict) or not isinstance(asset.get("href"), str):
        return {"decision": "ASSET_MISSING_OR_NO_HREF", "asset": name}
    href = asset["href"]
    try:
        validate_public_url(href)
    except ProbeError:
        return {
            "decision": "ASSET_URL_NOT_ALLOWLISTED",
            "asset": name,
            "url": safe_url_summary(href),
        }

    response = fetch_bounded(href, max_bytes=max_bytes)
    result = {
        "asset": name,
        "http_status": response["status"],
        "content_type": response["headers"].get("Content-Type"),
        "bytes_read": response["bytes_read"],
        "declared_bytes": response["declared_bytes"],
        "too_large": response["too_large"],
        "url": safe_url_summary(response["final_url"]),
        "raw_asset_stored": False,
    }
    if response["status"] != 200:
        result["decision"] = "HTTP_ASSET_FAILURE"
        return result
    if response["too_large"]:
        result["decision"] = "ASSET_EXCEEDS_BYTE_CAP"
        return result

    result["sha256"] = hashlib.sha256(response["payload"]).hexdigest()
    result["summary"] = parser(response["payload"])
    result["decision"] = result["summary"].get("decision", "PARSED")
    return result


def audit() -> dict:
    receipt = {
        "experiment": "E582",
        "collection": COLLECTION,
        "pinned_item_id": ITEM_ID,
        "search_url": safe_url_summary(API_URL),
        "search_payload": build_search_payload(),
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_qa_text_stored": False,
        "raw_mola_csv_stored": False,
        "raw_coordinates_stored": False,
        "decision": "ACQUISITION_NOT_ATTEMPTED",
    }
    search = fetch_bounded(
        API_URL,
        max_bytes=MAX_SEARCH_BYTES,
        method="POST",
        data=json.dumps(build_search_payload()).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    receipt["search_http_status"] = search["status"]
    receipt["search_bytes_read"] = search["bytes_read"]
    receipt["search_url_final"] = safe_url_summary(search["final_url"])
    if search["status"] != 200:
        receipt["decision"] = "STAC_SEARCH_FAILURE"
        return receipt
    if search["too_large"]:
        receipt["decision"] = "STAC_SEARCH_EXCEEDS_1MB_CAP"
        return receipt

    try:
        document = json.loads(search["payload"].decode("utf-8"))
    except Exception as error:
        raise ProbeError("STAC search response is not valid UTF-8 JSON") from error
    item, assets = parse_item(document)
    receipt["item"] = item

    qa_asset = assets.get("qa_metrics")
    mola_asset = assets.get("mola_csv")
    receipt["qa_metrics"] = audit_asset("qa_metrics", qa_asset, MAX_QA_BYTES, parse_qa_metrics)
    receipt["mola_csv"] = audit_asset(
        "mola_csv", mola_asset, MAX_CSV_BYTES, parse_mola_csv
    )
    qa_ok = receipt["qa_metrics"].get("http_status") == 200 and "summary" in receipt["qa_metrics"]
    mola_ok = receipt["mola_csv"].get("http_status") == 200 and "summary" in receipt["mola_csv"]
    receipt["decision"] = (
        "QA_AND_MOLA_ASSETS_ACQUIRED" if qa_ok and mola_ok
        else "PARTIAL_OR_INCOMPLETE_ASSET_AUDIT"
    )
    return receipt


def summarize_receipt(receipt: dict) -> dict:
    def asset_summary(name: str) -> dict:
        asset = receipt.get(name)
        if not isinstance(asset, dict):
            return {"decision": "NOT_REPORTED"}
        summary = asset.get("summary")
        if not isinstance(summary, dict):
            summary = {}
        return {
            "decision": asset.get("decision"),
            "http_status": asset.get("http_status"),
            "bytes_read": asset.get("bytes_read"),
            "sha256": asset.get("sha256"),
            "metric_count": summary.get("metric_count"),
            "row_count": summary.get("row_count"),
            "columns": summary.get("columns"),
            "raw_asset_stored": False,
        }

    item = receipt.get("item")
    if not isinstance(item, dict):
        item = {}
    return {
        "experiment": receipt.get("experiment", "E582"),
        "decision": receipt.get("decision"),
        "item_id": item.get("id"),
        "asset_keys": item.get("asset_keys", []),
        "qa_metrics": asset_summary("qa_metrics"),
        "mola_csv": asset_summary("mola_csv"),
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_qa_text_stored": False,
        "raw_mola_csv_stored": False,
        "raw_coordinates_stored": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e582/ctx-qa-mola-summary.json"))
    args = parser.parse_args()
    try:
        receipt = audit()
    except Exception as error:
        receipt = {
            "experiment": "E582",
            "pinned_item_id": ITEM_ID,
            "decision": "ACQUISITION_OR_PARSING_ERROR",
            "error_type": type(error).__name__,
            "error_message": str(error)[:300],
            "credentials_used": False,
            "raw_item_json_stored": False,
            "raw_qa_text_stored": False,
            "raw_mola_csv_stored": False,
            "raw_coordinates_stored": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summarize_receipt(receipt), sort_keys=True))


if __name__ == "__main__":
    main()
