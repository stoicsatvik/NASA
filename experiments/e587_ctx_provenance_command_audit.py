"""E587: audit item-specific CTX processing provenance without retaining raw text.

The runner pins the exact nine E583 STAC items, inventories provenance/control
assets, fetches only allowlisted text provenance under strict byte caps, and
stores command semantics plus hashes. Raw text, full paths, signed URLs,
coordinates, CSV rows, rasters, and credentials are never persisted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shlex
from pathlib import Path
from urllib.parse import urlencode, urlsplit, urlunsplit
import xml.etree.ElementTree as ET

try:
    from experiments.e582_ctx_qa_mola_audit import (
        API_URL,
        COLLECTION,
        MAX_SEARCH_BYTES,
        ProbeError,
        fetch_bounded,
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
        ProbeError,
        fetch_bounded,
        safe_url_summary,
        validate_public_url,
    )

JEZERO_BBOX = [76.69, 17.41, 78.69, 19.41]
SEARCH_LIMIT = 9
MAX_ITEMS = 9
MAX_PROVENANCE_BYTES = 1_000_000
MAX_TOTAL_PROVENANCE_BYTES = 5_000_000
MAX_PROVENANCE_ASSETS = 9
MAX_S3_PREFIX_BYTES = 500_000
MAX_TOTAL_S3_BYTES = 5_000_000
MAX_S3_KEYS = 100
MAX_SIDECAR_BYTES = 64_000
MAX_TOTAL_SIDECAR_BYTES = 512_000
FILE_EXTENSIONS = {
    ".tif", ".tiff", ".csv", ".cub", ".pc", ".las", ".laz", ".ply",
    ".dem", ".txt", ".img", ".json",
}
VALUE_OPTIONS = {
    "-o", "--output-prefix", "--csv-format", "--csv-srs", "--datum",
    "--semi-major-axis", "--semi-minor-axis", "--max-displacement",
    "--max-horizontal-offset", "--max-vertical-offset", "--alignment-method",
    "--num-iterations", "--outlier-ratio", "--max-num-reference-points",
    "--max-num-source-points", "--initial-transform",
    "--initial-transform-from-hillshading", "--search-radius-factor",
    "--dem-spacing", "--orthoimage",
}
PROVENANCE_WORDS = ("provenance", "processing", "command", "pipeline")
CONTROL_WORDS = ("mola", "control point", "ground control", "pedr")
TEXT_TYPES = {
    "text/plain", "text/xml", "application/xml", "application/json",
    "application/x-pvl", "application/x-shellscript",
}


def build_search_payload() -> dict:
    return {
        "collections": [COLLECTION],
        "bbox": JEZERO_BBOX,
        "limit": SEARCH_LIMIT,
    }


def asset_summary(key: str, asset: object) -> dict:
    if not isinstance(asset, dict):
        asset = {}
    href = asset.get("href")
    return {
        "key": str(key),
        "title": asset.get("title"),
        "type": asset.get("type"),
        "roles": asset.get("roles") if isinstance(asset.get("roles"), list) else None,
        "url": safe_url_summary(href) if isinstance(href, str) else None,
        "query_values_stored": False,
    }


def is_provenance_asset(key: str, asset: object) -> bool:
    title = asset.get("title", "") if isinstance(asset, dict) else ""
    haystack = f"{key} {title}".lower()
    return any(word in haystack for word in PROVENANCE_WORDS)


def is_control_asset(key: str, asset: object) -> bool:
    title = asset.get("title", "") if isinstance(asset, dict) else ""
    haystack = f"{key} {title}".lower()
    return any(word in haystack for word in CONTROL_WORDS)


def classify_input_role(filename: str) -> str:
    name = Path(filename).name.lower()
    if "mola" in name or "pedr" in name:
        return "MOLA_CONTROL"
    if "ctx" in name or "stereo" in name or "pointcloud" in name:
        return "CTX_STEREO"
    if name.endswith("_pc.tif") or name.endswith("-pc.tif") or name.endswith("/pc.tif"):
        return "CTX_STEREO"
    return "UNKNOWN"


def _file_basename(token: str) -> str | None:
    cleaned = token.strip(";,")
    if not cleaned or cleaned.startswith("-") or "$" in cleaned:
        return None
    name = Path(cleaned.replace("\\", "/")).name
    if Path(name).suffix.lower() not in FILE_EXTENSIONS:
        return None
    return name


def parse_command_line(line: str) -> dict | None:
    normalized = re.sub(r"<[^>]+>", " ", line).strip()
    try:
        tokens = shlex.split(normalized, posix=True)
    except ValueError:
        return None

    command_index = None
    tool = None
    for index, token in enumerate(tokens):
        candidate = Path(token.strip(";,")).name.lower()
        if candidate in {"geodiff", "pc_align"}:
            command_index = index
            tool = candidate
            break
    if command_index is None or tool is None:
        return None

    flags = []
    inputs = []
    index = command_index + 1
    while index < len(tokens):
        token = tokens[index]
        if token in VALUE_OPTIONS:
            flags.append(token)
            index += 2
            continue
        if token.startswith("-"):
            flags.append(token.split("=", 1)[0])
            index += 1
            continue
        filename = _file_basename(token)
        if filename:
            inputs.append(filename)
        index += 1

    inputs = inputs[:2]
    roles = [classify_input_role(name) for name in inputs]
    command_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    result = {
        "tool": tool,
        "decision": "OPERAND_ORDER_IDENTIFIED" if len(inputs) == 2 else "OPERAND_ORDER_UNRESOLVED",
        "input_files": inputs,
        "input_roles": roles,
        "flags": sorted(set(flags)),
        "command_sha256": command_hash,
        "raw_command_stored": False,
        "full_paths_stored": False,
    }

    if tool == "geodiff":
        if len(inputs) == 2:
            if "--absolute" in flags:
                semantics = "ABSOLUTE_DIFFERENCE_SIGN_UNAVAILABLE"
                label = semantics
            else:
                reverse = "--reverse" in flags
                semantics = "second_minus_first" if reverse else "first_minus_second"
                if roles == ["CTX_STEREO", "MOLA_CONTROL"]:
                    label = "MOLA_MINUS_CTX" if reverse else "CTX_MINUS_MOLA"
                elif roles == ["MOLA_CONTROL", "CTX_STEREO"]:
                    label = "CTX_MINUS_MOLA" if reverse else "MOLA_MINUS_CTX"
                else:
                    label = "ORDER_KNOWN_ROLES_UNKNOWN"
        else:
            semantics = "OPERAND_ORDER_UNRESOLVED"
            label = semantics
        result["difference_semantics"] = semantics
        result["interpreted_role_difference"] = label
        result["reverse_flag_present"] = "--reverse" in flags
        result["absolute_flag_present"] = "--absolute" in flags

    if tool == "pc_align":
        if len(inputs) == 2:
            result["reference_fixed_input"] = inputs[0]
            result["source_movable_input"] = inputs[1]
            result["forward_transform_direction"] = "second_source_to_first_reference"
            result["inverse_transform_direction"] = "first_reference_to_second_source"
            if roles == ["MOLA_CONTROL", "CTX_STEREO"]:
                result["identified_alignment_direction"] = "CTX_SOURCE_MOVED_TO_MOLA_REFERENCE"
            elif roles == ["CTX_STEREO", "MOLA_CONTROL"]:
                result["identified_alignment_direction"] = "MOLA_SOURCE_MOVED_TO_CTX_REFERENCE"
            else:
                result["identified_alignment_direction"] = "INPUT_ROLES_UNKNOWN"
        else:
            result["identified_alignment_direction"] = "OPERAND_ORDER_UNRESOLVED"
        result["saves_transformed_source"] = "--save-transformed-source-points" in flags
        result["saves_inverse_transformed_reference"] = (
            "--save-inv-transformed-reference-points" in flags
        )
    return result


def _string_fragments(value: object) -> list[str]:
    fragments = []
    if isinstance(value, str):
        fragments.append(value)
    elif isinstance(value, dict):
        for child in value.values():
            fragments.extend(_string_fragments(child))
    elif isinstance(value, list):
        for child in value:
            fragments.extend(_string_fragments(child))
    return fragments


def _logical_lines(text: str):
    pending = ""
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if pending:
            pending += " " + line
        else:
            pending = line
        if pending.endswith("\\"):
            pending = pending[:-1].rstrip()
            continue
        yield pending
        pending = ""
    if pending:
        yield pending


def parse_commands(provenance_text: str) -> list[dict]:
    fragments = [provenance_text]
    try:
        fragments.extend(_string_fragments(json.loads(provenance_text)))
    except (json.JSONDecodeError, TypeError):
        pass

    commands = {}
    for fragment in fragments:
        for line in _logical_lines(fragment):
            parsed = parse_command_line(line)
            if parsed is not None:
                commands[parsed["command_sha256"]] = parsed
    return [commands[key] for key in sorted(commands)]


def select_exact_features(features: object, e583_receipt: dict) -> tuple[list[dict], dict | None]:
    if not isinstance(e583_receipt, dict) or e583_receipt.get("experiment") != "E583":
        raise ValueError("input must be the committed E583 receipt")
    if e583_receipt.get("credentials_used") is not False:
        raise ValueError("credentialed E583 receipt is outside the frozen design")
    expected_rows = e583_receipt.get("items")
    if not isinstance(expected_rows, list) or len(expected_rows) != MAX_ITEMS:
        raise ValueError("E583 receipt must contain exactly nine items")
    expected_ids = {
        row.get("id") for row in expected_rows
        if isinstance(row, dict) and isinstance(row.get("id"), str)
    }
    if len(expected_ids) != MAX_ITEMS:
        raise ValueError("E583 item IDs must be non-empty and unique")
    if not isinstance(features, list):
        raise ValueError("STAC response must contain a feature list")

    selected = {}
    duplicates = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        item_id = feature.get("id")
        if not isinstance(item_id, str) or not item_id:
            continue
        if feature.get("collection") != COLLECTION:
            continue
        if item_id in selected:
            duplicates.append(item_id)
        else:
            selected[item_id] = feature

    actual_ids = set(selected)
    if duplicates or actual_ids != expected_ids:
        return [], {
            "decision": "ITEM_SET_MISMATCH",
            "expected_item_count": len(expected_ids),
            "actual_item_count": len(actual_ids),
            "missing_item_ids": sorted(expected_ids - actual_ids),
            "unexpected_item_ids": sorted(actual_ids - expected_ids),
            "duplicate_item_ids": sorted(set(duplicates)),
        }
    return [selected[item_id] for item_id in sorted(expected_ids)], None


def _media_type(asset: dict) -> str:
    value = asset.get("type")
    return value.split(";", 1)[0].strip().lower() if isinstance(value, str) else ""


def analyze_features(
    features: object,
    e583_receipt: dict,
    fetcher=fetch_bounded,
) -> dict:
    selected, mismatch = select_exact_features(features, e583_receipt)
    if mismatch:
        return {
            "experiment": "E587",
            **mismatch,
            "credentials_used": False,
            "raw_item_json_stored": False,
            "raw_provenance_text_stored": False,
        }

    total_bytes = 0
    total_candidates = 0
    total_downloaded = 0
    total_commands = 0
    item_results = []

    for feature in selected:
        item_id = feature["id"]
        assets = feature.get("assets")
        if not isinstance(assets, dict):
            assets = {}
        inventory = [
            asset_summary(str(key), value)
            for key, value in sorted(assets.items(), key=lambda pair: str(pair[0]))
        ]
        provenance_assets = [
            (str(key), value) for key, value in assets.items()
            if is_provenance_asset(str(key), value)
        ]
        control_assets = [
            asset_summary(str(key), value)
            for key, value in assets.items()
            if is_control_asset(str(key), value)
        ]
        provenance_results = []

        for key, asset in sorted(provenance_assets, key=lambda pair: pair[0]):
            total_candidates += 1
            summary = asset_summary(key, asset)
            result = {
                "asset": summary,
                "decision": "NOT_ATTEMPTED",
                "raw_provenance_text_stored": False,
            }
            if not isinstance(asset, dict) or not isinstance(asset.get("href"), str):
                result["decision"] = "ASSET_HREF_MISSING"
                provenance_results.append(result)
                continue
            media_type = _media_type(asset)
            if media_type not in TEXT_TYPES:
                result["decision"] = "NON_TEXT_PROVENANCE_NOT_FETCHED"
                provenance_results.append(result)
                continue
            try:
                validate_public_url(asset["href"])
            except Exception:
                result["decision"] = "URL_NOT_ALLOWLISTED"
                provenance_results.append(result)
                continue
            if total_bytes >= MAX_TOTAL_PROVENANCE_BYTES:
                result["decision"] = "TOTAL_BYTE_CAP_REACHED"
                provenance_results.append(result)
                continue
            if total_candidates > MAX_PROVENANCE_ASSETS:
                result["decision"] = "ASSET_COUNT_CAP_REACHED"
                provenance_results.append(result)
                continue

            remaining = MAX_TOTAL_PROVENANCE_BYTES - total_bytes
            byte_cap = min(MAX_PROVENANCE_BYTES, remaining)
            try:
                response = fetcher(asset["href"], max_bytes=byte_cap)
            except Exception as error:
                result["decision"] = "FETCH_ERROR"
                result["error_type"] = type(error).__name__
                provenance_results.append(result)
                continue

            total_bytes += int(response.get("bytes_read", 0) or 0)
            result.update({
                "http_status": response.get("status"),
                "bytes_read": response.get("bytes_read"),
                "declared_bytes": response.get("declared_bytes"),
                "too_large": response.get("too_large"),
                "content_type": response.get("headers", {}).get("Content-Type"),
                "final_url": safe_url_summary(response.get("final_url", asset["href"])),
            })
            if response.get("status") != 200:
                result["decision"] = "HTTP_FAILURE"
                provenance_results.append(result)
                continue
            if response.get("too_large"):
                result["decision"] = "ASSET_EXCEEDS_BYTE_CAP"
                provenance_results.append(result)
                continue

            payload = response.get("payload", b"")
            result["sha256"] = hashlib.sha256(payload).hexdigest()
            try:
                text = payload.decode("utf-8-sig")
            except UnicodeDecodeError:
                result["decision"] = "TEXT_DECODE_ERROR"
                provenance_results.append(result)
                continue
            commands = parse_commands(text)
            total_commands += len(commands)
            total_downloaded += 1
            result["decision"] = "COMMANDS_FOUND" if commands else "TEXT_FETCHED_NO_RELEVANT_COMMANDS"
            result["commands"] = commands
            result["raw_provenance_text_stored"] = False
            provenance_results.append(result)

        item_results.append({
            "id": item_id,
            "asset_keys": sorted(str(key) for key in assets),
            "asset_inventory": inventory,
            "control_asset_inventory": control_assets,
            "provenance_candidate_count": len(provenance_assets),
            "provenance_results": provenance_results,
        })

    if total_candidates == 0:
        decision = "PROVENANCE_ASSET_NOT_FOUND"
    elif total_commands:
        decision = "PROVENANCE_COMMANDS_FOUND"
    elif total_downloaded:
        decision = "PROVENANCE_TEXT_NO_RELEVANT_COMMANDS"
    else:
        decision = "PROVENANCE_NOT_ACQUIRED"

    return {
        "experiment": "E587",
        "decision": decision,
        "collection": COLLECTION,
        "item_count": len(selected),
        "exact_e583_item_set": True,
        "provenance_candidate_count": total_candidates,
        "provenance_asset_download_count": total_downloaded,
        "provenance_bytes_read": total_bytes,
        "relevant_command_count": total_commands,
        "items": item_results,
        "documented_tool_semantics": {
            "geodiff": "Default output is first DEM minus second DEM; --reverse flips the sign. --absolute removes sign information.",
            "pc_align": "First input is the fixed reference cloud; second input is the movable source cloud. The forward transform moves the second input to the first.",
            "source_urls": [
                "https://stereopipeline.readthedocs.io/en/latest/tools/geodiff.html",
                "https://stereopipeline.readthedocs.io/en/latest/tools/pc_align.html",
            ],
        },
        "interpretation_boundary": [
            "A command is item-specific only when it appears in that item's linked provenance asset.",
            "A geodiff sign is identified only when both input roles are recognized and --absolute is absent.",
            "pc_align input order identifies reference/source roles, not necessarily which transformed output was used to create the released DTM.",
            "MOLA control inputs are not held-out independent validation.",
            "No raw item JSON, provenance text, full local paths, signed URL values, coordinates, MOLA rows, rasters, or credentials are retained.",
        ],
        "credentials_used": False,
        "raw_item_json_stored": False,
        "raw_provenance_text_stored": False,
        "full_paths_stored": False,
        "signed_query_values_stored": False,
    }


def build_s3_list_url(dtm_href: str) -> str:
    validate_public_url(dtm_href)
    parsed = urlsplit(dtm_href)
    directory = parsed.path.rsplit("/", 1)[0].lstrip("/") + "/"
    query = urlencode({
        "list-type": "2",
        "prefix": directory,
        "max-keys": str(MAX_S3_KEYS),
    })
    url = urlunsplit((parsed.scheme, parsed.netloc, "/", query, ""))
    validate_public_url(url)
    return url


def _xml_local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def parse_s3_listing_xml(payload: bytes) -> dict:
    root = ET.fromstring(payload)
    root_name = _xml_local_name(root.tag)
    if root_name == "Error":
        code = next((child.text for child in root if _xml_local_name(child.tag) == "Code"), None)
        return {"decision": "S3_ERROR_RESPONSE", "error_code": code, "objects": []}

    values = {}
    objects = []
    for child in root:
        name = _xml_local_name(child.tag)
        if name == "IsTruncated":
            values["is_truncated"] = (child.text or "").strip().lower() == "true"
        elif name == "Contents":
            fields = {_xml_local_name(node.tag): node.text for node in child}
            key = fields.get("Key") or ""
            basename = Path(key).name
            if not basename:
                continue
            try:
                size = int(fields.get("Size") or 0)
            except ValueError:
                size = None
            etag = (fields.get("ETag") or "").strip('"') or None
            objects.append({
                "basename": basename,
                "size_bytes": size,
                "etag": etag,
                "last_modified": fields.get("LastModified"),
                "is_provenance_candidate": any(
                    word in basename.lower() for word in ("provenance", "command", "processing", "pipeline")
                ),
                "is_control_candidate": any(
                    word in basename.lower() for word in ("mola", "control", "pedr")
                ),
                "full_key_stored": False,
            })
    return {
        "decision": "LISTED",
        "is_truncated": values.get("is_truncated", False),
        "objects": objects,
    }


def audit_s3_prefixes(features: list[dict], fetcher=fetch_bounded) -> dict:
    total_bytes = 0
    listed_count = 0
    provenance_count = 0
    control_count = 0
    denied = False
    incomplete = False
    item_results = []

    for feature in features[:MAX_ITEMS]:
        item_id = feature.get("id")
        assets = feature.get("assets") if isinstance(feature.get("assets"), dict) else {}
        dtm = assets.get("dtm") if isinstance(assets.get("dtm"), dict) else {}
        href = dtm.get("href")
        result = {
            "id": item_id,
            "decision": "NOT_ATTEMPTED",
            "prefix_source": "DTM_asset_directory",
            "full_prefix_stored": False,
        }
        if not isinstance(href, str):
            result["decision"] = "DTM_ASSET_HREF_MISSING"
            incomplete = True
            item_results.append(result)
            continue
        try:
            url = build_s3_list_url(href)
        except Exception:
            result["decision"] = "DTM_ASSET_URL_NOT_ALLOWLISTED"
            incomplete = True
            item_results.append(result)
            continue
        result["request_url"] = safe_url_summary(url)
        if total_bytes >= MAX_TOTAL_S3_BYTES:
            result["decision"] = "TOTAL_S3_BYTE_CAP_REACHED"
            incomplete = True
            item_results.append(result)
            continue
        remaining = MAX_TOTAL_S3_BYTES - total_bytes
        try:
            response = fetcher(url, max_bytes=min(MAX_S3_PREFIX_BYTES, remaining))
        except Exception as error:
            result["decision"] = "S3_LIST_FETCH_ERROR"
            result["error_type"] = type(error).__name__
            incomplete = True
            item_results.append(result)
            continue
        total_bytes += int(response.get("bytes_read", 0) or 0)
        result["http_status"] = response.get("status")
        result["bytes_read"] = response.get("bytes_read")
        result["too_large"] = response.get("too_large")
        if response.get("status") in (401, 403):
            result["decision"] = "S3_LISTING_ACCESS_DENIED"
            denied = True
            item_results.append(result)
            break
        if response.get("status") != 200:
            result["decision"] = "S3_LISTING_HTTP_FAILURE"
            incomplete = True
            item_results.append(result)
            continue
        if response.get("too_large"):
            result["decision"] = "S3_LISTING_EXCEEDS_BYTE_CAP"
            incomplete = True
            item_results.append(result)
            continue
        try:
            parsed = parse_s3_listing_xml(response.get("payload", b""))
        except Exception as error:
            result["decision"] = "S3_LISTING_XML_PARSE_ERROR"
            result["error_type"] = type(error).__name__
            incomplete = True
            item_results.append(result)
            continue
        if parsed.get("decision") != "LISTED":
            result.update(parsed)
            incomplete = True
            item_results.append(result)
            continue

        objects = parsed["objects"]
        stac_basenames = {
            Path(asset.get("href", "")).name
            for asset in assets.values()
            if isinstance(asset, dict) and isinstance(asset.get("href"), str)
        }
        unadvertised = sorted(
            obj["basename"] for obj in objects
            if obj["basename"] not in stac_basenames
        )
        item_provenance = sum(1 for obj in objects if obj["is_provenance_candidate"])
        item_control = sum(1 for obj in objects if obj["is_control_candidate"])
        provenance_count += item_provenance
        control_count += item_control
        listed_count += 1
        if parsed.get("is_truncated"):
            incomplete = True
        result.update({
            "decision": "LISTED",
            "is_truncated": parsed.get("is_truncated", False),
            "object_count": len(objects),
            "provenance_object_count": item_provenance,
            "control_object_count": item_control,
            "unadvertised_object_basenames": unadvertised,
            "objects": objects,
        })
        item_results.append(result)

    if provenance_count:
        decision = "PROVENANCE_OBJECT_FOUND"
    elif denied and listed_count == 0:
        decision = "S3_LISTING_ACCESS_DENIED"
    elif incomplete or listed_count != min(len(features), MAX_ITEMS):
        decision = "S3_LISTING_INCOMPLETE"
    else:
        decision = "NO_PROVENANCE_OBJECT_IN_ITEM_PREFIXES"

    return {
        "decision": decision,
        "item_count_requested": min(len(features), MAX_ITEMS),
        "item_prefixes_listed": listed_count,
        "provenance_object_count": provenance_count,
        "mola_or_control_object_count": control_count,
        "bytes_read": total_bytes,
        "max_keys_per_prefix": MAX_S3_KEYS,
        "max_bytes_per_prefix": MAX_S3_PREFIX_BYTES,
        "max_total_bytes": MAX_TOTAL_S3_BYTES,
        "items": item_results,
        "full_keys_stored": False,
        "credentials_used": False,
    }


def build_s3_object_url(dtm_href: str, basename: str) -> str:
    validate_public_url(dtm_href)
    if (
        not isinstance(basename, str)
        or not basename.endswith(".json")
        or "/" in basename
        or "\\" in basename
        or basename in {".", ".."}
    ):
        raise ProbeError("sidecar basename is not an exact JSON object name")
    parsed = urlsplit(dtm_href)
    directory = parsed.path.rsplit("/", 1)[0]
    url = urlunsplit((parsed.scheme, parsed.netloc, directory + "/" + basename, "", ""))
    validate_public_url(url)
    return url


def _walk_json_strings(value: object, path: tuple[str, ...] = ()):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from _walk_json_strings(child, path + (str(key),))
    elif isinstance(value, list):
        if value and all(isinstance(child, str) for child in value):
            yield " ".join(value), path
        for index, child in enumerate(value):
            yield from _walk_json_strings(child, path + (str(index),))
    elif isinstance(value, str):
        yield value, path


def summarize_sidecar_json(payload: bytes) -> dict:
    document = json.loads(payload.decode("utf-8-sig"))
    if not isinstance(document, (dict, list)):
        raise ValueError("sidecar JSON root must be an object or array")
    relevant_paths = set()
    commands = {}
    relevant_value_hashes = []
    keywords = ("provenance", "processing", "command", "pipeline", "mola", "align", "geodiff")
    for text_value, path in _walk_json_strings(document):
        path_text = ".".join(path)
        if any(word in path_text.lower() for word in keywords):
            relevant_paths.add(path_text)
            relevant_value_hashes.append(hashlib.sha256(text_value.encode("utf-8")).hexdigest())
        for command in parse_commands(text_value):
            commands[command["command_sha256"]] = command
    top_level_keys = sorted(document.keys()) if isinstance(document, dict) else []
    return {
        "top_level_keys": [str(key) for key in top_level_keys],
        "relevant_key_paths": sorted(relevant_paths),
        "relevant_value_sha256": sorted(set(relevant_value_hashes)),
        "commands": [commands[key] for key in sorted(commands)],
        "command_count": len(commands),
        "decision": "COMMANDS_FOUND" if commands else "JSON_SIDECAR_NO_RELEVANT_COMMANDS",
        "raw_json_stored": False,
        "raw_string_values_stored": False,
        "full_paths_stored": False,
    }


def audit_sidecar_json(
    features: list[dict],
    prefix_inventory: dict,
    fetcher=fetch_bounded,
) -> dict:
    prefix_items = {
        row.get("id"): row
        for row in prefix_inventory.get("items", [])
        if isinstance(row, dict)
    }
    total_bytes = 0
    downloaded = 0
    total_commands = 0
    results = []

    for feature in features[:MAX_ITEMS]:
        item_id = feature.get("id")
        assets = feature.get("assets") if isinstance(feature.get("assets"), dict) else {}
        dtm = assets.get("dtm") if isinstance(assets.get("dtm"), dict) else {}
        dtm_href = dtm.get("href")
        listing = prefix_items.get(item_id, {})
        listed_objects = listing.get("objects", [])
        expected_basename = f"{item_id}.json"
        matches = [
            row for row in listed_objects
            if row.get("basename") == expected_basename
        ]
        result = {
            "id": item_id,
            "decision": "NOT_ATTEMPTED",
            "sidecar_basename": expected_basename,
            "raw_json_stored": False,
        }
        if not matches:
            result["decision"] = "EXACT_JSON_SIDECAR_NOT_LISTED"
            results.append(result)
            continue
        if not isinstance(dtm_href, str):
            result["decision"] = "DTM_ASSET_HREF_MISSING"
            results.append(result)
            continue
        if total_bytes >= MAX_TOTAL_SIDECAR_BYTES:
            result["decision"] = "TOTAL_SIDECAR_BYTE_CAP_REACHED"
            results.append(result)
            continue
        try:
            url = build_s3_object_url(dtm_href, expected_basename)
        except Exception:
            result["decision"] = "SIDECAR_URL_NOT_ALLOWLISTED"
            results.append(result)
            continue
        result["request_url"] = safe_url_summary(url)
        remaining = MAX_TOTAL_SIDECAR_BYTES - total_bytes
        try:
            response = fetcher(url, max_bytes=min(MAX_SIDECAR_BYTES, remaining))
        except Exception as error:
            result["decision"] = "SIDECAR_FETCH_ERROR"
            result["error_type"] = type(error).__name__
            results.append(result)
            continue
        total_bytes += int(response.get("bytes_read", 0) or 0)
        result["http_status"] = response.get("status")
        result["bytes_read"] = response.get("bytes_read")
        result["too_large"] = response.get("too_large")
        if response.get("status") != 200:
            result["decision"] = "SIDECAR_HTTP_FAILURE"
            results.append(result)
            continue
        if response.get("too_large"):
            result["decision"] = "SIDECAR_EXCEEDS_BYTE_CAP"
            results.append(result)
            continue
        payload = response.get("payload", b"")
        result["sha256"] = hashlib.sha256(payload).hexdigest()
        try:
            summary = summarize_sidecar_json(payload)
        except Exception as error:
            result["decision"] = "SIDECAR_JSON_PARSE_ERROR"
            result["error_type"] = type(error).__name__
            results.append(result)
            continue
        result.update(summary)
        downloaded += 1
        total_commands += summary["command_count"]
        results.append(result)

    if total_commands:
        decision = "SIDECAR_COMMANDS_FOUND"
    elif downloaded == len(features[:MAX_ITEMS]) and downloaded:
        decision = "SIDECAR_JSON_ACQUIRED_NO_RELEVANT_COMMANDS"
    elif downloaded:
        decision = "SIDECAR_JSON_PARTIAL_NO_RELEVANT_COMMANDS"
    else:
        decision = "SIDECAR_JSON_NOT_ACQUIRED"
    return {
        "decision": decision,
        "item_count_requested": min(len(features), MAX_ITEMS),
        "sidecar_download_count": downloaded,
        "total_bytes_read": total_bytes,
        "relevant_command_count": total_commands,
        "max_bytes_per_sidecar": MAX_SIDECAR_BYTES,
        "max_total_bytes": MAX_TOTAL_SIDECAR_BYTES,
        "items": results,
        "raw_json_stored": False,
        "raw_string_values_stored": False,
        "credentials_used": False,
    }


def audit(e583_receipt: dict) -> dict:
    payload = build_search_payload()
    response = fetch_bounded(
        API_URL,
        max_bytes=MAX_SEARCH_BYTES,
        method="POST",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    if response["status"] != 200:
        return {
            "experiment": "E587",
            "decision": "STAC_SEARCH_FAILURE",
            "http_status": response["status"],
            "bytes_read": response["bytes_read"],
            "credentials_used": False,
        }
    if response["too_large"]:
        return {
            "experiment": "E587",
            "decision": "STAC_SEARCH_EXCEEDS_1MB_CAP",
            "http_status": response["status"],
            "bytes_read": response["bytes_read"],
            "credentials_used": False,
        }
    try:
        document = json.loads(response["payload"].decode("utf-8"))
    except Exception as error:
        raise ProbeError("STAC response is not valid UTF-8 JSON") from error
    if not isinstance(document, dict) or document.get("type") != "FeatureCollection":
        raise ProbeError("STAC response is not a FeatureCollection")
    features = document.get("features")
    result = analyze_features(features, e583_receipt)
    selected, mismatch = select_exact_features(features, e583_receipt)
    if not mismatch:
        prefix_inventory = audit_s3_prefixes(selected)
        result["s3_prefix_inventory"] = prefix_inventory
        result["sidecar_json_inventory"] = audit_sidecar_json(selected, prefix_inventory)
    result["source"] = {
        "api": safe_url_summary(API_URL),
        "search_payload": payload,
        "http_status": response["status"],
        "response_bytes": response["bytes_read"],
        "response_sha256": hashlib.sha256(response["payload"]).hexdigest(),
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("research/results/E583_CTX_QA_COHORT_SCREEN_20261112.json"),
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(".artifacts/e587/ctx-provenance-command-audit.json"),
    )
    args = parser.parse_args()
    try:
        e583_receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
        result = audit(e583_receipt)
    except Exception as error:
        result = {
            "experiment": "E587",
            "decision": "ACQUISITION_OR_ANALYSIS_ERROR",
            "error_type": type(error).__name__,
            "error": str(error)[:300],
            "credentials_used": False,
            "raw_provenance_text_stored": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "experiment": "E587",
        "decision": result.get("decision"),
        "item_count": result.get("item_count"),
        "provenance_candidate_count": result.get("provenance_candidate_count"),
        "provenance_asset_download_count": result.get("provenance_asset_download_count"),
        "provenance_bytes_read": result.get("provenance_bytes_read"),
        "relevant_command_count": result.get("relevant_command_count"),
        "s3_prefix_decision": (result.get("s3_prefix_inventory") or {}).get("decision"),
        "s3_prefixes_listed": (result.get("s3_prefix_inventory") or {}).get("item_prefixes_listed"),
        "provenance_objects_in_prefixes": (result.get("s3_prefix_inventory") or {}).get("provenance_object_count"),
        "sidecar_json_decision": (result.get("sidecar_json_inventory") or {}).get("decision"),
        "sidecar_json_download_count": (result.get("sidecar_json_inventory") or {}).get("sidecar_download_count"),
        "sidecar_relevant_command_count": (result.get("sidecar_json_inventory") or {}).get("relevant_command_count"),
    }, sort_keys=True))


if __name__ == "__main__":
    main()
