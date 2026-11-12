"""E588: query the production USGS STAC item endpoint for processing provenance."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from experiments.e587_ctx_processing_provenance_audit import (  # noqa: E402
    COLLECTION,
    ITEM_ID,
    MAX_PROVENANCE_BYTES,
    _item_summary,
    parse_provenance_text,
    safe_url_summary,
)

API_HOST = "g6goyz4w56.execute-api.us-west-2.amazonaws.com"
API_COLLECTION_PATH = f"/prod/collections/{COLLECTION}/items"
API_ITEM_URL = f"https://{API_HOST}{API_COLLECTION_PATH}/{ITEM_ID}"
ASSET_HOSTS = {
    API_HOST,
    "astrogeo-ard.s3.amazonaws.com",
    "astrogeo-ard.s3-us-west-2.amazonaws.com",
    "astrogeo-ard.s3.us-west-2.amazonaws.com",
    "stac.astrogeology.usgs.gov",
}
USER_AGENT = "UnifiedParallelFoundry-E588-production-STAC-audit/1.0"
MAX_ITEM_BYTES = 2_000_000
TIMEOUT_SECONDS = 20


class ProbeError(RuntimeError):
    pass


def validate_url(url: str, allowed_hosts: set[str], *, exact_api_path: bool = False) -> None:
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in allowed_hosts:
        raise ProbeError("URL outside the pinned HTTPS host allowlist")
    if parsed.username or parsed.password or parsed.port not in (None, 443):
        raise ProbeError("URL contains credentials or a nonstandard port")
    if parsed.fragment:
        raise ProbeError("URL fragment is not permitted")
    if exact_api_path:
        if parsed.hostname != API_HOST or parsed.path != f"{API_COLLECTION_PATH}/{ITEM_ID}":
            raise ProbeError("API path does not match the pinned collection/item")
        if parsed.query:
            raise ProbeError("Pinned API item URL must not carry query parameters")
    if any(part == ".." for part in parsed.path.split("/")):
        raise ProbeError("URL path traversal is not permitted")


class AllowlistedRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self, allowed_hosts: set[str]):
        super().__init__()
        self.allowed_hosts = allowed_hosts

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_url(newurl, self.allowed_hosts)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_bounded(url: str, *, allowed_hosts: set[str], max_bytes: int) -> dict[str, Any]:
    validate_url(url, allowed_hosts, exact_api_path=(url == API_ITEM_URL))
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/geo+json, application/json, text/plain"},
    )
    opener = urllib.request.build_opener(AllowlistedRedirectHandler(allowed_hosts))
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            status = response.status
            final_url = response.geturl()
            validate_url(final_url, allowed_hosts)
            declared = response.headers.get("Content-Length")
            declared_bytes = int(declared) if declared and declared.isdigit() else None
            if declared_bytes is not None and declared_bytes > max_bytes:
                return {"status": status, "payload": b"", "bytes_read": 0, "declared_bytes": declared_bytes, "too_large": True, "final_url": safe_url_summary(final_url)}
            payload = response.read(max_bytes + 1)
            too_large = len(payload) > max_bytes
            return {
                "status": status,
                "payload": b"" if too_large else payload,
                "bytes_read": len(payload),
                "declared_bytes": declared_bytes,
                "too_large": too_large,
                "final_url": safe_url_summary(final_url),
            }
    except urllib.error.HTTPError as error:
        return {
            "status": error.code,
            "payload": b"",
            "bytes_read": 0,
            "declared_bytes": None,
            "too_large": False,
            "final_url": safe_url_summary(url),
            "error_type": "HTTPError",
        }


def parse_item_document(document: Any) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    if not isinstance(document, dict):
        raise ProbeError("production API returned a non-object")
    if document.get("id") != ITEM_ID or document.get("collection") != COLLECTION:
        raise ProbeError("production API returned a different item or collection")
    return _item_summary(document)


def audit() -> dict[str, Any]:
    response = fetch_bounded(API_ITEM_URL, allowed_hosts={API_HOST}, max_bytes=MAX_ITEM_BYTES)
    result: dict[str, Any] = {
        "experiment": "E588",
        "api_url": safe_url_summary(API_ITEM_URL),
        "http_status": response["status"],
        "bytes_read": response["bytes_read"],
        "declared_bytes": response["declared_bytes"],
        "too_large": response["too_large"],
        "final_url": response["final_url"],
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_provenance_stored": False,
        "raw_paths_stored": False,
        "signed_query_values_stored": False,
    }
    if response["status"] != 200 or response["too_large"]:
        result["decision"] = "PRODUCTION_ITEM_ENDPOINT_NOT_READABLE"
        result["error_type"] = response.get("error_type")
        return result

    document = json.loads(response["payload"].decode("utf-8"))
    summary, candidates = parse_item_document(document)
    provenance_results = []
    seen = set()
    for label, href in candidates[:2]:
        if href in seen:
            continue
        seen.add(href)
        try:
            validate_url(href, ASSET_HOSTS)
            fetched = fetch_bounded(href, allowed_hosts=ASSET_HOSTS, max_bytes=MAX_PROVENANCE_BYTES)
            entry = {
                "source": label,
                "url": safe_url_summary(href),
                "http_status": fetched["status"],
                "bytes_read": fetched["bytes_read"],
                "declared_bytes": fetched["declared_bytes"],
                "too_large": fetched["too_large"],
                "raw_asset_stored": False,
            }
            if fetched["status"] == 200 and not fetched["too_large"]:
                entry["summary"] = parse_provenance_text(fetched["payload"])
                entry["sha256"] = hashlib.sha256(fetched["payload"]).hexdigest()
            provenance_results.append(entry)
        except Exception as error:
            provenance_results.append({
                "source": label,
                "decision": "SAFE_FETCH_REJECTED_OR_FAILED",
                "error_type": type(error).__name__,
                "raw_asset_stored": False,
            })

    property_keys = summary["properties"]["provenance_property_keys"]
    commands = [
        command
        for asset in provenance_results
        for command in asset.get("summary", {}).get("commands", [])
    ]
    has_geodiff = any(c.get("tool") == "geodiff" and c.get("operand_count", 0) >= 2 for c in commands)
    has_pc_align = any(c.get("tool") == "pc_align" and c.get("operand_count", 0) >= 2 for c in commands)
    if has_geodiff and has_pc_align:
        decision = "ITEM_COMMAND_ORDER_RECOVERED"
    elif provenance_results:
        decision = "PROVENANCE_ASSET_PRESENT_PARTIAL_COMMAND_EVIDENCE"
    elif property_keys:
        decision = "PROVENANCE_PROPERTIES_PRESENT_NO_COMMAND_ASSET"
    else:
        decision = "NO_ITEM_SPECIFIC_PROVENANCE_EXPOSED_IN_PRODUCTION_STAC_ITEM"

    result.update({
        "decision": decision,
        "item": summary,
        "provenance_candidates_count": len(candidates),
        "provenance_assets": provenance_results,
    })
    return result


def summarize_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    item = receipt.get("item") if isinstance(receipt.get("item"), dict) else {}
    return {
        "experiment": receipt.get("experiment"),
        "decision": receipt.get("decision"),
        "api_url": receipt.get("api_url"),
        "http_status": receipt.get("http_status"),
        "bytes_read": receipt.get("bytes_read"),
        "item_id": item.get("id"),
        "asset_keys": item.get("asset_keys", []),
        "link_relations": [link.get("rel") for link in item.get("links", [])],
        "property_keys": item.get("properties", {}).get("property_keys", []),
        "provenance_property_keys": item.get("properties", {}).get("provenance_property_keys", []),
        "provenance_candidates_count": receipt.get("provenance_candidates_count", 0),
        "provenance_assets": receipt.get("provenance_assets", []),
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_provenance_stored": False,
        "raw_paths_stored": False,
        "signed_query_values_stored": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e588/production-stac-audit.json"))
    args = parser.parse_args()
    try:
        receipt = audit()
    except Exception as error:
        receipt = {
            "experiment": "E588",
            "decision": "ACQUISITION_OR_PARSING_ERROR",
            "error_type": type(error).__name__,
            "credentials_used": False,
            "raw_item_json_stored": False,
            "raw_provenance_stored": False,
            "raw_paths_stored": False,
            "signed_query_values_stored": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summarize_receipt(receipt), sort_keys=True))


if __name__ == "__main__":
    main()
