"""E522: test whether NASA's public Analog Explorer gallery is E001-ready.

This is a deterministic source-admissibility audit, not an analogue-recovery
experiment. The NASA gallery supplies curated pair labels and qualitative
context, but the page does not publish numeric site features, site coordinates,
footprints, or negative controls in the gallery records.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ROOT / "data" / "nasa_analog_explorer_pairs.csv"
SOURCE_URL = "https://science.nasa.gov/solar-system/analog-explorer/"


def load_catalogue(path: Path = CATALOGUE) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise ValueError("catalogue is empty")
    ids = [row["pair_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("pair_id values must be unique")
    for row in rows:
        if row["in_scope_moon_mars"] not in {"0", "1"}:
            raise ValueError("in_scope_moon_mars must be 0 or 1")
        if (not row["earth_site"] or not row["target_feature"] or not row["mechanism"]
                or row["source_url"] != SOURCE_URL or row["source_accessed_utc"] != "2026-11-10"):
            raise ValueError("every pair needs a named site, feature, source URL, and access date")
    return rows


def audit(rows: list[dict[str, str]] | None = None) -> dict:
    rows = rows if rows is not None else load_catalogue()
    scoped = [row for row in rows if row["in_scope_moon_mars"] == "1"]
    excluded = [row for row in rows if row["in_scope_moon_mars"] == "0"]
    body_counts = Counter(row["target_body"] for row in scoped)
    mechanism_counts = Counter(row["mechanism"] for row in scoped)

    # E001's centroid fold requires at least two same-family positives plus
    # negative controls. Grouping by body creates heterogeneous mechanisms;
    # grouping by mechanism leaves every gallery family with one positive.
    body_grouping_has_minimum_count = all(count >= 2 for count in body_counts.values())
    mechanism_grouping_has_reference_centroid = all(
        count >= 2 for count in mechanism_counts.values()
    )
    numeric_features_present = False
    coordinates_and_footprints_present = False
    negative_controls_present = False

    reasons = [
        "The gallery contains curated positive analogue pairs, not negative controls.",
        "The gallery page does not provide a numeric feature matrix for the named Earth sites.",
        "The gallery page does not provide site coordinates or analysis footprints in its pair records.",
        "Grouping by target body mixes distinct analogue mechanisms; grouping by mechanism leaves singleton positive families.",
    ]
    return {
        "source_url": SOURCE_URL,
        "source_accessed_utc": "2026-11-10",
        "catalogue_pair_count": len(rows),
        "moon_mars_pair_count": len(scoped),
        "out_of_scope_pair_count": len(excluded),
        "moon_mars_target_body_counts": dict(sorted(body_counts.items())),
        "mechanism_family_count": len(mechanism_counts),
        "mechanism_family_sizes": dict(sorted(mechanism_counts.items())),
        "body_grouping_has_minimum_positive_count": body_grouping_has_minimum_count,
        "mechanism_grouping_has_reference_centroid": mechanism_grouping_has_reference_centroid,
        "numeric_features_present": numeric_features_present,
        "coordinates_and_footprints_present": coordinates_and_footprints_present,
        "negative_controls_present": negative_controls_present,
        "e001_ready": False,
        "reasons": reasons,
        "claim_state": "SOURCE CATALOGUE SUPPORTED; E001 RECOVERY NOT YET MEASURED",
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
