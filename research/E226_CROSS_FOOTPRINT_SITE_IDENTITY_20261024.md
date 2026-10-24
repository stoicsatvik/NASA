# E226 — Cross-footprint site identity can fail even before planetary-analogue recovery

**24 October 2026.** Exploratory, post-E221/E223 experiment on the existing **150 real SRTM-derived, overlapping** Earth terrain windows. Immutable source Git blob: `781266d3c61a20411e372c1f81c07dd96e51378e`. The three source locations are **unvalidated research leads**, not established analogue labels.

## Falsifiable question

Can two elementary physical-terrain descriptors recognize the *same Earth source location* when the observation footprint changes from 2 km to 4 km, without fitting a model to the queries?

For each reference footprint, select exactly **one central-offset reference per site**. Query the 24 *noncentral* coordinate-offset windows per site at 2 km and 4 km, respectively: 72 queries per case. Rank three references by Euclidean distance after scaling each descriptor by **reference-only** population standard deviation. Evaluate relief-only, slope-only and two-feature ablations. Exact enumeration of all 3! reference-label permutations is a sensitivity check, not a statistical significance test.

## Exact exploratory measurements

| Query footprint → reference footprint | Relief only | Slope only | Two features |
|---|---:|---:|---:|
| 2 km → 2 km | 49/72 | 30/72 | **50/72 (69.4%)** |
| 4 km → 2 km | 48/72 | **4/72 (5.6%)** | **47/72 (65.3%)** |
| 2 km → 4 km | 39/72 | **10/72 (13.9%)** | **30/72 (41.7%)** |
| 4 km → 4 km | 51/72 | **68/72 (94.4%)** | **68/72 (94.4%)** |

Uniform random reference choice has expected accuracy 1/3 (24/72), **not an empirical confidence bound**.

For the 2 km queries against 4 km references, two-feature identity retrieval falls to **30/72**, compared with **68/72** for 4 km queries against 4 km references. The reverse transfer is asymmetric (47/72). The slope-only 4 km→2 km result is just **4/72**, which is worse than the uniform-random expectation.

**Exact label-permutation check:** In the 2 km→4 km two-feature case, the six reference-label permutations yield correct counts **[30, 3, 17, 16, 26, 52]**. A different assignment can score 52/72, so the observed 30/72 must not be promoted into a significance claim.

## What this eliminates

A simple two-feature, reference-normalized nearest-neighbor system does **not** consistently preserve even *source-site identity* across these two observation footprints. Footprint-dependent feature shifts are a concrete failure mode to address before attempting Earth–Moon–Mars similarity. The result is an **exploratory falsification of scale-agnostic nearest-neighbor transfer in this tiny source-site sanity test**, not a general impossibility result.

## Hard limits

- The source-site label is geographic provenance, **not independent known-analogue ground truth**. This is **NOT E001** and does not measure planetary analogue recovery.
- Only three sites, all selected as leads. No independently sourced negative sites. No independent held-out sites.
- All 24 shifted windows overlap their reference's source tile; same-footprint performance is especially susceptible to spatial leakage. Exact center query is excluded but **not** the overlapping data.
- The 72 queries are not independent observations, and the exact label-permutation counts do not justify inferential p-values.
- Feature choices, footprint sizes and comparisons were inspected after prior analyses, so this is **not preregistered**.
- SRTM-derived Mapzen mosaics are not independent NASADEM data; no new rasters or field observations were obtained.

## Reproduction

```bash
python -m unittest discover -s tests -p 'test_e226_cross_footprint_identity.py' -v
python research/e226_cross_footprint_identity.py --output e226_real_site_identity.json
```

The branch-scoped CI verifies six exact real-data counts, 12 cases and permutation-accounting invariants, and uploads full confusion matrices as a numerical artifact. No competition submission or deployment.

**Claim states:** E226 site-identity footprint sensitivity **SUPPORTED CONDITIONAL ON RECORDED REAL MEASUREMENTS**; cross-body similarity **NOT YET PROVEN**; E001 known-analogue recovery **NOT YET MEASURED**; novel analogue discovery and local validation advantage **NOT YET PROVEN**.

**Next decisive action:** independently sourced positive and negative planetary analogue labels, then blind leave-one-site-out recovery with physically matched descriptors, random and conventional baselines, and instrument uncertainty. Do not replace missing ground truth with more unvalidated source-site classification.
