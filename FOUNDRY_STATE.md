# FOUNDRY_STATE — NASA

Updated: 2026-11-10
Class: Tier A
Time horizon: NASA Space Apps Challenge, 14–15 Nov 2026
Working branch: `foundry/planetary-analog-v1`
Main objective: maximize uncertainty eliminated per run and converge on a scientifically defensible Space Apps entry.

## Current thesis

The leading candidate is the 2026 planetary-analog challenge: identify Earth environments analogous to Moon/Mars locations using open Earth + planetary datasets.

This is **NOT YET PROVEN** to be the best challenge.

## Claim state

- Repo operating system: SUPPORTED
- India/Maharashtra analogue literature leads: SUPPORTED as research leads, not as new discoveries
- Cross-body similarity model: NOT YET PROVEN
- Recovery of known analogue sites: NOT YET MEASURED
- Novel analogue discovery: NOT YET PROVEN
- Local field-validation advantage: NOT YET PROVEN
- Space Apps challenge-selection superiority: NOT YET PROVEN

## Highest-value frontier

Run `E001_KNOWN_ANALOG_RECOVERY` and the dataset-access spike before polishing UI.

Priority order:

1. verify remaining real lunar and Martian data ingestion and feature comparability; PAAD Earth and MGD3 Mars dune sources were already ingested in E317-E318;
2. derive a small set of physically comparable descriptors;
3. reproduce/recover known analogue environments using transparent baselines;
4. perform ablations and uncertainty analysis;
5. try to falsify the current challenge ranking;
6. only then build the polished geospatial product.

## Evidence gate

No claim that the system can identify useful Moon/Mars analogues until:

- at least one real lunar and one real Martian dataset are ingested;
- at least one known Earth analogue is held out and ranked independently;
- a random/simple baseline is beaten;
- ranking stability is measured;
- feature ablations are reported;
- instrument/resolution mismatch is documented.

## Proprietary-evidence strategy

Potential moat:

```
public NASA/partner data
→ physically justified comparison
→ prediction
→ permitted/non-destructive local observation
→ prediction error
→ proprietary validation corpus
→ improved model
```

A field trip does not count as progress unless a measurement maps directly to a model feature or validation question.

## Highest-value missing capability

Recruit one teammate with real planetary geology / Earth science / remote sensing / GIS evidence.

Do not optimize for prestige, follower count, or "AI" labels.

## Active issues

- #1 map every 2026 challenge and attempt to falsify current ranking
- #2 run E001 known-analogue recovery
- #3 dataset-access spike
- #4 Maharashtra field-validation feasibility
- #5 recruit planetary science / remote-sensing teammate

## Hourly Foundry contract

When this stream is selected by the Unified Parallel Foundry:

1. inspect exact current branch/PR/issue state;
2. choose the single action with highest expected uncertainty reduction;
3. prefer experiments/data access/validation over presentation;
4. preserve negative/null results;
5. do not manufacture commits if no evidence changes;
6. keep raw large datasets out of Git unless justified;
7. do not merge to `main` autonomously;
8. update this state only when durable evidence or frontier changes.

## Stop / pivot conditions

Pivot away from the planetary-analog track if any of these becomes clear:

- required datasets cannot be accessed or meaningfully compared;
- known analogue recovery fails after reasonable physically motivated revisions;
- another 2026 challenge clearly dominates the scorecard;
- required domain expertise cannot be recruited and scientific validity remains weak;
- the only differentiator becomes UI/LLM orchestration.

## Next trigger

**Independent semantic crosswalk + non-analogue controls + E001 known-site recovery.**

PAAD and MGD3 ingestion are already in E317-E318. The next substantive run must resolve label comparability and negative controls, not repeat data acquisition or add another planning document.


## E514 real matched-footprint falsification (2026-11-03)

- Draft research PR #68 on `research/e514-equal-physical-footprint-20261103`,
  stacked on E513 PR #67. Main unchanged.
- Official NASA PDS MOLA and NOAA ETOPO2022 downloads re-acquired and source
  hashes preserved; six exact-head synthetic tests passed in Actions
  https://github.com/stoicsatvik/NASA/actions/runs/41529678394.
- Nominal MOLA-cell physical support used to area-average real Earth DEM.
  Relative to E513 raw 5x5 pixel ranking, **3/5 nearest unverified Earth
  candidates changed**.
- **4/5 nearest candidates retained under all 500 spatial permutations**
  of each frozen MOLA target, indicating that this descriptor ranking often
  lacks discriminating spatial morphology. Five frozen targets are not
  independent analogue labels.
- Source-backed receipt and complete negative results:
  `research/E514_EQUAL_FOOTPRINT_REAL_RESULT_20261103.md`.
- **Claim:** equal-physical-support descriptive experiment SUPPORTED;
  morphology-sensitive analogue recovery NOT YET PROVEN; E001 known-site
  recovery NOT YET MEASURED; cross-body similarity, novel discovery and
  challenge superiority NOT YET PROVEN.
- **Highest-EV next:** independently labelled known analogue/non-analogue
  Earth sites and georegistered planetary references, then frozen random,
  histogram-only, physically weighted and leave-one-site-out E001 baselines.
  Do not repeat unlabelled candidate ranking as a substitute for recovery.


## E515 2026 challenge-selection rival falsification (2026-11-03)

- Isolated branch `research/e515-gistemp-block-null-challenge-audit-20261103` stacked on E514, main unchanged.
- NASA GISS GISTEMP v4 2001–2025 annual zonal snapshot: 25 years × 3 selected variables independently reconciled against the official NASA text on 2026-11-03, **75/75 numeric cells matched**. The live server response was not cryptographically archived; revisions remain possible.
- Exact integer OLS trends: global **+0.258769 °C/decade**, Arctic-minus-tropics **+0.484769 °C/decade**. Exact five-year-block permutation diagnostics: **1/120** and **6/120** absolute extremes, respectively; circular-shift diagnostic **1/25** each. These are **not calibrated p-values** because block exchangeability/stationarity is not established.
- Seven local deterministic controls passed on exact committed Git blobs, including recomputation of the committed JSON result; CI status tracked separately.
- All 14 official 2026 challenge summaries were screened for *current repo evidence readiness*, with unassessed challenges explicitly marked unknown rather than ranked inferior.
- **SUPPORTED:** an alternate challenge (Earth System Trend Detective) has a real-source-verified numerical analysis path. **NOT YET PROVEN:** any overall challenge ranking or complete Earth Trend solution.
- **E001 known-site recovery NOT YET MEASURED; cross-body similarity, analogue discovery and local validation advantage NOT YET PROVEN.**
- Evidence and limitations: `research/E515_CHALLENGE_SELECTION_GISTEMP_BLOCK_NULL_20261103.md`.
- Highest-EV next: independent analogue/non-analogue labels and leave-one-site-out E001, or a genuine hyperlocal Martian Map / regional Earth Trend acceptance gate before committing the final competition sprint.


## E001 spatial-scale falsification update (2026-11-10)

PR #83, head d8362fd43e35983f5669ba94a6a91d42742c89f3 on research/e001-spatial-scale-sensitivity-20261108, is an isolated synthetic diagnostic stacked on #82. It executes a deterministic 20-geometry sweep using the production E001 evaluator and exact-label null. The separated-pair fixture yields top-1=1, unrestricted p=3/70 and block-preserving p=3/6; at within-pair offset greater than block spacing, top-1 collapses to 0 and both p-values become 1.0. No block-preserving null in the specified grid reaches p<0.05. GitHub Actions run #42837210829 passed on that exact head. This is synthetic geometry sensitivity, not empirical analogue recovery.

## E522 — NASA Analog Explorer catalogue admissibility (2026-11-10)

The official NASA Analog Explorer gallery was transcribed into data/nasa_analog_explorer_pairs.csv with per-row source URL and access date. The inventory contains 11 pairs: 9 Moon/Mars pairs (6 Mars, 3 Moon) and 2 out-of-scope pairs (Venus, Enceladus). The deterministic admission script finds 9 singleton mechanism families. Grouping by target body meets a raw count minimum but mixes distinct physical mechanisms; grouping by mechanism leaves no reference centroid. The gallery supplies no numeric feature matrix, site coordinates/footprints, or negative controls, so it is not E001-ready. Four regression tests pass locally.

Prior PAAD ingestion and analysis are present in separate E317-E325 draft PR branches (PRs #27-#32), but those PRs remain unmerged; do not repeat the download. E317's first synthetic fixture failed (0 rows versus 4 expected), but E318 later ingested the official 2018 Mars MGD3 ZIP (2,982,330 bytes; SHA-256 92771c23cfa4a64dfcc38f5ad29de00adfa41b9f321d3665beb2112eefe3485e) and E319 source-fingerprinted the 45-site PAAD CSV (SHA-256 5be67b4da584987d9ce5207f2ee3c90b5b3b5849469461847111eaab5aafcecd). E319 found 21 single-token and 24 multi-token rows; only 8/45 had all raw tokens in the Mars 2007 codebook, 21/45 had partial overlap, and 16/45 had none. Direct code joining was rejected. E320's first CI attempt failed because pytest was absent; after adding the test dependency, 21 tests passed. E320 found 990 coordinate pairs, nearest pair 6.824912 km, and spatial groups covering 9/45 sites at 25/50 km and 16/45 at 100 km. E323 found raw-token nearest-site Jaccard 0.350053; 25/50 km blocking did not reduce it, while 100 km blocking reduced it to 0.235238. E325's first parser falsely treated free-text desert as Köppen D; the strict parser correction left 45/45 UNCLASSIFIED because source climate labels are English descriptions, not alphanumeric codes. Analyst climate groups are not independent source labels. E326's first ScienceBase request returned HTTP 403; a later retry recovered four volcanic rows and no dune positives or negatives. These are Earth-only lexical/spatial results, not matched Earth-Mars labels or E001 recovery. A separate 16-site public GitHub catalogue has all 16 records marked Draft and is not accepted as ground truth.

Exact claim states:
- Repo operating system: SUPPORTED.
- NASA gallery as qualitative curated analog source: SUPPORTED.
- Gallery alone as E001 numeric feature/label matrix: REJECTED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Local validation advantage: NOT YET PROVEN.
- Planetary-analog challenge superiority over every official 2026 challenge: NOT YET PROVEN.

The NASA challenge remains a candidate, not a locked selection. Next decisive step is actual PAAD data acquisition, metadata/hash verification, and a predeclared aeolian-specific E001 campaign with independent Mars reference data and negative controls. No fabricated measurements, local field data, or site-access claims.
