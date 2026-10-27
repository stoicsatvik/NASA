# E320: Real PAAD spatial proximity and holdout leakage audit (27 Oct 2026)

## Falsifiable question

Do independently named dune sites in the USGS Planetary Aeolian Analog Database (PAAD) occur close enough that a naive leave-one-site-out split could place nearby sites on opposite sides of a train/test boundary?

**Predeclared thresholds:** 25, 50 and 100 km. Use the 45 unique site names and coordinate pairs from the same SHA-256-pinned E317/E319 USGS CSV, all 990 unordered site pairs, a spherical Haversine distance (Earth radius 6371.0088 km), and connected components at each threshold. No class label is inferred from geography. The source provides only positive Earth dune analog sites, not independent Earth–Mars matches or negatives.

## Exact-head real-source measurement

[GitHub Actions run #40450592233](https://github.com/stoicsatvik/NASA/actions/runs/40450592233) **SUCCESS** on commit `8de8b0c5d8141f933e72b6489bcf5da0a6d66c4d`: 21 synthetic tests passed (seven new E320 controls plus seven E319 and seven E317 inherited controls), source download and SHA check passed, 45 sites and 990 pairs checked. Original CSV SHA-256 `5be67b4da584987d9ce5207f2ee3c90b5b3b5849469461847111eaab5aafcecd`. Raw CSV not committed; complete per-group JSON retained as CI artifact.

| Proximity threshold | Pairs within threshold | Connected groups | Multi-site groups | Sites in multi-site groups | Largest group |
|---|---:|---:|---:|---:|---:|
| 25 km | 10 | 39 | 3 | **9/45** | 5 |
| 50 km | 12 | 39 | 3 | **9/45** | 5 |
| 100 km | 19 | 34 | 5 | **16/45** | 6 |

Nearest two named sites: **6.824912 km** by the spherical model. At 25 km, the multi-site components include a five-site Campo Piedra Pomez/Purulla/Incahuasi/White Barchan group, a two-site Dumont/Ibex group, and a two-site Victoria/Wright Valley group. A connected component may link sites through intermediate neighbours even when endpoints are farther apart than the threshold.

## Interpretation and uncertainty eliminated

**SUPPORTED:** The *source-reported coordinates* place several separately named PAAD sites within the tested geographic distances. Therefore site-name-only leave-one-out is **not guaranteed to be spatially independent**. Spatial grouping is an available split safeguard, not a proof that sites share geology, labels, instruments, provenance or physical descriptors.

**NOT ESTABLISHED:** Coordinate geodetic accuracy, whether these nearby records refer to the same physical dune field, whether their geological measurements share sources, whether grouping actually changes a future model's held-out performance, or any Earth–Mars analogue recovery.

The 45 rows remain **positive-only**; no unknown site may be relabelled as a negative. The Earth/Mars morphology codebook mismatch from E319 remains unresolved. No E001 ranking or model was trained. Cross-body similarity and novel analogue discovery remain **NOT YET PROVEN**; E001 known-site recovery **NOT YET MEASURED**.

## Next decisive experiment

After independent label and descriptor harmonization, compare **site-name-only leave-one-out** versus **25/50/100 km spatial-group leave-one-group-out** on identical frozen physical features and independently verified positives/negatives. Test distance sensitivity and source overlap. If spatial blocking collapses apparent performance, preserve the negative result and reject the leaky baseline. Until labels are legitimate, do not invent a recovery benchmark.

No competition solution, submission, field sampling, deployment, outreach or main merge.
