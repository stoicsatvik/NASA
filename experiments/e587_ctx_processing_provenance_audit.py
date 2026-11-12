"""E587: inspect item-specific CTX processing provenance without retaining raw paths."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
from pathlib import Path
from typing import Any

from experiments.e582_ctx_qa_mola_audit import (
    API_URL,
    COLLECTION,
    ITEM_ID,
    MAX_SEARCH_BYTES,
    fetch_bounded,
    safe_url_summary,
    validate_public_url,
)

MAX_PROVENANCE_BYTES = 2_000_000
MAX_PROVENANCE_ASSETS = 2
USER_AGENT = "UnifiedParallelFoundry-E587-CTX-provenance-audit/1.0"

SAFE_SCALAR_PROPERTIES = {
    "datetime", "created", "updated", "platform", "gsd",
    "processing:level", "processing:software", "sci:doi",
}
PROVENANCE_TERMS = ("provenance", "processing", "lineage", "command", "history")
FILE_SUFFIXES = (".tif", ".tiff", ".cub", ".csv", ".las", ".laz", ".copc", ".pc", ".xyz")
GEODIFF_VALUE_OPTIONS = {
    "-o", "--output-prefix", "--csv-format", "--csv-srs", "--nodata-value",
    "--threads", "--cache-size-mb", "--tile-size", "--tif-compress",
}
PC_ALIGN_VALUE_OPTIONS = {
    "-o", "--output-prefix", "--max-displacement", "--max-horizontal-offset",
    "--max-vertical-offset", "--num-iterations", "--alignment-method",
    "--csv-format", "--csv-srs", "--outlier-ratio", "--max-num-reference-points",
    "--max-num-source-points", "--initial-transform", "--initial-ned-translation",
    "--initial-rotation-angle", "--initial-transform-from-hillshading",
    "--hillshade-command", "--nuth-options", "--initial-transform-ransac-params",
    "--max-iterations", "--max-threads",
}


class ProbeError(RuntimeError):
    pass


def build_search_payload() -> dict[str, Any]:
    return {"collections": [COLLECTION], "ids": [ITEM_ID], "limit": 1}


def _safe_scalar(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        if "://" in value:
            try:
                return safe_url_summary(value)
            except Exception:
                return "<url-redacted>"
        if re.search(r"(?i)(token|signature|password|authorization|api[_-]?key)\s*=", value):
            return "<sensitive-value-redacted>"
        return value[:200]
    if isinstance(value, list):
        return {"type": "array", "length": len(value)}
    if isinstance(value, dict):
        return {"type": "object", "keys": sorted(str(k) for k in value)[:40]}
    return {"type": type(value).__name__}


def _property_summary(properties: Any) -> dict[str, Any]:
    if not isinstance(properties, dict):
        return {"property_keys": [], "selected_properties": {}, "provenance_property_keys": []}
    keys = sorted(str(k) for k in properties)
    selected = {
        key: _safe_scalar(properties[key])
        for key in sorted(SAFE_SCALAR_PROPERTIES)
        if key in properties
    }
    provenance_keys = [
        key for key in keys
        if any(term in key.lower() for term in ("prov", "process", "lineage", "command"))
    ]
    return {
        "property_keys": keys[:160],
        "selected_properties": selected,
        "provenance_property_keys": provenance_keys,
    }


def _item_summary(feature: dict[str, Any]) -> tuple[dict[str, Any], list[tuple[str, str]]]:
    if feature.get("id") != ITEM_ID or feature.get("collection") != COLLECTION:
        raise ProbeError("STAC returned a different item or collection")
    assets = feature.get("assets")
    if not isinstance(assets, dict):
        raise ProbeError("pinned STAC item has no assets object")
    links = feature.get("links")
    if not isinstance(links, list):
        links = []

    asset_summaries = []
    candidates: list[tuple[str, str]] = []
    for key, asset in sorted(assets.items(), key=lambda pair: str(pair[0])):
        if not isinstance(asset, dict):
            continue
        href = asset.get("href")
        title = str(asset.get("title") or "")
        key_text = str(key)
        asset_summaries.append({
            "key": key_text,
            "title": title[:160],
            "type": asset.get("type"),
            "roles": asset.get("roles"),
            "url": safe_url_summary(href) if isinstance(href, str) else None,
        })
        haystack = (key_text + " " + title).lower()
        if isinstance(href, str) and any(term in haystack for term in PROVENANCE_TERMS):
            candidates.append((f"asset:{key_text}", href))

    link_summaries = []
    for index, link in enumerate(links):
        if not isinstance(link, dict):
            continue
        href = link.get("href")
        rel = str(link.get("rel") or "")
        title = str(link.get("title") or "")
        link_summaries.append({
            "rel": rel[:80],
            "title": title[:160],
            "type": link.get("type"),
            "url": safe_url_summary(href) if isinstance(href, str) else None,
        })
        haystack = (rel + " " + title).lower()
        if isinstance(href, str) and any(term in haystack for term in PROVENANCE_TERMS):
            candidates.append((f"link:{rel or index}", href))

    summary = {
        "id": feature.get("id"),
        "collection": feature.get("collection"),
        "properties": _property_summary(feature.get("properties")),
        "asset_keys": sorted(str(k) for k in assets),
        "assets": asset_summaries,
        "links": link_summaries,
        "raw_item_json_stored": False,
    }
    return summary, candidates


def _basename(token: str) -> str:
    clean = token.split("?", 1)[0].split("#", 1)[0]
    return re.split(r"[\\/]", clean)[-1].lower()


def classify_operand(token: str) -> str:
    name = _basename(token)
    if "mola" in name or "control" in name:
        return "MOLA_CONTROL"
    if "ctx" in name or "p18_007925" in name or "p19_008650" in name:
        return "CTX_DTM"
    if name.endswith(".csv"):
        return "CSV_UNKNOWN"
    if name.endswith((".tif", ".tiff", ".cub")):
        return "DEM_UNKNOWN"
    return "UNKNOWN"


def _logical_lines(text: str) -> list[str]:
    lines: list[str] = []
    buffer = ""
    for raw in text.splitlines():
        line = raw.rstrip()
        continued = line.endswith("\\")
        if continued:
            line = line[:-1].rstrip()
        buffer = (buffer + " " + line).strip()
        if not continued:
            if buffer:
                lines.append(buffer)
            buffer = ""
    if buffer:
        lines.append(buffer)
    return lines


def _file_operands(tokens: list[str], start: int, value_options: set[str]) -> tuple[list[str], bool]:
    operands: list[str] = []
    reverse = False
    index = start
    while index < len(tokens):
        token = tokens[index]
        if token == "--reverse":
            reverse = True
            index += 1
            continue
        if token.startswith("-"):
            option = token.split("=", 1)[0]
            if option in value_options and "=" not in token:
                index += 2
            else:
                index += 1
            continue
        lower = token.lower()
        if lower.endswith(FILE_SUFFIXES):
            operands.append(token)
        index += 1
    return operands, reverse


def _command_summary(line: str) -> dict[str, Any] | None:
    try:
        tokens = shlex.split(line, posix=True)
    except ValueError:
        return None
    command_index = None
    command_name = None
    for index, token in enumerate(tokens):
        base = _basename(token)
        if base in {"geodiff", "pc_align"}:
            command_index = index
            command_name = base
            break
    if command_index is None or command_name is None:
        return None

    options = GEODIFF_VALUE_OPTIONS if command_name == "geodiff" else PC_ALIGN_VALUE_OPTIONS
    operands, reverse = _file_operands(tokens, command_index + 1, options)
    operand_roles = [classify_operand(item) for item in operands[:2]]
    result: dict[str, Any] = {
        "tool": command_name,
        "operand_count": len(operands),
        "operand_roles": operand_roles,
        "operand_extensions": [
            next((suffix for suffix in FILE_SUFFIXES if _basename(item).endswith(suffix)), "unknown")
            for item in operands[:2]
        ],
        "command_line_sha256": hashlib.sha256(line.encode("utf-8")).hexdigest(),
        "raw_command_stored": False,
    }
    if command_name == "pc_align":
        result["reference_role"] = operand_roles[0] if len(operand_roles) > 0 else "UNRESOLVED"
        result["source_role"] = operand_roles[1] if len(operand_roles) > 1 else "UNRESOLVED"
        result["reference_source_order_resolved"] = len(operand_roles) >= 2
    else:
        result["reverse_flag"] = reverse
        if set(operand_roles) == {"CTX_DTM", "MOLA_CONTROL"}:
            result["default_sign_semantics"] = "CTX_MINUS_MOLA"
            result["effective_sign_semantics"] = "MOLA_MINUS_CTX" if reverse else "CTX_MINUS_MOLA"
        else:
            result["default_sign_semantics"] = "DEM_MINUS_CSV_OR_FIRST_MINUS_SECOND"
            result["effective_sign_semantics"] = "REQUIRES_ITEM_SPECIFIC_ROLE_AND_FLAG_CONTEXT"
    return result


def parse_provenance_text(payload: bytes) -> dict[str, Any]:
    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError:
        return {
            "decision": "PROVENANCE_NOT_UTF8_TEXT",
            "line_count": 0,
            "commands": [],
            "raw_provenance_stored": False,
        }
    commands = []
    for line in _logical_lines(text):
        summary = _command_summary(line)
        if summary is not None:
            commands.append(summary)
    return {
        "decision": "PROCESSING_COMMANDS_FOUND" if commands else "TEXT_WITHOUT_RECOGNIZED_COMMANDS",
        "line_count": len(text.splitlines()),
        "text_sha256": hashlib.sha256(payload).hexdigest(),
        "command_count": len(commands),
        "commands": commands[:40],
        "raw_provenance_stored": False,
    }


def audit() -> dict[str, Any]:
    search = fetch_bounded(
        API_URL,
        max_bytes=MAX_SEARCH_BYTES,
        method="POST",
        data=json.dumps(build_search_payload()).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/geo+json"},
    )
    if search["status"] != 200 or search["too_large"]:
        raise ProbeError(f"STAC search failed: HTTP {search['status']}")
    document = json.loads(search["payload"].decode("utf-8"))
    if document.get("type") != "FeatureCollection":
        raise ProbeError("STAC response is not a FeatureCollection")
    features = document.get("features")
    if not isinstance(features, list) or len(features) != 1:
        raise ProbeError("pinned STAC search did not return exactly one feature")
    feature = features[0]
    summary, candidates = _item_summary(feature)

    provenance_results = []
    seen = set()
    for label, href in candidates[:MAX_PROVENANCE_ASSETS]:
        if href in seen:
            continue
        seen.add(href)
        try:
            validate_public_url(href)
            fetched = fetch_bounded(href, max_bytes=MAX_PROVENANCE_BYTES)
            result = {
                "source": label,
                "url": safe_url_summary(href),
                "http_status": fetched["status"],
                "bytes_read": fetched["bytes_read"],
                "declared_bytes": fetched["declared_bytes"],
                "too_large": fetched["too_large"],
                "raw_asset_stored": False,
            }
            if fetched["status"] == 200 and not fetched["too_large"]:
                parsed = parse_provenance_text(fetched["payload"])
                result["summary"] = parsed
                result["sha256"] = hashlib.sha256(fetched["payload"]).hexdigest()
            provenance_results.append(result)
        except Exception as error:
            provenance_results.append({
                "source": label,
                "url": safe_url_summary(href),
                "decision": "SAFE_FETCH_REJECTED_OR_FAILED",
                "error_type": type(error).__name__,
                "raw_asset_stored": False,
            })

    property_keys = summary["properties"]["provenance_property_keys"]
    if provenance_results:
        decision = (
            "ITEM_COMMAND_ORDER_RECOVERED"
            if (
                any(command.get("tool") == "geodiff" and command.get("operand_count", 0) >= 2
                    for asset in provenance_results
                    for command in asset.get("summary", {}).get("commands", []))
                and any(command.get("tool") == "pc_align" and command.get("operand_count", 0) >= 2
                    for asset in provenance_results
                    for command in asset.get("summary", {}).get("commands", []))
            )
            else "PROVENANCE_ASSET_PRESENT_PARTIAL_COMMAND_EVIDENCE"
        )
    elif property_keys:
        decision = "PROVENANCE_PROPERTIES_PRESENT_NO_COMMAND_ASSET"
    else:
        decision = "NO_ITEM_SPECIFIC_PROVENANCE_EXPOSED_IN_PINNED_STAC_ITEM"

    return {
        "experiment": "E587",
        "decision": decision,
        "search_http_status": search["status"],
        "search_bytes_read": search["bytes_read"],
        "item": summary,
        "provenance_candidates_count": len(candidates),
        "provenance_assets": provenance_results,
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_provenance_stored": False,
        "raw_paths_stored": False,
        "signed_query_values_stored": False,
    }


def summarize_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    item = receipt.get("item")
    if not isinstance(item, dict):
        item = {}
    return {
        "experiment": receipt.get("experiment", "E587"),
        "decision": receipt.get("decision"),
        "search_http_status": receipt.get("search_http_status"),
        "search_bytes_read": receipt.get("search_bytes_read"),
        "item_id": item.get("id"),
        "property_keys": item.get("properties", {}).get("property_keys", []),
        "provenance_property_keys": item.get("properties", {}).get("provenance_property_keys", []),
        "asset_keys": item.get("asset_keys", []),
        "link_relations": [link.get("rel") for link in item.get("links", [])],
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
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e587/ctx-provenance-audit.json"))
    args = parser.parse_args()
    try:
        receipt = audit()
    except Exception as error:
        receipt = {
            "experiment": "E587",
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
