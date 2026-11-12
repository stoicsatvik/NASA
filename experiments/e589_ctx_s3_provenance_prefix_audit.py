"""E589: list one verified public S3 item prefix for an omitted provenance sidecar."""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
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
from experiments.e587_ctx_processing_provenance_audit import _command_summary, classify_operand, parse_provenance_text  # noqa: E402

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





def _tool_record_summary(tool: str, node: Any, path: str) -> dict[str, Any]:
    """Summarize a structured tool record without retaining its argument strings."""
    values: list[str] = []
    reverse = False
    if isinstance(node, dict):
        reverse = bool(node.get("reverse") or node.get("reverse_sign") or node.get("--reverse"))
        for key in ("argv", "args", "arguments", "command", "cmd", "invocation"):
            value = node.get(key)
            if isinstance(value, list) and all(isinstance(v, (str, int, float)) for v in value):
                tokens = [str(v) for v in value]
                if not any(token.lower().split("/")[-1] in {"pc_align", "geodiff"} for token in tokens[:2]):
                    tokens = [tool] + tokens
                line = shlex.join(tokens)
                if reverse and tool == "geodiff" and "--reverse" not in tokens:
                    line = tool + " --reverse " + line[len(tool):].lstrip()
                parsed = _command_summary(line)
                if parsed:
                    return {"path": path[:240], **parsed}
            if isinstance(value, str):
                line = value if tool in value else tool + " " + value
                if reverse and tool == "geodiff" and "--reverse" not in line:
                    line = tool + " --reverse " + line[len(tool):].lstrip()
                parsed = _command_summary(line)
                if parsed:
                    return {"path": path[:240], **parsed}
        for key in ("reference", "reference_cloud", "fixed", "target", "source", "source_cloud", "moving", "input", "input1", "input2", "dem", "dem1", "dem2", "csv"):
            value = node.get(key)
            if isinstance(value, str):
                values.append(value)
        if values:
            line = shlex.join([tool] + values + (["--reverse"] if reverse and tool == "geodiff" else []))
            parsed = _command_summary(line)
            if parsed:
                return {"path": path[:240], **parsed}
    elif isinstance(node, (str, list)):
        if isinstance(node, str):
            line = node if tool in node else tool + " " + node
        else:
            tokens = [str(v) for v in node]
            if not any(token.lower().split("/")[-1] in {"pc_align", "geodiff"} for token in tokens[:2]):
                tokens = [tool] + tokens
            line = shlex.join(tokens)
        if reverse and tool == "geodiff" and "--reverse" not in line:
            line = tool + " --reverse " + line[len(tool):].lstrip()
        parsed = _command_summary(line)
        if parsed:
            return {"path": path[:240], **parsed}
    return {
        "path": path[:240],
        "tool": tool,
        "record_type": type(node).__name__,
        "child_keys": sorted(str(k) for k in node)[:80] if isinstance(node, dict) else [],
        "operand_count": 0,
        "reference_role": "UNRESOLVED" if tool == "pc_align" else None,
        "source_role": "UNRESOLVED" if tool == "pc_align" else None,
        "reverse_flag": reverse if tool == "geodiff" else None,
        "command_arguments_recovered": False,
    }


def _structure_summary(node: Any, depth: int = 0) -> dict[str, Any]:
    if depth > 5:
        return {"type": type(node).__name__}
    if isinstance(node, dict):
        keys = sorted(str(k) for k in node)
        selected = {}
        for key in keys:
            if key.lower() in {"pc_align", "geodiff", "processing", "provenance", "commands", "command", "argv", "args", "arguments", "inputs", "outputs", "reference", "source", "parameters", "options"}:
                selected[key] = _structure_summary(node[key], depth + 1)
        return {"type": "object", "keys": keys[:100], "selected": selected}
    if isinstance(node, list):
        return {"type": "array", "length": len(node), "sample": _structure_summary(node[0], depth + 1) if node else None}
    if isinstance(node, str):
        return {"type": "string", "length": len(node)}
    return {"type": type(node).__name__}


def parse_provenance_payload(name: str, payload: bytes) -> dict[str, Any]:
    """Parse text or JSON provenance in memory; return command roles only."""
    is_json = name.lower().endswith(".json") or payload.lstrip().startswith((b"{", b"["))
    if not is_json:
        return parse_provenance_text(payload)
    try:
        document = json.loads(payload.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return {
            "decision": "JSON_SIDECAR_PARSE_FAILED",
            "text_sha256": hashlib.sha256(payload).hexdigest(),
            "command_count": 0,
            "commands": [],
            "raw_json_stored": False,
        }

    commands: list[dict[str, Any]] = []
    seen: set[str] = set()
    key_paths: list[dict[str, Any]] = []
    node_counts = {"objects": 0, "arrays": 0, "strings": 0}
    max_depth = 0

    def add_line(line: str) -> None:
        summary = _command_summary(line)
        if summary is None:
            return
        digest = summary["command_line_sha256"]
        if digest not in seen:
            seen.add(digest)
            commands.append(summary)

    def walk(node: Any, path: str = "$", depth: int = 0, inherited_tool: str | None = None) -> None:
        nonlocal max_depth
        if depth > 24:
            return
        max_depth = max(max_depth, depth)
        if isinstance(node, dict):
            node_counts["objects"] += 1
            local_tool = inherited_tool
            for key in node:
                if str(key).lower() in {"pc_align", "geodiff"}:
                    local_tool = str(key).lower()
            program = node.get("program") or node.get("tool") or node.get("executable") or local_tool
            argv = node.get("argv")
            args = node.get("args") or node.get("arguments")
            if isinstance(argv, list) and all(isinstance(v, (str, int, float)) for v in argv):
                argv_values = [str(v) for v in argv]
                has_tool = any(str(v).lower().split("/")[-1] in {"pc_align", "geodiff"} for v in argv_values[:2])
                if isinstance(program, str) and not has_tool:
                    argv_values = [program] + argv_values
                add_line(shlex.join(argv_values))
            elif isinstance(program, str) and program.lower().split("/")[-1] in {"pc_align", "geodiff"}:
                if isinstance(args, list) and all(isinstance(v, (str, int, float)) for v in args):
                    add_line(shlex.join([program] + [str(v) for v in args]))
                elif isinstance(args, str):
                    add_line(program + " " + args)
            command = node.get("command") or node.get("cmd") or node.get("invocation")
            if isinstance(command, str):
                add_line(command)
            elif isinstance(command, list) and all(isinstance(v, (str, int, float)) for v in command):
                add_line(shlex.join([str(v) for v in command]))
            for key, value in node.items():
                key_text = str(key)
                child_path = (path + "." + key_text)[:240]
                if any(term in key_text.lower() for term in ("command", "argv", "args", "invocation", "process", "history", "program", "tool", "pc_align", "geodiff", "reference", "source", "inputs", "outputs", "parameters", "options", "provenance")):
                    length = len(value) if isinstance(value, (str, list, dict)) else None
                    key_paths.append({"path": child_path, "type": type(value).__name__, "length": length})
                if isinstance(value, str):
                    node_counts["strings"] += 1
                    if key_text.lower() in {"program", "tool", "executable"}:
                        continue
                    if "pc_align" in value.lower() or "geodiff" in value.lower():
                        for parsed in parse_provenance_text(value.encode("utf-8")).get("commands", []):
                            digest = parsed["command_line_sha256"]
                            if digest not in seen:
                                seen.add(digest)
                                commands.append(parsed)
                else:
                    walk(value, child_path, depth + 1, local_tool)
        elif isinstance(node, list):
            node_counts["arrays"] += 1
            for index, value in enumerate(node[:5000]):
                walk(value, f"{path}[{index}]"[:240], depth + 1, inherited_tool)
        elif isinstance(node, str):
            node_counts["strings"] += 1
            if "pc_align" in node.lower() or "geodiff" in node.lower():
                for parsed in parse_provenance_text(node.encode("utf-8")).get("commands", []):
                    digest = parsed["command_line_sha256"]
                    if digest not in seen:
                        seen.add(digest)
                        commands.append(parsed)

    walk(document)

    tool_records: list[dict[str, Any]] = []
    def collect_tool_records(node: Any, path: str = "$", depth: int = 0) -> None:
        if depth > 24:
            return
        if isinstance(node, dict):
            for key, value in node.items():
                key_text = str(key).lower()
                child_path = (path + "." + str(key))[:240]
                if key_text in {"pc_align", "geodiff"}:
                    tool_records.append(_tool_record_summary(key_text, value, child_path))
                collect_tool_records(value, child_path, depth + 1)
        elif isinstance(node, list):
            for index, value in enumerate(node[:5000]):
                collect_tool_records(value, f"{path}[{index}]"[:240], depth + 1)

    collect_tool_records(document)
    property_keys = sorted(str(k) for k in document.get("properties", {})) if isinstance(document, dict) and isinstance(document.get("properties"), dict) else []
    asset_keys = sorted(str(k) for k in document.get("assets", {})) if isinstance(document, dict) and isinstance(document.get("assets"), dict) else []
    commands.extend(record for record in tool_records if record.get("tool") in {"pc_align", "geodiff"} and record.get("operand_count", 0) >= 2)
    return {
        "decision": "JSON_PROCESSING_COMMANDS_FOUND" if commands else "JSON_WITHOUT_RECOGNIZED_COMMANDS",
        "json_sha256": hashlib.sha256(payload).hexdigest(),
        "top_level_keys": sorted(str(k) for k in document)[:120] if isinstance(document, dict) else [],
        "property_keys": property_keys[:160],
        "asset_keys": asset_keys[:100],
        "structure": _structure_summary(document),
        "node_counts": node_counts,
        "max_depth": max_depth,
        "command_like_key_paths": key_paths[:120],
        "tool_records": tool_records[:40],
        "command_count": len(commands),
        "commands": commands[:40],
        "raw_json_stored": False,
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
                parsed = parse_provenance_payload(name, fetched["payload"])
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
