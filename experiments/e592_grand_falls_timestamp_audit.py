"""E592: audit timestamps in the bounded Grand Falls sensor CSV prefix."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
import statistics
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit

from experiments.e590_grand_falls_2023_2024_probe import (
    CATALOG_RECORD_ID,
    CATALOG_RECORD_URL,
    MAX_METADATA_BYTES,
    MAX_SAMPLE_BYTES,
    _complete_csv_prefix,
    _download_uri,
    _extract_file_records,
    _file_name,
    _file_size,
    classify_sample_response,
)
from experiments.e577_grand_falls_2017_2019_access_probe import (
    ALLOWED_HOSTS,
    TIMEOUT_SECONDS,
    USER_AGENT,
)

EXPERIMENT = "E592"
EXPECTED_FILE_NAME = "SensorData_07-07-23_to_11-03-23.csv"
EXPECTED_FILE_SIZE = 67_050_032
EXPECTED_PREFIX_SHA256 = "f9f150f9eee2f3a8e477614b1ad4cd2d4fd4de5de20d3d74e3350dc4f41e86a6"
EXPECTED_COMPLETE_LINES_SHA256 = "29f68a77ac948949d869a64790b7e7e7b795681fb81f2c6a4962657e980737f7"
TIMESTAMP_COLUMN = "Date and Time"
TIMESTAMP_FORMAT = "%m/%d/%Y %H:%M"


class ProbeError(RuntimeError):
    pass


def validate_sample_url(url: str) -> None:
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ProbeError("invalid URL port") from exc
    decoded_segments = [unquote(part) for part in parsed.path.split("/")]
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or port not in (None, 443)
        or any(part == ".." for part in decoded_segments)
    ):
        raise ProbeError("URL outside strict public ScienceBase/S3 boundary")


class StrictRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_sample_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_sample_bounded(url: str, *, limit: int) -> dict:
    """Read at most limit bytes and validate every redirect before following it."""
    validate_sample_url(url)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/csv,text/plain,*/*"},
    )
    opener = urllib.request.build_opener(StrictRedirectHandler())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read(limit)
            final_url = response.geturl()
            validate_sample_url(final_url)
            return {
                "status": response.status,
                "headers": response.headers,
                "payload": payload,
                "final_url": final_url,
            }
    except urllib.error.HTTPError as error:
        final_url = error.geturl()
        validate_sample_url(final_url)
        return {
            "status": error.code,
            "headers": error.headers,
            "payload": b"",
            "final_url": final_url,
        }


def _percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return int(ordered[index])


def summarize_timestamps(payload: bytes) -> dict:
    """Summarize parsed row timestamps without retaining raw timestamp strings."""
    decoded = payload.decode("utf-8-sig", errors="strict")
    reader = csv.DictReader(io.StringIO(decoded, newline=""))
    headers = reader.fieldnames or []
    if headers.count(TIMESTAMP_COLUMN) != 1:
        raise ValueError("CSV must contain exactly one Date and Time column")

    row_count = 0
    invalid_count = 0
    valid_count = 0
    previous: datetime | None = None
    first_in_file: datetime | None = None
    last_in_file: datetime | None = None
    chronological_min: datetime | None = None
    chronological_max: datetime | None = None
    seen: Counter[datetime] = Counter()
    intervals: list[int] = []

    for row in reader:
        row_count += 1
        raw = row.get(TIMESTAMP_COLUMN)
        if not isinstance(raw, str) or not raw.strip():
            invalid_count += 1
            previous = None
            continue
        try:
            parsed = datetime.strptime(raw.strip(), TIMESTAMP_FORMAT)
        except ValueError:
            invalid_count += 1
            previous = None
            continue

        valid_count += 1
        seen[parsed] += 1
        if first_in_file is None:
            first_in_file = parsed
        last_in_file = parsed
        chronological_min = parsed if chronological_min is None else min(chronological_min, parsed)
        chronological_max = parsed if chronological_max is None else max(chronological_max, parsed)

        if previous is not None:
            intervals.append(int((parsed - previous).total_seconds()))
        previous = parsed

    interval_counts = Counter(intervals)
    positive = [value for value in intervals if value > 0]
    negative_count = sum(value < 0 for value in intervals)
    zero_count = interval_counts.get(0, 0)
    one_minute_count = interval_counts.get(60, 0)
    duplicate_rows = sum(count - 1 for count in seen.values() if count > 1)
    duplicate_values = sum(1 for count in seen.values() if count > 1)

    if invalid_count:
        ordering = "INCOMPLETE_TIMESTAMP_PARSE"
    elif negative_count:
        ordering = "CONTAINS_OUT_OF_ORDER_ROWS"
    elif zero_count:
        ordering = "NONDECREASING_WITH_DUPLICATES"
    elif intervals:
        ordering = "STRICTLY_INCREASING"
    else:
        ordering = "INSUFFICIENT_ADJACENT_TIMESTAMPS"

    if intervals and all(value == 60 for value in intervals) and invalid_count == 0:
        cadence = "ALL_ADJACENT_VALID_ROWS_60_SECONDS"
    elif intervals:
        cadence = "MIXED_OR_NON_60_SECOND_INTERVALS"
    else:
        cadence = "NO_VALID_ADJACENT_INTERVALS"

    def iso(value: datetime | None) -> str | None:
        return value.isoformat(timespec="seconds") if value is not None else None

    return {
        "timestamp_column": TIMESTAMP_COLUMN,
        "timestamp_format": TIMESTAMP_FORMAT,
        "row_count": row_count,
        "valid_timestamp_count": valid_count,
        "invalid_timestamp_count": invalid_count,
        "parse_success_fraction": valid_count / row_count if row_count else None,
        "first_timestamp_in_file_order_naive": iso(first_in_file),
        "last_timestamp_in_file_order_naive": iso(last_in_file),
        "chronological_min_naive": iso(chronological_min),
        "chronological_max_naive": iso(chronological_max),
        "timezone_status": "NOT_ENCODED_IN_COLUMN; parsed as naive wall-clock values; no UTC conversion",
        "ordering": ordering,
        "cadence": cadence,
        "adjacent_interval_count": len(intervals),
        "negative_interval_count": negative_count,
        "zero_interval_count": zero_count,
        "duplicate_timestamp_value_count": duplicate_values,
        "duplicate_timestamp_row_count": duplicate_rows,
        "one_minute_interval_count": one_minute_count,
        "one_minute_interval_fraction": one_minute_count / len(intervals) if intervals else None,
        "positive_interval_count": len(positive),
        "positive_interval_min_seconds": min(positive) if positive else None,
        "positive_interval_median_seconds": statistics.median(positive) if positive else None,
        "positive_interval_p95_seconds": _percentile(positive, 0.95),
        "positive_interval_max_seconds": max(positive) if positive else None,
        "positive_gaps_over_60_seconds": sum(value > 60 for value in positive),
        "positive_gaps_over_300_seconds": sum(value > 300 for value in positive),
        "common_interval_seconds": [
            {"seconds": seconds, "count": count}
            for seconds, count in sorted(interval_counts.items(), key=lambda item: (-item[1], item[0]))[:10]
        ],
        "raw_timestamps_stored": False,
    }


def audit(metadata_fetcher=None, sample_fetcher=None) -> dict:
    if metadata_fetcher is None:
        from experiments.e590_grand_falls_2023_2024_probe import fetch_bounded
        metadata_fetcher = fetch_bounded
    if sample_fetcher is None:
        sample_fetcher = fetch_sample_bounded

    result = {
        "experiment": EXPERIMENT,
        "source_item_id": CATALOG_RECORD_ID,
        "source_file_name": EXPECTED_FILE_NAME,
        "expected_file_size_bytes": EXPECTED_FILE_SIZE,
        "metadata_http_status": None,
        "sample_http_status": None,
        "decision": "ACQUISITION_NOT_STARTED",
        "credentials_used": False,
        "raw_rows_stored": False,
        "raw_values_stored": False,
        "raw_timestamps_stored": False,
        "raw_urls_stored": False,
        "raw_coordinates_stored": False,
        "full_file_downloaded": False,
    }

    try:
        metadata = metadata_fetcher(CATALOG_RECORD_URL, limit=MAX_METADATA_BYTES)
        result["metadata_http_status"] = metadata["status"]
        if metadata["status"] != 200:
            result["decision"] = "CATALOG_METADATA_UNAVAILABLE"
            return result

        metadata_payload = metadata["payload"]
        result["catalog_metadata_sha256"] = hashlib.sha256(metadata_payload).hexdigest()
        document = json.loads(metadata_payload.decode("utf-8"))
        item_id = document.get("id") or document.get("itemId")
        if str(item_id or "") != CATALOG_RECORD_ID:
            result["decision"] = "CATALOG_ITEM_ID_NOT_CONFIRMED"
            return result

        records = _extract_file_records(document, CATALOG_RECORD_ID)
        matches = [
            record for record in records
            if _file_name(record) == EXPECTED_FILE_NAME
            and _file_size(record) == EXPECTED_FILE_SIZE
        ]
        result["matching_file_record_count"] = len(matches)
        if len(matches) != 1:
            result["decision"] = "EXPECTED_FILE_RECORD_NOT_UNIQUE"
            return result

        uri = _download_uri(matches[0])
        if not uri:
            result["decision"] = "EXPECTED_FILE_URL_UNAVAILABLE"
            return result
        validate_sample_url(uri)

        sample = sample_fetcher(uri, limit=MAX_SAMPLE_BYTES)
        result["sample_http_status"] = sample["status"]
        mode = classify_sample_response(
            sample["status"], sample["headers"], sample["payload"],
            EXPECTED_FILE_SIZE, MAX_SAMPLE_BYTES,
        )
        content_type = str(sample["headers"].get("Content-Type") or "").lower()
        result["sample_response"] = {
            "mode": mode,
            "content_type": content_type,
            "content_length": sample["headers"].get("Content-Length"),
            "bytes_read": len(sample["payload"]),
            "final_host": urlsplit(sample["final_url"]).hostname,
            "prefix_sha256": hashlib.sha256(sample["payload"]).hexdigest(),
            "html_response": "text/html" in content_type,
        }
        if mode is None:
            result["decision"] = "BOUNDED_PREFIX_NOT_CONFIRMED"
            return result

        complete_payload = _complete_csv_prefix(sample["payload"])
        if not complete_payload:
            result["decision"] = "NO_COMPLETE_CSV_LINES"
            return result

        result["complete_lines_bytes"] = len(complete_payload)
        result["complete_lines_sha256"] = hashlib.sha256(complete_payload).hexdigest()
        result["prefix_matches_e590_receipt"] = (
            result["sample_response"]["prefix_sha256"] == EXPECTED_PREFIX_SHA256
        )
        result["complete_lines_match_e590_receipt"] = (
            result["complete_lines_sha256"] == EXPECTED_COMPLETE_LINES_SHA256
        )
        result["timestamp_audit"] = summarize_timestamps(complete_payload)
        result["published_logging_note"] = (
            "The E590 source report records the Data.gov description as 1 Hz sampling "
            "averaged/logged at one-minute intervals. This audit measures only the "
            "Date and Time row intervals in the bounded prefix; it does not verify "
            "raw 1 Hz acquisition or sensor averaging."
        )
        result["decision"] = (
            "TIMESTAMP_AUDIT_COMPLETE"
            if result["timestamp_audit"]["valid_timestamp_count"] > 0
            else "NO_VALID_TIMESTAMPS"
        )
        return result
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["decision"] = "AUDIT_ERROR"
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    summary = {
        "experiment": receipt.get("experiment"),
        "decision": receipt.get("decision"),
        "metadata_http_status": receipt.get("metadata_http_status"),
        "sample_http_status": receipt.get("sample_http_status"),
        "sample_response": receipt.get("sample_response"),
        "timestamp_audit": receipt.get("timestamp_audit"),
        "prefix_matches_e590_receipt": receipt.get("prefix_matches_e590_receipt"),
        "complete_lines_match_e590_receipt": receipt.get("complete_lines_match_e590_receipt"),
        "credentials_used": receipt.get("credentials_used"),
        "raw_rows_stored": receipt.get("raw_rows_stored"),
        "raw_timestamps_stored": receipt.get("raw_timestamps_stored"),
        "full_file_downloaded": receipt.get("full_file_downloaded"),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
