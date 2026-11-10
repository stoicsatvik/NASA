"""E530: source-pinned PAAD/MGD3 cross-body feature-admissibility audit.

This is a fail-closed readiness experiment, not a similarity model. It refuses
to equate ambiguous taxonomy codes or treat unlabelled records as negatives.
"""
from __future__ import annotations
import argparse
import csv
import json
from collections import Counter
from pathlib import Path

PAAD_DEFINITIONS = {
    "B": "barchan and barchanoid ridges combined",
    "C": "complex", "L": "longitudinal", "P": "parabolic",
    "S": "star", "SS": "sand sheet", "TR": "transverse ridge",
    "R": "reversing dunes", "MG": "mega-ripples", "RP": "ripples",
    "TIB": "topographically induced bedforms", "G": "Gobi", "WB": "whale back",
}
MGD3_DEFINITIONS = {
    "B": "barchan dune", "Bd": "barchanoid dune", "D": "dome dune",
    "L": "linear dune", "S": "star dune", "T": "transverse dune",
    "SS": "sand sheet",
}
MISSING = {"", "nan", "na", "n/a", "none", "null", "<< empty cell >>"}
STRICT = {"S", "SS"}
CANDIDATE = {"L"}
AMBIGUOUS = {"B"}

def missing(value):
    return value is None or str(value).strip().lower() in MISSING

def tokens(value):
    if missing(value):
        return []
    return [part.strip() for part in str(value).split(",") if part.strip()]

def read_csv(path):
    with open(path, newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))

def covered(rows, accepted):
    return sum(bool(set(tokens(row.get("Dune_Type"))) & accepted) for row in rows)

def summarize(paad, mgd3, join_rows):
    if not paad or not mgd3 or not join_rows:
        raise ValueError("all three source tables must be nonempty")
    if len({r["Field_Site"] for r in paad}) != len(paad):
        raise ValueError("PAAD Field_Site values are not unique")
    if len({r["Dune_ID"] for r in mgd3}) != len(mgd3):
        raise ValueError("MGD3 Dune_ID values are not unique")

    p_counts = Counter(t for r in paad for t in tokens(r.get("Dune_Type")))
    m_counts = Counter(t for r in mgd3 for t in tokens(r.get("Dune_Type")))
    shared = set(p_counts) & set(m_counts)
    strict = set(STRICT)
    candidate = strict | CANDIDATE
    naive = candidate | AMBIGUOUS

    parsed = []
    for row in join_rows:
        try:
            payload = json.loads(row["row_json"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("malformed 2018 row_json") from exc
        parsed.append({**row, "payload": payload})
    eq = [r for r in parsed if "Equatorial" in r.get("workbook", "")]
    matched = [r for r in eq if str(r.get("matched_2007_spatial", "")).lower() == "true"]
    stability = [r for r in eq if r.get("sheet") == "Stability Index"]
    stability_ids = [str(r["payload"].get("Dune_ID", "")) for r in stability]
    themis = [r for r in eq if r.get("sheet") == "THEMIS ATI, TES dune modeling"]

    summaries = {}
    mineral_fields = ("Feldspar", "High-Silica Phases", "Olivine", "Pyroxene",
                      "Sulfate", "Carbonate", "Quartz", "Hematite")
    for sheet in ("Global Summary ocks <7000", "Global Summary all ocks"):
        selected = [r for r in eq if r.get("sheet") == sheet]
        payloads = [r["payload"] for r in selected]
        summaries[sheet] = {
            "rows": len(selected),
            "unique_ids": len({str(p.get("Dune ID", "")) for p in payloads if not missing(p.get("Dune ID"))}),
            "matched_rows": sum(str(r.get("matched_2007_spatial", "")).lower() == "true" for r in selected),
            "thermal_inertia": sum(not missing(p.get("Average Bolometer nighttime thermal inertia (tiu)")) for p in payloads),
            "albedo": sum(not missing(p.get("Average Daytime Albedo")) for p in payloads),
            "mineral_composition": sum(any(not missing(p.get(f)) for f in mineral_fields) for p in payloads),
        }

    strict_p, strict_m = covered(paad, strict), covered(mgd3, strict)
    candidate_p, candidate_m = covered(paad, candidate), covered(mgd3, candidate)
    naive_p, naive_m = covered(paad, naive), covered(mgd3, naive)
    target_fields = {"Target_Body", "Target_Planet", "target_body", "family"}
    return {
        "experiment": "E530_CROSSBODY_FEATURE_ADMISSIBILITY",
        "status": "AUDITED",
        "paad": {
            "rows": len(paad), "unique_sites": len({r["Field_Site"] for r in paad}),
            "missing": {f: sum(missing(r.get(f)) for r in paad)
                        for f in ("Sand_Source", "Composition_of_Sand", "Elevation", "Areal_Coverage")},
            "dune_type_token_counts": dict(sorted(p_counts.items())),
            "target_body_label_field_present": bool(target_fields & set(paad[0])),
            "non_analogue_control_labels": 0,
        },
        "mgd3_2007": {
            "rows": len(mgd3), "unique_dune_ids": len({r["Dune_ID"] for r in mgd3}),
            "dune_type_token_counts": dict(sorted(m_counts.items())),
            "area_km2_nonmissing": sum(not missing(r.get("Area_sinu_")) for r in mgd3),
            "average_elevation_m_nonmissing": sum(not missing(r.get("Avg_El")) for r in mgd3),
        },
        "mgd3_2018_equatorial_join": {
            "rows": len(eq), "matched_rows": len(matched),
            "unique_2007_dune_ids_matched": len({r["dune_id"] for r in matched}),
            "unmatched_2007_dune_ids": len(mgd3) - len({r["dune_id"] for r in matched}),
            "stability_index_rows": len(stability),
            "stability_index_unique_ids": len(set(stability_ids)),
            "stability_index_duplicate_rows": len(stability_ids) - len(set(stability_ids)),
            "stability_index_matched_rows": sum(str(r.get("matched_2007_spatial", "")).lower() == "true" for r in stability),
            "themis_ati_tes_rows": len(themis),
            "themis_ati_tes_matched_rows": sum(str(r.get("matched_2007_spatial", "")).lower() == "true" for r in themis),
            "global_summary_sheets": summaries,
        },
        "dune_type_crosswalk": {
            "raw_shared_tokens": sorted(shared),
            "strict_name_matches": sorted(strict),
            "candidate_semantic_matches_not_admitted": sorted(CANDIDATE),
            "ambiguous_matches_rejected": sorted(AMBIGUOUS),
            "paad_only_tokens": sorted(set(p_counts) - set(m_counts)),
            "mgd3_only_tokens": sorted(set(m_counts) - set(p_counts)),
            "coverage_sensitivity": {
                "strict_exact": {"paad_sites": strict_p, "paad_total": len(paad), "mgd3_fields": strict_m, "mgd3_total": len(mgd3)},
                "candidate_plus_L": {"paad_sites": candidate_p, "paad_total": len(paad), "mgd3_fields": candidate_m, "mgd3_total": len(mgd3)},
                "naive_including_B": {"paad_sites": naive_p, "paad_total": len(paad), "mgd3_fields": naive_m, "mgd3_total": len(mgd3)},
            },
            "interpretation": (
                "PAAD B combines barchan and barchanoid ridges; MGD3 separates B=barchan and Bd=barchanoid. "
                "L is longitudinal versus linear and remains a candidate, not an admitted exact match. "
                "S and SS have matching names/definitions. TR (transverse ridge) is not equated with T (transverse dune)."
            ),
        },
        "feature_admissibility": {
            "directly_shared_quantitative_features": [],
            "candidate_pairs": [
                {"paad": "Elevation (m)", "mgd3": "Avg_El (m)", "status": "WITHIN_BODY_NORMALIZATION_ONLY",
                 "reason": "Earth sea-level/GMTED2010 or literature elevations and Mars MOLA-based elevation do not share an absolute datum."},
                {"paad": "Areal_Coverage (approximate km2)", "mgd3": "Area_sinu_ (km2)", "status": "SENSITIVITY_ONLY",
                 "reason": "Approximate literature site coverage and THEMIS polygon area have different spatial support and mapping rules."},
                {"paad": "Composition_of_Sand (narrative)", "mgd3": "mineral abundances (%)", "status": "NOT_COMPARABLE_AS_STORED",
                 "reason": "PAAD prose mixes source-specific qualitative/quantitative descriptions; MGD3 reports instrument-derived abundances with errors."},
                {"paad": "Dune_Type", "mgd3": "Dune_Type", "status": "PARTIAL_CATEGORICAL_ONLY",
                 "reason": "Only S and SS are strict name/definition matches; L is a candidate and B is ambiguous."},
            ],
            "earth_only": ["Koppen-Geiger climate class", "sand source narrative"],
            "mars_only": ["THEMIS thermal inertia", "daytime albedo", "TES mineral abundances/errors", "morphologic stability index"],
        },
        "e001_readiness": {
            "ready": False,
            "reasons": [
                "PAAD has no per-site target-body/family label in its core schema.",
                "PAAD supplies analog-site records only and no non-analogue control labels.",
                "No shared quantitative physical descriptor family is directly admissible.",
                "Dune-type overlap is partial and some shared tokens are semantically ambiguous.",
            ],
        },
        "claim_states": {
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
        },
        "provenance": {
            "paad_doi": "10.5066/P9IFVZEX",
            "mgd3_2007_doi": "10.3133/ofr20071158",
            "mgd3_2018_doi": "10.3133/ofr20181164",
            "paad_source_artifact_id": 13804420438,
            "mgd3_source_artifact_id": 13804087352,
            "paad_archive_sha256": "404d938ec4d55e1bac4a6bb06d463434a4c7e2fdb291fca026fb8ef90bc2427e",
            "mgd3_2007_shapefiles_sha256": "a43e8f842aa0e9b1edb920a2624a430ebf7fb6a059fc9c6f1ae37cc179635f34",
            "mgd3_2007_tables_sha256": "9f2e7fe86f813cafcabf34587648e2d6d31a6207046a6d32fb2a98953c8cadb1",
            "mgd3_2018_workbook_sha256": "92771c23cfa4a64dfcc38f5ad29de00adfa41b9f321d3665beb2112eefe3485e",
        },
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--paad", required=True, type=Path)
    parser.add_argument("--mgd3-2007", required=True, type=Path)
    parser.add_argument("--mgd3-2018-join", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = summarize(read_csv(args.paad), read_csv(args.mgd3_2007), read_csv(args.mgd3_2018_join))
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered)

if __name__ == "__main__":
    main()
