"""E305: exploratory audit of published real THEMIS temperatures vs observation time.

Secondary published numerical observations, manually transcribed from Ahern et al.
(2021), JGR Planets, DOI 10.1029/2020JE006713, Table 4 (Bagnold Dunes).
NOT raw PDS pixels, an instrument calibration audit, or E001 analogue recovery.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import statistics
from functools import lru_cache
from pathlib import Path

SOURCE = "https://doi.org/10.1029/2020JE006713"
TABLE = "Table 4, Gale crater Bagnold Dunes (BD), 24 observations"
DATA = Path(__file__).parent / "data/e305_ahern_gale_bagnold_table4.csv"


def load(path: Path = DATA) -> list[dict]:
    raw = path.read_bytes()
    with path.open(newline="") as f:
        rows = list(csv.DictReader(f))
    required = {"image_id", "solar_longitude_deg", "local_time_h", "mars_year", "temperature_k", "vis_taud"}
    if len(rows) != 24 or any(set(row) != required for row in rows):
        raise ValueError("Unexpected published-table transcription structure")
    if len({r["image_id"] for r in rows}) != 24:
        raise ValueError("Duplicate THEMIS image ID")
    for r in rows:
        for key in required - {"image_id"}:
            r[key] = float(r[key])
            if not math.isfinite(r[key]):
                raise ValueError("Nonfinite table value")
        if not (0 <= r["solar_longitude_deg"] < 360 and 0 <= r["local_time_h"] < 24
                and 100 <= r["temperature_k"] <= 400):
            raise ValueError("Invalid physical bounds")
    return rows


def longitude_distance(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def matched(rows: list[dict], tolerance_deg: float) -> list[dict]:
    """Maximum-cardinality, minimum-total-season-distance one-to-one matching.

    No temperatures are used for selecting pairs. Ties follow CSV order.
    Distinct Mars years and atmospheres are NOT controlled by this matching.
    """
    if not (0 < tolerance_deg <= 180):
        raise ValueError("Invalid tolerance")
    morning = [r for r in rows if r["local_time_h"] < 12]
    evening = [r for r in rows if r["local_time_h"] >= 12]

    @lru_cache(None)
    def solve(i: int, mask: int) -> tuple:
        if i == len(morning):
            return (0, 0.0, ())
        best = solve(i + 1, mask)
        for j, e in enumerate(evening):
            if mask & (1 << j):
                continue
            d = longitude_distance(morning[i]["solar_longitude_deg"], e["solar_longitude_deg"])
            if d > tolerance_deg:
                continue
            tail = solve(i + 1, mask | (1 << j))
            candidate = (tail[0] + 1, tail[1] - d, ((i, j, d),) + tail[2])
            if candidate[:2] > best[:2]:
                best = candidate
        return best

    chosen = solve(0, 0)[2]
    return [
        {"morning_id": morning[i]["image_id"], "evening_id": evening[j]["image_id"],
         "solar_longitude_separation_deg": round(d, 6),
         "mars_years": [int(morning[i]["mars_year"]), int(evening[j]["mars_year"])],
         "evening_minus_morning_k": round(evening[j]["temperature_k"] - morning[i]["temperature_k"], 6)}
        for i, j, d in chosen
    ]


def run(path: Path = DATA) -> dict:
    rows = load(path)
    morning = [r["temperature_k"] for r in rows if r["local_time_h"] < 12]
    evening = [r["temperature_k"] for r in rows if r["local_time_h"] >= 12]
    sensitivity = {}
    for tol in (5, 10, 15, 20):
        pairs = matched(rows, tol)
        deltas = [p["evening_minus_morning_k"] for p in pairs]
        sensitivity[str(tol)] = {
            "n_disjoint_pairs": len(pairs),
            "all_evening_warmer": bool(deltas) and all(x > 0 for x in deltas),
            "mean_difference_k": round(statistics.mean(deltas), 6) if deltas else None,
            "minimum_difference_k": min(deltas) if deltas else None,
        }
    pairs10 = matched(rows, 10)
    return {
        "schema": "nasa/e305/published-themis-time-audit/v1",
        "source": SOURCE,
        "table": TABLE,
        "provenance": "Manual transcription of publisher Table 4; not an independent pixel-level verification",
        "transcription_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "measurement_status": "SECONDARY_PUBLISHED_REAL_OBSERVATIONS",
        "sample_count": len(rows),
        "morning_count": len(morning),
        "evening_count": len(evening),
        "morning_mean_k": round(statistics.mean(morning), 6),
        "evening_mean_k": round(statistics.mean(evening), 6),
        "unmatched_evening_minus_morning_mean_k": round(statistics.mean(evening) - statistics.mean(morning), 6),
        "ten_degree_pairs": pairs10,
        "ten_degree_positive_signs": sum(p["evening_minus_morning_k"] > 0 for p in pairs10),
        "sensitivity": sensitivity,
        "conclusion": "Observation time is a major uncontrolled nuisance for raw cross-scene brightness-temperature ranking in this small published sample",
        "not_causal": True,
        "confounds": ["different Mars years", "atmospheric opacity", "seasonal context", "nonrandom observation schedule", "within-site repeat dependence"],
        "e001_known_analogue_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "novel_analogue_discovery": "NOT YET PROVEN",
        "new_raw_pds_measurements": 0,
    }


if __name__ == "__main__":
    output = Path(__file__).parent / "results/e305_published_themis_time_audit.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = run()
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"output": str(output), "summary": payload["sensitivity"]}, sort_keys=True))
