"""E589: list one verified public S3 item prefix for an omitted provenance sidecar."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.e588_ctx_production_api_provenance_audit import (  # noqa: E402
    ASSET_HOSTS,
    COLLECTION,
    ITEM_ID,
    MAX_PROVENANCE_BYTES,
    fetch_bounded,
    safe_url_summary,
)
from experiments.e587_ctx_processing_provenance_audit import parse_provenance_text  # noqa: E402

BUCKET_URL = "https://astrogeo-ard.s3-us-west-2.amazonaws.com/"
ITEM_PREFIX = f"mars/mro/ctx/controlled/usgs/{ITEM_ID}/"
MAX_LIST_BYTES = 1_000_000
MAX_KEYS = 100
MAX_TEXT_ASSETS = 1
S3_NS = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
KNOWN_NON_PROVENANCE_TEXT = {"qa_metrics.txt", f"{ITEM_ID.lower()}_mola_shots.csv"}


def build_list_url() -> str:
    query = urllib.parse.urlencode({
        "list-type": "2",
        "prefix": ITEM_PREFIX,
        "max-keys": str(MAX_KEYS),
    })
    return BUCKET_URL + "?" + query


def _relative_name(key: str) -> str | None:
    if not key.startswith(ITEM_PREFIX):
        return None
    relative = key[len(ITEM_PREFIX):]
    if not relative or relative.startswith("/") or ".." in relative.split("/"):
        return None
    return relative


def _is_provenance_candidate(name: str) -> bool:
    lower = name.lower()
    if any(term in lower for term in ("provenance", "processing", "command", "lineage", "history")):
        return True
    if lower in KNOWN_NON_PROVENANCE_TEXT:
        return False
    return lower.endswith((".txt", ".json", ".xml", ".log"))


def parse_s3_listing(payload: bytes) -> dict[str, Any]:
    root = ET.fromstring(payload)
    root_name = root.tag.rsplit("}", 1)[-1]
    if root_name == "Error":
        code = root.findtext("s3:Code", default="UNKNOWN", namespaces=S3_NS)
        return {"decision": "S3_ERROR_XML", "error_code": code, "objects": [], "truncated": False}
    if root_name != "ListBucketResult":
        raise ValueError("unexpected S3 listing response root")
    objects = []
    for node in root.findall("s3:Contents", S3_NS):
        key = node.findtext("s3:Key", default="", namespaces=S3_NS)
        name = _relative_name(key)
        if name is None:
            continue
        size_text = node.findtext("s3:Size", default="", namespaces=S3_NS)
        etag = node.findtext("s3:ETag", default="", namespaces=S3_NS).strip('"')
        modified = node.findtext("s3:LastModified", default="", namespaces=S3_NS)
        objects.append({
            "name": name[:240],
            "size_bytes": int(size_text) if size_text.isdigit() else None,
            "etag": etag[:120] if etag else None,
            "last_modified": modified[:40] if modified else None,
            "provenance_candidate": _is_provenance_candidate(name),
        })
    truncated = root.findtext("s3:IsTruncated", default="false", namespaces=S3_NS).lower() == "true"
    return {
        "decision": "LISTING_PARSED",
        "object_count": len(objects),
        "truncated": truncated,
        "objects": objects[:MAX_KEYS],
        "raw_s3_xml_stored": False,
        "full_object_keys_stored": False,
    }


def audit() -> dict[str, Any]:
    url = build_list_url()
    response = fetch_bounded(url, allowed_hosts=ASSET_HOSTS, max_bytes=MAX_LIST_BYTES)
    receipt: dict[str, Any] = {
        "experiment": "E589",
        "collection": COLLECTION,
        "item_id": ITEM_ID,
        "bucket_host": "astrogeo-ard.s3-us-west-2.amazonaws.com",
        "prefix_item_id": ITEM_ID,
        "http_status": response["status"],
        "bytes_read": response["bytes_read"],
        "declared_bytes": response["declared_bytes"],
        "too_large": response["too_large"],
        "credentials_used": False,
        "raw_s3_xml_stored": False,
        "full_object_keys_stored": False,
        "raw_provenance_stored": False,
        "local_paths_stored": False,
        "signed_query_values_stored": False,
    }
    if response["status"] != 200 or response["too_large"]:
        receipt["decision"] = "S3_PREFIX_LISTING_DENIED_OR_FAILED"
        receipt["error_type"] = response.get("error_type")
        return receipt

    listing = parse_s3_listing(response["payload"])
    receipt["listing"] = listing
    if listing.get("decision") == "S3_ERROR_XML":
        receipt["decision"] = "S3_PREFIX_LISTING_DENIED_OR_FAILED"
        receipt["s3_error_code"] = listing.get("error_code")
        return receipt
    candidates = [obj for obj in listing["objects"] if obj.get("provenance_candidate")]
    receipt["provenance_candidate_names"] = [obj["name"] for obj in candidates]
    receipt["provenance_assets"] = []
    if listing.get("truncated"):
        receipt["decision"] = "S3_PREFIX_LISTING_TRUNCATED"
        return receipt
    if not candidates:
        receipt["decision"] = "NO_PROVENANCE_SIDECAR_IN_LISTED_PREFIX"
        return receipt

    for obj in candidates[:MAX_TEXT_ASSETS]:
        name = obj["name"]
        if "/" in name:
            receipt["provenance_assets"].append({
                "name": name,
                "decision": "NESTED_OBJECT_NOT_FETCHED",
                "raw_provenance_stored": False,
            })
            continue
        object_url = BUCKET_URL + urllib.parse.quote(ITEM_PREFIX + name, safe="/")
        try:
            fetched = fetch_bounded(object_url, allowed_hosts=ASSET_HOSTS, max_bytes=MAX_PROVENANCE_BYTES)
            entry = {
                "name": name,
                "http_status": fetched["status"],
                "bytes_read": fetched["bytes_read"],
                "declared_bytes": fetched["declared_bytes"],
                "too_large": fetched["too_large"],
                "raw_provenance_stored": False,
            }
            if fetched["status"] == 200 and not fetched["too_large"]:
                parsed = parse_provenance_text(fetched["payload"])
                entry["summary"] = parsed
                entry["sha256"] = hashlib.sha256(fetched["payload"]).hexdigest()
            receipt["provenance_assets"].append(entry)
        except Exception as error:
            receipt["provenance_assets"].append({
                "name": name,
                "decision": "SAFE_FETCH_REJECTED_OR_FAILED",
                "error_type": type(error).__name__,
                "raw_provenance_stored": False,
            })

    commands = [
        command
        for asset in receipt["provenance_assets"]
        for command in asset.get("summary", {}).get("commands", [])
    ]
    has_geodiff = any(c.get("tool") == "geodiff" and c.get("operand_count", 0) >= 2 for c in commands)
    has_pc_align = any(c.get("tool") == "pc_align" and c.get("operand_count", 0) >= 2 for c in commands)
    if has_geodiff and has_pc_align:
        receipt["decision"] = "ITEM_COMMAND_ORDER_RECOVERED_FROM_S3_SIDECAR"
    elif receipt["provenance_assets"]:
        receipt["decision"] = "PROVENANCE_SIDECAR_FOUND_COMMANDS_PARTIAL_OR_UNREADABLE"
    else:
        receipt["decision"] = "PROVENANCE_OBJECT_FOUND_NOT_FETCHED"
    return receipt


def summarize_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    listing = receipt.get("listing") if isinstance(receipt.get("listing"), dict) else {}
    return {
        "experiment": receipt.get("experiment"),
        "decision": receipt.get("decision"),
        "collection": receipt.get("collection"),
        "item_id": receipt.get("item_id"),
        "http_status": receipt.get("http_status"),
        "bytes_read": receipt.get("bytes_read"),
        "object_count": listing.get("object_count"),
        "objects": listing.get("objects", []),
        "truncated": listing.get("truncated"),
        "provenance_candidate_names": receipt.get("provenance_candidate_names", []),
        "provenance_assets": receipt.get("provenance_assets", []),
        "credentials_used": False,
        "raw_s3_xml_stored": False,
        "full_object_keys_stored": False,
        "raw_provenance_stored": False,
        "local_paths_stored": False,
        "signed_query_values_stored": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e589/s3-prefix-audit.json"))
    args = parser.parse_args()
    try:
        receipt = audit()
    except Exception as error:
        receipt = {
            "experiment": "E589",
            "decision": "ACQUISITION_OR_PARSING_ERROR",
            "error_type": type(error).__name__,
            "credentials_used": False,
            "raw_s3_xml_stored": False,
            "full_object_keys_stored": False,
            "raw_provenance_stored": False,
            "local_paths_stored": False,
            "signed_query_values_stored": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summarize_receipt(receipt), sort_keys=True))


if __name__ == "__main__":
    main()
