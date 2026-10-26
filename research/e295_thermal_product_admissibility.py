"""E295: source-grounded THEMIS product admissibility and monotone-stretch falsification.

Synthetic mathematical counterexample, not a new planetary measurement.
Research only; no E001 recovery or pre-event competition solution.
"""
from __future__ import annotations

import json
from pathlib import Path

SOURCES = {
    "themis_night_global_mosaic": {
        "source": "https://astrogeology.usgs.gov/search/map/mars_odyssey_themis_ir_night_60n60s_mosaic_100m_v14",
        "kind": "visual_stretched_blended",
        "quantity": "display_intensity",
        "unit": None,
        "reason": "USGS states original temperature values were stretched and blended for visualization",
    },
    "themis_ir_pbt": {
        "source": "https://ode.rsl.wustl.edu/venus/pagehelp/Content/Missions_Instruments/Mars_Odyssey/THEMIS/ODTGEO/IR/IRPBT4.htm",
        "kind": "calibrated_product_family",
        "quantity": "brightness_temperature",
        "unit": "K",
        "reason": "Projected per-observation brightness-temperature products; individual PDS labels must be verified",
    },
    "diviner_stn": {
        "source": "https://github.com/stoicsatvik/NASA/pull/22",
        "kind": "calibrated_product_family",
        "quantity": "nighttime_temperature_deviation",
        "unit": "K",
        "reason": "Rock-free regolith nighttime temperature deviation, not absolute brightness temperature",
    },
}
REQUIRED_OBSERVATION_FIELDS = (
    "label_verified", "valid_mask_verified", "observation_time_verified",
    "footprint_verified", "projection_verified",
)


def product_gate(product: str, observation: dict | None = None) -> dict:
    """Fail closed: catalog units are not proof of a particular pixel's units."""
    if product not in SOURCES:
        return {"status": "UNKNOWN_PRODUCT", "quantitative": False}
    source = SOURCES[product]
    if source["kind"] == "visual_stretched_blended":
        return {"status": "REJECT_VISUAL_MOSAIC", "quantitative": False,
                "source": source["source"], "reason": source["reason"]}
    metadata = observation or {}
    missing = [k for k in REQUIRED_OBSERVATION_FIELDS if metadata.get(k) is not True]
    if missing:
        return {"status": "NEEDS_PRODUCT_METADATA", "quantitative": False,
                "missing": missing, "source": source["source"]}
    return {"status": "WITHIN_PRODUCT_QUANTITATIVE_CANDIDATE", "quantitative": True,
            "cross_body_comparable": False, "quantity": source["quantity"],
            "unit": source["unit"], "source": source["source"]}


def cross_product_gate(a: str, b: str, observations: tuple[dict, dict]) -> dict:
    first, second = product_gate(a, observations[0]), product_gate(b, observations[1])
    if not first.get("quantitative") or not second.get("quantitative"):
        return {"status": "REJECT_UNVERIFIED_QUANTITATIVE_INPUT"}
    if first["quantity"] != second["quantity"]:
        return {"status": "REJECT_QUANTITY_MISMATCH", "units_match": first["unit"] == second["unit"]}
    return {"status": "HARMONIZATION_NOT_ESTABLISHED", "cross_body_comparable": False}


def piecewise_linear(x: float, anchors: tuple[tuple[float, float], ...]) -> float:
    if not anchors or any(anchors[i][0] >= anchors[i+1][0] or
                          anchors[i][1] >= anchors[i+1][1]
                          for i in range(len(anchors)-1)):
        raise ValueError("Anchors must increase strictly in both coordinates")
    if x < anchors[0][0] or x > anchors[-1][0]:
        raise ValueError("Outside explicit synthetic anchors")
    for (x0, y0), (x1, y1) in zip(anchors, anchors[1:]):
        if x0 <= x <= x1:
            return y0 + (x - x0) * (y1 - y0) / (x1 - x0)
    return anchors[-1][1]


def counterexample() -> dict:
    """An invertible monotone display stretch reverses nearest-site ranking."""
    target_k, a_k, b_k = 245., 240., 260.
    anchors = ((240., 0.), (245., 90.), (260., 100.))
    t, a, b = (piecewise_linear(x, anchors) for x in (target_k, a_k, b_k))
    raw_distances = {"A": abs(a_k-target_k), "B": abs(b_k-target_k)}
    display_distances = {"A": abs(a-t), "B": abs(b-t)}
    return {
        "synthetic_only": True,
        "physical_k": {"target": target_k, "A": a_k, "B": b_k},
        "strictly_monotone_display_anchors": anchors,
        "raw_distances_k": raw_distances,
        "display_distances_arbitrary_units": display_distances,
        "raw_nearest": min(raw_distances, key=raw_distances.get),
        "display_nearest": min(display_distances, key=display_distances.get),
        "inference": "Nearest-neighbor ranking is not invariant under arbitrary monotone display stretch",
    }


def run() -> dict:
    complete = {key: True for key in REQUIRED_OBSERVATION_FIELDS}
    return {
        "schema": "nasa/e295/thermal-source-admissibility/v1",
        "experiment": "Quantitative product admissibility and monotone-display counterexample",
        "sources": SOURCES,
        "synthetic_counterexample": counterexample(),
        "gates": {
            "visual_mosaic": product_gate("themis_night_global_mosaic", complete),
            "pbt_without_label": product_gate("themis_ir_pbt", {}),
            "pbt_complete_hypothetical_metadata": product_gate("themis_ir_pbt", complete),
            "pbt_vs_diviner_complete_hypothetical_metadata": cross_product_gate(
                "themis_ir_pbt", "diviner_stn", (complete, complete)),
        },
        "claim": "USGS THEMIS global mosaics are visual, not calibrated temperatures; mathematical rank reversal is PROVEN for the synthetic transform",
        "e001_known_analogue_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "new_real_measurements": 0,
        "limitations": [
            "No new THEMIS PBT bytes or individual observation labels ingested",
            "Monotone display transform is illustrative, not a measured USGS mosaic transform",
            "Product gate is a fail-closed research control, not a validated harmonization model",
            "K in distinct instrument quantities does not imply comparability",
        ],
    }


if __name__ == "__main__":
    path = Path(__file__).parent / "results/e295_thermal_product_admissibility.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = run()
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"result": str(path), "counterexample": payload["synthetic_counterexample"],
                      "gates": payload["gates"]}, indent=2))
