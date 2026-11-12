"""E574: decompose E573's HiRISE valid-point support difference.

This is a deterministic analysis of a pinned E573 aggregate receipt, not a
new raster acquisition. It separates footprint extent from valid-mask
differences inside the shared footprint. It makes no accuracy or registration
claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

EXPECTED_SOURCE = {
    "workflow_run_id": 43155697664,
    "artifact_id": 13916101713,
    "artifact_receipt_sha256": "939e3c3b81917f50065f4a1296e909bcfd95144e20257fc8939035ae0f5450a",
    "artifact_zip_sha256": "da4e03d6f923cdb789f8349157ecd704ea40ae3ce9d2513ffb7d13cde44ac172",
    "source_branch": "research/e573-hirise-translation-envelope-20261112",
    "source_commit": "7f6541e10a823402c2c50bcf6647e425d037ca3a",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _validate_source(source: dict[str, Any]) -> None:
    for key, expected in EXPECTED_SOURCE.items():
        _require(source.get(key) == expected, f"source provenance mismatch: {key}")


def _validate_baseline(baseline: dict[str, Any]) -> tuple[int, int, int]:
    observed = baseline["observed_mola_points"]
    valid_2020 = baseline["hirise_2020_valid"]
    valid_2025 = baseline["hirise_2025_valid"]
    shared_points = baseline["shared_footprint_points"]
    both_valid = baseline["both_valid_within_shared_footprint"]
    both_nodata = baseline["both_nodata_within_shared_footprint"]
    valid_2025_shared_only = baseline["hirise_2025_only_valid_within_shared_footprint"]
    valid_2020_shared_only = baseline["hirise_2020_only_valid_within_shared_footprint"]
    valid_2025_2020_outside = baseline["hirise_2025_valid_where_2020_outside"]
    valid_2020_2025_outside = baseline["hirise_2020_valid_where_2025_outside"]

    _require(observed == 346, "unexpected frozen MOLA denominator")
    _require(
        both_valid + both_nodata + valid_2025_shared_only + valid_2020_shared_only == shared_points,
        "shared footprint partition does not reconcile",
    )
    _require(
        both_valid + valid_2020_shared_only + valid_2020_2025_outside == valid_2020,
        "2020 valid-point partition does not reconcile",
    )
    _require(
        both_valid + valid_2025_shared_only + valid_2025_2020_outside == valid_2025,
        "2025 valid-point partition does not reconcile",
    )

    shared = valid_2025_shared_only - valid_2020_shared_only
    footprint = valid_2025_2020_outside - valid_2020_2025_outside
    total = valid_2025 - valid_2020
    _require(baseline["shared_footprint_validity_delta"] == shared, "shared-footprint delta disagrees with source counts")
    _require(baseline["footprint_only_validity_delta"] == footprint, "footprint-only delta disagrees with source counts")
    _require(baseline["total_valid_support_delta"] == total, "total support delta disagrees with source counts")
    _require(total == shared + footprint, "baseline support decomposition does not reconcile")
    _require(total > 0, "baseline total support delta must be positive")
    return total, shared, footprint


def _validate_sensitivity(name: str, mode: dict[str, Any]) -> None:
    _require(mode["offsets"] == 13, f"{name} must contain 13 frozen offsets")
    for suffix in ("min", "max"):
        total = mode[f"total_valid_delta_{suffix}"]
        shared = mode[f"shared_footprint_validity_delta_{suffix}"]
        footprint = mode[f"footprint_only_validity_delta_{suffix}"]
        _require(total == shared + footprint, f"{name} {suffix} support decomposition does not reconcile")
        _require(total >= 0 and shared >= 0 and footprint >= 0, f"{name} {suffix} components must be nonnegative")
    for component in ("total_valid_delta", "shared_footprint_validity_delta", "footprint_only_validity_delta"):
        _require(mode[f"{component}_min"] <= mode[f"{component}_max"], f"{name} {component} range is reversed")


def run(input_path: Path) -> dict[str, Any]:
    source = json.loads(input_path.read_text(encoding="utf-8"))
    _validate_source(source["source"])
    baseline = source["baseline"]
    common = source["common_mode_translation"]
    differential = source["differential_2025_translation"]
    total, shared, footprint = _validate_baseline(baseline)
    _validate_sensitivity("common_mode", common)
    _validate_sensitivity("differential_2025", differential)

    persists = (
        common["total_valid_delta_min"] > 0
        and differential["total_valid_delta_min"] > 0
        and common["shared_footprint_validity_delta_min"] > 0
        and differential["shared_footprint_validity_delta_min"] > 0
        and common["footprint_only_validity_delta_min"] >= 0
        and differential["footprint_only_validity_delta_min"] >= 0
    )
    return {
        "experiment": "E574_E573_SUPPORT_GAIN_DECOMPOSITION",
        "date": "2026-11-12",
        "source": source["source"],
        "baseline": baseline,
        "decomposition": {
            "total_net_support_delta": total,
            "shared_footprint_validity_delta": shared,
            "footprint_only_validity_delta": footprint,
            "footprint_component_share_pct": 100.0 * footprint / total,
            "shared_footprint_component_share_pct": 100.0 * shared / total,
        },
        "sensitivity": {
            "common_mode_translation": common,
            "differential_2025_translation": differential,
            "advantage_persists_at_every_tested_offset": persists,
        },
        "interpretation": [
            f"At zero offset, {footprint} of {total} net additional valid points ({100.0 * footprint / total:.2f}%) arise from footprint extent.",
            f"The remaining {shared} of {total} ({100.0 * shared / total:.2f}%) arise from valid/nodata differences inside the shared footprint.",
            f"Across common-mode offsets, total delta is {common['total_valid_delta_min']}–{common['total_valid_delta_max']}, shared-footprint delta is {common['shared_footprint_validity_delta_min']}–{common['shared_footprint_validity_delta_max']}, and footprint delta is {common['footprint_only_validity_delta_min']}–{common['footprint_only_validity_delta_max']}.",
            f"Across 2025-only differential offsets, total delta is {differential['total_valid_delta_min']}–{differential['total_valid_delta_max']}, shared-footprint delta is {differential['shared_footprint_validity_delta_min']}–{differential['shared_footprint_validity_delta_max']}, and footprint delta is {differential['footprint_only_validity_delta_min']}–{differential['footprint_only_validity_delta_max']}.",
            "This is point-support availability, not terrain accuracy, independent horizontal registration, route safety, or analogue similarity.",
        ],
        "claim_state": source["claim_boundary"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.input)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": result["experiment"],
        "total_net_support_delta": result["decomposition"]["total_net_support_delta"],
        "shared_footprint_delta": result["decomposition"]["shared_footprint_validity_delta"],
        "footprint_only_delta": result["decomposition"]["footprint_only_validity_delta"],
        "footprint_component_share_pct": result["decomposition"]["footprint_component_share_pct"],
        "advantage_persists_at_every_tested_offset": result["sensitivity"]["advantage_persists_at_every_tested_offset"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
