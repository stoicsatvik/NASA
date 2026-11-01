# E480 | Exact margin-conditioned observation-mask falsification (2026-11-01)

## Question

E476 reported vertical-minus-horizontal observed adjacency excesses at three nonrandom Martian sites, with fixed-count shuffle tails of approximately 0.0023, 0.0145, and 0.0048. E478 showed that zero complete five-point slope stencils at 40°S is common under an *unstructured* fixed-count null (61.0571%). Does the apparent directional excess survive a stricter null preserving measured row and column occupancies?

## Pinned real-source inputs and exact test

Reused archived E472 Actions artifact #13075465278, file e472_mars_source.json, SHA-256 2e70d84ca45cc4730c87e8931194c5ba1cd7a31bdd15e9a7883c5611578c9dfb, derived from official PDS MOLA 128ppd observation-count ranges. No new instrument measurements were acquired. Center 5x5 masks at 45°E, 0.5°S, 20°S, and 40°S were parsed without interpolating missing bins. Define D = vertical observed neighbor pairs minus horizontal observed neighbor pairs. Exhaustively enumerate all binary 5x5 matrices preserving (a) row counts, (b) column counts, and (c) both sets of margins. Each feasible matrix receives equal weight within its stated null. Report exact *one-sided* P(D >= observed D) and the fraction with zero complete centered five-point stencils. These are conditional structural controls, not physical models of MOLA sampling or inferential population p-values.

| Mars site | Observed bins | D (V−H) | Row-fixed P(D≥obs) | Column-fixed P(D≥obs) | Both-fixed P(D≥obs) | Both-fixed feasible masks |
|---|---:|---:|---:|---:|---:|---:|
| 0.5°S | 11/25 | +6 | 316/100000 = 0.00316 | 5/5 = 1 | 1/1 = 1 | 1 |
| 20°S | 3/25 | +2 | 5/125 = 0.04 | 3/10 = 0.30 | 1/1 = 1 | 1 |
| 40°S | 15/25 | +6 | 489/50000 = 0.00978 | 4/500 = 0.008 | 2/12 = 0.16667 | 12 |

**Critical structural counterexample:** the 40°S central 5x5 observed-count mask has column totals **[3, 3, 0, 5, 4]**. Every possible centered five-point stencil necessarily touches the entirely unobserved middle column. Thus **all 500/500 column-margin-preserving masks and all 12/12 both-margin-preserving masks have zero usable stencils**, even though E478's unconditional fixed-count null puts only 61.0571% probability on zero stencils. At 0.5°S the column margins [0, 5, 1, 5, 0] also force zero complete stencils; at 20°S only three observed bins exist, below the five-bin minimum.

The E476 fixed-count anisotropy result remains valid for its *different null*. What fails is treating its small unstructured-shuffle tail as evidence of unexplained directional arrangement after accounting for both row and column occupancies. The 40°S both-margin conditional one-sided tail is **2/12**, not unusually small. The other two both-margin cohorts each contain exactly one feasible mask, making residual-arrangement inference impossible rather than providing positive evidence of a sampling mechanism.

## Validation

Five local pytest tests passed against the pinned archived source, including source-tamper rejection, malformed masks, empty/full controls, all three exact conditional nulls, and an independent brute-force both-margin oracle (12 feasible 40°S masks, 2 extreme). Python compilation passed. Numerical receipt: research/results/e480_margin_conditioned_mask_null_20261101.json, with exact integer counts. **No E480-specific GitHub Actions CI was run**, due prior warnings of exhausted included Actions minutes; no paid capacity was enabled. The source ZIP remains outside Git; no large or raw data was committed.

## Claims and next move

- **SUPPORTED** for three selected real-source windows: conditioning on observed row/column margins changes the interpretation of anisotropy and explains impossibility of complete measured-only five-point stencils under the stated conditional nulls.
- **NOT YET PROVEN:** physical instrument-track causation, globally representative geometry, independent effective resolution, physically comparable terrain descriptors, Earth/Moon/Mars analogue similarity, or 2026 challenge superiority.
- **NOT YET MEASURED:** E001 known-site recovery. No novel analogue or local-validation advantage established.
- **Next:** stop further count-mask-only null refinement unless it changes descriptor eligibility. Obtain count-positive directional *elevation pairs* with physical lags, elevation datum, instrument uncertainties and independence gates, then source independently labelled analogue positives/negatives and run frozen E001 random/Euclidean/physically weighted baselines with leave-one-site-out evaluation. Preserve failure/pivot evidence. Do not polish geospatial UI before evidence gate.

Reproduce: python research/e480_margin_conditioned_mask_null.py /path/e472_mars_source.json ; E480_MARS_SOURCE=/path/e472_mars_source.json python -m pytest -q research/test_e480_margin_conditioned_mask_null.py.
