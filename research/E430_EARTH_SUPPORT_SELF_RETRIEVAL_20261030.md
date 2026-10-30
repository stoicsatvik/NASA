# E430 | Real Earth DEM support-change self-retrieval falsification

**30 October 2026. Pre-event data-quality experiment; not a competition solution.**

## Question and frozen evidence
If four common terrain descriptors from E214's **real, source-fingerprinted Mapzen Skadi** Earth DEM patches represent a stable site signature, can a 2-km descriptor identify its own site's 4-km patch among three distinct candidate sites, without using coordinates or names as features?

Source: `research/results/e214_earth_skadi_real_data_20261024.json`, produced from source tiles in E214. Sites are **Lonar, Western Ghats and Ladakh research leads only**, not verified Moon/Mars analogues or negatives. The 2- and 4-km patches overlap; this is a support-stability diagnostic, **not an independent site holdout**. No raw rasters were reingested in E430.

Features: plane-detrended relief SD (metres), slope p50, slope p90 (dimensionless), and elevation range (metres). Compare two transparent, fixed distances: Euclidean after pooled six-row z scaling and Euclidean distance of feature log ratios. Positive finite values required. Query each 2-km site against all three 4-km sites; also omit each feature in turn. There is no training, fitted supervised model, planetary data, or label tuning. Pooled z scaling uses both supports, so this is descriptive, not a deployable blind model.

## Independently reproduced result
| Frozen distance | All four features: correct self-retrieval | Omit elevation range |
| --- | ---: | ---: |
| Pooled z-score Euclidean | **2/3** | **2/3** |
| Log-ratio Euclidean | **2/3** | **0/3** |

With all features, **Lonar and Western Ghats** retrieve their own larger patch, while **Ladakh retrieves Western Ghats** instead of itself under both distances. Under the log-ratio elevation-range ablation, all three 2-km queries select the wrong 4-km site. The other three single-feature ablations retain 2/3 under both distances.

A second independent Python implementation and a JavaScript implementation agreed on all ten 3-query configurations (two distances × five feature sets). Full-precision source values were used; rounded distances are only for display. The code and four repository tests are committed, but **the exact committed Python script and full test suite were not executed**; no paid GitHub Actions was requested.

The within-site p90 slope changes substantially with footprint: Lonar 0.4827→0.1418, Western Ghats 0.7508→0.5654, Ladakh 0.4665→0.6657. Elevation range changes 131→132 m, 395→531 m, and 336→742 m, respectively.

## Interpretation
- **SUPPORTED IN A SIX-ROW REAL-SOURCE DESCRIPTOR REANALYSIS:** these four E214 features do not always recover the same site across a 2→4 km support change, even in an Earth-only same-source control. Log-ratio self-retrieval is highly sensitive to retaining elevation range in this tiny cohort.
- **NOT ESTABLISHED:** any population error rate, general site-retrieval performance, actual Moon/Mars cross-instrument comparability, or a scientifically valid analogue ranking. Three sites, overlapping supports, no independent negatives and no uncertainty model are inadequate for statistical significance or a general claim.
- **E001 known-site recovery: NOT YET MEASURED. Cross-body similarity: NOT YET PROVEN. Novel analogue discovery: NOT YET PROVEN. Local validation advantage: NOT YET PROVEN. Challenge superiority: NOT YET PROVEN.**

## Next discriminating experiment
Acquire independently characterized paired Earth/Moon/Mars sites with spatially independent controls. Fix a common physical footprint, frequency band and instrument-missingness model **before** scoring; compare geography-only, random, physically weighted and standardized Euclidean baselines. Preserve false positives. If this is infeasible before 14–15 November, reconsider the officially listed alternative challenges rather than investing in a geospatial UI.

No fieldwork, outreach, new competition solution, main merge, public deployment, spending or irreversible action.
