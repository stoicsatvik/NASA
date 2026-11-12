"""E578: bounded acquisition/schema audit of the independent USGS analog-site layer.

The probe reads only a public ScienceBase metadata record and, when a small
explicitly linked file passes a byte-range check, a file capped at 5 MB.
It stores hashes, schema, counts and aggregate bounds, never raw site rows.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
import struct
import urllib.parse
import zipfile
from pathlib import Path, PurePosixPath

from experiments.e577_grand_falls_2017_2019_access_probe import (
    MAX_FILE_BYTES,
    MAX_HEADER_BYTES,
    MAX_METADATA_BYTES,
    fetch_bounded,
    parse_content_range,
    safe_url_summary,
    summarize_text,
)

ITEM_ID = "5f88940b82cebb8c13d912ee"
DOI = "10.5066/P9J72921"
ITEM_FIELDS = "title,files.name,files.size,files.downloadUri,files.url"
ITEM_URL = (
    f"https://www.sciencebase.gov/catalog/item/{ITEM_ID}?"
    + urllib.parse.urlencode({"format": "json", "fields": ITEM_FIELDS})
)
SUPPORTED_EXTENSIONS = {".zip", ".geojson", ".json", ".csv", ".tsv", ".txt"}


def file_name(record: dict) -> str:
    return str(record.get("name") or record.get("fileName") or record.get("filename") or "")


def file_size(record: dict) -> int | None:
    value = record.get("size") or record.get("sizeBytes") or record.get("fileSize")
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def download_uri(record: dict) -> str | None:
    value = record.get("downloadUri") or record.get("downloadUrl")
    return value.strip() if isinstance(value, str) and value.strip() else None


def choose_candidate(files: list[dict]) -> dict | None:
    candidates = []
    for record in files:
        name = file_name(record)
        size = file_size(record)
        uri = download_uri(record)
        if (
            PurePosixPath(name).suffix.lower() in SUPPORTED_EXTENSIONS
            and size is not None
            and size <= MAX_FILE_BYTES
            and uri
        ):
            candidates.append((size, name.lower(), record))
    return min(candidates, key=lambda item: (item[0], item[1]))[2] if candidates else None


def parse_shapefile_header(payload: bytes) -> dict:
    if len(payload) < 100:
        raise ValueError("shapefile header shorter than 100 bytes")
    file_code = struct.unpack_from(">i", payload, 0)[0]
    file_length_bytes = struct.unpack_from(">i", payload, 24)[0] * 2
    version = struct.unpack_from("<i", payload, 28)[0]
    shape_type = struct.unpack_from("<i", payload, 32)[0]
    bounds = struct.unpack_from("<4d", payload, 36)
    if file_code != 9994 or version != 1000 or file_length_bytes < 100:
        raise ValueError("invalid shapefile header signature or length")
    return {
        "file_code": file_code,
        "version": version,
        "shape_type": shape_type,
        "declared_bytes": file_length_bytes,
        "bounds": [float(value) for value in bounds],
    }


def parse_dbf_header(payload: bytes) -> dict:
    if len(payload) < 33:
        raise ValueError("DBF header too short")
    record_count = struct.unpack_from("<I", payload, 4)[0]
    header_length, record_length = struct.unpack_from("<HH", payload, 8)
    if header_length < 33 or header_length > len(payload):
        raise ValueError("DBF header length outside inspected bytes")
    fields = []
    offset = 32
    while offset + 32 <= header_length and payload[offset] != 0x0D:
        raw_name = payload[offset : offset + 11].split(b"\x00", 1)[0]
        fields.append({
            "name": raw_name.decode("ascii", errors="replace").strip(),
            "type": chr(payload[offset + 11]),
            "width": int(payload[offset + 16]),
            "decimals": int(payload[offset + 17]),
        })
        offset += 32
    return {
        "record_count": int(record_count),
        "header_length": int(header_length),
        "record_length": int(record_length),
        "fields": fields,
    }


def summarize_zip(payload: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        files = [item for item in archive.infolist() if not item.is_dir()]
        members = [
            {
                "name": PurePosixPath(item.filename).name,
                "extension": PurePosixPath(item.filename).suffix.lower(),
                "size_bytes": item.file_size,
            }
            for item in files
        ]
        by_ext = {}
        for item in files:
            by_ext.setdefault(PurePosixPath(item.filename).suffix.lower(), []).append(item)
        summary = {
            "member_count": len(files),
            "members": members,
            "shapefile": None,
            "dbf": None,
            "projection": None,
        }
        shp = sorted(by_ext.get(".shp", []), key=lambda item: item.filename.lower())
        dbf = sorted(by_ext.get(".dbf", []), key=lambda item: item.filename.lower())
        prj = sorted(by_ext.get(".prj", []), key=lambda item: item.filename.lower())
        if shp:
            with archive.open(shp[0]) as stream:
                summary["shapefile"] = parse_shapefile_header(stream.read(100))
        if dbf:
            with archive.open(dbf[0]) as stream:
                summary["dbf"] = parse_dbf_header(stream.read(4096))
        if prj:
            with archive.open(prj[0]) as stream:
                projection = stream.read(8192).decode("utf-8", errors="replace")
            epsg = re.findall(r'(?:AUTHORITY|ID)\s*\[\s*"EPSG"\s*,\s*"?(\d+)"?', projection, flags=re.I)
            summary["projection"] = {
                "bytes_inspected": len(projection.encode("utf-8")),
                "sha256": hashlib.sha256(projection.encode("utf-8")).hexdigest(),
                "epsg_authority_candidates": sorted(set(epsg)),
                "wkt_stored": False,
            }
        return summary


def summarize_geojson(payload: bytes) -> dict:
    document = json.loads(payload.decode("utf-8"))
    features = document.get("features", []) if isinstance(document, dict) else []
    property_keys = sorted({
        str(key)
        for feature in features if isinstance(feature, dict)
        for key in (feature.get("properties") or {}).keys()
    })
    geometry_types = sorted({
        str((feature.get("geometry") or {}).get("type"))
        for feature in features if isinstance(feature, dict)
    })
    return {
        "format": "geojson",
        "feature_count": len(features),
        "property_keys": property_keys,
        "geometry_types": geometry_types,
        "raw_features_stored": False,
    }


def inspect_payload(name: str, payload: bytes) -> dict:
    extension = PurePosixPath(name).suffix.lower()
    result = {
        "bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "prefix_hex": payload[:8].hex(),
    }
    if extension == ".zip" or payload.startswith(b"PK\x03\x04"):
        result["format"] = "zip"
        result["vector_summary"] = summarize_zip(payload)
    elif extension in {".geojson", ".json"}:
        result.update(summarize_geojson(payload))
    elif extension in {".csv", ".tsv", ".txt"}:
        result["format"] = "delimited_text"
        result["schema_summary"] = summarize_text(payload)
    else:
        result["format"] = "unrecognized"
    return result


def safe_file_record(record: dict) -> dict:
    uri = download_uri(record)
    preview = record.get("url") if isinstance(record.get("url"), str) else None
    return {
        "name": file_name(record),
        "size_bytes": file_size(record),
        "download_uri": safe_url_summary(uri) if uri else None,
        "preview_url": safe_url_summary(preview) if preview else None,
    }


def audit() -> dict:
    metadata = fetch_bounded(ITEM_URL, limit=MAX_METADATA_BYTES)
    result = {
        "experiment": "E578",
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
        "credentials_used": False,
        "raw_rows_stored": False,
        "raw_files_committed": False,
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
    result["file_inventory"] = [
        safe_file_record(record) for record in files if isinstance(record, dict)
    ]
    candidate = choose_candidate([record for record in files if isinstance(record, dict)])
    if candidate is None:
        result["decision"] = "NO_SMALL_EXPLICITLY_LINKED_VECTOR_FILE"
        return result

    name = file_name(candidate)
    size = file_size(candidate)
    uri = download_uri(candidate)
    result["selected_file"] = safe_file_record(candidate)
    range_end = min(MAX_HEADER_BYTES - 1, size - 1)
    header = fetch_bounded(uri, limit=range_end + 1, range_header=f"bytes=0-{range_end}")
    content_range = parse_content_range(header["headers"].get("Content-Range"))
    range_valid = bool(
        content_range
        and content_range[0] == 0
        and content_range[1] == range_end
        and len(header["payload"]) == range_end + 1
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

    full = fetch_bounded(uri, limit=MAX_FILE_BYTES)
    result["full_file_http_status"] = full["status"]
    if full["status"] != 200 or len(full["payload"]) != size:
        result["decision"] = "FULL_FILE_NOT_SIZE_MATCHED"
        result["full_file_bytes"] = len(full["payload"])
        return result
    result["data_sample"] = inspect_payload(name, full["payload"])
    vector = result["data_sample"].get("vector_summary", {})
    dbf = vector.get("dbf") if isinstance(vector, dict) else None
    shp = vector.get("shapefile") if isinstance(vector, dict) else None
    if dbf and shp and dbf.get("record_count", 0) > 0:
        result["decision"] = "PUBLIC_ANALOG_POINT_LAYER_ACQUIRED_SCHEMA_VERIFIED"
    elif result["data_sample"].get("feature_count", 0) > 0:
        result["decision"] = "PUBLIC_ANALOG_FEATURE_COLLECTION_ACQUIRED"
    else:
        result["decision"] = "PUBLIC_FILE_ACQUIRED_SCHEMA_INCOMPLETE"
    return result


def summarize_receipt(receipt: dict) -> dict:
    sample = receipt.get("data_sample")
    vector = sample.get("vector_summary") if isinstance(sample, dict) else None
    dbf = vector.get("dbf") if isinstance(vector, dict) else None
    shp = vector.get("shapefile") if isinstance(vector, dict) else None
    return {
        "experiment": receipt.get("experiment"),
        "decision": receipt.get("decision"),
        "metadata_http_status": receipt.get("metadata_http_status"),
        "file_count": receipt.get("file_count"),
        "selected_file": (
            receipt.get("selected_file", {}).get("name")
            if isinstance(receipt.get("selected_file"), dict)
            else None
        ),
        "record_count": dbf.get("record_count") if isinstance(dbf, dict) else None,
        "dbf_fields": [field.get("name") for field in dbf.get("fields", [])] if isinstance(dbf, dict) else [],
        "shape_type": shp.get("shape_type") if isinstance(shp, dict) else None,
        "credentials_used": False,
        "raw_rows_stored": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--out",
        type=Path,
        default=Path(".artifacts/e578/known-terrestrial-analog-sites.json"),
    )
    args = parser.parse_args()
    try:
        receipt = audit()
    except Exception as error:
        receipt = {
            "experiment": "E578",
            "doi": DOI,
            "item_id": ITEM_ID,
            "decision": "ACQUISITION_ERROR",
            "error_type": type(error).__name__,
            "error_message": str(error)[:300],
            "credentials_used": False,
            "raw_rows_stored": False,
            "raw_files_committed": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(summarize_receipt(receipt), sort_keys=True))


if __name__ == "__main__":
    main()
