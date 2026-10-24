# E223 — Independent-site coordinate jitter changes the interpretation of E221

**Date:** 2026-10-24. **Input:** E221's 150 actual Mapzen Skadi SRTM-derived, overlapping Earth elevation windows at three unvalidated research leads, two footprints, 25 fixed coordinate offsets each. Input Git blob: `781266d3c61a20411e372c1f81c07dd96e51378e`.

## Falsifiable question

E221 shifted all three research sites by the **same** offset, producing 25 synchronized three-site rankings. But real site-coordinate errors need not move in lockstep. Does the E221 conclusion survive all independent choices of one of the 25 offsets at each site?

Enumerate the exact Cartesian product of the recorded measurements: `25^3 = 15,625` site-offset assignments for **each** of four descriptor/footprint combinations. Compare the ranking at the central coordinates with (a) the 25 common-offset assignments and (b) all 15,625 independent-site assignments. No new elevation data, hidden labels, or model fitting.

## Exact conditional results

| Metric / footprint | Central ordering preserved, shared 25 offsets | Central ordering preserved, independent 15,625 combinations | Most frequent top site, independent |
|---|---:|---:|---|
| Detrended relief SD / 2 km | 19/25 = 76% | 12,117/15,625 = **77.5488%** | Western Ghats 89.4784% |
| Slope p90 / 2 km | 6/25 = 24% | 2,625/15,625 = **16.8%** | Western Ghats 95.52% |
| Detrended relief SD / 4 km | 16/25 = 64% | 10,250/15,625 = **65.6%** | Ladakh 65.6% |
| Slope p90 / 4 km | 25/25 = 100% | 15,625/15,625 = **100%** | Ladakh 100% |

**Important distinction:** The full three-site *ordering* can be unstable while the top-ranked site is quite stable. At 2 km slope p90, the center's entire ordering survives only 16.8% of independent assignments, but the Western Ghats lead stays top in 95.52% of them. At 4 km slope p90, the ordering survives every tested assignment. Do not call every descriptor unstable.

## What this eliminates

The 25 synchronized E221 rankings are not a complete characterization of site-specific coordinate perturbations. Enumerating independent offsets can expose more rank orderings than synchronized shifts (e.g. six distinct relief orderings at 2 km versus three under synchronized shifts). Thus reporting only synchronized shifts hides possible worst-case rank reversals.

## Interpretation limits

- **These fractions are NOT empirical probabilities**, confidence intervals, independently sampled replicates, or measured geolocation uncertainty. They are exact fractions of a **uniformly weighted, analyst-selected finite grid**.
- All windows overlap, so multiplying them into 15,625 combinations does not create 15,625 independent Earth observations.
- Sites are unvalidated research leads. No planetary analogue identity was recovered; E001 remains **NOT YET MEASURED**.
- No Moon/Mars measurements are compared here. Cross-body similarity remains **NOT YET PROVEN**.
- Geolocation perturbations of ±500 m were assumed, not inferred from instrument accuracy.
- The underlying Mapzen products are SRTM-derived/mosaicked, not direct NASADEM with pixel-level provenance.

## Reproduction

```bash
python -m unittest discover -s tests -p 'test_e223_independent_jitter_rank.py' -v
python research/e223_independent_jitter_rank.py --output research/results/e223_independent_jitter_rank_local.json
```

The branch-specific GitHub Actions workflow checks the full E221 input and validates exact known rank-count invariants. CI uploads the computed JSON as an artifact; no downloaded raster bytes are committed.

**Claim:** Finite-grid independent-jitter sensitivity **SUPPORTED CONDITIONAL ON E221 MEASUREMENTS**. It does not support new analogue identification.

**Next decisive experiment:** Obtain independent geological/planetary analogue reference labels and negative controls. Evaluate E001 with physically comparable descriptors, blind holdouts and a random baseline. If labels are unavailable, explicitly document that blocker rather than treating these rank audits as recovery evidence.
