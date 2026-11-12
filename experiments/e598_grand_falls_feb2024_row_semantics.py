"""E598: bounded full-file row/group audit of the February 2024 Grand Falls release."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
from pathlib import Path

from experiments.e590_grand_falls_2023_2024_probe import (
    CATALOG_RECORD_ID,
    CATALOG_RECORD_URL,
    MAX_METADATA_BYTES,
    _download_uri,
    _extract_file_records,
    _file_name,
    _file_size,
)
from experiments.e595_grand_falls_sensor_dictionary import (
    EXPECTED_CATALOG_METADATA_SHA256,
    fetch_strict_bounded,
    validate_public_url,
)
from experiments.e597_grand_falls_row_group_semantics import CHANNELS, summarize_rows

EXPERIMENT = "E598"
EXPECTED_FILE_NAME = "SensorData_02-14-24_to_02-16-24.csv"
EXPECTED_FILE_SIZE = 1_091_813
MAX_FILE_BYTES = 5_000_000


def select_exact_file(records: list[dict]) -> dict:
    matches = [
        record for record in records
        if _file_name(record) == EXPECTED_FILE_NAME
        and _file_size(record) == EXPECTED_FILE_SIZE
    ]
    if len(matches) != 1:
        raise ValueError(f"expected exactly one pinned February 2024 CSV record; found {len(matches)}")
    return matches[0]


def classify_csv_response(content_type: str, payload: bytes) -> str | None:
    if content_type == "text/csv":
        return "STRICT_TEXT_CSV"
    try:
        header = next(csv.reader(io.StringIO(payload.decode("utf-8-sig"))))
    except (UnicodeDecodeError, csv.Error, StopIteration):
        return None
    required = {"Date and Time", "Record Number"}
    for columns in CHANNELS.values():
        required.update(columns)
    if len(header) != len(set(header)) or not required.issubset(set(header)):
        return None
    return "NONSTANDARD_CONTENT_TYPE_BUT_EXACT_CSV_SCHEMA_VALID"


def summarize_payload(payload: bytes) -> dict:
    if len(payload) != EXPECTED_FILE_SIZE:
        raise ValueError("payload byte count differs from the exact catalogue size")
    digest = hashlib.sha256(payload).hexdigest()
    try:
        text = payload.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        header = next(reader)
        rows = list(reader)
    except (UnicodeDecodeError, csv.Error, StopIteration) as exc:
        return {
            "experiment": EXPERIMENT,
            "parse_status": "FAILED_CLOSED",
            "parse_error_class": type(exc).__name__,
            "parse_error": str(exc)[:240],
            "sample": {
                "mode": "bounded_exact_file",
                "file_bytes": len(payload),
                "file_sha256": digest,
                "raw_file_retained": False,
                "raw_rows_retained": False,
            },
        }

    try:
        summary = summarize_rows(header, rows)
    except (ValueError, TypeError) as exc:
        return {
            "experiment": EXPERIMENT,
            "parse_status": "FAILED_CLOSED",
            "parse_error_class": type(exc).__name__,
            "parse_error": str(exc)[:240],
            "schema": {
                "column_count": len(header),
                "required_channel_schema_present": False,
            },
            "sample": {
                "mode": "bounded_exact_file",
                "file_bytes": len(payload),
                "file_sha256": digest,
                "raw_file_retained": False,
                "raw_rows_retained": False,
            },
        }

    timestamps = summary["timestamps"]
    vectors = summary["within_timestamp_group"]
    records = summary["record_number"]
    reference_2023 = {
        "source_file": "SensorData_07-07-23_to_11-03-23.csv",
        "sample_mode": "5 MB bounded prefix of 67,050,032-byte file",
        "row_count": 85_145,
        "timestamp_groups": 14_192,
        "group_size_distribution": {"2": 1, "3": 1, "6": 14_190},
        "unique_channel_vector_count_distribution": {
            "1": 10_480, "2": 2_902, "3": 614, "4": 176, "5": 18, "6": 2
        },
        "record_ids_unique": True,
        "record_number_unit_steps": 85_144,
    }
    return {
        "experiment": EXPERIMENT,
        "parse_status": "PARSED",
        "source_item_id": CATALOG_RECORD_ID,
        "source_file_name": EXPECTED_FILE_NAME,
        "source_file_size_bytes": EXPECTED_FILE_SIZE,
        "sample": {
            "mode": "bounded_exact_file",
            "file_bytes": len(payload),
            "file_sha256": digest,
            "full_small_file_read": True,
            "raw_file_retained": False,
            "raw_rows_retained": False,
            "raw_timestamps_retained": False,
            "raw_record_numbers_retained": False,
            "raw_channel_values_retained": False,
        },
        "schema": {
            "column_count": len(header),
            "required_channel_schema_present": True,
            "incomplete_rows_dropped": summary["incomplete_rows_dropped"],
        },
        "row_count": summary["row_count"],
        "record_number": records,
        "timestamps": timestamps,
        "within_timestamp_group": vectors,
        "channel_summary": summary["channel_summary"],
        "comparison_to_2023": {
            "reference": reference_2023,
            "group_size_distribution_exactly_matches": (
                timestamps["group_size_distribution"] == reference_2023["group_size_distribution"]
            ),
            "record_ids_unique_in_this_file": (
                records["unique_record_ids"] == summary["row_count"]
            ),
            "all_timestamp_groups_have_repeated_rows": timestamps["all_groups_repeated"],
            "groups_with_channel_vector_duplicates": (
                vectors["groups_with_all_rows_channel_vectors_identical"]
                + vectors["groups_with_partial_channel_vector_duplicates"]
            ),
            "groups_with_all_channel_vectors_distinct": (
                vectors["groups_with_all_rows_channel_vectors_distinct"]
            ),
        },
        "claim_state": {
            "February_2024_row_and_timestamp_structure": "MEASURED",
            "cross_release_pattern_recurrence": "MEASURED_DESCRIPTIVELY_ONLY",
            "physical_cause_of_repeated_rows": "NOT_YET_PROVEN",
            "sensor_synchronization": "NOT_YET_PROVEN",
            "sensor_calibration": "NOT_YET_PROVEN",
            "sediment_mass_conversion": "NOT_YET_PROVEN",
            "cross_body_similarity": "NOT_YET_PROVEN",
            "known_site_recovery": "NOT_YET_MEASURED",
        },
    }


def rejected_size_mismatch_receipt(
    *,
    metadata_sha256: str,
    metadata_status: int,
    response_status: int,
    content_type: str,
    content_length: int,
    payload: bytes,
    final_host: str,
) -> dict:
    """Return a sanitized negative receipt without parsing a size-mismatched payload."""
    return {
        "experiment": EXPERIMENT,
        "parse_status": "REJECTED_CATALOGUE_SIZE_MISMATCH",
        "source_item_id": CATALOG_RECORD_ID,
        "source_file_name": EXPECTED_FILE_NAME,
        "source_file_size_bytes": EXPECTED_FILE_SIZE,
        "response": {
            "http_status": response_status,
            "content_type": content_type,
            "content_length_header": content_length,
            "bytes_read": len(payload),
            "payload_sha256": hashlib.sha256(payload).hexdigest(),
            "catalogue_size_match": False,
            "csv_header_admissible": classify_csv_response(content_type, payload) is not None,
        },
        "claim_state": {
            "exact_catalogue_file_identity": "SUPPORTED_AS_PINNED",
            "metadata_supplied_download_payload": "NOT_ESTABLISHED",
            "row_semantics": "NOT_YET_MEASURED",
            "cross_body_similarity": "NOT_YET_PROVEN",
            "known_site_recovery": "NOT_YET_MEASURED",
        },
        "provenance": {
            "catalog_metadata_sha256": metadata_sha256,
            "catalog_metadata_http_status": metadata_status,
            "csv_http_status": response_status,
            "csv_final_host": final_host,
            "credentials_used": False,
            "read_limit_bytes": MAX_FILE_BYTES,
            "raw_payload_retained": False,
            "raw_urls_retained": False,
        },
    }


def acquire_and_audit() -> dict:
    metadata = fetch_strict_bounded(CATALOG_RECORD_URL, limit=MAX_METADATA_BYTES)
    if metadata["status"] != 200:
        raise ValueError(f"catalog metadata HTTP status {metadata['status']}")
    metadata_payload = metadata["payload"]
    metadata_sha = hashlib.sha256(metadata_payload).hexdigest()
    if metadata_sha != EXPECTED_CATALOG_METADATA_SHA256:
        raise ValueError("catalog metadata SHA-256 differs from the E590/E595 pinned catalogue")
    document = json.loads(metadata_payload.decode("utf-8"))
    item_id = document.get("id") or document.get("itemId")
    if str(item_id or "") != CATALOG_RECORD_ID:
        raise ValueError("catalog item ID mismatch")

    records = _extract_file_records(document, CATALOG_RECORD_ID)
    selected = select_exact_file(records)
    uri = _download_uri(selected)
    if not uri:
        raise ValueError("exact February 2024 file record has no allowlisted public download URI")
    validate_public_url(uri)

    if EXPECTED_FILE_SIZE > MAX_FILE_BYTES:
        raise ValueError("pinned file exceeds the E598 byte ceiling")
    response = fetch_strict_bounded(uri, limit=MAX_FILE_BYTES)
    if response["status"] != 200:
        raise ValueError(f"CSV HTTP status {response['status']}")
    headers = response["headers"]
    content_type = headers.get_content_type()
    content_length = int(headers.get("Content-Length") or 0)
    payload = response["payload"]
    if content_length != EXPECTED_FILE_SIZE or len(payload) != EXPECTED_FILE_SIZE:
        return rejected_size_mismatch_receipt(
            metadata_sha256=metadata_sha,
            metadata_status=metadata["status"],
            response_status=response["status"],
            content_type=content_type,
            content_length=content_length,
            payload=payload,
            final_host=response["final_url"].split("/")[2],
        )

    content_type_policy = classify_csv_response(content_type, payload)
    if content_type_policy is None:
        return {
            "experiment": EXPERIMENT,
            "parse_status": "REJECTED_CONTENT_TYPE_OR_HEADER",
            "source_item_id": CATALOG_RECORD_ID,
            "source_file_name": EXPECTED_FILE_NAME,
            "source_file_size_bytes": EXPECTED_FILE_SIZE,
            "response": {
                "http_status": response["status"],
                "content_type": content_type,
                "content_length": content_length,
                "bytes_read": len(payload),
                "payload_sha256": hashlib.sha256(payload).hexdigest(),
                "csv_header_admissible": False,
            },
            "claim_state": {
                "exact_catalogue_file_identity": "SUPPORTED_AS_PINNED",
                "file_payload_as_expected_csv": "NOT_ESTABLISHED",
                "row_semantics": "NOT_YET_MEASURED",
                "cross_body_similarity": "NOT_YET_PROVEN",
                "known_site_recovery": "NOT_YET_MEASURED",
            },
            "provenance": {
                "catalog_metadata_sha256": metadata_sha,
                "catalog_metadata_http_status": metadata["status"],
                "csv_http_status": response["status"],
                "csv_final_host": response["final_url"].split("/")[2],
                "credentials_used": False,
                "read_limit_bytes": MAX_FILE_BYTES,
                "raw_payload_retained": False,
                "raw_urls_retained": False,
            },
        }

    result = summarize_payload(payload)
    result["provenance"] = {
        "catalog_metadata_sha256": metadata_sha,
        "catalog_metadata_http_status": metadata["status"],
        "csv_http_status": response["status"],
        "csv_content_type": content_type,
        "content_type_policy": content_type_policy,
        "csv_content_length": content_length,
        "csv_final_host": response["final_url"].split("/")[2],
        "credentials_used": False,
        "read_limit_bytes": MAX_FILE_BYTES,
        "full_small_file_read": True,
        "raw_urls_retained": False,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = acquire_and_audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
