"""E598: duplicate-aware within-site wind/particle association and circular-shift null."""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import math
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np

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
from experiments.e597_grand_falls_row_group_semantics import (
    ALL_CHANNELS,
    CHANNELS,
    EXPECTED_COMPLETE_LINES_BYTES,
    EXPECTED_COMPLETE_LINES_SHA256,
    EXPECTED_PREFIX_SHA256,
    EXPECTED_ROW_COUNT,
    MAX_PREFIX_BYTES,
    TIMESTAMP_FORMAT,
)

EXPECTED_FILE_NAME = "SensorData_07-07-23_to_11-03-23.csv"
EXPECTED_FILE_SIZE = 67_050_032
SEED = 20261112
PERMUTATIONS = 999
MIN_CIRCULAR_SHIFT = 60
WIND_CHANNELS = CHANNELS["wind_speed_mph"]
PARTICLE_CHANNELS = CHANNELS["particle_count"]


def rankdata_average(values: np.ndarray) -> np.ndarray:
    values = np.asarray(values, dtype=float)
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    ranks = np.empty(len(values), dtype=float)
    start = 0
    while start < len(values):
        end = start + 1
        while end < len(values) and sorted_values[end] == sorted_values[start]:
            end += 1
        average_rank = ((start + 1) + end) / 2.0
        ranks[order[start:end]] = average_rank
        start = end
    return ranks


def correlation_matrix(wind: np.ndarray, particle: np.ndarray, method: str = "spearman") -> np.ndarray:
    wind = np.asarray(wind, dtype=float)
    particle = np.asarray(particle, dtype=float)
    if wind.ndim != 2 or particle.ndim != 2 or wind.shape[1] != particle.shape[1]:
        raise ValueError("wind and particle matrices must be 2D with the same observation count")
    if method == "spearman":
        wind = np.vstack([rankdata_average(row) for row in wind])
        particle = np.vstack([rankdata_average(row) for row in particle])
    elif method != "pearson":
        raise ValueError("method must be spearman or pearson")
    wind = wind - wind.mean(axis=1, keepdims=True)
    particle = particle - particle.mean(axis=1, keepdims=True)
    wind_norm = np.linalg.norm(wind, axis=1, keepdims=True)
    particle_norm = np.linalg.norm(particle, axis=1, keepdims=True)
    if np.any(wind_norm == 0) or np.any(particle_norm == 0):
        raise ValueError("constant channel cannot be correlated")
    wind = wind / wind_norm
    particle = particle / particle_norm
    return wind @ particle.T


def circular_shift_max_null(
    wind_spearman_ranks: np.ndarray,
    particle_spearman_ranks: np.ndarray,
    *,
    permutations: int = PERMUTATIONS,
    min_shift: int = MIN_CIRCULAR_SHIFT,
    seed: int = SEED,
) -> dict:
    wind = np.asarray(wind_spearman_ranks, dtype=float)
    particle = np.asarray(particle_spearman_ranks, dtype=float)
    if wind.ndim != 2 or particle.ndim != 2 or wind.shape[1] != particle.shape[1]:
        raise ValueError("rank matrices must share observation count")
    n = wind.shape[1]
    if n <= 2 * min_shift + 1:
        raise ValueError("series too short for requested circular shift")
    wind = wind - wind.mean(axis=1, keepdims=True)
    particle = particle - particle.mean(axis=1, keepdims=True)
    wind_norm = np.linalg.norm(wind, axis=1, keepdims=True)
    particle_norm = np.linalg.norm(particle, axis=1, keepdims=True)
    wind = wind / wind_norm
    particle = particle / particle_norm
    observed = wind @ particle.T
    observed_max = float(np.max(np.abs(observed)))
    rng = np.random.default_rng(seed)
    possible = np.arange(min_shift, n - min_shift, dtype=int)
    shifts = rng.choice(possible, size=permutations, replace=False)
    null_max = np.empty(permutations, dtype=float)
    for index, shift in enumerate(shifts):
        null_max[index] = np.max(np.abs(wind @ np.roll(particle, int(shift), axis=1).T))
    p_value = (1 + int(np.count_nonzero(null_max >= observed_max))) / (permutations + 1)
    return {
        "permutations": permutations,
        "seed": seed,
        "minimum_shift_minutes": min_shift,
        "maximum_shift_minutes": int(n - min_shift),
        "observed_max_abs_spearman": observed_max,
        "familywise_p_value": p_value,
        "null_max_mean": float(np.mean(null_max)),
        "null_max_median": float(np.median(null_max)),
        "null_max_95th_percentile": float(np.quantile(null_max, 0.95)),
        "null_max_99th_percentile": float(np.quantile(null_max, 0.99)),
        "null_maximum": float(np.max(null_max)),
        "observed_exceeds_null_95th": bool(observed_max > np.quantile(null_max, 0.95)),
        "shift_draws_unique": len(set(int(value) for value in shifts)) == permutations,
    }


def _read_prefix(prefix: bytes) -> tuple[list[str], list[dict[str, str]], dict]:
    if len(prefix) != MAX_PREFIX_BYTES:
        raise ValueError("prefix byte count mismatch")
    prefix_sha = hashlib.sha256(prefix).hexdigest()
    if prefix_sha != EXPECTED_PREFIX_SHA256:
        raise ValueError("prefix SHA differs from E592")
    complete_bytes = prefix.rfind(b"\n") + 1
    complete = prefix[:complete_bytes]
    complete_sha = hashlib.sha256(complete).hexdigest()
    if complete_bytes != EXPECTED_COMPLETE_LINES_BYTES or complete_sha != EXPECTED_COMPLETE_LINES_SHA256:
        raise ValueError("complete-line SHA differs from E592")
    reader = csv.DictReader(io.StringIO(complete.decode("utf-8-sig")))
    header = reader.fieldnames or []
    required = {"Date and Time", "Record Number", *ALL_CHANNELS}
    if required.difference(header):
        raise ValueError(f"required columns missing: {sorted(required.difference(header))}")
    rows = list(reader)
    if len(rows) != EXPECTED_ROW_COUNT or any(None in row for row in rows):
        raise ValueError("complete row count or width differs from E592")
    return header, rows, {
        "prefix_bytes": len(prefix),
        "complete_lines_bytes": complete_bytes,
        "prefix_sha256": prefix_sha,
        "complete_lines_sha256": complete_sha,
        "complete_rows": len(rows),
    }


def build_observation_matrices(header: list[str], rows: list[dict[str, str]]) -> dict:
    groups = defaultdict(dict)
    raw_vectors = []
    for row in rows:
        timestamp = datetime.strptime(row["Date and Time"].strip(), TIMESTAMP_FORMAT)
        vector = tuple(float(row[column]) for column in ALL_CHANNELS)
        if not all(math.isfinite(value) for value in vector):
            raise ValueError("non-finite channel value")
        raw_vectors.append(vector)
        groups[timestamp].setdefault(vector, vector)

    ordered_times = sorted(groups)
    group_means = []
    first_unique = []
    unique_vectors = []
    unique_counts = []
    for timestamp in ordered_times:
        vectors = list(groups[timestamp].values())
        unique_counts.append(len(vectors))
        unique_vectors.extend(vectors)
        first_unique.append(vectors[0])
        group_means.append(np.mean(np.asarray(vectors, dtype=float), axis=0))
    raw = np.asarray(raw_vectors, dtype=float)
    dedup = np.asarray(unique_vectors, dtype=float)
    group_mean = np.asarray(group_means, dtype=float)
    first = np.asarray(first_unique, dtype=float)
    if group_mean.shape[0] != len(ordered_times):
        raise ValueError("timestamp aggregation mismatch")
    return {
        "raw": raw,
        "unique_vectors": dedup,
        "group_mean": group_mean,
        "first_unique": first,
        "timestamps": ordered_times,
        "unique_counts": unique_counts,
    }


def _channel_matrix(matrix: np.ndarray, columns: list[str]) -> np.ndarray:
    indices = [ALL_CHANNELS.index(column) for column in columns]
    return matrix[:, indices].T


def _matrix_summary(matrix: np.ndarray, label: str) -> dict:
    wind = _channel_matrix(matrix, WIND_CHANNELS)
    particle = _channel_matrix(matrix, PARTICLE_CHANNELS)
    raw_spearman = correlation_matrix(wind, particle, "spearman")
    raw_pearson = correlation_matrix(wind, particle, "pearson")
    log_particle = np.log1p(particle)
    log_spearman = correlation_matrix(wind, log_particle, "spearman")
    binary_particle = (particle > 0).astype(float)
    binary_spearman = correlation_matrix(wind, binary_particle, "spearman")
    zero_fraction = {
        column: float(np.mean(matrix[:, ALL_CHANNELS.index(column)] == 0))
        for column in WIND_CHANNELS + PARTICLE_CHANNELS
    }
    nonzero_count = {
        column: int(np.count_nonzero(matrix[:, ALL_CHANNELS.index(column)]))
        for column in WIND_CHANNELS + PARTICLE_CHANNELS
    }
    return {
        "observation_unit": label,
        "observation_count": int(matrix.shape[0]),
        "spearman_raw_particle_count": raw_spearman.tolist(),
        "spearman_log1p_particle_count": log_spearman.tolist(),
        "spearman_binary_particle_detection": binary_spearman.tolist(),
        "pearson_raw_particle_count": raw_pearson.tolist(),
        "zero_fraction": zero_fraction,
        "nonzero_count": nonzero_count,
        "max_abs_spearman_log1p": float(np.max(np.abs(log_spearman))),
    }


def analyze_prefix(prefix: bytes) -> dict:
    header, rows, sample = _read_prefix(prefix)
    matrices = build_observation_matrices(header, rows)
    raw = matrices["raw"]
    unique = matrices["unique_vectors"]
    group_mean = matrices["group_mean"]
    first = matrices["first_unique"]

    primary_wind = _channel_matrix(group_mean, WIND_CHANNELS)
    primary_particle = np.log1p(_channel_matrix(group_mean, PARTICLE_CHANNELS))
    wind_ranks = np.vstack([rankdata_average(row) for row in primary_wind])
    particle_ranks = np.vstack([rankdata_average(row) for row in primary_particle])
    null = circular_shift_max_null(wind_ranks, particle_ranks)

    raw_summary = _matrix_summary(raw, "all raw rows; pseudoreplication sensitivity only")
    unique_summary = _matrix_summary(unique, "unique channel vectors within timestamp; group-size weighted sensitivity")
    group_summary = _matrix_summary(group_mean, "one mean per timestamp across unique vectors; primary")
    first_summary = _matrix_summary(first, "first unique vector per timestamp; sensitivity")

    vector_counts = Counter(matrices["unique_counts"])
    unique_total = sum(matrices["unique_counts"])
    duplicate_rows = len(raw) - unique_total
    return {
        "experiment": "E598",
        "source_item_id": CATALOG_RECORD_ID,
        "source_file_name": EXPECTED_FILE_NAME,
        "source_file_size_bytes": EXPECTED_FILE_SIZE,
        "sample": sample,
        "timestamp_groups": len(matrices["timestamps"]),
        "unique_channel_vectors": unique_total,
        "duplicate_row_slots_within_timestamp_groups": duplicate_rows,
        "duplicate_row_fraction": duplicate_rows / len(raw),
        "unique_vectors_per_group_distribution": dict(sorted((str(k), v) for k, v in vector_counts.items())),
        "correlation_sensitivity": {
            "raw_rows": raw_summary,
            "unique_vectors": unique_summary,
            "timestamp_group_mean": group_summary,
            "first_unique_vector": first_summary,
        },
        "primary_null": null,
        "wind_channel_order": WIND_CHANNELS,
        "particle_channel_order": PARTICLE_CHANNELS,
        "permutation_policy": {
            "null": "circular shift particle series relative to wind series",
            "preserves": "within-series order/autocorrelation",
            "breaks": "same-minute wind/particle alignment",
            "familywise_statistic": "maximum absolute Spearman correlation across all 9 channel pairs",
            "minimum_shift_minutes": MIN_CIRCULAR_SHIFT,
            "permutations": PERMUTATIONS,
            "seed": SEED,
        },
        "interpretation_boundary": (
            "This is a single-site association test on one bounded prefix. It is not causal, does not calibrate "
            "sensor outputs to sediment mass, and does not establish cross-site or cross-body transfer. "
            "Raw-row results are sensitivity-only because repeated channel vectors inflate row count."
        ),
        "claim_state": {
            "within_site_wind_particle_association": "MEASURED",
            "robust_association_after_circular_shift_null": "SUPPORTED" if null["familywise_p_value"] <= 0.05 else "NOT_SUPPORTED_IN_THIS_PREFIX",
            "sensor_synchronization": "NOT_YET_PROVEN",
            "sensor_calibration": "NOT_YET_PROVEN",
            "sediment_mass_conversion": "NOT_YET_PROVEN",
            "cross_body_similarity": "NOT_YET_PROVEN",
            "known_site_recovery": "NOT_YET_MEASURED",
        },
        "raw_data_retained": False,
        "raw_timestamps_retained": False,
        "raw_channel_values_retained": False,
    }


def acquire_prefix() -> bytes:
    metadata = fetch_strict_bounded(CATALOG_RECORD_URL, limit=MAX_METADATA_BYTES)
    if metadata["status"] != 200:
        raise ValueError(f"metadata HTTP status {metadata['status']}")
    if hashlib.sha256(metadata["payload"]).hexdigest() != EXPECTED_CATALOG_METADATA_SHA256:
        raise ValueError("catalog metadata SHA mismatch")
    document = json.loads(metadata["payload"].decode("utf-8"))
    item_id = document.get("id") or document.get("itemId")
    if str(item_id or "") != CATALOG_RECORD_ID:
        raise ValueError("catalog item ID mismatch")
    records = _extract_file_records(document, CATALOG_RECORD_ID)
    matches = [
        item for item in records
        if _file_name(item) == EXPECTED_FILE_NAME and _file_size(item) == EXPECTED_FILE_SIZE
    ]
    if len(matches) != 1:
        raise ValueError("source CSV metadata record is not unique")
    url = _download_uri(matches[0])
    if not url:
        raise ValueError("source CSV download URI unavailable")
    validate_public_url(url)
    response = fetch_strict_bounded(url, limit=MAX_PREFIX_BYTES)
    if response["status"] != 200:
        raise ValueError(f"CSV HTTP status {response['status']}")
    if response["headers"].get_content_type() != "text/csv":
        raise ValueError("CSV content type mismatch")
    if int(response["headers"].get("Content-Length") or 0) != EXPECTED_FILE_SIZE:
        raise ValueError("CSV Content-Length mismatch")
    if len(response["payload"]) != MAX_PREFIX_BYTES:
        raise ValueError("bounded prefix length mismatch")
    return response["payload"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = analyze_prefix(acquire_prefix())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
