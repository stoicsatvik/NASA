"""E577: bounded anonymous access probe for the independent 2017–2019 Grand Falls release.

Only a metadata-selected small CSV/TXT/ZIP is eligible. The workflow stores a
sanitized receipt, never raw field rows, raw URLs, signed query values, or files.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import re
import statistics
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

ITEM_ID = "5f6e51f182ce38aaa24a73a7"
DOI = "10.5066/P9IYGDGQ"
ITEM_FIELDS = "title,files.name,files.size,files.downloadUri,files.url"
ITEM_URL = f"https://www.sciencebase.gov/catalog/item/{ITEM_ID}?" + urllib.parse.urlencode({"format": "json", "fields": ITEM_FIELDS})
ALLOWED_HOSTS = {
    "www.sciencebase.gov",
    "sciencebase.gov",
    "sciencebase.usgs.gov",
    "prod-is-usgs-sb-prod-content.s3.amazonaws.com",
}
MAX_METADATA_BYTES = 5_000_000
MAX_HEADER_BYTES = 4_096
MAX_FILE_BYTES = 5_000_000
TIMEOUT_SECONDS = 20
USER_AGENT = "UnifiedParallelFoundry-E577-public-data-probe/1.0"
DATA_EXTENSIONS = {".csv", ".txt", ".tsv", ".dat", ".zip"}
SUMMARY_FIELD = re.compile(r"wind|speed|flux|sediment|weight|temperature|pressure|direction|sensit|bsne", re.I)
TIME_FIELD = re.compile(r"date|time|timestamp|datetime", re.I)


class ProbeError(RuntimeError):
    pass


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
            raise urllib.error.URLError("redirect outside pinned public ScienceBase/S3 hosts")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def validate_public_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise ProbeError("URL outside pinned public HTTPS host allowlist")


def safe_url_summary(url: str) -> dict:
    parsed = urllib.parse.urlsplit(url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "path": parsed.path,
        "query_key_names": sorted({k.lower() for k, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)}),
        "query_values_stored": False,
    }


def fetch_bounded(url: str, *, limit: int, range_header: str | None = None) -> dict:
    validate_public_url(url)
    headers = {"User-Agent": USER_AGENT, "Accept": "*/*"}
    if range_header:
        headers["Range"] = range_header
    request = urllib.request.Request(url, headers=headers)
    opener = urllib.request.build_opener(SafeRedirectHandler())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read(limit + 1)
            if len(payload) > limit:
                raise ProbeError("response exceeded byte cap")
            final_url = response.geturl()
            validate_public_url(final_url)
            return {"status": response.status, "headers": response.headers, "payload": payload, "final_url": final_url}
    except urllib.error.HTTPError as error:
        payload = error.read(limit + 1)
        if len(payload) > limit:
            payload = payload[:limit]
        final_url = error.geturl()
        validate_public_url(final_url)
        return {"status": error.code, "headers": error.headers, "payload": payload, "final_url": final_url}


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


def choose_candidate(files: list[dict]) -> dict | None:
    candidates = []
    for record in files:
        name = _file_name(record)
        extension = PurePosixPath(name).suffix.lower()
        size = _file_size(record)
        uri = _download_uri(record)
        if extension in DATA_EXTENSIONS and size is not None and size <= MAX_FILE_BYTES and uri:
            candidates.append((size, name.lower(), record))
    return min(candidates, key=lambda item: (item[0], item[1]))[2] if candidates else None


def parse_content_range(value: str | None) -> tuple[int, int, int] | None:
    if not value:
        return None
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", value.strip())
    if not match:
        return None
    start, end, total = map(int, match.groups())
    if start > end or end >= total:
        return None
    return start, end, total


def _delimiter(header_line: str) -> str:
    candidates = [",", "\t", ";", "|"]
    return max(candidates, key=header_line.count)


def summarize_text(payload: bytes) -> dict:
    decoded = payload.decode("utf-8-sig", errors="replace")
    first_line = next((line for line in decoded.splitlines() if line.strip()), "")
    if not first_line:
        return {"format": "empty_text", "header_columns": [], "row_count": 0}
    delimiter = _delimiter(first_line)
    reader = csv.DictReader(io.StringIO(decoded), delimiter=delimiter)
    columns = [str(name).strip() for name in (reader.fieldnames or [])]
    numeric_values: dict[str, list[float]] = {c: [] for c in columns if SUMMARY_FIELD.search(c)}
    time_bounds: dict[str, list[str]] = {c: [] for c in columns if TIME_FIELD.search(c)}
    row_count = 0
    for row in reader:
        row_count += 1
        for column in numeric_values:
            try:
                value = float((row.get(column) or "").strip())
            except (TypeError, ValueError):
                continue
            if math.isfinite(value):
                numeric_values[column].append(value)
        for column in time_bounds:
            value = (row.get(column) or "").strip()
            if value:
                time_bounds[column].append(value)
    summaries = {}
    for column, values in numeric_values.items():
        if values:
            summaries[column] = {
                "n": len(values),
                "missing_or_non_numeric": row_count - len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.fmean(values),
                "std_sample": statistics.stdev(values) if len(values) > 1 else 0.0,
            }
    bounds = {
        column: {"min": min(values), "max": max(values), "n": len(values)}
        for column, values in time_bounds.items() if values
    }
    return {
        "format": "delimited_text",
        "delimiter": "tab" if delimiter == "\t" else delimiter,
        "header_columns": columns,
        "row_count": row_count,
        "time_bounds": bounds,
        "numeric_summaries": summaries,
    }


def summarize_zip(payload: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = [
            info for info in archive.infolist()
            if not info.is_dir()
            and PurePosixPath(info.filename).suffix.lower() in {".csv", ".txt", ".tsv", ".dat"}
            and 0 < info.file_size <= MAX_FILE_BYTES
        ]
        if not members:
            return {"format": "zip_without_small_delimited_member", "member_count": len(archive.infolist())}
        member = min(members, key=lambda info: (info.file_size, info.filename.lower()))
        data = archive.read(member)
        return {
            "format": "zip_with_delimited_member",
            "member_name": PurePosixPath(member.filename).name,
            "member_size_bytes": len(data),
            "member_sha256": hashlib.sha256(data).hexdigest(),
            "member_summary": summarize_text(data),
        }


def inspect_payload(name: str, payload: bytes) -> dict:
    extension = PurePosixPath(name).suffix.lower()
    result = {"bytes": len(payload), "sha256": hashlib.sha256(payload).hexdigest(), "prefix_hex": payload[:8].hex()}
    if extension == ".zip" or payload.startswith(b"PK\x03\x04"):
        result["data_summary"] = summarize_zip(payload)
    elif extension in {".csv", ".txt", ".tsv", ".dat"}:
        result["data_summary"] = summarize_text(payload)
    else:
        result["data_summary"] = {"format": "unrecognized_or_non_tabular"}
    return result


def _safe_file_record(record: dict) -> dict:
    uri = _download_uri(record)
    url = record.get("url") if isinstance(record.get("url"), str) else None
    return {
        "name": _file_name(record),
        "size_bytes": _file_size(record),
        "download_uri": safe_url_summary(uri) if uri else None,
        "preview_url": safe_url_summary(url) if url else None,
    }


def audit() -> dict:
    metadata = fetch_bounded(ITEM_URL, limit=MAX_METADATA_BYTES)
    result = {
        "experiment": "E577",
        "doi": DOI,
        "item_id": ITEM_ID,
        "metadata_fields_requested": ITEM_FIELDS.split(","),
        "metadata_http_status": metadata["status"],
        "metadata_bytes": len(metadata["payload"]),
        "metadata_sha256": hashlib.sha256(metadata["payload"]).hexdigest(),
        "metadata_url": safe_url_summary(metadata["final_url"]),
        "file_inventory": [],
        "selected_file": None,
        "header_probe": None,
        "data_sample": None,
        "raw_values_stored": False,
        "raw_files_committed": False,
        "credentials_used": False,
        "decision": "METADATA_UNAVAILABLE",
    }
    if metadata["status"] != 200:
        return result
    item = json.loads(metadata["payload"].decode("utf-8"))
    files = item.get("files", [])
    if not isinstance(files, list):
        files = []
    result["item_title_present"] = bool(item.get("title"))
    result["file_count"] = len(files)
    result["file_inventory"] = [_safe_file_record(f) for f in files if isinstance(f, dict)]
    candidate = choose_candidate([f for f in files if isinstance(f, dict)])
    if candidate is None:
        result["decision"] = "NO_SMALL_METADATA_LINKED_DELIMITED_FILE"
        return result
    name = _file_name(candidate)
    size = _file_size(candidate)
    uri = _download_uri(candidate)
    result["selected_file"] = _safe_file_record(candidate)
    header = fetch_bounded(uri, limit=MAX_HEADER_BYTES, range_header=f"bytes=0-{MAX_HEADER_BYTES-1}")
    content_range = parse_content_range(header["headers"].get("Content-Range"))
    expected_end = min(MAX_HEADER_BYTES - 1, size - 1)
    range_valid = bool(
        content_range
        and content_range[0] == 0
        and content_range[1] == expected_end
        and len(header["payload"]) == expected_end + 1
    )
    result["header_probe"] = {
        "http_status": header["status"],
        "content_type": header["headers"].get("Content-Type"),
        "content_range": header["headers"].get("Content-Range"),
        "content_range_valid": range_valid,
        "bytes_read": len(header["payload"]),
        "final_url": safe_url_summary(header["final_url"]),
        "header_sha256": hashlib.sha256(header["payload"]).hexdigest(),
    }
    if header["status"] != 206 or not range_valid:
        result["decision"] = "BOUNDED_RANGE_NOT_CONFIRMED"
        return result
    if content_range[2] != size:
        result["metadata_vs_content_range_size_match"] = False
        result["content_range_total_bytes"] = content_range[2]
        result["decision"] = "METADATA_SIZE_MISMATCH"
        return result
    result["metadata_vs_content_range_size_match"] = True
    full = fetch_bounded(uri, limit=MAX_FILE_BYTES, range_header=None)
    result["full_file_http_status"] = full["status"]
    result["full_file_content_type"] = full["headers"].get("Content-Type")
    if full["status"] != 200 or len(full["payload"]) != size:
        result["decision"] = "FULL_FILE_NOT_SIZE_MATCHED"
        result["full_file_bytes"] = len(full["payload"])
        return result
    result["data_sample"] = inspect_payload(name, full["payload"])
    result["decision"] = "SMALL_PUBLIC_DATA_FILE_ACQUIRED_AND_PROFILED"
    return result


def summarize_receipt(receipt: dict) -> dict:
    """Return a null-safe, credential-free summary of an E577 receipt."""
    data_sample = receipt.get("data_sample")
    data_summary = (
        data_sample.get("data_summary")
        if isinstance(data_sample, dict)
        else None
    )
    row_count = (
        data_summary.get("row_count")
        if isinstance(data_summary, dict)
        else None
    )
    if row_count is None and isinstance(data_summary, dict):
        member_summary = data_summary.get("member_summary")
        if isinstance(member_summary, dict):
            row_count = member_summary.get("row_count")
    selected_file = receipt.get("selected_file")
    selected_name = (
        selected_file.get("name")
        if isinstance(selected_file, dict)
        else None
    )
    return {
        "experiment": receipt.get("experiment"),
        "decision": receipt.get("decision"),
        "metadata_http_status": receipt.get("metadata_http_status"),
        "file_count": receipt.get("file_count"),
        "selected_file": selected_name,
        "data_rows": row_count,
        "credentials_used": False,
        "raw_values_stored": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e577/grand-falls-2017-2019.json"))
    args = parser.parse_args()
    try:
        receipt = audit()
    except Exception as error:
        receipt = {
            "experiment": "E577",
            "doi": DOI,
            "item_id": ITEM_ID,
            "decision": "ACQUISITION_ERROR",
            "error_type": type(error).__name__,
            "error_message": str(error)[:300],
            "raw_values_stored": False,
            "raw_files_committed": False,
            "credentials_used": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summarize_receipt(receipt), sort_keys=True))


if __name__ == "__main__":
    main()
