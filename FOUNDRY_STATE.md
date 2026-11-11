# FOUNDRY_STATE — NASA

Updated: 2026-11-11
Class: Tier A
Time horizon: NASA Space Apps Challenge, 14–15 Nov 2026
Working branch: `research/e533-candidate-label-source-review-20261111`
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

Evidence before UI. E001 is not ready until independent Earth positive sites, defensible non-analogue controls and physically comparable features exist.

Priority order:

1. E527 acquired the official 2007 MGD3 spatial package (547 polygons/IDs); E528 linked 535/547 unique IDs to the 2018 workbook. E530 then found no directly admissible shared quantitative physical-feature family in the current PAAD/MGD3 pair.
2. Preserve the E530 negative result: PAAD has 45 known-analogue records but no target-body/family labels or non-analogue controls; strict Dune_Type overlap is S/SS, L is a candidate and B is ambiguous. Do not treat a codebook ID join as physical comparability.
3. Seek independent legitimate Earth positive-site data and defensible non-analogue controls; derive only features with compatible physical meaning, support and uncertainty. Run E001 only after those inputs exist.
4. Keep the all-14 challenge screen open. E531 found Martian Map remains the most frequent top score under tested perturbations, but its margin over MODIS/VIIRS is not robust to moderate subjective score uncertainty.
5. Martian Map is a serious alternative with MOLA/CTX/HiRISE preparation and a verified MGD3 context layer, but route-safety validation is absent. Respect the preparation-only boundary in the `martian` repo; no competition solution code before the official event window.
6. Perform ablations and uncertainty analysis before any geospatial UX polish.

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

**Acquire an independent, source-backed Earth positive-site layer and a defensible non-analogue control population; then test whether any physically comparable descriptor survives support/uncertainty audits before attempting E001.**

E527/E528 spatial acquisition and ID joining are complete. E530 found no directly admissible shared quantitative features in the current PAAD/MGD3 pair. The next run must address independent labels/controls or falsify another feature family, not repeat ingestion or polish UI.


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


## E527-E529 exact-head acquisition and linkage correction (2026-11-11)

The earlier E525/E528 preflight statements are superseded by the exact-head acquisition evidence below.

- E527 workflow run #42904750899 succeeded on exact head 03300510d932128df58f64dc91bf04bd0825617f. The official 2007 MGD3 Shapefiles.zip and Tables.zip were acquired with source hashes preserved. The core Dune_Field layer has 547 polygons and 547 unique Dune_IDs in a Mars sinusoidal CRS. The same-release Softcopy table joins 547/547 IDs with no duplicates.
- E528 parsed the official 2018 Equatorial and South Polar workbooks. The Equatorial workbook contains 956 worksheet rows; 535 unique 2007 IDs match and 12 of the 547 spatial IDs are absent from the 2018 workbook. This is record linkage only, not physical similarity.
- The official 2018 report restricts detailed thermal/compositional analysis to dune fields >=300 km2. The 58 Global Summary IDs are therefore a selected large-field subset, not a representative sample of all 547 MGD3 spatial fields.
- The 2018 Equatorial Global Summary sheets each contain 58 unique IDs, all matched to 2007; thermal inertia and albedo are present for 58/58. Mineral fields are present for 42/58 in the "ocks <7000" sheet and 52/58 in the "all ocks" sheet. Stability Index has 787 rows, 786 unique IDs, one duplicate and 535 matched rows. THEMIS ATI/TES modeling has 53 rows and 40 matched rows.
- The South Polar workbook is outside the 2007 spatial layer's 65°S–65°N coverage; its unmatched rows are not treated as failed equatorial joins.
- E529 inspected the official 2007 documentation and metadata archives. No crosswalk was accepted automatically from token overlap.

Source artifacts: PAAD workflow #42902970540 / artifact 13804420438; MGD3 E527-E529 workflow #42904750899 / artifact 13804087352. Source archive SHA-256 values and exact URLs are preserved in the E530 report and JSON.

## E530 — PAAD / MGD3 cross-body feature admissibility (2026-11-11)

E530 used the actual PAAD, 2007 MGD3 and 2018 MGD3 artifact tables. The reproducible script and result are in experiments/e530_crossbody_feature_admissibility.py and research/E530_CROSSBODY_FEATURE_ADMISSIBILITY_20261111.md.

- PAAD has 45 unique analog-site records, but no per-site target-body/family labels and no non-analogue controls. Missingness: composition 16/45, approximate area 12/45, sand source 3/45, elevation 1/45.
- Strict Dune_Type matches are S (star) and SS (sand sheet). L (longitudinal vs linear) remains a candidate. B is rejected as ambiguous because PAAD combines barchan and barchanoid ridges while MGD3 separates B and Bd. TR (transverse ridge) is not equated with T (transverse dune).
- Strict S/SS coverage is 16/45 PAAD sites and 132/547 Mars fields. Adding candidate L gives 20/45 and 152/547. Naively including ambiguous B inflates apparent coverage to 29/45 and 255/547 (1.81× and 1.93× the strict coverage).
- No directly shared quantitative feature family is admitted. Elevation and area require within-body normalization / support sensitivity; PAAD composition prose is not equivalent to MGD3 instrument-derived mineral abundances; Earth climate/sand-source fields have no MGD3 counterpart; Mars thermal inertia/albedo/mineral/stability fields are absent from PAAD.
- E001 is NOT READY on these tables. Do not invent target-body labels, use unlisted sites as negatives, or run a ranking with fabricated controls.
- Six local tests passed on an equivalent local harness. The committed branch test module was not executed on this runtime, and no E530 exact-head Actions run was triggered; E527 exact-head acquisition and the source artifacts are validated separately.

Claim states remain: repo operating system SUPPORTED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge-selection superiority NOT YET PROVEN.

Next: ingest the separate public USGS 2020 Known Terrestrial Analog Sites point layer as a candidate positive source (not a negative-control set), then acquire defensible non-analogue controls and Earthdata-derived Earth descriptors at matched physical support. Preserve all unlabelled sites as UNLABELLED. Do not lock the planetary-analog challenge; the current Martian Map lead remains provisional pending the next evidence gate.


## E527–E530 — MGD3 spatial acquisition, join and cross-body feature-admissibility falsification (2026-11-11)

- E527 acquired the official USGS 2007 MGD3 spatial package. The archive contains **547 dune-field polygons/IDs**. E528 linked **535/547 unique IDs** to the 2018 MGD3 Equatorial workbook. E527 exact-head Actions run [#42904750899](https://github.com/stoicsatvik/NASA/actions/runs/42904750899) passed on commit `03300510d932128df58f64dc91bf04bd0825617f`.
- E530 evaluated the actual PAAD/MGD3 artifacts. PAAD has 45 known-analogue records but no target-body/family labels and no non-analogue control population. No directly admissible shared quantitative physical-feature family exists in the current PAAD/2018-workbook pair.
- Strict Dune_Type overlap is S/SS; L remains a candidate and B is ambiguous. Naively admitting B inflates apparent coverage 1.81x on PAAD and 1.93x on MGD3. Do not convert ambiguous codebook overlap into physical similarity.
- E530 exact workflow run [#42911904361](https://github.com/stoicsatvik/NASA/actions/runs/42911904361) passed on commit `1b6e44b0fba6aaae6ba0c0a2fcf7053c99881206`; six local tests also passed on the equivalent harness. The later current PR #89 head includes documentation/state updates; no new scientific claim is implied by those updates.
- E001 known-site recovery remains **NOT YET MEASURED**, not BLOCKED. Independent Earth positive sites, defensible non-analogue controls and physically comparable descriptors remain viable computational avenues.

## E531 — all-14 challenge score sensitivity (2026-11-11)

A deterministic 200,000-draw Monte Carlo sensitivity experiment was run for each score perturbation amplitude +/-0.25, +/-0.50 and +/-0.75. Five base weights were independently perturbed by multiplicative uniform [0.8,1.2] factors and renormalized; each of the 14x5 subjective scores was independently perturbed and clipped to [1,5]. Seed 526 is frozen.

- At +/-0.25, Martian Map is top in 83.97% of perturbation draws and MODIS/VIIRS in 15.88%.
- At +/-0.50, Martian Map is top in 65.40%, MODIS/VIIRS in 27.46%, CLPS in 4.75% and Earth Trend in 2.38%.
- At +/-0.75, Martian Map is top in 54.34%, MODIS/VIIRS in 28.55%, CLPS in 10.48% and Earth Trend in 6.32%.
- The 5th percentile of the Martian Map minus MODIS/VIIRS score gap is negative even at +/-0.25 and becomes more negative as score uncertainty grows.

This is a **heuristic scorecard robustness diagnostic**, not a probability of judging success. Martian Map remains the most frequent top option in these scenarios, but challenge-selection superiority remains **NOT YET PROVEN**. Keep Martian Map and MODIS/VIIRS as a provisional top tier.

Reproducible source: `experiments/e531_challenge_selection_sensitivity.py`; result: `research/results/E531_CHALLENGE_SELECTION_SENSITIVITY_20261111.json`; report: `research/E531_CHALLENGE_SELECTION_SENSITIVITY_20261111.md`.

## Current claim-state restatement (2026-11-11)

- Repo operating system: **SUPPORTED**
- Cross-body similarity: **NOT YET PROVEN**
- Known-site recovery: **NOT YET MEASURED**
- Novel analogue discovery: **NOT YET PROVEN**
- Local validation advantage: **NOT YET PROVEN**
- Space Apps challenge-selection superiority: **NOT YET PROVEN**



## E532 — independent public analogue-catalogue audit (2026-11-11)

- Audited the pinned public `rachellelecussan/planetary-analogue-catalogue` GeoJSON at source commit `62e6339bdf308de3bc987388d0faa7130cf57de9`. The source README declares `data/` CC BY 4.0; no raw data or photos were copied.
- The 16-point catalogue has primary labels Mars 10, Moon 2, Early Earth 2, Enceladus 1 and Europa 1. All 16 records are marked `Draft`; none is `Verified`.
- Its 96 references include 33 marked peer-reviewed, 63 not marked peer-reviewed, 33 unique DOI-bearing references and one reference marked unverified. It lists 42 photos with individual licences.
- Seven sites are flagged sensitive. Coordinate precision is approximately 10 km for 10 sites, approximately 1 km for 2, and region-only for 4.
- Numeric descriptors are incomplete (for example extent 8/16, pH 4/16, altitude minimum 3/16, maximum 7/16). The catalogue has no explicit non-analogue control population.
- **Result:** supported as a candidate-positive discovery index and literature-navigation aid; **rejected for current use as E001 ground truth**. No E001 ranking was run. The 12 Mars/Moon primary candidates require source-by-source review; Draft status and missing controls prevent a recovery claim.
- Exact-head PR Actions run [#42924295331](https://github.com/stoicsatvik/NASA/actions/runs/42924295331) passed all 4 tests and fetched the pinned source; SHA-256 `09ad7d62eefd40c86acaee945fb2d1f045b199c958830ba8715e7774311afb0d`.
- Reproducible audit: `experiments/e532_public_catalogue_audit.py`; fixture tests: `experiments/test_e532_public_catalogue_audit.py`; CI receipt artifact: `e532-public-analogue-catalogue-audit`. The script pins the source commit, enforces URL/size limits, computes SHA-256, and does not store the external dataset.
- Claim states unchanged: cross-body similarity **NOT YET PROVEN**; known-site recovery **NOT YET MEASURED**; novel analogue discovery **NOT YET PROVEN**; challenge-selection superiority **NOT YET PROVEN**.
- Next: acquire the separate official USGS 2020 Known Terrestrial Analog Sites point layer (DOI `10.5066/P9J72921`) as candidate positives; independently review a predeclared subset and obtain defensible non-analogue controls plus matched physical descriptors. Absence from a positive catalogue is not a negative label.


## E532 coordinate-type validation hardening — 2026-11-11

Code review found that Python's `bool` subclasses `int`, so a malformed GeoJSON point such as `[true, 20.0]` could pass the previous numeric-coordinate predicate. The E532 audit now explicitly excludes booleans and adds a regression fixture. This does not change the pinned external dataset or its candidate-only status. The original live-source receipt #42924295331 remains valid for its earlier code head; the new predicate has focused local validation, while exact-head live-source rerun remains pending.


## E533 — source audit of six Mars/Moon candidate labels (2026-11-11)

- New isolated branch `research/e533-candidate-label-source-review-20261111`, stacked on E532 PR #91; no main changes.
- Reconciled the stale E532 next action: USGS 2020 Known Terrestrial Analog Sites (DOI `10.5066/P9J72921`) was already acquired by E326 in PR #33 on 2026-10-27. It yielded four public features, all volcanic, with `AnalogBody` missing/null-like in all four. It is not a dune or Moon/Mars control cohort; do not re-ingest.
- Predeclared a purposeful six-record subset from the pinned 16-site catalogue: Atacama Yungay, Río Tinto, Holuhraun, Lava Beds, Mauna Kea and Haughton. Four are Mars-primary and two Moon-primary.
- Reviewed the cited primary sources and a directly relevant additional source where recorded. All six support the **narrow candidate-label claim** for their stated feature scope. The support types differ: hyperarid soil/habitability; acidic geochemistry; fissure-fed lava morphology; lunar lava-tube prospecting; lunar instrument/ISRU field testing; and impact/Mars remote-sensing research.
- All six source-catalogue records remain `Draft`. The other six Mars/Moon primary candidates remain unaudited. This is a purposeful evidence-availability subset, not a random sample or independent expert verification.
- No coordinates were geocoded, no sensitive locations were exposed, no non-analogue controls were created, and no E001 ranking or leave-one-site-out recovery was run.
- Reproducible crosswalk: `research/E533_CANDIDATE_LABEL_SOURCE_REVIEW_20261111.csv`; pinned-source verifier: `experiments/e533_candidate_label_source_review.py`; fixtures: `experiments/test_e533_candidate_label_source_review.py`; receipt artifact: `e533-candidate-label-source-review`.
- Candidate-label support for these six narrow claims: **SUPPORTED**. Catalogue-wide E001 ground truth: **NOT READY**. Cross-body similarity: **NOT YET PROVEN**. Known-site recovery: **NOT YET MEASURED**. Novel analogue discovery: **NOT YET PROVEN**. Challenge-selection superiority: **NOT YET PROVEN**.
- Next: audit the remaining six Mars/Moon candidate records with the same source-to-feature criteria; then acquire defensible controls and matched-support physical descriptors. Absence from a positive catalogue remains UNLABELLED, never negative.
