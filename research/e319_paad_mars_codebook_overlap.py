"""E319: falsify the assumption that PAAD and MGD3 labels are already harmonized.

This is a SOURCE-SCHEMA audit of real Earth data against the *published* 2007
MGD3 Table 1 code strings, NOT a trained cross-body analogue model.
Exact code-string overlap is a necessary but insufficient condition for
semantic equivalence. The 2018 MGD3 workbook is not the 2007 morphology table.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path

from research.e317_paad_independent_source import (
    SOURCE, _read, metadata_summary,
)

EXPECTED_CSV_SHA256 = "5be67b4da584987d9ce5207f2ee3c90b5b3b5849469461847111eaab5aafcecd"
PAAD_FILENAME = "Planetary Aeolian Analog Database_core attributes.csv"
MARS_CODEBOOK_SOURCE = "https://doi.org/10.1029/2007JE002943"
# Hayward et al. (2007), Table 1. Exact case is deliberate: Bd != B.
# These are source-reported assignment counts, NOT independent Martian sites.
MARS_CODE_ASSIGNMENTS = {
    "SS": 128, "D": 8, "B": 144, "Bd": 261,
    "T": 91, "L": 27, "S": 6, "U": 275,
}
MAX_ROWS = 5000


def split_raw_codes(value: str) -> tuple[str, ...]:
    """Lexical tokens only. Never expand abbreviations or infer morphology."""
    if not isinstance(value, str):
        raise TypeError("raw dune type must be text")
    return tuple(part.strip() for part in re.split(r"[,;/+]", value)
                 if part.strip())


def audit_csv(data: bytes) -> dict:
    reader = csv.DictReader(io.StringIO(data.decode("utf-8-sig")))
    if not reader.fieldnames or not {"Field_Site", "Dune_Type"} <= set(reader.fieldnames):
        raise ValueError("required PAAD columns absent")
    raw_categories = Counter()
    tokens = Counter()
    unsupported = Counter()
    seen_sites = set()
    total = 0
    with_any = 0
    single = 0
    multiple = 0
    all_exact = 0
    partially_exact = 0
    for row in reader:
        if not any((v or "").strip() for v in row.values() if isinstance(v, str)):
            continue
        total += 1
        if total > MAX_ROWS:
            raise ValueError("PAAD row limit exceeded")
        site = (row.get("Field_Site") or "").strip()
        if not site or site in seen_sites:
            raise ValueError("missing or duplicated PAAD site identifier")
        seen_sites.add(site)
        raw = (row.get("Dune_Type") or "").strip()
        raw_categories[raw] += 1
        parts = split_raw_codes(raw)
        tokens.update(parts)
        unsupported.update(p for p in parts if p not in MARS_CODE_ASSIGNMENTS)
        if parts:
            with_any += 1
            single += len(parts) == 1
            multiple += len(parts) > 1
            matched = sum(p in MARS_CODE_ASSIGNMENTS for p in parts)
            all_exact += matched == len(parts)
            partially_exact += 0 < matched < len(parts)
    return {
        "earth_rows": total,
        "distinct_sites": len(seen_sites),
        "nonempty_dune_type_rows": with_any,
        "single_token_rows": single,
        "multi_token_rows": multiple,
        "rows_with_all_tokens_in_mars_2007_codebook": all_exact,
        "rows_with_partial_codebook_overlap": partially_exact,
        "raw_dune_type_cells": dict(sorted(raw_categories.items())),
        "raw_token_counts": dict(sorted(tokens.items())),
        "tokens_not_in_mars_2007_codebook": dict(sorted(unsupported.items())),
        "mars_2007_codebook_assignment_counts": MARS_CODE_ASSIGNMENTS,
        "mars_2007_codebook_source": MARS_CODEBOOK_SOURCE,
        "status": "LEXICAL_OVERLAP_ONLY_NOT_SEMANTIC_HARMONIZATION",
        "earth_codebook_semantics": "UNVERIFIED",
        "mars_2018_workbook_morphology_linkage": "NOT ESTABLISHED",
        "independent_positive_negative_pairs": "ABSENT",
        "e001_known_site_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "limitations": [
            "Matching letter codes do not prove that two data curators used the same taxonomy.",
            "Multiple dune types at one site are not independent training examples.",
            "Mars Table 1 assignment counts are not distinct Mars site counts.",
            "No Earth-Mars site pair or independently labeled negative site was supplied.",
            "No physical descriptor or blind analogue recovery was evaluated.",
        ],
    }


def retrieve_paad() -> tuple[bytes, dict]:
    metadata_raw = _read(SOURCE, 2_000_000)
    summary = metadata_summary(json.loads(metadata_raw))
    matches = [f for f in summary["files"]
               if f["name"] == PAAD_FILENAME and f.get("_uri")]
    if len(matches) != 1:
        raise ValueError("expected unique official PAAD core CSV not found")
    entry = matches[0]
    if not isinstance(entry["bytes_declared"], int) or not (0 < entry["bytes_declared"] < 1_000_000):
        raise ValueError("PAAD declared size outside bounded range")
    data = _read(entry["_uri"], 1_000_000)
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_CSV_SHA256:
        raise ValueError("PAAD source bytes differ from E317 frozen source")
    return data, {
        "source": SOURCE, "doi": summary["doi"], "filename": PAAD_FILENAME,
        "sha256": digest, "bytes": len(data),
        "metadata_sha256": hashlib.sha256(metadata_raw).hexdigest(),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    data, source = retrieve_paad()
    result = audit_csv(data)
    result["source_receipt"] = source
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": result["status"], "earth_rows": result["earth_rows"],
        "single_token_rows": result["single_token_rows"],
        "multi_token_rows": result["multi_token_rows"],
        "rows_with_all_tokens_in_mars_2007_codebook": result["rows_with_all_tokens_in_mars_2007_codebook"],
        "rows_with_partial_codebook_overlap": result["rows_with_partial_codebook_overlap"],
        "tokens_not_in_mars_2007_codebook": result["tokens_not_in_mars_2007_codebook"],
        "sha256": source["sha256"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
