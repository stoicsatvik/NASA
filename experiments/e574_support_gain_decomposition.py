"""E574: decompose E573's HiRISE valid-point support difference.

This is a deterministic analysis of E573's aggregate receipt, not a new
raster acquisition. It separates the net difference attributable to the
larger 2025 footprint from the difference in valid masks inside the shared
footprint. It makes no accuracy or registration claim.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def run(input_path: Path) -> dict[str, Any]:
    source = json.loads(input_path.read_text(encoding="utf-8"))
    baseline = source["baseline"]
    common = source["common_mode_translation"]
    differential = source["differential_2025_translation"]

    for name, mode in (("common_mode", common), ("differential_2025", differential)):
        if mode["offsets"] != 13:
            raise ValueError(f"{name} must contain 13 frozen offsets")
        for suffix in ("min", "max"):
            total = mode[f"total_valid_delta_{suffix}"]
            shared = mode[f"shared_footprint_validity_delta_{suffix}"]
            footprint = mode[f"footprint_only_validity_delta_{suffix}"]
            if total != shared + footprint:
                raise ValueError(f"{name} {suffix} support decomposition does not reconcile")

    total = baseline["total_valid_support_delta"]
    shared = baseline["shared_footprint_validity_delta"]
    footprint = baseline["footprint_only_validity_delta"]
    if total != shared + footprint:
        raise ValueError("baseline support decomposition does not reconcile")
    if baseline["hirise_2025_only_valid_within_shared_footprint"] != 83:
        raise ValueError("unexpected 2025 shared-footprint valid-only count")
    if baseline["hirise_2020_only_valid_within_shared_footprint"] != 61:
        raise ValueError("unexpected 2020 shared-footprint valid-only count")

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
            "advantage_persists_at_every_tested_offset": (
                common["total_valid_delta_min"] > 0
                and differential["total_valid_delta_min"] > 0
                and common["shared_footprint_validity_delta_min"] > 0
                and differential["shared_footprint_validity_delta_min"] > 0
            ),
        },
        "interpretation": [
            "At the zero-offset baseline, 73 of the 95 net additional valid points (76.84%) arise from points inside the 2025 footprint but outside the 2020 footprint.",
            "The remaining 22 of 95 (23.16%) arise from different valid/nodata masks within the 239-point shared footprint.",
            "Across the 13 tested common-mode offsets, the total advantage is 94-95 points, the shared-footprint component is 21-22, and the footprint component is 73.",
            "Across the 13 tested 2025-only differential offsets, the total advantage is 95 points, the shared-footprint component is 22, and the footprint component is 73.",
            "This is support availability, not terrain accuracy, independent horizontal registration, route safety, or analogue similarity.",
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
