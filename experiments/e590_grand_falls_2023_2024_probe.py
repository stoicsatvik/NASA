"""E590: bounded anonymous access audit for the 2023–2024 Grand Falls release.

The source is a distinct USGS data release (DOI 10.5066/P13HPPYM), not a
retry of the 2017–2019 item used by E577. At most one metadata-selected
small CSV/TXT/TSV/DAT/ZIP is acquired. Only hashes and aggregate summaries
are written; no raw rows, signed URLs, credentials or field coordinates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.parse
from pathlib import Path, PurePosixPath

from experiments.e577_grand_falls_2017_2019_access_probe import (
    MAX_FILE_BYTES,
    MAX_HEADER_BYTES,
    MAX_METADATA_BYTES,
    choose_candidate,
    fetch_bounded,
    inspect_payload,
    parse_content_range,
)

ITEM_ID = "67bf94acd34e8876fcbfc91b"
DOI_REDIRECT_ITEM_ID = "677ee6bed34e760b392c4aa3"
DOI = "10.5066/P13HPPYM"
ITEM_FIELDS = "title,files.name,files.size,files.downloadUri,files.url"
ITEM_URL = (
    f"https://www.sciencebase.gov/catalog/item/{ITEM_ID}?"
    + urllib.parse.urlencode({"format": "json", "fields": ITEM_FIELDS})
)


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
    return value.strip() if isinstance(value, str) and value.strip() else None


def _safe_file_record(record: dict) -> dict:
    uri = _download_uri(record)
    if uri:
        parsed = urllib.parse.urlsplit(uri)
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
        "name": PurePosixPath(name).name,
        "extension": PurePosixPath(name).suffix.lower(),
        "size_bytes": _file_size(record),
        "download_uri": url_summary,
    }


def audit() -> dict:
    result = {
        "experiment": "E590",
        "doi": DOI,
        "item_id": ITEM_ID,
        "doi_redirect_item_id": DOI_REDIRECT_ITEM_ID,
        "source": "USGS Grand Falls Dune Field, July 2023–November 2024",
        "metadata_fields_requested": ITEM_FIELDS.split(","),
        "metadata_http_status": None,
        "metadata_bytes": None,
        "metadata_sha256": None,
        "file_count": None,
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
        metadata = fetch_bounded(ITEM_URL, limit=MAX_METADATA_BYTES)
        result["metadata_http_status"] = metadata["status"]
        result["metadata_bytes"] = len(metadata["payload"])
        result["metadata_sha256"] = hashlib.sha256(metadata["payload"]).hexdigest()
        if metadata["status"] != 200:
            result["decision"] = "METADATA_HTTP_ERROR"
            return result

        item = json.loads(metadata["payload"].decode("utf-8"))
        result["item_title_present"] = bool(item.get("title"))
        files = item.get("files", [])
        if not isinstance(files, list):
            files = []
        files = [record for record in files if isinstance(record, dict)]
        result["file_count"] = len(files)
        result["file_inventory"] = [_safe_file_record(record) for record in files]

        candidate = choose_candidate(files)
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
            "host": urllib.parse.urlsplit(header["final_url"]).hostname,
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
    except Exception as exc:  # preserve bounded transport/parser failure without leaking URLs
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
        "metadata_http_status": receipt["metadata_http_status"],
        "file_count": receipt["file_count"],
        "selected_file": receipt["selected_file"],
        "data_sample": (
            {
                "bytes": receipt["data_sample"]["bytes"],
                "sha256": receipt["data_sample"]["sha256"],
                "summary": receipt["data_sample"]["summary"],
            }
            if receipt["data_sample"] else None
        ),
        "credentials_used": receipt["credentials_used"],
        "raw_values_stored": receipt["raw_values_stored"],
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
