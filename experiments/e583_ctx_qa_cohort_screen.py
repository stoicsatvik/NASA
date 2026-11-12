"""E583: screen a bounded Jezero CTX cohort using only per-item QA metrics.

This is a metadata/QA screen, not raster analysis or independent validation.
Raw item JSON and QA text are never persisted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

try:
    from experiments.e582_ctx_qa_mola_audit import (
        API_URL,
        COLLECTION,
        MAX_SEARCH_BYTES,
        MAX_QA_BYTES,
        ProbeError,
        fetch_bounded,
        parse_qa_metrics,
        safe_url_summary,
        validate_public_url,
    )
except ModuleNotFoundError as error:
    if error.name != "experiments":
        raise
    from e582_ctx_qa_mola_audit import (
        API_URL,
        COLLECTION,
        MAX_SEARCH_BYTES,
        MAX_QA_BYTES,
        ProbeError,
        fetch_bounded,
        parse_qa_metrics,
        safe_url_summary,
        validate_public_url,
    )

JEZERO_BBOX = [76.69, 17.41, 78.69, 19.41]
SEARCH_LIMIT = 9
MAX_ITEMS = 9


def build_search_payload() -> dict:
    return {
        "collections": [COLLECTION],
        "bbox": JEZERO_BBOX,
        "limit": SEARCH_LIMIT,
    }


def select_items(document: dict, max_items: int = MAX_ITEMS) -> list[dict]:
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ProbeError("Jezero search did not return a STAC FeatureCollection")
    features = document.get("features")
    if not isinstance(features, list):
        raise ProbeError("STAC FeatureCollection has no feature list")

    selected = []
    seen = set()
    for feature in features:
        if not isinstance(feature, dict):
            continue
        item_id = feature.get("id")
        if not isinstance(item_id, str) or not item_id or item_id in seen:
            continue
        if feature.get("collection") != COLLECTION:
            continue
        properties = feature.get("properties")
        if not isinstance(properties, dict):
            properties = {}
        assets = feature.get("assets")
        if not isinstance(assets, dict):
            assets = {}
        qa_asset = assets.get("qa_metrics")
        selected.append({
            "id": item_id,
            "datetime": properties.get("datetime"),
            "bbox": feature.get("bbox"),
            "qa_asset": qa_asset if isinstance(qa_asset, dict) else None,
            "asset_keys": sorted(str(key) for key in assets.keys()),
        })
        seen.add(item_id)

    selected.sort(key=lambda item: item["id"])
    return selected[:max_items]


def summarize_metrics(parsed: dict) -> dict:
    metrics = parsed.get("metrics")
    if not isinstance(metrics, list):
        metrics = []
    values = {
        str(item.get("key", "")).strip().lower(): item.get("value")
        for item in metrics
        if isinstance(item, dict)
    }

    def find(*names):
        for name in names:
            value = values.get(name.lower())
            if isinstance(value, (int, float)):
                return float(value)
        return None

    return {
        "mean_difference_m": find("mean difference"),
        "median_difference_m": find("median difference"),
        "stddev_difference_m": find("stddev of difference", "standard deviation of difference"),
        "min_difference_m": find("min difference", "minimum difference"),
        "max_difference_m": find("max difference", "maximum difference"),
        "metric_count": parsed.get("metric_count", 0),
    }


def audit_item(item: dict) -> dict:
    result = {
        "id": item["id"],
        "datetime": item.get("datetime"),
        "bbox": item.get("bbox"),
        "asset_keys": item.get("asset_keys", []),
        "raw_qa_text_stored": False,
    }
    asset = item.get("qa_asset")
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

    result["url"] = safe_url_summary(href)
    try:
        response = fetch_bounded(href, max_bytes=MAX_QA_BYTES)
    except Exception as error:
        result["decision"] = "QA_ASSET_FETCH_ERROR"
        result["error_type"] = type(error).__name__
        return result

    result["http_status"] = response["status"]
    result["bytes_read"] = response["bytes_read"]
    result["declared_bytes"] = response["declared_bytes"]
    result["too_large"] = response["too_large"]
    result["content_type"] = response["headers"].get("Content-Type")
    if response["status"] != 200:
        result["decision"] = "QA_ASSET_HTTP_FAILURE"
        return result
    if response["too_large"]:
        result["decision"] = "QA_ASSET_EXCEEDS_1MB_CAP"
        return result

    result["sha256"] = hashlib.sha256(response["payload"]).hexdigest()
    try:
        parsed = parse_qa_metrics(response["payload"])
    except Exception as error:
        result["decision"] = "QA_ASSET_PARSE_ERROR"
        result["error_type"] = type(error).__name__
        return result
    result["decision"] = parsed.get("decision", "QA_PARSED")
    result["metrics"] = summarize_metrics(parsed)
    result["raw_qa_text_stored"] = False
    return result


def audit() -> dict:
    payload = build_search_payload()
    receipt = {
        "experiment": "E583",
        "collection": COLLECTION,
        "bbox": JEZERO_BBOX,
        "search_payload": payload,
        "search_url": safe_url_summary(API_URL),
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_qa_text_stored": False,
        "decision": "ACQUISITION_NOT_ATTEMPTED",
    }
    search = fetch_bounded(
        API_URL,
        max_bytes=MAX_SEARCH_BYTES,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
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

    items = select_items(document)
    receipt["search_result_count"] = len(document.get("features", []))
    receipt["selected_item_count"] = len(items)
    receipt["items"] = [audit_item(item) for item in items]
    success_count = sum(
        item.get("decision") == "QA_KEY_VALUE_SUMMARY"
        for item in receipt["items"]
    )
    receipt["qa_success_count"] = success_count
    receipt["decision"] = (
        "QA_COHORT_ACQUIRED"
        if items and success_count == len(items)
        else "PARTIAL_OR_INCOMPLETE_QA_COHORT"
    )
    return receipt


def summarize_receipt(receipt: dict) -> dict:
    return {
        "experiment": receipt.get("experiment", "E583"),
        "decision": receipt.get("decision"),
        "search_http_status": receipt.get("search_http_status"),
        "search_result_count": receipt.get("search_result_count"),
        "selected_item_count": receipt.get("selected_item_count"),
        "qa_success_count": receipt.get("qa_success_count"),
        "items": [
            {
                "id": item.get("id"),
                "datetime": item.get("datetime"),
                "decision": item.get("decision"),
                "metrics": item.get("metrics"),
                "sha256": item.get("sha256"),
            }
            for item in receipt.get("items", [])
        ],
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_qa_text_stored": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e583/ctx-qa-cohort.json"))
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
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summarize_receipt(receipt), sort_keys=True))


if __name__ == "__main__":
    main()
