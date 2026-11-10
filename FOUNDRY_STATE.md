# FOUNDRY_STATE — NASA

Updated: 2026-11-11
Class: Tier A
Time horizon: NASA Space Apps Challenge, 14–15 Nov 2026
Working branch: `research/e527-mgd3-spatial-ingestion-20261111`
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

1. PAAD 45-site live ingestion is complete (E523); 2018 MGD3 workbook ingestion is complete (E318); the separate 2007 MGD3 spatial layer is documented but not ingested (E525); ingest and join that layer before feature comparison;
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

**Ingest official MGD3 spatial polygons/attributes, verify CRS and Dune ID join to the 2018 workbook, then build a matched Earth/Mars descriptor matrix and run E001 against predeclared controls.**

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

The NASA challenge remains a candidate, not a locked selection. E523 PAAD acquisition is complete. Next decisive step is official MGD3 spatial-layer ingestion, CRS/ID validation, join to the 2018 workbook, then a physically comparable Earth/Mars descriptor matrix and E001 leave-one-site-out evaluation with independent controls. No fabricated measurements, local field data, or site-access claims.


## E524 — PAAD / MGD3 physical-feature admissibility (2026-11-11)

Executed the source-pinned workbook-only audit in experiments/e524_paad_mgd3_feature_admissibility.py using the E523 PAAD normalized CSV SHA-256 0eb40273f9f685e4fd67181c63fa51e24e2fa348cc850cb1641d5e43af221334 and E318 2018 MGD3 ZIP SHA-256 92771c23cfa4a64dfcc38f5ad29de00adfa41b9f321d3665beb2112eefe3485e.

- PAAD: 45 rows, 45 unique site names and coordinate pairs, 13 raw dune-type tokens. Missingness: composition 16/45, approximate area 12/45, sand source 3/45, elevation 1/45; climate descriptions 0/45 missing but are raw source text, not validated Köppen codes.
- MGD3 2018 global-summary worksheet rows are 58, 59, 51 and 53 (not unique-site counts). Thermal inertia and albedo are present in 58, 58, 51 and 51 rows; mineral-field coverage is 42, 52, 37 and 48 rows respectively. The profiled summaries contain no coordinate/footprint fields.
- Nine descriptor families were checked. Zero are directly admissible from the currently ingested PAAD CSV plus the profiled 2018 workbook summaries. Morphology taxonomies differ; PAAD mineralogy is heterogeneous prose while MGD3 is instrument-derived abundance; Earth thermal inertia/albedo are absent; the 2018 summary exposes area rank rather than physical area.
- No independent non-analogue labels exist. No distance metric or E001 ranking is admissible from these two source tables alone.
- Eight local tests passed, including literal-NaN missingness, duplicate-site rejection, source-hash gates, worksheet-row semantics and fail-closed label handling. Exact-head GitHub CI is pending.
- Result: WORKBOOK-ONLY NO DIRECT SHARED DESCRIPTOR ADMITTED. This is not a conclusion about all MGD3 data.

## E525 — MGD3 spatial-layer source discovery (2026-11-11)

The official USGS 2007 MGD3 release documents approximately 550 dune-field polygons, a 37-column attribute table, dune type, area, volume, MOLA-based average elevation, dune orientation and THEMIS infrared imagery at 100 m/pixel. Primary source: https://pubs.usgs.gov/of/2007/1158/. This separate spatial source is DOCUMENTED_NOT_INGESTED; its CRS, geometry, field definitions and Dune ID compatibility with the 2018 workbook have not been verified.

The inventory is not exhaustive: small dune fields and areas without adequate coverage are omitted. Absence is not a negative analogue label. The 100 m/pixel THEMIS support is not automatically the support of MOLA elevation or polygon area. E524 therefore remains a workbook-only audit.

## E526 — 2026 challenge-selection falsification update (2026-11-11)

All 14 official challenge summaries are compared in research/E526_CHALLENGE_RANKING_FALSIFICATION_20261111.md and the scorecard. Earth System Trend Detective retains a source-reconciled 75/75 GISTEMP numerical path (E515). Martian Map retains MOLA ingestion but no validated hyperlocal route-safety model. Field Shift has an ARGUS codebase but no farmer/soil evidence. Planetary analog has the most assembled cross-body source pipeline, but E524 found zero directly admissible descriptors in the currently ingested pair and E001 remains unmeasured; E525 creates a documented spatial-data path but does not execute it.

Challenge-selection superiority remains NOT YET PROVEN. Do not lock the planetary-analog challenge or infer other challenges infeasible from missing audits.

## Updated next decisive experiment

Retrieve the official 2007 MGD3 spatial package through USGS download/ScienceBase/OGC endpoints; verify source hash, CRS, geometry and 37-column schema; join spatial features to the 2018 workbook by Dune ID; report matched/unmatched IDs; then construct the first physically comparable Earth/Mars feature matrix and run E001 leave-one-site-out against random, histogram-only and physically weighted baselines. Preserve nulls and unlabeled controls.

## E528 integration preflight — actual MGD3 Dune ID field (2026-11-11)

A source-to-source integration review of the E527→E528 path found a deterministic header-binding defect before any scientific join was claimed.

- E527's ID-field recognizer explicitly admits the long USGS field name `Dune  Field Lon+Lat ID` (and its regression fixture already exercises that name).
- E527 writes the original DBF field name into `mgd3_2007_dune_fields.csv`.
- E528 previously accepted only normalized headers exactly equal to `Dune_ID` / `DuneID`; its tests used only the canonical alias. Therefore the actual E527 output schema could be rejected by E528 before the 2018 workbook join.
- E528 now uses a fail-closed field resolver aligned with E527's recognized aliases: exact canonical IDs first, otherwise one unique Dune + delimited ID field. Missing or ambiguous candidates are rejected.
- Regression tests now cover the long USGS field plus a nearby non-ID azimuth field, ambiguous Dune-ID candidates, canonical Dune_ID, and missing headers.
- Focused local integration harness: **3/3 tests passed** for actual long-field admission, ambiguity rejection, and canonical/missing-header controls.
- Commits on the isolated E527 branch: source `c9a33d46f84dfcf5db7b90aa96ffffa267ef464a`; tests/head `7fc6a9d76d74d0094ee7ac07e18ba04fe8ad845f`.
- GitHub exact-head Actions status is **not yet verified**. The E527 workflow is push/workflow_dispatch-triggered; the available commit-run reader only exposes PR-triggered runs, and no check/status was returned for the new head.
- The official 2007 archive has **not yet been ingested in this run**, the E528 2018 workbook join has **not yet been executed**, and E529 codebook interpretation remains pending. This is an integration-contract correction, not evidence of matched IDs or physical feature comparability.

Claim states unchanged: cross-body similarity **NOT YET PROVEN**; known-site recovery **NOT YET MEASURED**; novel analogue discovery **NOT YET PROVEN**; challenge-selection superiority **NOT YET PROVEN**.

Next: obtain the exact-head E527-E529 workflow receipt, inspect archive hash/CRS/schema and matched/unmatched Dune IDs, then audit codebook definitions before any physical descriptor crosswalk.


## 2026 challenge-selection falsification screen (2026-11-11)

The full 14-challenge screen is recorded in `research/CHALLENGE_SELECTION_SCREEN_20261111.md`. First-pass weighted readiness screen (data 25%, measurable validation 25%, portfolio reuse 20%, differentiation 15%, 48-hour feasibility 15%) does **not** support planetary analog as the current default. Martian Map ranks first at 4.10/5, MODIS/VIIRS at 4.00, CLPS at 3.85, Earth System Trend Detective at 3.80; planetary analog scores 2.93 because known-site recovery and cross-body descriptors are still unmeasured. These are heuristic readiness scores, not judging predictions.

The best current execution candidate is therefore **Challenge 11: Interplanetary Survival Guide: Martian Map**, provisionally. Existing `stoicsatvik/martian` is preparation-only (not a solution) and records MOLA/CTX/HiRISE source families; the NASA MGD3 spatial ingestion can potentially supply a dune layer. Challenge 10 remains alive only behind the E527 archive/schema/CRS gate and a real E001 leave-one-site-out recovery result. MODIS/VIIRS and CLPS remain live alternatives.

Do not lock or submit. Re-score after official MGD3 ingestion and a reproducible Mars-layer registration test. Keep observed terrain/environment layers separate from crew fatigue, oxygen assumptions and mission rules; RAD/REMS are local rover observations, not global safety forecasts. Challenge-selection superiority remains **NOT YET PROVEN**.


## E527/E528 actual MGD3 acquisition and join (2026-11-11)

Exact-head Actions run [#42922184681](https://github.com/stoicsatvik/NASA/actions/runs/42922184681) on the E527 branch passed **22 parser/provenance tests** and completed the live archive acquisition, 2018 workbook join and prior E529 keyword audit.

- Official 2007 Shapefiles.zip: 60,597,152 bytes; SHA-256 `a43e8f842aa0e9b1edb920a2624a430ebf7fb6a059fc9c6f1ae37cc179635f34`.
- Core layer: **547 POLYGON geometries, 547 nonempty unique Dune_IDs, zero duplicates**. CRS is Mars sinusoidal on the 3,396,190 m MOLA sphere; native coordinates are metres. The polygon bounding box is recorded in the receipt.
- Official 2007 Tables.zip: SHA-256 `9f2e7fe86f813cafcabf34587648e2d6d31a6207046a6d32fb2a98953c8cadb1`. The same-release Softcopy table joined **547/547** unique IDs to the spatial layer using the long field name `Dune  Field Lon+Lat ID`.
- Official 2018 workbook: 2,982,330 bytes; SHA-256 `92771c23cfa4a64dfcc38f5ad29de00adfa41b9f321d3665beb2112eefe3485e`, matching E318 exactly. E528 normalized **1,853** ID-bearing rows across eight worksheets and linked **535 unique Equatorial Dune_IDs** to the 2007 spatial inventory. Four worksheets contain matches. Each Equatorial Global Summary sheet has 58/58 IDs matched; the Stability Index has 535/786 unique IDs matched; the THEMIS ATI/TES modeling sheet has 40/53 rows matched. South Polar sheets have no matches because they lie outside the 2007 layer's equatorial coverage; they are not treated as negative sites.
- The 2007 Dune_ID encoding decodes to longitude and aerocentric latitude at 0.1-degree precision. Those values are identifier-derived and are not independent coordinates or a positional-accuracy measurement.
- The previous E529 audit verified 12 documentation entries and 20 metadata entries, preserving archive hashes. Its bounded keyword excerpts were insufficient for a full codebook crosswalk.

## E529 full field-definition extraction (2026-11-11)

The E529 parser now extracts complete numbered field definitions from `ReadMe_GIS.txt` and `ReadMe_Softcopy.txt`, preserves source-document SHA-256 values, decodes Windows-1252 en-dash separators, and distinguishes unit parentheses from field aliases. All seven E529 unit tests passed in an isolated local harness (including three new parser-focused fixtures); this is not a full repository CI run. The current extractor has **not yet been rerun against the live USGS archives**; the 22-test exact-head workflow above predates this change. See `research/E529_MGD3_FIELD_DEFINITION_EXTRACTION_20261111.md`.

E530 remains a decisive negative admissibility result: strict Dune_Type matches are S/SS; L remains a candidate; B is ambiguous because PAAD combines barchan/barchanoid while MGD3 separates B/Bd. Naively admitting B inflates coverage 1.81× on PAAD and 1.93× on MGD3. No directly shared quantitative physical-feature family is admitted. E001 remains NOT READY; no analogue recovery or cross-body similarity is claimed.

## Current frontier after E531 (2026-11-11)

- E531 keeps Martian Map and MODIS/VIIRS in a provisional top tier. Martian Map is the most frequent top choice in the tested perturbation families (83.97%, 65.40%, 54.34%), but its 5th-percentile score margin over MODIS/VIIRS is negative even at ±0.25. These are heuristic scorecard perturbations, not judging probabilities. Do not lock the challenge.
- The 2007 MGD3 dune layer is now available as source-backed Mars context. It does **not** validate a route-safety model or a cross-body analogue model.
- Highest-value next actions: (1) run the updated E529 full-field extractor on the official archives and inspect the exact Dune_Type, area, average-elevation and mean-height definitions; (2) only then update E530's conservative crosswalk if a source-backed equivalence exists; (3) test CRS/extent/coverage registration of MGD3 against the existing MOLA/CTX/HiRISE layers in `stoicsatvik/martian`. Keep observed terrain layers separate from crew fatigue, oxygen assumptions and mission rules.

Claim states remain: cross-body similarity **NOT YET PROVEN**; known-site recovery **NOT YET MEASURED**; novel analogue discovery **NOT YET PROVEN**; route safety **NOT VALIDATED**; challenge-selection superiority **NOT YET PROVEN**.


## E529 CI syntax correction — 2026-11-11

The latest E527/E528/E529 workflow failure [#42923772054](https://github.com/stoicsatvik/NASA/actions/runs/42923772054) was a Python syntax error in E529 ZIP path normalization, before any live acquisition step. Corrected the escaped backslash in commit [ed7db2b](https://github.com/stoicsatvik/NASA/commit/ed7db2b7163fc5474a3a598d6dc89b3127bacaad). The exact current E529 module/test files passed **7/7** unit tests in an isolated Python harness and imported successfully. This does not substitute for exact-head Actions or live archive extraction; the corrected commit has no returned combined status. Prior E527/E528 live acquisition evidence from run #42922184681 remains valid for its earlier code head (547/547 spatial IDs, 547/547 same-release table join, 535 unique Equatorial 2018 IDs). Re-run the full workflow on the corrected head before accepting the new E529 field-definition extraction as live-source validated. No taxonomy or E001 claim changes.
