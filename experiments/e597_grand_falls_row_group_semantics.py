"""E597: row identity and timestamp-group audit of a pinned Grand Falls CSV prefix."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
from collections import Counter, defaultdict
from datetime import datetime
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

EXPERIMENT = "E597"
EXPECTED_FILE_NAME = "SensorData_07-07-23_to_11-03-23.csv"
EXPECTED_FILE_SIZE = 67_050_032
MAX_PREFIX_BYTES = 5_000_000
EXPECTED_PREFIX_SHA256 = "f9f150f9eee2f3a8e477614b1ad4cd2d4fd4de5de20d3d74e3350dc4f41e86a6"
EXPECTED_COMPLETE_LINES_BYTES = 4_999_997
EXPECTED_COMPLETE_LINES_SHA256 = "29f68a77ac948949d869a64790b7e7e7b795681fb81f2c6a4962657e980737f7"
EXPECTED_ROW_COUNT = 85_145
TIMESTAMP_FORMAT = "%m/%d/%Y %H:%M"
CHANNELS = {
    "wind_speed_mph": [
        "Wind Speed - Low (mph)", "Wind Speed - Mid (mph)", "Wind Speed - High (mph)"
    ],
    "particle_count": [
        "Particle Count_Tot(1)", "Particle Count_Tot(2)", "Particle Count_Tot(3)"
    ],
    "kinetic_energy_uncalibrated": [
        "Kinetic Energy_Tot(1)", "Kinetic Energy_Tot(2)", "Kinetic Energy_Tot(3)"
    ],
    "wbsne_voltage_mvv": [
        "wBSNE #1 average (mV/V)", "wBSNE #2 average (mV/V)", "wBSNE #3 average (mV/V)"
    ],
}
ALL_CHANNELS = [column for family in CHANNELS.values() for column in family]


def _number(value: str | None) -> float | None:
    if value is None or not value.strip():
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _summarize_dict_rows(rows: list[dict[str, str]]) -> dict:
    row_count = len(rows)
    invalid_timestamp = invalid_record_number = 0
    record_ids: list[int] = []
    timestamps: list[datetime] = []
    groups = defaultdict(list)
    per_channel_values = {column: [] for column in ALL_CHANNELS}
    per_channel_missing = Counter()
    per_channel_saturation = Counter()
    row_nonnull_count = Counter()
    family_complete_rows = Counter()
    family_any_rows = Counter()

    for row in rows:
        raw_timestamp = (row.get("Date and Time") or "").strip()
        try:
            timestamp = datetime.strptime(raw_timestamp, TIMESTAMP_FORMAT)
            timestamps.append(timestamp)
        except ValueError:
            invalid_timestamp += 1
            timestamp = None

        raw_record = (row.get("Record Number") or "").strip()
        try:
            number = float(raw_record)
            if not number.is_integer():
                raise ValueError
            record_id = int(number)
            record_ids.append(record_id)
        except ValueError:
            invalid_record_number += 1
            record_id = None

        signature = []
        nonnull = 0
        for family, columns in CHANNELS.items():
            family_values = []
            for column in columns:
                value = _number(row.get(column))
                signature.append(value)
                if value is None:
                    per_channel_missing[column] += 1
                else:
                    nonnull += 1
                    per_channel_values[column].append(value)
                    if family == "particle_count" and value == 7999:
                        per_channel_saturation[column] += 1
                family_values.append(value)
            if all(value is not None for value in family_values):
                family_complete_rows[family] += 1
            if any(value is not None for value in family_values):
                family_any_rows[family] += 1
        row_nonnull_count[nonnull] += 1
        if timestamp is not None:
            groups[timestamp].append({
                "record_id": record_id,
                "signature": tuple(signature),
                "nonnull_channels": nonnull,
            })

    if invalid_timestamp or invalid_record_number:
        raise ValueError("invalid timestamp or record-number values found")

    record_diffs = [b - a for a, b in zip(record_ids, record_ids[1:])]
    diff_counts = Counter(record_diffs)
    group_sizes = Counter(len(group) for group in groups.values())
    group_record_distinct = group_record_sequential = 0
    group_all_rows_distinct = group_all_rows_identical = 0
    group_partial_signature_duplicates = 0
    group_all_channels_complete = group_any_channel_missing = 0
    unique_signatures_per_group = Counter()
    for group in groups.values():
        ids = [item["record_id"] for item in group]
        if len(set(ids)) == len(ids):
            group_record_distinct += 1
        if len(ids) > 1 and all(b - a == 1 for a, b in zip(ids, ids[1:])):
            group_record_sequential += 1
        signatures = [item["signature"] for item in group]
        unique_signatures = len(set(signatures))
        unique_signatures_per_group[unique_signatures] += 1
        if unique_signatures == len(group):
            group_all_rows_distinct += 1
        elif unique_signatures == 1:
            group_all_rows_identical += 1
        else:
            group_partial_signature_duplicates += 1
        if all(item["nonnull_channels"] == len(ALL_CHANNELS) for item in group):
            group_all_channels_complete += 1
        else:
            group_any_channel_missing += 1

    interval_counts = Counter(
        int((later - earlier).total_seconds())
        for earlier, later in zip(timestamps, timestamps[1:])
    )
    nondecreasing = all(b >= a for a, b in zip(timestamps, timestamps[1:]))
    channel_summary = {}
    for column, values in per_channel_values.items():
        channel_summary[column] = {
            "numeric_count": len(values),
            "missing_or_non_numeric_count": per_channel_missing[column],
            "min": min(values) if values else None,
            "max": max(values) if values else None,
            "mean": round(statistics.fmean(values), 9) if values else None,
            "sample_sd": round(statistics.stdev(values), 9) if len(values) > 1 else None,
            "saturation_at_7999_count": per_channel_saturation[column],
        }

    return {
        "row_count": row_count,
        "record_number": {
            "source_definition": "Sequential number assigned to row by computer",
            "numeric_record_count": len(record_ids),
            "unique_record_ids": len(set(record_ids)),
            "min_record_id": min(record_ids) if record_ids else None,
            "max_record_id": max(record_ids) if record_ids else None,
            "strictly_increasing": all(diff > 0 for diff in record_diffs),
            "unit_step_count": sum(diff == 1 for diff in record_diffs),
            "gap_count": sum(diff > 1 for diff in record_diffs),
            "reset_or_duplicate_count": sum(diff <= 0 for diff in record_diffs),
            "difference_counts": dict(sorted((str(k), v) for k, v in diff_counts.items())),
            "timestamp_groups_with_distinct_record_ids": group_record_distinct,
            "timestamp_groups_with_sequential_record_ids": group_record_sequential,
        },
        "timestamps": {
            "format": TIMESTAMP_FORMAT,
            "timezone": "NOT_ENCODED; naive wall-clock parse only",
            "valid_timestamp_rows": len(timestamps),
            "invalid_timestamp_rows": invalid_timestamp,
            "distinct_timestamp_groups": len(groups),
            "group_size_distribution": dict(sorted((str(k), v) for k, v in group_sizes.items())),
            "group_size_min": min(group_sizes) if group_sizes else None,
            "group_size_max": max(group_sizes) if group_sizes else None,
            "mean_group_size": round(statistics.fmean(len(group) for group in groups.values()), 6),
            "median_group_size": statistics.median(len(group) for group in groups.values()),
            "all_groups_repeated": all(size > 1 for size in group_sizes),
            "adjacent_interval_seconds": dict(sorted((str(k), v) for k, v in interval_counts.items())),
            "nondecreasing_in_file_order": nondecreasing,
        },
        "within_timestamp_group": {
            "unique_channel_vector_count_distribution": dict(sorted(
                (str(k), v) for k, v in unique_signatures_per_group.items()
            )),
            "groups_with_all_rows_channel_vectors_distinct": group_all_rows_distinct,
            "groups_with_all_rows_channel_vectors_identical": group_all_rows_identical,
            "groups_with_partial_channel_vector_duplicates": group_partial_signature_duplicates,
            "groups_with_all_rows_all_12_channels_present": group_all_channels_complete,
            "groups_with_any_row_channel_missing": group_any_channel_missing,
            "row_nonnull_channel_count_distribution": dict(sorted(
                (str(k), v) for k, v in row_nonnull_count.items()
            )),
            "family_rows_with_all_three_channels_present": dict(sorted(family_complete_rows.items())),
            "family_rows_with_any_channel_present": dict(sorted(family_any_rows.items())),
        },
        "channel_summary": channel_summary,
    }


def summarize_rows(header: list[str], rows: list[list[str]]) -> dict:
    if not header or len(set(header)) != len(header):
        raise ValueError("invalid CSV header")
    required = {"Date and Time", "Record Number", *ALL_CHANNELS}
    missing_header = sorted(required.difference(header))
    if missing_header:
        raise ValueError(f"required source columns missing: {missing_header}")
    dict_rows = []
    incomplete = 0
    for row in rows:
        if len(row) != len(header):
            incomplete += 1
            continue
        dict_rows.append(dict(zip(header, row)))
    result = _summarize_dict_rows(dict_rows)
    result["incomplete_rows_dropped"] = incomplete
    return result


def summarize_prefix(prefix: bytes) -> dict:
    if len(prefix) != MAX_PREFIX_BYTES:
        raise ValueError(f"expected exactly {MAX_PREFIX_BYTES} prefix bytes")
    prefix_sha = hashlib.sha256(prefix).hexdigest()
    if prefix_sha != EXPECTED_PREFIX_SHA256:
        raise ValueError("5 MB prefix hash differs from the E590/E592 pinned sample")
    complete_bytes = prefix.rfind(b"\n") + 1
    complete = prefix[:complete_bytes]
    complete_sha = hashlib.sha256(complete).hexdigest()
    if complete_bytes != EXPECTED_COMPLETE_LINES_BYTES or complete_sha != EXPECTED_COMPLETE_LINES_SHA256:
        raise ValueError("complete-line prefix differs from E592")
    reader = csv.reader(io.StringIO(complete.decode("utf-8-sig")))
    header = next(reader)
    rows = list(reader)
    summary = summarize_rows(header, rows)
    if summary["row_count"] != EXPECTED_ROW_COUNT:
        raise ValueError(f"row count changed: expected {EXPECTED_ROW_COUNT}, got {summary['row_count']}")
    return {
        "experiment": EXPERIMENT,
        "source_item_id": CATALOG_RECORD_ID,
        "source_file_name": EXPECTED_FILE_NAME,
        "source_file_size_bytes": EXPECTED_FILE_SIZE,
        "sample": {
            "mode": "bounded_stream_prefix",
            "prefix_bytes": len(prefix),
            "complete_lines_bytes": complete_bytes,
            "prefix_sha256": prefix_sha,
            "complete_lines_sha256": complete_sha,
            "row_count": summary["row_count"],
            "incomplete_rows_dropped": summary["incomplete_rows_dropped"],
            "column_count": len(header),
            "columns": header,
            "raw_rows_retained": False,
            "raw_timestamps_retained": False,
            "raw_record_numbers_retained": False,
            "raw_channel_values_retained": False,
        },
        **{key: value for key, value in summary.items() if key not in {"row_count", "incomplete_rows_dropped"}},
        "interpretation_boundary": (
            "Repeated timestamp groups with sequential Record_Number values are distinct row records. "
            "They do not by themselves identify why multiple rows share a minute, prove sensor synchronization, "
            "replicate independence, calibration or sediment mass flux."
        ),
        "claim_state": {
            "source_dictionary_row_id_semantics": "SUPPORTED_AS_REPORTED",
            "observed_row_id_progression": "MEASURED",
            "observed_timestamp_group_structure": "MEASURED",
            "sensor_synchronization": "NOT_YET_PROVEN",
            "sensor_calibration": "NOT_YET_PROVEN",
            "sediment_mass_conversion": "NOT_YET_PROVEN",
            "cross_body_similarity": "NOT_YET_PROVEN",
            "known_site_recovery": "NOT_YET_MEASURED",
        },
    }


def acquire_and_audit() -> dict:
    metadata = fetch_strict_bounded(CATALOG_RECORD_URL, limit=MAX_METADATA_BYTES)
    if metadata["status"] != 200:
        raise ValueError(f"catalog metadata HTTP status {metadata['status']}")
    metadata_payload = metadata["payload"]
    metadata_sha = hashlib.sha256(metadata_payload).hexdigest()
    if metadata_sha != EXPECTED_CATALOG_METADATA_SHA256:
        raise ValueError("catalog metadata SHA-256 mismatch")
    document = json.loads(metadata_payload.decode("utf-8"))
    item_id = document.get("id") or document.get("itemId")
    if str(item_id or "") != CATALOG_RECORD_ID:
        raise ValueError("catalog item ID mismatch")
    records = _extract_file_records(document, CATALOG_RECORD_ID)
    matches = [
        record for record in records
        if _file_name(record) == EXPECTED_FILE_NAME and _file_size(record) == EXPECTED_FILE_SIZE
    ]
    if len(matches) != 1:
        raise ValueError("expected CSV file record is not unique")
    uri = _download_uri(matches[0])
    if not uri:
        raise ValueError("CSV download URI unavailable")
    validate_public_url(uri)
    response = fetch_strict_bounded(uri, limit=MAX_PREFIX_BYTES)
    if response["status"] != 200:
        raise ValueError(f"CSV HTTP status {response['status']}")
    headers = response["headers"]
    if headers.get_content_type() != "text/csv":
        raise ValueError("CSV content type mismatch")
    if int(headers.get("Content-Length") or 0) != EXPECTED_FILE_SIZE:
        raise ValueError("CSV Content-Length mismatch")
    if len(response["payload"]) != MAX_PREFIX_BYTES:
        raise ValueError("bounded CSV prefix byte count mismatch")
    result = summarize_prefix(response["payload"])
    result["provenance"] = {
        "catalog_metadata_sha256": metadata_sha,
        "catalog_metadata_http_status": metadata["status"],
        "csv_http_status": response["status"],
        "csv_content_type": headers.get_content_type(),
        "csv_content_length": int(headers.get("Content-Length")),
        "csv_final_host": response["final_url"].split("/")[2],
        "credentials_used": False,
        "full_file_downloaded": False,
        "raw_urls_retained": False,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = acquire_and_audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
