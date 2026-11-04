# E493 — Adversarial audit of a public planetary-analogue benchmark (2026-11-02)

## Decision question
Does the leading 2026 planetary-analogue Space Apps direction still offer a distinctive, defensible **evidence** advantage, or is a published competitor's apparent perfect validation a weak/easy-control result? This is a **challenge-selection falsification** experiment, not E001 known-site recovery.

## Independently accessed, pinned sources
Third-party public repository: `Yakiyo/terra-nova`, commit `7128cc5363e916e422f7c770db9983981c0716f2` (2026-10-31). Read-only inspection; no collaboration, copying of implementation, or contact.
- `data/known_analogs.json`, Git blob `d75240ce203ddb00b2d9186e7981ab90720ff9a3`
- `data/targets.json`, Git blob `ed326364e2ba4bad3e05a0bb48d06c23d7c87d4c`
- `src/compute/validation.py`, source-inspected at the pinned commit
- Public README at that commit states ROC-AUC 1.00 for its built-in targets; **that reported score was NOT independently rerun**.
- Official challenge: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/

## Direct, reproducible source audit
Parse the two pinned JSON files, classify `sites[*].kind`, `sites[*].bodies`, `negatives[*].reason`, and count `criteria` entries with `earth_percentile` instead of a measured, physically matched target `value`.

| Observation | Measured source count |
|---|---:|
| Catalogued sites | 12 |
| Environmental positive sites | 8 |
| Geology-only sites excluded from environmental AUC positives | 4 |
| Negative sites | 8 |
| Negative sites with reason exactly 'dense vegetation or humid climate' | 8 / 8 |
| Moon environmental positives | 3 |
| Mars environmental positives | 5 |
| Published target profiles | 5 |
| Targets using at least one editorial Earth-percentile proxy | 5 / 5 |
| Total `earth_percentile` proxy criteria | 10 |
| Moon-positive/negative AUC comparisons per target (without missing cells) | 3 × 8 = 24 |
| Mars-positive/negative AUC comparisons per target (without missing cells) | 5 × 8 = 40 |

The public `validate()` implementation compares environmental positive sites with these humid/vegetated negatives. Its `roc_auc()` is a pairwise Mann–Whitney statistic. Its `novelty()` is a distance threshold to this twelve-site catalog (150 km 'known', 500 km 'near_known'), **not a literature-wide novelty determination**. Target terrain slope/roughness are commonly editorial Earth-percentile classes because measurement resolutions differ, rather than co-registered LOLA/MOLA and Earth rasters.

## What the audit falsifies
- **REJECTED as an inference:** a reported ROC-AUC of 1.00 on these controls establishes recovery of independent, difficult, geologically meaningful analogue sites. All eight negatives are deliberately humid/vegetated, so the test does not distinguish two barren candidate terrains.
- **SUPPORTED BY PINNED SOURCE INSPECTION:** a public competing prototype already has multi-target scoring, a global Earth screening grid, and an interactive globe. A generic 'score a globe' UI is not a defensible differentiation claim.
- **NOT PROVEN:** competitor's numerical AUC (not rerun), actual model quality, relative challenge ranking, our cross-body similarity, any new analogue discovery, local field-validation advantage, and E001 known-site recovery.

This does **not** accuse the competitor of misrepresentation: its README explicitly describes the limits of its screening benchmark. The audit concerns what our team may responsibly infer from that benchmark.

## Decision consequence
Raise the cloneability penalty of a generic global analog-scoring demo; do **not** yet pivot away from the challenge. The distinguishing experiment remains a source-pinned, instrument-aware, **independently labelled** held-out recovery test that includes *hard negatives* (arid, volcanic, polar or cratered Earth sites that are NOT validated analogues for the chosen mission stress), rather than only rainforest/cropland controls.

## Next decisive experiment, not more scaffolding
1. Download real georeferenced LOLA and MOLA elevation windows plus Earth DEM windows at compatible physical baselines, record datums/projections/missingness.
2. Obtain positive and **same-biome negative** labels from independent planetary analogue literature; keep the label corpus out of feature construction.
3. Run frozen random, single-feature, Euclidean and physically weighted baselines with leave-one-site-out, permutation and feature-ablation checks.
4. Report failures and false positives. Pivot if no robust out-of-sample signal survives.

No physical measurements, external data download, dataset-derived numerical model performance, private access, deployment, outreach, competition submission or main merge occurred in E493.
