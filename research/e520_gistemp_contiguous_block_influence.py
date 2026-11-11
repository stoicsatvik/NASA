"""E520: retrospective contiguous evaluation-block exclusion, with frozen forecasts.

Run: python -m research.e520_gistemp_contiguous_block_influence
Exclusions affect scoring ONLY, not expanding-origin training or forecasts.
"""
import csv
from research.e519_gistemp_leave_one_year_out import DATA, COLUMNS, METHODS, errors


def winner(scores):
    """Deterministic tie-breaking in declared method order."""
    return min(METHODS, key=lambda method: (scores[method], METHODS.index(method)))


def influence(error_series, block_size):
    n = len(error_series[METHODS[0]])
    assert 0 < block_size < n
    assert all(len(error_series[k]) == n for k in METHODS)
    baseline = winner({k: sum(error_series[k]) / n for k in METHODS})
    cases = []
    for start in range(n - block_size + 1):
        remaining = [i for i in range(n) if not start <= i < start + block_size]
        scores = {k: sum(error_series[k][i] for i in remaining) / len(remaining)
                  for k in METHODS}
        cases.append((2011 + start, 2011 + start + block_size - 1, winner(scores)))
    return baseline, cases


def main():
    with DATA.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    years = [int(row["year"]) for row in rows]
    assert years == list(range(2001, 2026))
    for zone, column in COLUMNS:
        series = errors(years, [int(row[column]) / 100 for row in rows])
        for size in (1, 2, 5):
            original, cases = influence(series, size)
            flips = [(start, end, selected) for start, end, selected in cases
                     if selected != original]
            assert len(cases) == 16 - size
            print(f"{zone} block={size} baseline={original} flips={len(flips)}/{len(cases)} cases={flips}")


if __name__ == "__main__":
    main()
