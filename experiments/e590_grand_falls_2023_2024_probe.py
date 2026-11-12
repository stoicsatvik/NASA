"""E590: bounded access audit for the 2023–2024 Grand Falls USGS release.

The DOI landing item and the Data.gov catalog identifier are distinct
ScienceBase/catalog identifiers. This probe checks the documented parent/
child structure and both top-level and facet-attached files. At most one
small metadata-listed delimited file/ZIP is acquired; only aggregate
summaries and hashes are retained.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from experiments.e577_grand_falls_2017_2019_access_probe import (
    ALLOWED_HOSTS,
    MAX_FILE_BYTES,
    MAX_HEADER_BYTES,
    MAX_METADATA_BYTES,
    fetch_bounded,
    inspect_payload,
    parse_content_range,
)

PARENT_ITEM_ID = "677ee6bed34e760b392c4aa3"
CATALOG_RECORD_ID = "67bf94acd34e8876fcbfc91b"
DOI = "10.5066/P13HPPYM"
ITEM_FIELDS = "title,files,facets"
PARENT_ITEM_URL = (
    f"https://www.sciencebase.gov/catalog/item/{PARENT_ITEM_ID}?"
    + urllib.parse.urlencode({"format": "json", "fields": ITEM_FIELDS})
)
CATALOG_RECORD_URL = (
    f"https://www.sciencebase.gov/catalog/item/{CATALOG_RECORD_ID}?"
    + urllib.parse.urlencode({"format": "json", "fields": ITEM_FIELDS})
)
CHILDREN_URL = (
    "https://www.sciencebase.gov/catalog/items?"
    + urllib.parse.urlencode({
        "q": "",
        "filter": f"parentId={PARENT_ITEM_ID}",
        "format": "json",
        "max": "100",
    })
)
DATA_EXTENSIONS = {".csv", ".txt", ".tsv", ".dat", ".zip"}


def _file_name(record: dict) -> str:
    return str(record.get("name") or record.get("fileName") or record.get("filename") or "")


def _file_size(record: dict) -> int | None:
    value = record.get("size") or record.get("sizeBytes") or record.get("fileSize")
    try:
        size = int(value)
    except (TypeError, ValueError):
        return None
    return size if size > 0 else None


def _download_uri(record: dict) -> str | None:
    value = record.get("downloadUri") or record.get("downloadUrl")
    from_url_field = False
    if not isinstance(value, str) or not value.strip():
        value = record.get("url")
        from_url_field = True
    if not isinstance(value, str) or not value.strip():
        return None
    parsed = urlsplit(value.strip())
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        return None
    if from_url_field and not (
        parsed.hostname == "prod-is-usgs-sb-prod-content.s3.amazonaws.com"
        or "/catalog/file/get/" in parsed.path
        or "/manager/download/" in parsed.path
    ):
        return None
    return value.strip()


def _safe_file_record(record: dict) -> dict:
    uri = _download_uri(record)
    if uri:
        parsed = urlsplit(uri)
        url_summary = {
            "scheme": parsed.scheme,
            "host": parsed.hostname,
            "query_key_names": sorted(
                {key.lower() for key, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)}
            ),
            "query_values_stored": False,
        }
    else:
        url_summary = None
    name = _file_name(record)
    return {
        "source_item_id": record.get("_source_item_id"),
        "name": PurePosixPath(name).name,
        "extension": PurePosixPath(name).suffix.lower(),
        "size_bytes": _file_size(record),
        "download_uri": url_summary,
    }


def _extract_file_records(item: dict, source_item_id: str) -> list[dict]:
    records: list[dict] = []
    top_level = item.get("files", [])
    if isinstance(top_level, list):
        records.extend(record for record in top_level if isinstance(record, dict))
    facets = item.get("facets", [])
    if isinstance(facets, list):
        for facet in facets:
            if isinstance(facet, dict) and isinstance(facet.get("files"), list):
                records.extend(record for record in facet["files"] if isinstance(record, dict))
    elif isinstance(facets, dict) and isinstance(facets.get("files"), list):
        records.extend(record for record in facets["files"] if isinstance(record, dict))

    unique: dict[tuple[str, int | None, str | None], dict] = {}
    for record in records:
        copy = dict(record)
        copy["_source_item_id"] = source_item_id
        key = (_file_name(copy), _file_size(copy), _download_uri(copy))
        unique[key] = copy
    return list(unique.values())


def _choose_candidate(records: list[dict]) -> dict | None:
    candidates = []
    for record in records:
        extension = PurePosixPath(_file_name(record)).suffix.lower()
        size = _file_size(record)
        uri = _download_uri(record)
        if extension in DATA_EXTENSIONS and size is not None and size <= MAX_FILE_BYTES and uri:
            candidates.append((size, _file_name(record).lower(), record))
    return min(candidates, key=lambda item: (item[0], item[1]))[2] if candidates else None


def _children_summary(document: dict) -> list[dict]:
    items = document.get("items", []) if isinstance(document, dict) else []
    if not isinstance(items, list):
        return []
    result = []
    for item in items[:100]:
        if not isinstance(item, dict):
            continue
        item_id = item.get("id") or item.get("itemId")
        title = item.get("title")
        if item_id:
            result.append({"id": str(item_id), "title": str(title or "")})
    return result


def audit() -> dict:
    result = {
        "experiment": "E590",
        "doi": DOI,
        "doi_parent_item_id": PARENT_ITEM_ID,
        "data_gov_catalog_record_id": CATALOG_RECORD_ID,
        "source": "USGS Grand Falls Dune Field, July 2023–November 2024",
        "metadata_fields_requested": ITEM_FIELDS.split(","),
        "parent_metadata_http_status": None,
        "parent_metadata_sha256": None,
        "parent_file_count": None,
        "children_search_http_status": None,
        "child_count": None,
        "catalog_record_metadata_http_status": None,
        "catalog_record_metadata_sha256": None,
        "catalog_record_file_count": None,
        "catalog_record_id_in_parent_children": None,
        "child_items": [],
        "file_count": 0,
        "file_inventory": [],
        "selected_file": None,
        "range_probe": None,
        "data_sample": None,
        "credentials_used": False,
        "raw_values_stored": False,
        "raw_files_committed": False,
        "signed_query_values_stored": False,
        "decision": "ACQUISITION_ERROR",
    }
    try:
        parent_files: list[dict] = []
        parent = fetch_bounded(PARENT_ITEM_URL, limit=MAX_METADATA_BYTES)
        result["parent_metadata_http_status"] = parent["status"]
        if parent["status"] == 200:
            result["parent_metadata_sha256"] = hashlib.sha256(parent["payload"]).hexdigest()
            parent_doc = json.loads(parent["payload"].decode("utf-8"))
            result["parent_title_present"] = bool(parent_doc.get("title"))
            parent_files = _extract_file_records(parent_doc, PARENT_ITEM_ID)
            result["parent_file_count"] = len(parent_files)

        children_response = fetch_bounded(CHILDREN_URL, limit=MAX_METADATA_BYTES)
        result["children_search_http_status"] = children_response["status"]
        children: list[dict] = []
        if children_response["status"] == 200:
            result["children_search_sha256"] = hashlib.sha256(children_response["payload"]).hexdigest()
            children = _children_summary(json.loads(children_response["payload"].decode("utf-8")))
            result["child_count"] = len(children)
            result["child_items"] = children
            result["catalog_record_id_in_parent_children"] = any(
                item["id"] == CATALOG_RECORD_ID for item in children
            )

        catalog_files: list[dict] = []
        catalog_record = fetch_bounded(CATALOG_RECORD_URL, limit=MAX_METADATA_BYTES)
        result["catalog_record_metadata_http_status"] = catalog_record["status"]
        if catalog_record["status"] == 200:
            result["catalog_record_metadata_sha256"] = hashlib.sha256(catalog_record["payload"]).hexdigest()
            catalog_doc = json.loads(catalog_record["payload"].decode("utf-8"))
            result["catalog_record_title_present"] = bool(catalog_doc.get("title"))
            catalog_files = _extract_file_records(catalog_doc, CATALOG_RECORD_ID)
            result["catalog_record_file_count"] = len(catalog_files)

        all_files = parent_files + catalog_files
        unique_files: dict[tuple[str | None, str, int | None], dict] = {}
        for record in all_files:
            key = (record.get("_source_item_id"), _file_name(record), _file_size(record))
            unique_files[key] = record
        all_files = list(unique_files.values())
        result["file_count"] = len(all_files)
        result["file_inventory"] = [_safe_file_record(record) for record in all_files]

        if not all_files:
            if parent["status"] != 200 and catalog_record["status"] != 200:
                result["decision"] = "METADATA_UNAVAILABLE"
            else:
                result["decision"] = "NO_FILE_RECORDS_IN_TOP_LEVEL_OR_FACETS"
            return result

        candidate = _choose_candidate(all_files)
        if candidate is None:
            result["decision"] = "NO_SMALL_METADATA_LINKED_DELIMITED_FILE"
            return result

        name = _file_name(candidate)
        size = _file_size(candidate)
        uri = _download_uri(candidate)
        result["selected_file"] = _safe_file_record(candidate)
        if size is None or uri is None:
            result["decision"] = "SELECTED_FILE_METADATA_INCOMPLETE"
            return result

        expected_end = min(MAX_HEADER_BYTES - 1, size - 1)
        header = fetch_bounded(
            uri,
            limit=MAX_HEADER_BYTES,
            range_header=f"bytes=0-{expected_end}",
        )
        content_range = parse_content_range(header["headers"].get("Content-Range"))
        range_valid = bool(
            content_range
            and content_range[0] == 0
            and content_range[1] == expected_end
            and content_range[2] == size
            and len(header["payload"]) == expected_end + 1
        )
        result["range_probe"] = {
            "http_status": header["status"],
            "content_type": header["headers"].get("Content-Type"),
            "content_range_valid": range_valid,
            "content_range_total_bytes": content_range[2] if content_range else None,
            "bytes_read": len(header["payload"]),
            "sha256": hashlib.sha256(header["payload"]).hexdigest(),
            "host": urlsplit(header["final_url"]).hostname,
        }
        if header["status"] != 206 or not range_valid:
            result["decision"] = "BOUNDED_RANGE_NOT_CONFIRMED"
            return result

        full = fetch_bounded(uri, limit=MAX_FILE_BYTES)
        if full["status"] != 200 or len(full["payload"]) != size:
            result["decision"] = "FULL_FILE_SIZE_OR_STATUS_MISMATCH"
            result["full_file_http_status"] = full["status"]
            result["full_file_bytes"] = len(full["payload"])
            return result

        sample_summary = inspect_payload(name, full["payload"])
        sample_summary.pop("prefix_hex", None)
        result["data_sample"] = {
            "bytes": len(full["payload"]),
            "sha256": hashlib.sha256(full["payload"]).hexdigest(),
            "summary": sample_summary,
        }
        result["decision"] = "SMALL_PUBLIC_FIELD_DATA_FILE_ACQUIRED_AND_PROFILED"
        return result
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": receipt["experiment"],
        "decision": receipt["decision"],
        "parent_metadata_http_status": receipt["parent_metadata_http_status"],
        "parent_file_count": receipt["parent_file_count"],
        "children_search_http_status": receipt["children_search_http_status"],
        "child_count": receipt["child_count"],
        "catalog_record_metadata_http_status": receipt["catalog_record_metadata_http_status"],
        "catalog_record_file_count": receipt["catalog_record_file_count"],
        "catalog_record_id_in_parent_children": receipt["catalog_record_id_in_parent_children"],
        "file_count": receipt["file_count"],
        "selected_file": receipt["selected_file"],
        "data_sample": receipt["data_sample"],
        "credentials_used": receipt["credentials_used"],
        "raw_values_stored": receipt["raw_values_stored"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
