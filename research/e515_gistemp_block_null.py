"""E515: exact block-permutation diagnostic on an existing NASA GISTEMP snapshot.

This is a retrospective *diagnostic*, NOT a calibrated climate significance test:
permuting five-year blocks assumes exchangeability that warming climate data do
not establish. It does not infer causes, forecast climate, or validate the
independently transcribed source snapshot.

Run from the NASA repository root:
    python -m research.e515_gistemp_block_null
"""
from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

SOURCE = Path(__file__).with_name("gistemp_zonal_2001_2025_snapshot.csv")
FIELDS = (
    "global_centi_c",
    "tropics_24S_24N_centi_c",
    "arctic_64N_90N_centi_c",
)
YEARS = tuple(range(2001, 2026))
BLOCK_SIZE = 5


def read_snapshot(path: Path = SOURCE) -> dict[str, object]:
    raw = path.read_bytes()
    try:
        rows = list(csv.DictReader(raw.decode("utf-8").splitlines()))
    except (UnicodeDecodeError, csv.Error) as exc:
        raise ValueError("invalid CSV encoding or structure") from exc
    if not rows or set(rows[0]) != {"year", *FIELDS}:
        raise ValueError("unexpected snapshot columns")
    try:
        years = tuple(int(row["year"]) for row in rows)
        series = {field: tuple(int(row[field]) for row in rows) for field in FIELDS}
    except (ValueError, TypeError, KeyError) as exc:
        raise ValueError("missing or noninteger snapshot value") from exc
    if years != YEARS:
        raise ValueError("expected exactly the ordered 2001-2025 annual series")
    return {"sha256": hashlib.sha256(raw).hexdigest(), "years": years, "series": series}


def slope_numerator(values: tuple[int, ...]) -> int:
    """Exact centered covariance numerator, valid for equally spaced years."""
    n = len(values)
    if n < 2:
        raise ValueError("need at least two annual observations")
    # The factor 2 keeps all operations exact for even or odd n.
    return sum((2 * i - (n - 1)) * value for i, value in enumerate(values))


def slope_c_per_decade(values: tuple[int, ...]) -> float:
    n = len(values)
    num = slope_numerator(values)
    den = sum((2 * i - (n - 1)) ** 2 for i in range(n))
    # x centered in half-years; values in centi-degrees C.
    return 20.0 * num / den / 100.0


def diagnostic(values: tuple[int, ...], block_size: int = BLOCK_SIZE) -> dict[str, object]:
    if len(values) != 25 or block_size != 5:
        raise ValueError("E515 freezes 25 observations and five 5-year blocks")
    blocks = tuple(values[i : i + block_size] for i in range(0, 25, block_size))
    observed = slope_numerator(values)
    permuted = tuple(
        slope_numerator(tuple(v for idx in ordering for v in blocks[idx]))
        for ordering in itertools.permutations(range(len(blocks)))
    )
    shifted = tuple(slope_numerator(values[k:] + values[:k]) for k in range(25))
    return {
        "observed_c_per_decade": round(slope_c_per_decade(values), 9),
        "five_year_block_permutations": len(permuted),
        "block_extreme_two_sided": sum(abs(v) >= abs(observed) for v in permuted),
        "block_tail_fraction": sum(abs(v) >= abs(observed) for v in permuted) / len(permuted),
        "block_null_slope_range_c_per_decade": [
            round(min(slope_c_per_decade(tuple(v for idx in p for v in blocks[idx])) for p in itertools.permutations(range(5))), 9),
            round(max(slope_c_per_decade(tuple(v for idx in p for v in blocks[idx])) for p in itertools.permutations(range(5))), 9),
        ],
        "circular_shifts": len(shifted),
        "circular_extreme_two_sided": sum(abs(v) >= abs(observed) for v in shifted),
        "circular_tail_fraction": sum(abs(v) >= abs(observed) for v in shifted) / len(shifted),
    }


def run(path: Path = SOURCE) -> dict[str, object]:
    source = read_snapshot(path)
    series = source["series"]
    assert isinstance(series, dict)
    arctic = series["arctic_64N_90N_centi_c"]
    tropics = series["tropics_24S_24N_centi_c"]
    values = {**series, "arctic_minus_tropics_centi_c": tuple(a - t for a, t in zip(arctic, tropics))}
    return {
        "experiment": "E515",
        "source": "NASA GISTEMP v4 zonal annual snapshot manually transcribed 2026-10-10",
        "official_source": "https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts%2BdSST.txt",
        "snapshot_sha256": source["sha256"],
        "years": [2001, 2025],
        "n_annual_observations": 25,
        "null_warning": "Descriptive block-exchangeability/circular-shift diagnostics only; not calibrated statistical p-values or climate attribution.",
        "results": {name: diagnostic(tuple(y)) for name, y in values.items()},
        "claim": "Retrospective trend diagnostic SUPPORTED for this pinned transcription; NASA source revalidation and independent trend inference NOT YET PROVEN.",
    }


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True))
