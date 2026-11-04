"""Fail-closed audit for locally acquired planetary point CSV. No download implied."""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path

REQUIRED = ("source_url", "product_id", "body", "coordinate_frame",
            "latitude_unit", "longitude_unit", "value_unit",
            "native_resolution", "native_resolution_unit", "missing_tokens")


def audit(csv_path: Path, metadata_path: Path):
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    missing = [key for key in REQUIRED if not meta.get(key)]
    if missing:
        raise ValueError("Missing provenance fields: " + ", ".join(missing))
    if meta["latitude_unit"] != "degree" or meta["longitude_unit"] != "degree":
        raise ValueError("Only geographic degree coordinates supported")
    if meta["body"] not in ("Earth", "Moon", "Mars"):
        raise ValueError("Unrecognized body")
    tokens = meta["missing_tokens"]
    if not isinstance(tokens, list) or not all(isinstance(t, str) for t in tokens):
        raise ValueError("missing_tokens must be a list of strings")
    digest = hashlib.sha256(csv_path.read_bytes()).hexdigest()
    rows = valid = absent = 0
    minimum, maximum = math.inf, -math.inf
    with csv_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not {"latitude", "longitude", "value"}.issubset(reader.fieldnames or []):
            raise ValueError("CSV needs latitude, longitude, value")
        for rows, row in enumerate(reader, 1):
            try:
                lat, lon = float(row["latitude"]), float(row["longitude"])
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Row {rows}: invalid coordinates") from exc
            if not (math.isfinite(lat) and math.isfinite(lon)
                    and -90 <= lat <= 90 and -180 <= lon <= 180):
                raise ValueError(f"Row {rows}: coordinates outside range")
            raw = row["value"]
            if raw in tokens:
                absent += 1
                continue
            try:
                val = float(raw)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Row {rows}: undeclared fill or invalid value") from exc
            if not math.isfinite(val):
                raise ValueError(f"Row {rows}: nonfinite value")
            valid += 1
            minimum, maximum = min(minimum, val), max(maximum, val)
    if not valid:
        raise ValueError("No valid measurements")
    return dict(sha256=digest, rows=rows, valid=valid, missing=absent,
                minimum=minimum, maximum=maximum, value_unit=meta["value_unit"],
                product_id=meta["product_id"], source_url=meta["source_url"],
                coordinate_frame=meta["coordinate_frame"],
                native_resolution=meta["native_resolution"],
                native_resolution_unit=meta["native_resolution_unit"],
                note="Audit only; source authenticity and cross-body comparability unverified")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path)
    parser.add_argument("metadata", type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.csv, args.metadata), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
