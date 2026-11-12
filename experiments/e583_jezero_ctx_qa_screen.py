"""E583: screen multiple Jezero CTX items using bounded QA-metric assets.

Only item IDs, timestamps, QA numeric summaries, hashes and redacted URL
summaries are retained. No raw item JSON, QA text, raster, MOLA rows or
coordinates are persisted.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from unittest.mock import patch

from experiments.e582_ctx_qa_mola_audit import (
    API_URL,
    COLLECTION,
    ITEM_ID,
    MAX_SEARCH_BYTES,
    MAX_QA_BYTES,
    ProbeError,
    fetch_bounded,
    parse_qa_metrics,
    safe_url_summary,
    validate_public_url,
)

JEZERO_BBOX = [76.69, 17.41, 78.69, 19.41]
MAX_BBOX_ITEMS = 10
USER_AGENT = "UnifiedParallelFoundry-E583-Jezero-CTX-QA-screen/1.0"


def build_bbox_payload(limit: int = MAX_BBOX_ITEMS) -> dict:
    if not 1 <= limit <= MAX_BBOX_ITEMS:
        raise ValueError("limit must be between 1 and MAX_BBOX_ITEMS")
    return {"collections": [COLLECTION], "bbox": JEZERO_BBOX, "limit": limit}


def build_pinned_payload() -> dict:
    return {"collections": [COLLECTION], "ids": [ITEM_ID], "limit": 1}


def parse_features(document: dict, *, max_items: int) -> list[dict]:
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ProbeError("STAC search did not return a FeatureCollection")
    features = document.get("features")
    if not isinstance(features, list):
        raise ProbeError("STAC FeatureCollection has no features array")
    if len(features) > max_items:
        raise ProbeError("STAC response exceeded the frozen item cap")
    parsed = []
    seen = set()
    for feature in features:
        if not isinstance(feature, dict):
            raise ProbeError("STAC feature is not an object")
        if feature.get("collection") != COLLECTION:
            raise ProbeError("STAC feature belongs to a different collection")
        item_id = feature.get("id")
        if not isinstance(item_id, str) or not item_id.strip():
            raise ProbeError("STAC feature has no stable item ID")
        if item_id in seen:
            raise ProbeError("duplicate item ID in one STAC response")
        seen.add(item_id)
        properties = feature.get("properties")
        assets = feature.get("assets")
        if not isinstance(properties, dict):
            properties = {}
        if not isinstance(assets, dict):
            assets = {}
        parsed.append({
            "id": item_id,
            "datetime": properties.get("datetime"),
            "assets": assets,
        })
    return parsed


def merge_features(*groups: list[dict], cap: int = MAX_BBOX_ITEMS + 1) -> list[dict]:
    merged = []
    seen = set()
    for group in groups:
        for item in group:
            item_id = item["id"]
            if item_id in seen:
                continue
            seen.add(item_id)
            merged.append(item)
            if len(merged) >= cap:
                return merged
    return merged


def post_search(payload: dict) -> dict:
    response = fetch_bounded(
        API_URL,
        max_bytes=MAX_SEARCH_BYTES,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/json",
        },
    )
    summary = {
        "http_status": response["status"],
        "bytes_read": response["bytes_read"],
        "too_large": response["too_large"],
        "url": safe_url_summary(response["final_url"]),
    }
    if response["status"] != 200:
        return {"summary": summary, "features": [], "decision": "STAC_SEARCH_FAILURE"}
    if response["too_large"]:
        return {"summary": summary, "features": [], "decision": "STAC_SEARCH_TOO_LARGE"}
    try:
        document = json.loads(response["payload"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ProbeError("STAC search response was not valid UTF-8 JSON") from error
    features = parse_features(document, max_items=MAX_BBOX_ITEMS)
    summary["item_count"] = len(features)
    return {"summary": summary, "features": features, "decision": "STAC_SEARCH_OK"}


def metric_map(parsed: dict) -> dict:
    metrics = parsed.get("metrics")
    if not isinstance(metrics, list):
        return {}
    output = {}
    for metric in metrics:
        if not isinstance(metric, dict):
            continue
        key = " ".join(str(metric.get("key", "")).lower().split())
        if key:
            output[key] = {
                "value": metric.get("value"),
                "unit": metric.get("unit"),
            }
    return output


def audit_item(item: dict) -> dict:
    assets = item.get("assets") if isinstance(item.get("assets"), dict) else {}
    asset = assets.get("qa_metrics")
    result = {
        "item_id": item["id"],
        "datetime": item.get("datetime"),
        "asset_keys": sorted(str(key) for key in assets.keys()),
        "raw_qa_text_stored": False,
    }
    if not isinstance(asset, dict) or not isinstance(asset.get("href"), str):
        result["decision"] = "QA_ASSET_MISSING"
        return result
    href = asset["href"]
    try:
        validate_public_url(href)
    except ProbeError:
        result["decision"] = "QA_ASSET_URL_NOT_ALLOWLISTED"
        result["url"] = safe_url_summary(href)
        return result
    try:
        response = fetch_bounded(href, max_bytes=MAX_QA_BYTES)
    except Exception as error:
        result["decision"] = "QA_ASSET_FETCH_ERROR"
        result["error_type"] = type(error).__name__
        result["url"] = safe_url_summary(href)
        return result
    result.update({
        "http_status": response["status"],
        "bytes_read": response["bytes_read"],
        "declared_bytes": response["declared_bytes"],
        "too_large": response["too_large"],
        "url": safe_url_summary(response["final_url"]),
    })
    if response["status"] != 200:
        result["decision"] = "QA_ASSET_HTTP_FAILURE"
        return result
    if response["too_large"]:
        result["decision"] = "QA_ASSET_EXCEEDS_CAP"
        return result
    import hashlib
    result["sha256"] = hashlib.sha256(response["payload"]).hexdigest()
    parsed = parse_qa_metrics(response["payload"])
    result["decision"] = parsed.get("decision", "QA_PARSED")
    result["metrics"] = metric_map(parsed)
    result["metric_count"] = parsed.get("metric_count", 0)
    result["unparsed_nonempty_lines"] = parsed.get("unparsed_nonempty_lines", 0)
    return result


def audit() -> dict:
    bbox = post_search(build_bbox_payload())
    pinned = post_search(build_pinned_payload())
    items = merge_features(bbox["features"], pinned["features"])
    results = [audit_item(item) for item in items]
    successful = sum(1 for item in results if item.get("http_status") == 200 and item.get("metrics"))
    return {
        "experiment": "E583",
        "collection": COLLECTION,
        "query": {"kind": "Jezero bbox", "bbox": JEZERO_BBOX, "limit": MAX_BBOX_ITEMS},
        "pinned_item_id": ITEM_ID,
        "bbox_search": bbox["summary"],
        "pinned_search": pinned["summary"],
        "bbox_search_decision": bbox["decision"],
        "pinned_search_decision": pinned["decision"],
        "item_count": len(results),
        "successful_qa_count": successful,
        "items": results,
        "decision": "QA_SCREEN_COMPLETE" if results and successful == len(results) else "PARTIAL_OR_INCOMPLETE_QA_SCREEN",
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_qa_text_stored": False,
        "raw_raster_stored": False,
        "raw_mola_rows_stored": False,
        "raw_coordinates_stored": False,
    }


def summarize_receipt(receipt: dict) -> dict:
    return {
        "experiment": receipt.get("experiment", "E583"),
        "decision": receipt.get("decision"),
        "item_count": receipt.get("item_count", 0),
        "successful_qa_count": receipt.get("successful_qa_count", 0),
        "items": [
            {
                "item_id": item.get("item_id"),
                "datetime": item.get("datetime"),
                "decision": item.get("decision"),
                "http_status": item.get("http_status"),
                "metrics": item.get("metrics", {}),
                "sha256": item.get("sha256"),
            }
            for item in receipt.get("items", [])
            if isinstance(item, dict)
        ],
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_qa_text_stored": False,
        "raw_raster_stored": False,
        "raw_mola_rows_stored": False,
        "raw_coordinates_stored": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(".artifacts/e583/jezero-ctx-qa-screen.json"),
    )
    args = parser.parse_args()
    try:
        receipt = audit()
    except Exception as error:
        receipt = {
            "experiment": "E583",
            "decision": "ACQUISITION_OR_PARSING_ERROR",
            "error_type": type(error).__name__,
            "credentials_used": False,
            "raw_item_json_stored": False,
            "raw_qa_text_stored": False,
            "raw_raster_stored": False,
            "raw_mola_rows_stored": False,
            "raw_coordinates_stored": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(summarize_receipt(receipt), sort_keys=True))


if __name__ == "__main__":
    main()
