# FOUNDRY_STATE — NASA

Updated: 2026-11-12
Class: Tier A
Time horizon: NASA Space Apps Challenge, 14–15 Nov 2026
Working branch: `research/e582-ctx-slope-error-envelope-20261112`
Main objective: maximize uncertainty eliminated per run and converge on a scientifically defensible Space Apps entry.

## Current thesis

The planetary-analog challenge remains the current scientific research thesis under test, but it is not the current readiness leader and is NOT YET PROVEN to be the best challenge. The all-14 screen currently places #11 Martian Map (4.10) and #9 MODIS/VIIRS (4.00) in a provisional top tier; #10 planetary analog remains 2.93. The 0.10 gap and factor-ablation reversal are below the predeclared meaningful threshold. No challenge is locked.

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
4. Keep the all-14 challenge screen open. E541's all-14 screen places Martian Map (4.10) and MODIS/VIIRS (4.00) ahead of planetary analog (2.93) on the current rubric; ranking margins remain sensitive to subjective weights, so no challenge is locked.
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

**E560 has now completed the bounded official USGS ScienceBase metadata audit (11 Nov 2026).** Exact-head Actions run #43068609889 passed 13/13 deterministic tests and acquired the pinned metadata anonymously. The item JSON returned HTTP 200 (19,203 bytes); the only file was the 9,406-byte FGDC XML. The live receipt reports a catalogue MD5 mismatch, zero vector links, and no feature payload. The XML itself says the 192 points are for discovery/reference rather than analysis and may be displaced by up to 10 km from feature centroids. Its 0.6096 m coordinate-resolution field is not positional accuracy. Do not pursue this item/WFS as an E001 analytical label source. Preserve the checksum discrepancy and do not claim 192 acquired features.

The planetary-analog challenge remains **NOT YET PROVEN** as the best challenge. The all-14 screen and E541 factor ablation still put Martian Map (#11, 4.10) and MODIS/VIIRS (#9, 4.00) in a provisional top tier; the 0.10 gap is below the predeclared 0.25 threshold, and MODIS/VIIRS wins when portfolio reuse is removed. Planetary analog (#10, 2.93) remains a conditional research challenger, not the current readiness leader. No challenge is locked.

Next highest-information work: test actual CRS registration and spatial coverage for the Martian Map layers on one pinned Mars area, and independently verify a no-credential public MODIS/VIIRS data path with a measurable validation target. Reassess the 14-challenge screen only when those results change a scored factor. Keep analog work focused on independent positive sites, defensible non-analogue controls and physically comparable features. No UI polish before the evidence gate.

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
  of each frozen MOLA target, indicating that this descriptor ranking often  lacks discriminating spatial morphology. Five frozen targets are not
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

## E534 — complete source review of the remaining Mars/Moon candidates (2026-11-11)

- Preserved E533's six-record subset and audited the remaining six primary Mars/Moon candidates against the same pinned E532 GeoJSON revision: Dallol, McMurdo Dry Valleys, Arkaroola/Mount Painter, Lanzarote lava tubes, Bockfjord/Svalbard and Boulby Mine.
- Primary sources support each record's **narrow candidate-label claim**, with scope limits retained: hydrothermal Fe geochemistry; dry-valley microclimate/geomorphology; hyperspectral method transfer; lava-tube mineralogy/microbial biomarkers; Martian-meteorite carbonate-globule mineralogy; and deep-subsurface instrument/habitability research.
- E534 validates the exact six prior E533 IDs and six new IDs, DOI membership for the new catalogue references, target-body consistency, and preservation of Draft status. It preserves E533's Haughton supplemental DOI as external corroboration rather than falsely requiring it to appear in the catalogue reference list.
- Cumulative source review is now 12/12 Mars/Moon primary candidates: Mars 10, Moon 2. All 12 remain Draft; catalogue Verified count is 0. No negative controls were created and no site was promoted.
- Exact-head Actions run [#42939838865](https://github.com/stoicsatvik/NASA/actions/runs/42939838865) passed 9/9 tests, fetched the pinned source and emitted artifact [#13819608032](https://github.com/stoicsatvik/NASA/actions/runs/42939838865/artifacts/13819608032).
- PR #93 is draft and stacked on E533 PR #92; no merge or main-branch change.
- Claim states remain: E001 readiness **NOT READY**; known-site recovery **NOT YET MEASURED**; cross-body similarity **NOT YET PROVEN**; novel analogue discovery **NOT YET PROVEN**; challenge-selection superiority **NOT YET PROVEN**.
- Next: construct a predeclared non-analogue control universe and matched-support descriptors with units, uncertainty, spatial support and provenance. Absence from this positive catalogue remains UNLABELLED, never negative.

## E535 independent Earth aeolian dataset discovery (2026-11-11)

USGS source review identified the Grand Falls Dune Field, Navajo Nation, Arizona, as a candidate positive site with independent public field-data releases from 2013–2024. The release family includes wind/sediment-flux measurements, time-lapse imagery, photogrammetry-derived DEMs and orthomosaics; USGS explicitly describes the active dune field as a Mars analogue. The 2022–2023 and 2023–2024 products provide DEM/orthomosaic and meteorological/imagery components; 2023–2024 weather is 15-minute in the windy season and hourly in calmer months, cameras are 10-minute, and passive sediment samplers are retrieved about every two weeks in the windy season.

This raises the evidence potential of the planetary-analog track for a narrow **aeolian-process** experiment. It does not yet make the data E001-ready: raw files have not been downloaded or hashed, CRS/resolution/nodata/units are uninspected, and no non-analogue controls or Mars/Earth matched-support descriptors exist. The heuristic score is unchanged; Martian Map and MODIS/VIIRS remain the provisional top tier pending data ingestion and validation.

Source report: `research/E535_GRAND_FALLS_AEOLIAN_DATA_SOURCE_AUDIT_20261111.md`; registry: `data/grand_falls_source_registry.csv`. Public data access is not field-access permission; the site is on Navajo Nation land and new geological fieldwork requires applicable permits. No fieldwork, sampling or contact was performed.

## E536 — bounded ScienceBase raw-raster ingestion probe (2026-11-11)

A new isolated workflow probes the official ScienceBase item API for the USGS 2022–2023 Grand Falls photogrammetry item (`662bccfad34ea70bd5f11f88`), follows at most two child levels, inventories attached files, and downloads only the smallest directly listed GeoTIFF/ZIP under a 50 MB cap. It hashes any downloaded archive/raster and attempts to record TIFF shape, dtype, GeoTIFF tags, nodata and unit keys plus unit-agnostic pixel statistics. It stores the receipt and sample only as a short-retention Actions artifact; no raw raster is committed. The experiment result remains **PENDING** until exact-head Actions completes. No CRS, resolution, vertical unit, or successful raw ingestion is claimed in advance.


### NASA E536 raw-raster acquisition correction (2026-11-11)

The first E536 raw-ingestion run (#42954866734) returned a 4,255-byte HTML preview page for the 619,492-byte ScienceBase DEM entry; tifffile rejected it (`TiffFileError`, header `<!do`). The initial receipt incorrectly set `raw_sample_downloaded=true` after the byte transfer. This negative result is preserved.

E536.1 now rejects manager preview URLs as non-direct downloads, checks HTTPS ScienceBase catalog endpoints, content type and TIFF/ZIP magic, caps metadata JSON at 5 MiB, and uses the official item-files ZIP endpoint only when all catalogue sizes are known and total <=50,000,000 bytes. The current item-file size sum is 48,431,208 bytes. It extracts only the smallest TIFF and sets `raw_sample_downloaded=true` only if tifffile successfully inspects it. Ten fixture tests were added; the first run caught a 2,000-byte error in the test's expected catalogue-size sum, now corrected. Current exact-head workflow is pending.


## E538 — ScienceBase single-file DEM route (2026-11-11)

- E536 metadata access succeeded for all five pinned item records. E536 raw-ingestion run #42959249524 returned a 1,002,830-byte item ZIP, but both TIFF members were zero bytes; raw_sample_downloaded=false. Independent E537 run #42958393094 reproduced the zero-byte DEM.
- E538 tested the documented single-file catalog route with the exact DEM filename and a 5 MB response cap. The request was anonymous HTTPS, host/path allowlisted, and accepted only TIFF magic or a ZIP with exactly one non-empty exact-name DEM member.
- Exact-head run [#42965502695](https://github.com/stoicsatvik/NASA/actions/runs/42965502695), commit 91c14ea0ed9c03c06c6bf7bbfa36661e5807d177: **7/7 deterministic tests passed**; the live single-file request returned **HTTP 404**. No response payload or DEM was acquired, and no TIFF metadata was inspected.
- Result: the documented ?name= route is not usable for this item in the tested public context. This does not prove that every official ScienceBase/S3 access path is unavailable; it does rule out treating this guessed single-file route as a working fix.
- Next: inspect only the public item metadata for an explicitly exposed anonymous cloud/download URL or select another source item with a verified direct file link. Do not use credentials, access-control bypasses, or further guessed endpoints. If no public direct URL is exposed, stop repeated acquisition attempts and retain the negative result.
- Claim boundary unchanged: Grand Falls remains a candidate Earth aeolian-process source; no raw DEM, CRS, resolution, nodata, vertical datum, calibrated pixel values, matched Mars/Earth descriptors, or E001 analogue recovery are established. No fieldwork, contact, merge, deployment, or competition submission.


## E540 — bounded anonymous DEM header falsification (2026-11-11)
- Draft PR #99, branch research/e540-bounded-dem-header-probe-20261111, exact head 009e834b14aa7010ec6c2050cabd0fcb7b72c72c, stacked on E539 / PR #98.
- Exact-head Actions run [#42974585326](https://github.com/stoicsatvik/NASA/actions/runs/42974585326) succeeded; deterministic tests **8/8 passed**.
- Pinned ScienceBase item metadata returned HTTP 200 and exactly one record matched GFDF_Ripples_2023_04_18_DEM.tif. The record's own anonymous downloadUri was requested with Range bytes=0-31; exactly 32 bytes were returned under HTTP 206.
- The response was text/html; charset=UTF-8, Content-Range bytes 0-31/4255, while the metadata file size is 619,492 bytes. No TIFF magic was present. Bounded header SHA-256: da601195ac485b469d11020bd536befb96529d3a1f367ed9e97db3d7095afc6b.
- Result: **NON_TIFF_HEADER**. The tested manager/download route returns a partial HTML representation, not DEM bytes. This falsifies this route only; it does not prove every ScienceBase/USGS route or other public datasets are inaccessible.
- No credentials, raw bytes, raw URL/query values, full-file download, fieldwork, contact, merge, deployment or competition submission.
- Claim states unchanged: repo operating system SUPPORTED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge-selection superiority NOT YET PROVEN.
- **Next:** stop guessing alternate URL shapes for this item. Pivot to a separately documented raw-data endpoint or independent MOLA/LOLA/Diviner/Earthdata source. E001 remains NOT YET MEASURED / NOT READY, not BLOCKED.


## E541 — challenge-selection leave-one-factor-out falsification (2026-11-11)

- Draft PR #100, branch `research/e541-challenge-selection-factor-ablation-20261111`, stacked on E540 / PR #99.
- Re-scored all 14 challenge candidates after removing each of the five score factors in turn and renormalizing the remaining weights.
- Martian Map #11 leads the frozen scorecard 4.10 vs MODIS/VIIRS #9 at 4.00, but the 0.10 gap is below the 0.25 meaningful-difference threshold.
- Removing portfolio reuse flips the leader: MODIS/VIIRS 4.125 vs Martian Map 4.000 (gap 0.125, still not meaningful). Removing the other four factors leaves Martian Map ahead by 0.029–0.300; the 0.300 gaps occur only when data-readiness or validation, two core criteria, is removed.
- No other challenge enters the top two under a single-factor ablation. Planetary analog #10 remains outside the top five under all five ablations.
- For #10 to match MODIS/VIIRS 4.00 with reuse/differentiation/feasibility held fixed, its data-readiness + validation scores must sum to at least 7.8 (currently 3.5); to match Martian Map 4.10 they must sum to at least 8.2. This is a concrete evidence gate, not a target to inflate heuristically.
- Official scope cross-check: Martian Map asks for an integrated layered view of a Mars location/route from multiple NASA missions; it does not require a route-safety claim. MODIS/VIIRS asks for a harmonized burning-activity calendar. Planetary analog asks for new Earth analog identification/characterization. Links and method are in `research/E541_CHALLENGE_SELECTION_FACTOR_ABLATION_20261111.md`.
- Result: #11 and #9 remain a provisional tie. The #11 lead is partly a portfolio-reuse tie-break, not evidence of scientific/judging superiority. #10 is NOT YET PROVEN as the best challenge; E001 remains NOT YET MEASURED.
- No new dataset was ingested, no E001 experiment/fieldwork was run, no credentials were created, and no UI polish/competition submission/merge/deployment occurred.
- Next: test MOLA/CTX/HiRISE geometry, CRS registration and actual coverage on one pinned Mars area. If insufficient, lower #11 and reassess #9.

## E542 — Jezero MOLA / CTX / HiRISE coverage and reference audit (2026-11-11)

- Draft PR is stacked on E541 / PR #100; main remains unchanged.
- Official PDS MOLA label confirms the 128ppd MEGT44N000HB tile covers 0–44°N / 0–90°E at 0.463 km/pixel at the equator. It uses simple cylindrical projection, planetocentric latitude, positive-east longitude, IAU2000 and a 3396.0 km sphere. Empty bins are interpolated; the label reports about 55% of equatorial bins contain a shot and gaps can reach 12 km. This is not a Jezero-local count measurement.
- USGS 2020 TRN CTX DTM metadata gives 20 m/pixel and bbox 77.1605–77.699°E / 18.211–18.7212°N, Mars 2015 metadata, 3396.19 km sphere, planetocentric latitude, positive-east longitude and MOLA control.
- USGS 2025 MSR TRN HiRISE metadata gives 1 m/pixel and bbox 77.057–77.380°E / 18.135–18.588°N, the same published Mars 2015 sphere/projection conventions, MOLA control, and CTX-reference alignment below 6 m at p93 and 10.2 m at p99; 8/10 stereo pairs were completed.
- Deterministic envelope audit: MOLA tile contains both product envelopes; CTX/HiRISE metadata envelopes overlap over 77.1605–77.380°E / 18.211–18.588°N, a spherical bounding-box area of 275.88 km². This is not valid-pixel area or raster registration.
- Nominal linear resolution ratios: MOLA:CTX 23.15:1; CTX:HiRISE 20:1; MOLA:HiRISE 463:1.
- MOLA IAU2000 / 3396.0 km metadata differs from Mars 2015 / 3396.19 km CTX/HiRISE metadata by 190 m in reference sphere radius. This is not a measured elevation bias or a vertical correction. Explicit transformation and local MOLA observed-count masking remain mandatory.
- The 2021 Science Investigation CTX extension is not interchangeable with the TRN reference: its additional orbits were MOLA-localized and the published Jezero comparison reports significant pixel offsets from HRSC. Keep it quarantined until independently registered.
- Local deterministic harness: 11/11 tests passed. No raw raster bytes, pixel values or local MOLA counts were acquired; no DEM residual or raster registration was measured.
- Claim: Jezero multi-resolution published-metadata coverage compatibility SUPPORTED. Raw raster co-registration NOT YET MEASURED. Cross-body similarity NOT YET PROVEN. Known-site recovery NOT YET MEASURED. Novel analogue discovery NOT YET PROVEN. Challenge-selection superiority NOT YET PROVEN.
- Next: acquire bounded official CTX TRN and HiRISE raster subsets plus MOLA topography/counts; inspect labels, nodata, units, CRS and valid footprints; pin the exact 2025 CTX reference; transform to one Mars body-fixed reference and compare elevation profiles/control residuals. Do not infer route safety.


## E543 — Jezero local MOLA scale anisotropy (2026-11-11)

E542's 463 m/pixel MOLA value is an equatorial nominal spacing, not an isotropic local ground spacing. For the simple-cylindrical MOLA grid, east-west ground spacing scales by cos(planetocentric latitude), while north-south spacing remains 463 m. At the CTX/HiRISE overlap-envelope centroid (18.3995°N), the nominal local MOLA spacing is 439.3309 m east-west and 463.0000 m north-south. This changes the local MOLA:CTX ratio to 21.9665:1 east-west / 23.15:1 north-south and MOLA:HiRISE to 439.33:1 / 463:1. These remain metadata/projection-derived nominal ratios, not measured effective raster resolution. Exact-head Actions run #42998924344 passed 14/14 deterministic tests and JSON receipt validation. No raster bytes, pixel values, local MOLA shot counts, or co-registration residuals were acquired. Next: inspect actual GeoTIFF grid transforms and local counts before selecting resampling or alignment parameters.


## E544 — bounded official Jezero CTX TRN DTM acquisition (2026-11-11)

- Isolated branch: `research/e544-ctx-raw-raster-ingestion-20261111`, based on E543 / PR #102; draft PR pending.
- Pinned the official USGS Astrogeology CTX TRN DTM direct file URL (DOI 10.5066/P906QQT8), published at approximately 9.3 MB and 20 m/pixel.
- Added a bounded HTTPS allowlist, 20 MB cap, TIFF/BigTIFF magic validation, redirect-host validation, GeoTIFF parsing, and five deterministic 64×64 sample windows. Only transport metadata, SHA-256, raster metadata and sample summaries are retained; no raw pixels or raster file are committed or uploaded.
- Fixture tests cover exact source URL policy, TIFF signatures, HTML-preview rejection, transport receipts, nodata masking and bounded GeoTIFF sampling.
- Exact-head GitHub Actions result is pending at this state update. No successful acquisition is claimed until the live workflow receipt proves TIFF parsing and valid sampled pixels.
- If the direct URL returns HTTP 403/404/410 or non-TIFF bytes, preserve the route-specific negative result and stop guessing URL shapes. If successful, proceed to pinned HiRISE lineage and MOLA topography/counts, then common-support raster comparison.
- Claim states unchanged pending evidence: raw CTX GeoTIFF acquisition NOT YET MEASURED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; route safety NOT CLAIMED.


## E544 — bounded official Jezero CTX TRN DTM acquisition (2026-11-11)

- Isolated branch: `research/e544-ctx-raw-raster-ingestion-20261111`, based on E543 / PR #102; draft PR pending.
- Pinned the official USGS Astrogeology CTX TRN DTM direct file URL (DOI 10.5066/P906QQT8), published at approximately 9.3 MB and 20 m/pixel.
- Added a bounded HTTPS source allowlist, 20 MB cap, TIFF/BigTIFF magic validation, exact redirect-object allowlist, GeoTIFF parsing, and five deterministic 64×64 sample windows. Only transport metadata, SHA-256, raster metadata and sample summaries are retained; no raw pixels or raster file are committed or uploaded.
- Initial exact-head Actions #43010052871 passed 10/10 fixture tests but classified the documented redirect to `asc-pds-services.s3.us-west-2.amazonaws.com` as outside the first, too-narrow allowlist. The official USGS CTX directory lists the exact TIFF object under that S3 host. This was an allowlist false negative; no raster bytes were acquired by the initial run.
- E544 now permits only the exact source URL and exact corresponding S3 object path listed by the official USGS directory. The corrected live acquisition result is pending; no successful acquisition is claimed yet.
- If the exact S3 object returns HTTP 403/404/410 or non-TIFF bytes, preserve that route-specific negative result and stop guessing URL shapes. If successful, proceed to pinned HiRISE lineage and MOLA topography/counts, then common-support raster comparison.
- Claim states unchanged pending evidence: raw CTX GeoTIFF acquisition NOT YET MEASURED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; route safety NOT CLAIMED.


### E544 exact-head result (2026-11-11)

- Exact-head branch `research/e544-ctx-raw-raster-ingestion-20261111`, head `e64a9e69d86d2a1953e71a07821d4e73c75d9294`; draft PR pending.
- GitHub Actions [#43010645516](https://github.com/stoicsatvik/NASA/actions/runs/43010645516) succeeded: **12/12 fixture tests passed**, live bounded acquisition completed, receipt artifact **13850830857** uploaded.
- The official USGS URL redirected to the exact CTX object listed in the official PDS S3 directory. HTTP 200, image/tiff, **9,662,387 bytes**; SHA-256 `16a1aa66c3f48c1bca252795827db7b417876217aff0f5e1aff18027fab2327b`.
- Rasterio inspected a one-band float32 GeoTIFF, **1596 × 1512**, CRS **ESRI:103885**, **20 × 20** CRS-unit affine spacing, and bounds 4573663.250853–4605583.250853 / 1079453.140188–1109693.140188. Nodata is `-3.4028226550889045e+38`.
- Five deterministic 64×64 windows contained **20,480/20,480 valid pixels**; sampled values ranged from -2699.7209 to -2033.5281. The GeoTIFF band-unit tag is absent; the USGS product metadata separately lists vertical coordinate-system units as metres. Do not conflate those two sources.
- Only a compact JSON receipt was uploaded; no raster or raw pixel array was committed/uploaded.
- Raw CTX GeoTIFF acquisition and bounded sample inspection for this pinned product: **SUPPORTED**. CTX/HiRISE raster co-registration NOT YET MEASURED; MOLA local observed-count support NOT YET MEASURED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; route safety NOT CLAIMED.
- Next decisive gate: pin the exact 2025 HiRISE CTX-reference lineage, acquire a bounded HiRISE raster sample and MOLA topography plus observed-count tile, then compare only over verified common valid-pixel support. Do not infer route safety.


## E545 — bounded Jezero MOLA observed-count support (2026-11-11)

- Isolated branch: research/e545-mola-observed-support-20261111, based on E544.
- Tests the missing local-support premise directly instead of substituting the global equatorial 55% observed-bin statement.
- Pins the PDS Geosciences Node 128 ppd MOLA topography tile MEGT44N000HB and companion count tile MEGC44N000HB, including their PDS3 labels.
- Samples a 33 × 33 window centered at the published CTX/2025-HiRISE overlap-envelope centroid (18.3995°N, 77.27025°E). Requests only complete fixed-width rows with exact HTTP Range; combined image transfer is capped at 1.2 MB and full-file responses are refused.
- Validates PDS label dimensions, sample types, units, projection, byte offsets, HTTP 206, Content-Range and byte counts. Uses count > 0 to separate observed bins from interpolated topography.
- Retains only hashes, source metadata and compact sample statistics; raw raster bytes and pixel arrays are not committed or uploaded.
- Exact-head run #43013238079 and post-documentation reruns #43016218070/#43016212376 succeeded; the measured result is recorded below. Bounded MOLA ingestion and local shot support are supported for this 33 × 33 window only; common-valid-pixel support with CTX/HiRISE is not established.
- Claim states remain: cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; route safety NOT CLAIMED.


### E545 exact-head result (2026-11-11)

Exact-head GitHub Actions run 43013238079 succeeded (11 November 2026):

- Deterministic E545 fixtures: 13/13 passed.
- Both PDS labels returned HTTP 200 and passed the frozen dimensions/type/projection contract.
- Topography range: HTTP 206, 760,320 bytes, Content-Range bytes 75110400-75870719/129761280, SHA-256 26bc6c5c3b5445690558a2d2b7af89d8be4d0ef4071eb0f6640c807143db7cd7.
- Counts range: HTTP 206, 380,160 bytes, Content-Range bytes 37555200-37935359/64880640, SHA-256 216841a8e5ad73ea0051e7227bd64086708ae617e451de450904b4f4f0b82b8b.
- The 33 × 33 window contains 346/1,089 bins with count > 0 (31.7723% observed; 743 bins have zero recorded shots and interpolated topography). Positive counts range 1–7, median 2, sum 650.
- Observed-bin topography: min -2,530 m, median -2,080 m, mean -2,115.806 m, max -1,696 m, population SD 228.663 m. These are PDS MOLA areoid-relative values, not yet transformed to the CTX/HiRISE reference.
- Receipt artifact 13851307843; ZIP SHA-256 0c52efbc41515eab4c8f6f25da9b699d74b38edd1395414f51d97cb16f1d23ba. No raw pixels or raster bytes were retained.
- Outcome: MOLA_OBSERVED_SUPPORT_MEASURED. Bounded MOLA ingestion and local observed-shot support for this window: SUPPORTED. The 31.8% result is a measured local coverage fraction, not a global coverage estimate or a co-registration result.
- The MOLA window is centered inside the CTX/HiRISE metadata-envelope intersection; its full footprint extends beyond that intersection. It is not a verified common-valid-pixel window.
- Cross-body similarity remains NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; route safety NOT CLAIMED.


## E546 — bounded 2025 HiRISE archive range-access feasibility (2026-11-11)

- Isolated branch: \`research/e546-hirise-zip-range-feasibility-20261111\`, based on E545 / PR #105; draft PR only.
- Pinned the official USGS 2025 MSR TRN HiRISE mosaic ZIP (DOI 10.5066/P13CPYYU; published archive size 5.3 GB).
- Tests whether exact HTTP Range access can inspect the ZIP tail, ZIP64 metadata, central directory, one DTM member's local header and four-byte TIFF signature without downloading or extracting the archive.
- Hard transfer budget: 8.52 MB; the workflow refuses a server that ignores Range and never follows redirects.
- Deterministic fixture suite covers URL allowlisting, exact 206/Content-Range validation, ignored Range, redirects, ZIP EOCD, multi-disk rejection, central-directory parsing, path traversal and local-header agreement.
- Exact-head Actions [#43018937442](https://github.com/stoicsatvik/NASA/actions/runs/43018937442) succeeded: 12/12 fixtures passed. The 5,468,062,403-byte ZIP64 archive supports exact HTTP Range; 17 entries and a 3,215-byte central directory were parsed. Exactly one DTM TIFF was found, but it is ZIP method 8 (DEFLATE), 675,625,590 compressed / 711,891,990 uncompressed bytes. The orthomosaic is also deflated (4,631,266,296 / 4,674,976,833 bytes). Only 68,993 bytes were transferred; no raster values were read. Receipt artifact 13854770384, SHA-256 82eb60c3c2871d076bace47fde5db08fe31022623d3de700335d504d513a6efe.
- Outcome: archive range access SUPPORTED; DTM random access through this ZIP layout NOT SUPPORTED. Do not download the 5.3 GB archive or the 676 MB DTM member.
- Next gate depends on the measured member compression method: stored TIFF may permit bounded internal IFD/tile reads; ZIP-deflated TIFF does not permit ordinary random access without full-member decompression and must not trigger a multi-gigabyte download.
- Claim states remain: cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; challenge-selection superiority NOT YET PROVEN; route safety NOT CLAIMED.


### E546 exact-head failure and result reconciliation

- First live run #43018471829 passed 11/11 fixtures but hit a ZIP64 receipt-accounting bug after central-directory parsing; no receipt was produced. The runner fix was committed.
- Intermediate run #43018803181 caught a double-escaped ZIP64 signature fixture (1 failure, 11 passes); the fixture was corrected.
- Final exact-head run #43018937442 passed 12/12 and completed the bounded source probe. The source is range-readable, but the selected DTM and orthomosaic are ZIP-deflated. Total transfer was 68,993 bytes; no raster pixels were acquired.
- Current result: public archive Range access SUPPORTED; random access through this ZIP member layout NOT SUPPORTED; raster values and CTX/HiRISE registration NOT YET MEASURED.
- Next: search only for separately published controlled, range-addressable HiRISE products. Do not substitute uncontrolled RDRs and do not download the multi-gigabyte archive.


## E547 — bounded direct controlled HiRISE GeoTIFF range probe (2026-11-11)

- Isolated branch: \`research/e547-hirise-direct-geotiff-range-20261111\`, stacked on E546 / PR #106; draft PR only.
- E546 found the 2025 MSR HiRISE DTM is ZIP-DEFLATE inside the 5.47 GB archive; no small raster window can be read through ZIP member offsets without decompressing the 676 MB DTM member.
- Identified a distinct official 2020 Mars 2020 TRN HiRISE DTM GeoTIFF in the USGS S3 directory: \`JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif\`, DOI 10.5066/P9REJ9JN. This is not the 2025 MSR mosaic (DOI 10.5066/P13CPYYU) and must not be conflated with it.
- Added a Range-only TIFF metadata/segment probe. It validates the exact source URL, HTTP 206 and Content-Range, parses TIFF structure using a seekable bounded reader, and reads at most one compressed tile/strip no larger than 512,000 bytes.
- Hard total transfer cap: 1,000,000 bytes. If the server ignores Range, the response body is closed without consumption. No pixel values are decoded; only compact metadata and hashes are retained.
- Added deterministic synthetic tests for tiled TIFF parsing, oversized segment refusal, Range ignored, Content-Range mismatch, transfer cap and invalid seeks.
- Exact-head Actions [#43022208448](https://github.com/stoicsatvik/NASA/actions/runs/43021100543) succeeded: 8/8 fixture tests passed; the 1,839,545,409-byte TIFF returned HTTP 200 with `Accept-Ranges: bytes`. TIFF is 21,400 × 21,488 float32, uncompressed, one row per strip (21,488 strips; 85,600 bytes/row), not tiled. ModelPixelScale [1,1,0], ModelTiepoint [0,0,0,4577366,1106618,0], GeoKeyDirectory present. One 85,600-byte strip was read by exact Range; total 12 requests / 258,025 bytes, below the 1 MB cap. Receipt artifact 13855557466, ZIP SHA-256 2513dc52d9abfc3bbaa1442d61382fd1c230cbda1fef7d551772d0dcdc9a4f2c.
- Outcome: direct 2020 TIFF metadata and one strip range read SUPPORTED. COG status NOT CLAIMED; pixel values NOT decoded; 64×64 window NOT YET MEASURED; CTX/HiRISE registration NOT YET MEASURED. This is the 2020 TRN product, not the 2025 MSR mosaic.
- Next: inspect the sidecar label for vertical units/nodata; then test a preregistered 64×64 window. The TIFF is uncompressed float32 with one row per strip, so 64 rows × 64 columns should require 64 exact 256-byte payload ranges (16,384 payload bytes) if row offset/count invariants hold. Decode only after confirming nodata semantics, then compare coordinates/CRS to E544 without assuming datum or exact CTX-reference identity. Keep 2020 and 2025 products separate.


## E548 — bounded controlled HiRISE pixel-window acquisition (2026-11-11)

- Draft PR #108, stacked on E547 / PR #107; main unchanged.
- Exact-head Actions #43023187910 passed 9/9 deterministic tests and completed the live bounded acquisition.
- The 2020 TRN HiRISE PDS3 label (2,296 bytes; SHA-256 99b972f7ea13f9e05e9d3f265435a0566b53dbde4088781673edeb0b6d24cade) identifies IEEE_REAL / 32-bit samples, equirectangular projection, centre latitude/longitude 0°, A-axis radius 3,396.19 km and 59,274.6975 pixels/degree. It does not expose a standalone UNIT or MISSING_CONSTANT field.
- GeoTIFF GDAL_NODATA supplies -3.4028226550889045e+38; no nodata values occurred in the preregistered 64×64 window.
- Actual bounded pixel sample: 4,096/4,096 finite and usable; min −2,439.2717, median −2,436.7209, mean −2,436.6555, SD 1.2090, max −2,433.9929. Sample SHA-256 f9cb7459bc3c6030c29c84070913cf4ff20d0650a3e4c4d438bcf255c2c2ae65.
- 74 exact Range requests / 188,767 bytes transferred, below the 1 MB cap; receipt artifact 13854994460.
- GeoTIFF ProjectedCSTypeGeoKey is 32767 (user-defined), so direct code equality with E544's ESRI:103885 is not meaningful. Both official USGS product pages independently specify equirectangular projection, 3,396,190 m spherical radii, planetocentric latitude, positive-east longitude and metre vertical units. Exact parameter-level equivalence still requires reconstruction from the label/GeoKeys.
- E548 supports bounded 2020 HiRISE pixel acquisition only. Common valid-pixel support, local CTX/HiRISE residual, cross-body similarity, E001 known-site recovery, novel analogue discovery and local validation advantage remain NOT ESTABLISHED / NOT YET MEASURED / NOT YET PROVEN as applicable. No raw pixels were retained or uploaded.

Next: reconstruct the user-defined HiRISE projection, verify parameter equivalence with the E544 CTX CRS, and run an area-matched CTX-versus-HiRISE elevation comparison with nodata masks and preregistered ±6 m shift sensitivity. Preserve the published ~0.4 m median offset as external context, not as a result of this local sample.


## E549 — matched-support Jezero CTX / HiRISE comparison (2026-11-11)

- Draft PR #109, stacked on E548 / PR #108; main unchanged.
- Actions #43024094876 passed 5/5 deterministic geometry/area-weighting tests and completed the live comparison.
- The HiRISE PDS3-derived equirectangular CRS is parameter-equivalent to the E544 CTX ESRI:103885 CRS under pyproj. Both use a 3,396,190 m spherical radius, centre latitude/longitude 0°, and metre map units; derived HiRISE scale is exactly 1 m/pixel.
- CTX source bytes: 9,662,387; SHA-256 16a1aa66c3f48c1bca252795827db7b417876217aff0f5e1aff18027fab2327b, matching E544. HiRISE acquisition: 223 exact Range requests / 353,859 bytes, below the 1 MB cap.
- The preregistered 10×10 CTX block has 100/100 valid cells and 100/100 HiRISE area coverage at 100% under the ≥99% rule.
- Zero-shift CTX-minus-area-weighted-HiRISE residual: median −2.7484 m, mean −2.7088 m, SD 1.3677 m, MAE 2.7088 m, RMSE 3.0345 m, p95 absolute 4.8544 m, range −6.2199 to −0.1766 m.
- The fixed ±6 m translation sensitivity grid retains negative medians from −2.4270 m to −3.0173 m. No shift was fitted.
- This local result is discordant with the USGS product metadata's ~+0.4 m median offset statement and description of CTX floating above HiRISE. It is one 200 m patch, not a global contradiction or proof of product error. Plausible explanations: local seam/vertical bias, spatially varying registration, local terrain/surface differences, or unresolved product metadata interpretation. The CTX metadata separately reports 3.8 m vertical registration between component DTMs after HRSC alignment.
- Claim state: physical map-definition equivalence SUPPORTED; common valid-area support for this patch SUPPORTED; local vertical difference MEASURED; local horizontal registration residual NOT YET MEASURED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN.

Next decisive experiment: E550 spatially replicate this comparison at a preregistered 3×3 grid of 100 m patches across the full metadata overlap. Determine whether the negative residual is local or systematic, preserve all patch results, and retain a fixed ±6 m translation sensitivity without fitting a corrective shift.


## E550 — nine-patch spatial CTX / HiRISE residual campaign (2026-11-11)

- Draft PR #110, stacked on E549 / PR #109; main unchanged.
- Actions #43025080316 passed 3/3 deterministic design tests and completed the live nine-patch campaign.
- Nine 100 m patches were selected at 15%, 50%, and 85% of the CTX/HiRISE metadata-overlap envelope. Only 6/9 had common valid HiRISE support; the other three (x15_y15, x50_y85, x85_y85) had none. The six supported patches had 25/25 cells each: **150/225 common cells (66.7%)**. Metadata-envelope overlap is therefore not common valid-pixel support.
- CTX source hash matched E544; 9,662,387 bytes downloaded. HiRISE acquisition used 223 exact Range requests / 353,859 bytes, below the 1 MB cap.
- Six supported patch medians (CTX minus area-weighted HiRISE): −1.515, −3.152, −5.014, −2.727, +2.425, −2.427 m. Pooled 150-cell median −2.3149 m, mean −2.2881 m, SD 3.0036 m, MAE 3.0621 m, RMSE 3.7764 m, p95 absolute 6.9772 m, range −13.9472 to +3.1226 m.
- Residual sign varies spatially: one supported patch is positive while five are negative. Fixed cardinal ±6 m sensitivity does not yield one translation that resolves the pattern. The published USGS ~+0.4 m median offset is not reproduced by this non-random six-patch sample; no global contradiction or product defect is inferred.
- Claim state: CRS parameter equivalence SUPPORTED; metadata envelope versus common support distinction MEASURED; sampled-grid common support PARTIAL; local residual distribution MEASURED; global offset reproduction NOT ESTABLISHED; local horizontal registration residual NOT YET MEASURED; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED.

Next: inspect CTX component-DTM seam/quality provenance and seek independent HRSC/MOLA reference data for the six supported patches. Do not fit a correction. Then run E001 known-analogue recovery with transparent random, Euclidean and physically weighted baselines.


## E551 — exact patch-level spatial permutation null for E550 (2026-11-11)

E551 reanalyses the E550 receipt artifact (Actions run 43025458917; artifact 13855824623; receipt SHA-256 bb13f638136d038ec10d683b26fdc48d684fce38957360bc60f121b6d3401123). Nine preregistered positions were attempted, but only six had common valid support (25/25 CTX cells at 100% HiRISE area coverage); x15_y15, x50_y85 and x85_y85 had zero common valid cells. The six patch medians are preserved in data/e550_patch_summaries.json; no raw raster is retained.

The observed six-patch plane has R² 0.5843 and gradient norm 0.4357 m/km. Exact enumeration of all 720 assignments gives p(R² >= observed)=0.2444 and p(gradient norm >= observed)=0.1500. Five of six medians are negative, but the exact two-sided sign-test p=0.21875. Leave-one-patch-out R² ranges 0.1069–0.9145. **Negative result:** a spatially coherent residual gradient is NOT SUPPORTED by this six-patch null test. The six local vertical residuals remain measured; the plane is not a correction surface or geophysical model.

The permutation assumes exchangeability of the six measured patch medians. Three unsupported positions are excluded and spatially informative missingness remains unresolved. Patch medians, not individual pixels, are the permutation units. Local exact tests: 6/6 passed. Exact-head Actions runs 43027847026 and 43027841221 both succeeded; all 6 tests passed and the exact 720-permutation receipt reproduced.

Claim states remain: common support PARTIAL (six of nine positions); local vertical residual MEASURED for six patches only; global vertical offset reproduction NOT ESTABLISHED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; route safety NOT CLAIMED.


## E553 — nine-position missingness sensitivity after E552 nodata provenance (2026-11-11)

- Companion E552 draft PR #112 found that all three unsupported E550 windows (`x15_y15`, `x50_y85`, `x85_y85`) exactly match the product's declared all-nodata digest. The physical cause of nodata remains **NOT DETERMINED**; all six other windows remain valid.
- E553 keeps the six measured medians fixed and evaluates 125 hypothetical completions using the min/Q1/median/Q3/max of the six observed values at each missing position. Each completion receives an exact 9! permutation test for plane R² and gradient norm: **45,360,000 exact permutation evaluations**.
- Across completions, exact R² p-values range **0.0183–0.9898** and gradient p-values **0.0180–0.9897**. Four of 125 hypothetical completions yield p<0.05 for both statistics. This fraction is **not a probability** and the imputed values are not measurements.
- **Interpretation:** E551's six-patch null remains valid for the six measured locations. The nine-position spatial-gradient claim is **NOT IDENTIFIABLE** from current support; missingness can change the conditional null result. Do not fit a correction plane or impute into the science product.
- Exact tested code head `ac9d07aa594102899812b79cd7e0d850172a4758`; Actions PR run [43033652738](https://github.com/stoicsatvik/NASA/actions/runs/43033652738) and push run [43033646927](https://github.com/stoicsatvik/NASA/actions/runs/43033646927) both **SUCCESS**; 5 deterministic tests passed; artifact `13862081912`.
- Report: `research/E553_MISSINGNESS_SENSITIVITY_20261111.md`; result: `research/results/E553_MISSINGNESS_SENSITIVITY_20261111.json`.
- Claim states: six-patch gradient **NOT SUPPORTED BY E551 NULL**; nine-position gradient **NOT IDENTIFIABLE**; conditional missingness sensitivity diagnostic **SUPPORTED**; cross-body similarity **NOT YET PROVEN**; known-site recovery **NOT YET MEASURED**; novel analogue discovery **NOT YET PROVEN**; route safety **NOT CLAIMED**.
- Next: recover valid support at the three nodata positions through a separately verified footprint or preserve the partial-coverage result. E001 still requires independently labelled Earth positive sites, hard negatives and physically comparable descriptors. No field data or route-safety validation was created.


## E554 exact-head update (2026-11-11)

The E554 bounded neighborhood workflow [#43044286332](https://github.com/stoicsatvik/NASA/actions/runs/43044286332) passed 6/6 tests. All three E550 unsupported positions had 16,384/16,384 finite nodata pixels, zero non-finite pixels, zero usable pixels, and zero usable pixels in the central 64×64. The three sampled windows share the same constant-nodata byte digest. Transfer was 368,991 bytes across 394 exact ranges. This establishes local 128 m support gaps, not their cause. The next gate is product-specific FOM/footprint provenance; no imputation, correction plane, or route-safety claim.


## E554 — HiRISE nodata-neighborhood audit (2026-11-11)

Draft PR #114, branch `research/e554-hirise-nodata-neighborhood-20261111`. Exact-head Actions run [#43044286332](https://github.com/stoicsatvik/NASA/actions/runs/43044286332) succeeded. Three 128×128 neighborhoods centered on the E550 unsupported positions each contained 16,384/16,384 nodata pixels and zero usable pixels, including the central 64×64. The live probe used 394 exact HTTP Range requests / 368,991 bytes under the 1 MB cap. The GeoTIFF nodata value is -3.4028226550889045e+38. The nearby-support-boundary explanation is not supported within these sampled 128 m neighborhoods, but the physical cause remains NOT DETERMINED (footprint exclusion, quality/terrain mask, or another product rule remain viable).

Claim: local 128 m nodata neighborhoods MEASURED; common support at the three positions NOT RECOVERED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; route safety NOT CLAIMED.

Next: stop repeated local pixel probes. Seek independent USGS footprint/quality-mask provenance or preserve partial coverage; return effort to independent Earth positive-site/control discovery before E001.


## E556 NASADEM HGT access gate (2026-11-11)

- Draft PR #116 on `research/e556-nasadem-earth-candidate-sample-20261111`, stacked on E554; main unchanged.
- Exact implementation head `24e7238f329df6f9189cee939c20258043489009`; [Actions #43049875930](https://github.com/stoicsatvik/NASA/actions/runs/43049875930) SUCCESS, 8/8 deterministic tests; aggregate artifact #13868747953, ZIP SHA-256 `ffe193339d56983d88ad0f8cfac13fcc67c29a1333cfec2275aca7f24b5c3d5a`.
- NASA CMR returned `NASADEM_HGT_n19e076` / tile `N19E076` for both Lonar (19.9750 N, 76.5090 E) and nearby comparison (19.8000 N, 76.3000 E).
- Both CMR responses were 3,206 bytes with distinct preserved SHA-256 values in `research/E556_NASADEM_EARTH_CANDIDATE_SAMPLE_20261111.md`.
- The only returned data path is `/lp-prod-protected/NASADEM_HGT.001/NASADEM_HGT_n19e076/NASADEM_HGT_n19e076.zip`. Outcome **EARTHDATA_AUTH_REQUIRED**. No credentials, redirects, range requests or raster bytes.
- **SUPPORTED:** CMR tile metadata resolution. **BLOCKED:** anonymous NASADEM pixel access through this path. No elevation sample was measured.
- E557 tests an anonymous Copernicus GLO-30 public COG as auxiliary data; do not treat it as a mandatory NASA challenge resource or merge DSM values naively with planetary elevation.


## E557 Copernicus GLO-30 sample gate (2026-11-11)

- Draft PR #117, branch `research/e557-copernicus-glo30-lonar-sample-20261111`, stacked on E556; main unchanged.
- Exact code/test head `0679ef0ab45903738fdf80e086b078e61533c077`; [Actions #43050765819](https://github.com/stoicsatvik/NASA/actions/runs/43050765819) SUCCESS, 7/7 deterministic tests; artifact #13868973608, ZIP SHA-256 `55830d1d3457d0692f61492fb7caede6777797f5bd930bb7590fe1772a053ca7`.
- Public Copernicus GLO-30 COG tile `N19_00_E076_00` HEAD 200, object size 39,295,710 bytes, range support confirmed; exact 16,384-byte header range returned HTTP 206 and TIFF signature. No full tile or raw window was committed.
- Raster metadata: 3600×3600 float32, EPSG:4326, 1 arc-second, 1024×1024 DEFLATE COG blocks, 2/4/8 overviews, `AREA_OR_POINT=Point`, no GeoTIFF unit tag. Official handbook specifies metres and EGM2008 vertical datum; GLO-30 is a DSM including vegetation/buildings.
- Two 17×17 windows were measured. Lonar literature lead: 289 valid samples, all exactly 479.500 m (SD/relief/slope 0). Nearby comparison point: median 570.597 m, mean 569.788 m, SD 4.520 m, relief 14.064 m, central slope 4.760°. Both windows cover ~465×492 m. The flat Lonar patch is not interpreted without WBM/FLM lineage; it may be water or a point away from the crater rim. Coordinates are approximate; this is not a site-wide sample.
- **SUPPORTED:** anonymous GLO-30 tile access and descriptive DSM windows. **NOT ESTABLISHED:** bare-earth comparability, site labels, cross-body similarity, known-site recovery, novel discovery or local validation advantage.
- Next: obtain WBM/FLM/source-lineage masks if public, sample a coordinate-uncertainty-aware rim/annulus, and audit independent positive-candidate catalogues. Keep DSM distinct from MOLA/CTX/HiRISE; no E001 claim.


## E558 external candidate-catalogue audit (2026-11-11)

- Source 1: Rachelle Le Cussan, `rachellelecussan/planetary-analogue-catalogue`, commit `62e6339bdf308de3bc987388d0faa7130cf57de9`, `data/sites.geojson` blob `156edd871599cf9ac9c083658d14d034f660e35d`, generated 2026-10-12, data CC BY 4.0. Metadata-only source audit; no source files were modified.
- 16 candidate sites, 96 references, 33 peer-reviewed references, 1 marked unverified. All 16 records are Draft; none is second-person Verified. Target distribution: Mars 10, Early Earth 2, Moon 2, Enceladus 1, Europa 1. Coordinate precision: 10 approximately 10 km, 2 approximately 1 km, 4 region-only. Seven sites omit analogue limitations. No India/Maharashtra site and no non-analogue controls.
- This is a candidate-positive catalogue, not ground truth. Its coordinate precision makes sub-kilometre raster sampling around most points unjustified. Record-level analogue claims require original-reference review.
- Source 2 located, not yet acquired: USGS *Known Terrestrial Analog Sites for Planetary Science*, DOI `10.5066/P9J72921`, 2020 point layer, public CC0 1.0. Feature count, schema, archive checksum and overlap with PAAD / the 16-site catalogue remain UNKNOWN until the actual vector data is downloaded and parsed. It is another candidate-positive source, not a negative/control set.
- Durable audit: `research/E558_PUBLIC_ANALOGUE_CATALOGUE_AUDIT_20261111.md`. No controls, labels, raw measurements or validation results were fabricated.

## NASA event-window decision state

- The 14-challenge screen remains a heuristic readiness ranking, not a judging-probability estimate and not a locked challenge decision.
- NASA's official site confirms the 2026 event is **14–15 November 2026**. Recheck all official challenge resource lists and submission/judging guidance as they become available before locking a challenge; an independent data-atlas currently points to **13 November** for the resource/guide release, which is a monitoring cue, not an authoritative NASA rule.
- The planetary-analog challenge remains **NOT YET PROVEN** to be the best challenge. The current research track has useful data-access evidence but no E001 known-site recovery and no cross-body similarity result.



## E559 exact-head live result (2026-11-11)

- Exact code/test head: `905e6d91e3876b66146c64ea3de9bbf994857ed6`.
- Dedicated exact-head workflow [#43064153053](https://github.com/stoicsatvik/NASA/actions/runs/43064153053): SUCCESS; **11/11 deterministic tests** and bounded live source audit completed. Duplicate push-triggered run [#43064147215](https://github.com/stoicsatvik/NASA/actions/runs/43064147215) also succeeded.
- Both exact public prefixes were fully enumerated without pagination: AUXFILES 5 objects / 1,753 XML bytes; PREVIEW 8 objects / 2,610 XML bytes. All six actual layers/lineage objects were found from the listing. Raster COG filenames differ from the handbook's simplified DGED basename for EDM/FLM/HEM/WBM; listing-driven selection succeeded. ACM and SRC names matched the handbook convention.
- Two bounded 17×17 windows were sampled for EDM, FLM, WBM and HEM. At the frozen Lonar literature-lead coordinate (19.9750 N, 76.5090 E): **289/289 WBM pixels = lake; 289/289 EDM pixels = lake; 289/289 FLM pixels = edited except filled; HEM = 0/289 valid pixels (all -32767 sentinel)**. The previously observed flat 479.500 m E557 DSM patch is therefore a water-edited lake observation, not usable bare-earth/topographic morphology evidence. Exclude this point from terrain-descriptor comparisons; do not reinterpret it as a positive analogue label.
- At the nearby comparison coordinate (19.8000 N, 76.3000 E): 289/289 WBM pixels = no water; 289/289 EDM = not edited; 289/289 FLM = not edited/not filled; HEM has 289 valid values, median 0.4560666 m, range 0.2976013–1.2218320 m. This point remains an unlabelled nearby comparison, **not a negative analogue**.
- ACM KML: one geocell placemark, 16,172 ICESat points, tile-level absolute vertical accuracy LE68 1.415 m and LE90 1.665 m. These are tile-level statistics, not Lonar-specific validation. SRC KML: 37 scene placemarks with source-scene IDs and acquisition metadata. Raw raster windows and complete KML were not retained.
- **SUPPORTED:** public quality-mask and source-lineage acquisition for this exact Copernicus tile; water-edited status at the frozen Lonar coordinate. **NOT ESTABLISHED:** local bare-earth elevation, any analogue label, cross-body similarity, known-site recovery, novel discovery, or local validation advantage.
- E559's CLI summary initially referenced a nonexistent key and then mislabeled filename equality as layer presence. Both integration defects were corrected; the exact-head 11-test run now reports actual layer presence separately from handbook filename equality. Earlier failed run #43062858434 is preserved as a failure; no data result was claimed from that failed process.

## E560 - USGS catalogue acquisition result (2026-11-11)

- Exact ScienceBase item JSON returned HTTP 200 (19,203 bytes) for item 5f88940b82cebb8c13d912ee; title and ID matched.
- The item listed one file, `AnalogSites_metadata.xml` (9,406 bytes). Downloaded size matched; no vector file or vector URL was exposed in the downloaded FGDC XML.
- The XML provisionally declares 192 entity points and fields FID/Shape/Name/AnalogType/Lat/Lon/AnalogBody, Mercator_1SP / WGS_1984 / meters, and AnalogType values Impact Crater, Dunes and Volcanic Eruption.
- The XML explicitly says it is for identification/discovery, not for analysis, and point locations may be wrong by up to 10 km from feature centroids. It is marked In work / update as needed; lineage is None / Unknown. Treat it only as a candidate discovery index, never precise ground truth or a training label set.
- Integrity discrepancy: item JSON MD5 `def5fcdca1a6e7dd4389def926c3c1f1` versus computed XML MD5 `d514547ac0dd7e68a302e03cd4c59d9f`; size matches at 9,406 bytes; XML SHA-256 `0b38af81da5fd638f830b066c4d6c6626b899ef0c1aad16a4cecef33821ef855`. FGDC claims remain provisional until this is reconciled.
- E560 exact code/test head `85063538913db181e7f21478b2ebb4c38a98356c`: [Actions #43069286871](https://github.com/stoicsatvik/NASA/actions/runs/43069286871) succeeded, **13/13 deterministic tests** and bounded live metadata acquisition. Subsequent E560 commits are documentation-only; current E560 branch head is `be3c2b5e007fb0913b4a4f12e5fd7953c8d57447`. Earlier exact code run [#43068609889](https://github.com/stoicsatvik/NASA/actions/runs/43068609889) also passed 13/13.
- The ScienceBase item JSON exposed one ArcGIS REST FeatureServer web link on `services.arcgis.com`; its `token` query value was not retained or reused. E560 did not follow the link.
- No vector features or coordinates were acquired by E560. No overlap, known-site recovery, controls or E001 result.

## E561 - public ArcGIS analogue service audit (2026-11-11)

- E561 verified the public ArcGIS service item ID and layer 0 schema. Anonymous Query is explicitly allowed. Layer 0 is a point layer with FID/Name/AnalogType/Lat/Lon/AnalogBody, object-ID field FID, WKID 3857 and max record count 2,000.
- The exact count-only request (`where=1=1&returnCountOnly=true&f=json`) returned **4 records**, not the FGDC metadata's provisional 192. No feature rows, geometries or coordinates were requested or downloaded.
- The service metadata reports static data and a 10 July 2024 last-edit date. It also advertises anonymous update/delete permissions; E561 used GET-only requests and performed no writes.
- Exact-query hardening now permits only `f=json` for metadata and the exact count-only parameter map for the query endpoint. Token parameters, duplicate keys, fragments, `outFields`, geometry-return flags and arbitrary query additions are rejected.
- Latest exact-head PR workflow [#43070943518](https://github.com/stoicsatvik/NASA/actions/runs/43070943518) and push workflow [#43070938391](https://github.com/stoicsatvik/NASA/actions/runs/43070938391) passed **7/7 deterministic tests** and repeated the live count-only query. Earlier E561 runs [#43070089505](https://github.com/stoicsatvik/NASA/actions/runs/43070089505) and [#43070045960](https://github.com/stoicsatvik/NASA/actions/runs/43070045960) also passed 7/7 and confirmed the same count. The intermediate push run [#43070930458](https://github.com/stoicsatvik/NASA/actions/runs/43070930458) was cancelled by the concurrency group after a subsequent commit; it is not a scientific failure.
- **SUPPORTED:** public service metadata, layer schema, anonymous read access and count-only query. **NOT ESTABLISHED:** that the four service records are the 192 FGDC points, version equivalence, coordinate accuracy, analytical suitability, any labels, or E001 recovery.
- E560's ScienceBase XML MD5 mismatch remains unresolved. The ArcGIS service count of four is a version/provenance discrepancy, not a replacement for the FGDC count. Do not request feature rows until publisher provenance reconciles the two representations.

## Updated next decisive gate

Reconcile the ArcGIS service item/version and the ScienceBase XML checksum discrepancy before any feature-row acquisition. If the publisher's version lineage cannot be established, retain the service only as an unverified discovery endpoint and stop short of using it as an analytical label source. No E001 recovery, coordinate overlap, control validation, or quantitative analogue result is claimed. No follow-up to previously contacted nonresponders.


### E561 ArcGIS Portal item metadata (11 November 2026)

- Public Portal item JSON confirms item ID `db564f72235f49b39c4147df36fd3308`, title Terrestrial Analog Sites for Planetary Science, type Feature Service, access public, owner account `mahunter@usgs.gov_USGS`, created 2020-11-17 18:08:27 UTC and modified 2024-07-09 18:04:14 UTC.
- Its service URL matches the ArcGIS service host/path after case normalization; no query parameters or token are present. The 178-character description does not mention DOI 10.5066/P9J72921, the ScienceBase item ID or FGDC.
- Layer last edit is 2024-07-10 18:37:49.500 UTC, ~24 h 33 min 35.5 s after item modified. The item identity is confirmed, but the version relationship to the 192-point FGDC release is not.
- Count-only query still returns **4**, versus the provisional FGDC count 192. No feature rows or coordinates were acquired.
- Final exact-head PR workflow [#43073044735](https://github.com/stoicsatvik/NASA/actions/runs/43073044735) passed **14/14 tests** and completed the live metadata/schema/count audit. Artifact [#13879985771](https://github.com/stoicsatvik/NASA/actions/runs/43073044735/artifacts/13879985771).
- Earlier negative attempts are preserved: Portal item `f=json`/`f=pjson` initially returned `text/plain` and was rejected; accepting parseable JSON exposed a case-only path difference, now recorded explicitly. The ScienceBase XML MD5 mismatch remains unresolved.


## E562 — FIRMS credential-free data-access audit (2026-11-12)

Exact-head PR #121 on `research/e562-firms-source-access-audit-20261112`, stacked on E561; main unchanged. Dedicated Actions run #43085578996 passed 6/6 deterministic tests and the bounded live audit. Artifact #13886920824 records:

- Official FIRMS tutorial sample returned HTTP 200, 6,077,404 bytes, SHA-256 `edf79f62b35ba4485d7c85e01be5f6f61d30ab7b4addcf2eea00e2581982c30f`; 74,605 rows × 14 fields; one acquisition date (2023-07-12); VIIRS only; versions 2.0NRT and 2.0URT; no missing values in the sample.
- Exact listed South Asia daily VIIRS file returned HTTP 303 without credentials; redirect not followed.
- A bounded area API request using literal placeholder `NO_KEY` returned HTTP 400 and was classified MAP_KEY_REQUIRED.
- No Earthdata token or MAP_KEY was created, read, stored or used. No raw rows were retained.

Claim updates:
- Public static VIIRS sample ingestion: SUPPORTED.
- Current/historical MODIS+VIIRS access without credentials: NOT YET PROVEN.
- Cross-sensor harmonization and regional/global fire calendar: NOT YET MEASURED.
- All challenge-selection superiority claims remain NOT YET PROVEN. E541's provisional #11/#9 top tier and reversal under removal of portfolio-reuse weight remain unchanged; no challenge is locked.

The official FIRMS page requires Earthdata Login for daily text downloads; the area/data-availability API requires a free MAP_KEY. The static 2023 VIIRS sample is a parser/visualization fixture, not a paired MODIS/VIIRS validation cohort. See `research/E562_FIRMS_CREDENTIAL_FREE_ACCESS_AUDIT_20261112.md`.

### Next decisive gate (deadline-aware)

E563 has completed the pinned Jezero three-way MOLA/CTX/HiRISE common-point-support experiment. Do not repeat the same CRS or local support probes.

- Exact-head draft PR #122 on research/e563-mola-ctx-hirise-common-support-20261112, stacked on E562; main unchanged.
- Actions run #43089442518 passed all 6 deterministic geometry/mask tests and the bounded live acquisition. Artifact #13886639834.
- MOLA: 346/1,089 bins (31.7723%) have observed laser-shot counts > 0; zero-count/interpolated bins are excluded.
- CTX: 346/346 observed MOLA point centers map to valid CTX pixels.
- HiRISE: 256/346 are inside the raster bounds; 164/346 are finite, non-nodata. Thus 90 are outside the raster bounds and 92 are inside-but-nodata.
- Three-way common point support: 164/346 = 47.3988%. This is point-center support, not area coverage. The bounded HiRISE sample used 29 row ranges / 959,660 bytes under the 2.5 MB cap.
- CTX and PDS3-derived HiRISE CRS parameters are pyproj-equivalent. The 190 m reference-radius difference is documented. The inverse-transform numerical round-trip is not an independent horizontal registration residual.
- Claims: bounded MOLA observed-shot support SUPPORTED; CTX/HiRISE CRS parameter equivalence SUPPORTED; three-way point support PARTIAL FOR THIS BOUNDED WINDOW; independent horizontal registration residual NOT YET MEASURED; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; route safety NOT CLAIMED.

Challenge-selection consequences:
- Martian Map (#11) loses any assumption that the three-layer metadata envelope is fully common-valid coverage. The bounded observed-MOLA sample has only 47.4% three-way point support and no independent route-safety or horizontal-control validation.
- MODIS/VIIRS (#9) still has only a static one-day VIIRS sample on a credential-free path; daily South Asia data and area API remain credential-gated.
- Planetary analog (#10) still lacks independent analysis-grade Earth positive sites, defensible non-analogue controls and an E001 recovery result.
- Keep the all-14 challenge screen open. #11/#9 remain provisional competitors, not proven winners; #10 is not yet the best-supported challenge. Re-score only when a scored factor changes from new evidence. No challenge is locked.

Next highest-information work: find and verify an independent, analysis-grade Earth analogue plus non-analogue control source with stable geospatial geometry and scientifically meaningful labels. Document label semantics, positional uncertainty, feature availability and provenance. Run E001 only when the positive/control universe and physically comparable feature family pass that admissibility gate. If that gate cannot be met before the event, prefer a challenge whose decisive data and validation gates are already measurable rather than polishing an unvalidated analog map.

## E563 — three-way MOLA / CTX / HiRISE common-point-support result (2026-11-12)

- Research PR #122, branch research/e563-mola-ctx-hirise-common-support-20261112, stacked on E562.
- Exact-head Actions run #43089442518: success; 6/6 deterministic tests and bounded live source acquisition passed. Artifact #13886639834.
- Source hashes and acquisition receipts are retained in the PR artifact and report research/E563_THREE_WAY_COMMON_SUPPORT_20261112.md; no raw raster samples were committed.
- Observed MOLA bins: 346/1,089. Valid CTX point centers: 346. HiRISE in-bounds point centers: 256; valid non-nodata HiRISE point centers: 164. Three-way valid point centers: 164/346 (47.3988%).
- HiRISE nodata value: -3.4028226550889045e+38 from GeoTIFF GDAL_NODATA. The 92 in-bounds-but-nodata points are not imputed.
- HiRISE acquisition: 29 row-range requests, 959,660 bytes, 2.5 MB cap. CTX GeoTIFF: 9,662,387 bytes. MOLA topography/count ranges: 760,320 / 380,160 bytes; both exact HTTP 206 ranges matched their declared Content-Range.
- The 190 m MOLA/Mars 2015 reference-radius difference is not interpreted as a measured displacement. No independent control-point residual or vertical comparison was run.
- The live `tifffile` reader emitted a nonfatal GDAL_NODATA-to-float32 parsing warning; the explicit nodata resolver recovered the tag value and excluded all 92 in-bounds nodata points. Warning preserved, not suppressed.
- Result: three-way spatial point support is PARTIAL in this bounded Jezero window. This weakens full-layer readiness for Martian Map; it does not prove the map challenge infeasible and does not validate route safety.



## E564 — unsupported HiRISE point clustering diagnostic (12 November 2026)

A draft follow-up branch, research/e564-hirise-support-clustering-20261112, is stacked on E563 PR #122. It reuses only E563's in-memory boolean support masks and adds four-neighbor component sizes plus a fixed-count random-label reference for CTX-invalid, HiRISE-outside and HiRISE-inside-nodata bins. The reference is descriptive, not an inferential p-value, because the uniform-label null does not model raster footprint geometry or nodata generation. No raster values or point coordinates are persisted. Exact-head live results are pending; do not claim a physical cause, registration correction, route safety or analogue recovery.


## E565 — footprint-conditioned HiRISE nodata null (12 November 2026)

- Draft PR #124, branch `research/e565-footprint-conditioned-nodata-null-20261112`, code head `0ff4527b195e2df28d1992e5c8d35b7acfd863b7`, stacked on E564 PR #123.
- E564 exact-head workflow [#43104061311](https://github.com/stoicsatvik/NASA/actions/runs/43104061311) succeeded and measured 346 observed MOLA bins, 164/346 (47.3988%) three-way MOLA/CTX/HiRISE valid point centers, 90 outside HiRISE bounds and 92 in-bounds-but-nodata. The 92 nodata points formed 8 four-connected components [44,16,10,7,7,3,3,2] with 96 same-category cardinal edges. The 90 outside points formed 6 components [59,11,8,4,4,4] with 113 same-category edges. E564's all-observed fixed-count reference is descriptive only; it mixes deterministic raster-footprint geometry with internal nodata.
- E565 added a second fixed-count random-label reference that preserves the actual HiRISE in-bounds observed-MOLA footprint and randomizes the 92 nodata labels only among the 256 in-bounds nodes. Exact-head Actions [#43104583925](https://github.com/stoicsatvik/NASA/actions/runs/43104583925) passed **13/13 tests** and reacquired the same bounded source masks. Artifact [13892504439](https://github.com/stoicsatvik/NASA/actions/runs/43104583925/artifacts/13892504439), ZIP SHA-256 `36ad0ecfe853dc5f27b552ed9803d40a7b34e56775cf826ff55f86143b8cbf7a`.
- Footprint-conditioned nodata reference: 256 eligible nodes, 299 in-bounds cardinal edges, 96 observed nodata adjacency edges; 9,999 permutations, null mean 38.3311, 95th percentile 46, upper-tail reference fraction 0.0001. This remains **descriptive, not an inferential p-value**: spatial dependence and nodata generation within the fixed footprint may still violate exchangeability.
- Interpretation: nodata clustering remains pronounced after conditioning on the raster footprint; this does not identify the physical cause, validate a horizontal registration correction, establish vertical agreement or route safety, recover known analogues, or prove cross-body similarity. Do not promote the upper-tail fraction to a p-value.
- Claim states remain unchanged: bounded MOLA support SUPPORTED; CRS parameter equivalence SUPPORTED; three-way point support PARTIAL FOR THIS BOUNDED WINDOW; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; route safety NOT CLAIMED.
- Next highest-information move: inspect the pinned HiRISE product's nodata/quality-mask semantics and seek an overlapping or independent DTM coverage source for the same area. Avoid further same-window permutation variants unless they preserve a materially stronger spatial null. Reassess Martian Map readiness against MODIS/VIIRS only when a scored evidence factor changes; no challenge is locked.


## E566 — 2025 USGS HiRISE DTM/confidence archive access (2026-11-12)

The official USGS 2025 Mars Sample Return HiRISE DTM/Orthoimage archive (DOI 10.5066/P13CPYYU) was tested through its exact published S3 URL without credentials. Exact-head Actions run 43113419588 passed 6/6 deterministic fixtures and successfully read the ZIP central directory using HTTP Range only.

Measured:
- Archive size: 5,468,062,403 bytes; Accept-Ranges: bytes.
- 17 ZIP members; 4 TIFF members: one DTM, two confidence rasters, one orthoimage.
- DTM: 675,625,590 compressed / 711,891,990 uncompressed bytes.
- FOM_ColorConfidence: 95,525,154 compressed / 1,540,258,047 uncompressed bytes.
- FOM_Confidence: 65,308,185 compressed / 66,059,236 uncompressed bytes.
- All four TIFF prefixes have valid TIFF magic. The three science members use ZIP deflate, so direct random access within the ZIP is not available; a selected member must be decompressed first.
- 17 range requests transferred 20,311 bytes under the 32 MiB cap. No pixel values, raw member contents or point coordinates were retained.

Claim update:
- Public archive range access without credentials: **SUPPORTED**.
- DTM and confidence member presence: **SUPPORTED at archive level**.
- GeoTIFF georeferencing and confidence semantics: **NOT YET MEASURED**.
- 2025 valid-pixel support at the E563 observed-MOLA points: **NOT YET MEASURED**.
- Replacement of 2020 HiRISE nodata: **NOT YET MEASURED**.
- Independent horizontal registration: **NOT YET MEASURED**; the 2025 product is aligned to CTX.
- Cross-body similarity: **NOT YET PROVEN**.
- E001 known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Route safety: **NOT CLAIMED**.

The highest-value next gate is to decompress only the 65.3 MB FOM_Confidence member, inspect its GeoTIFF metadata/semantics, and sample the frozen 346 observed-MOLA point centers. Decompress the 675.6 MB DTM member only if that confidence audit shows useful coverage. This is a data-readiness result for Martian Map #11, not evidence that #11 is superior to every official challenge.


## E568 exact-head result (12 November 2026)

- Branch `research/e568-2025-hirise-dtm-observed-point-support-20261112`, head `0d692a630d30ed7cf2bb4b2e19b1a1f56804149c`. Dedicated Actions run [#43115633885](https://github.com/stoicsatvik/NASA/actions/runs/43115633885) succeeded; the bounded raster/archive audit completed. Receipt artifact [#13899160705](https://github.com/stoicsatvik/NASA/actions/runs/43115633885/artifacts/13899160705).
- DTM: 259/346 observed MOLA point centers valid (74.86%); 329/346 inside raster bounds (95.09%); 259/329 in-bounds points valid (78.72%).
- FOM_Confidence: exactly the same validity mask at these points: 259 both-valid, 87 both-invalid, zero confidence-only or DTM-only points. This is a mask-alignment observation for this window, not a calibrated confidence result.
- Raw FOM codes among valid samples: 14=112, 13=52, 15=49, 12=23, 11=5, 3=4, 8=3, 4=2, 5=2, 7=2, 10=2, 6=2, plus one remaining category count; numeric meanings remain uninterpreted.
- Archive access used 712 HTTP ranges and transferred 742,395,283 bytes under the 850 MiB cap. The 5.47 GB archive and orthoimage were not downloaded; only the selected DTM and FOM members were decompressed to temporary files, then deleted. No per-point values or coordinates were retained.
- Compared with E563's 2020 aggregate 164/346 valid points, the 2025 product has 95 more valid point centers (+27.46 percentage points). This is an aggregate cross-run comparison, **not a paired per-point improvement test**: E563 did not retain its point mask. Do not claim a causal or statistically independent improvement.
- Claim states: 2025 DTM GeoTIFF readability SUPPORTED for this pinned member; DTM support MEASURED for this bounded window; DTM/FOM mask alignment MEASURED for this bounded window; independent horizontal registration NOT YET MEASURED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; route safety NOT CLAIMED.
- Next: if the 2020-vs-2025 coverage difference is used in the challenge score, first run a paired 346-point mask cross-tab and CRS/registration sensitivity; otherwise keep it as bounded data-readiness evidence and return to E001 known-site recovery. No UI polish gate has been met.


## E568 exact-head result and validation (12 November 2026)

- Code/test head 41915fa71cbdd77bcf124d9763dec24fae3511f6; exact-head Actions [#43117751701](https://github.com/stoicsatvik/NASA/actions/runs/43117751701) passed 16 deterministic tests and completed the bounded live acquisition; artifact #13898873321.
- 742,395,283 bytes transferred in 712 HTTP range requests under the 850 MiB cap. Only the pinned DTM and FOM_Confidence members were streamed; no full archive or orthoimage download; temporary rasters deleted.
- At the 346 frozen observed MOLA point centers: 329 inside both grids, 17 outside both, 259 valid in both, 70 in-bounds nodata in both, zero discordant validity points. DTM/FOM grids have identical CRS, transform, bounds and 1 m resolution. The cross-tab code now reports shared-footprint nodata separately from points outside both rasters and rejects valid/out-of-bounds mask contradictions.
- 2025 DTM support is 259/346 versus E563's 2020 aggregate 164/346 (+95 centers, +27.46 pp); this is not paired per-point overlap because E563 did not retain its point mask. DTM units are not declared; vertical datum and independent registration remain unverified. FOM codes are not interpreted.
- The E568 branch remains stacked on E567 and has diverged from the current E567 base; PR #127 reports non-mergeable. No rebase, force-push or merge was attempted; keep the PR draft until the stack is reconciled.


## E569 exact-head paired 2020/2025 HiRISE point support (12 November 2026)

- Code/test head: `3136df0d66389a781d2ac0310f2453b8e19038b6`. Exact-head Actions [#43125278384](https://github.com/stoicsatvik/NASA/actions/runs/43125278384) passed all 8 deterministic paired-mask tests and completed the bounded live acquisition; compact receipt artifact [#13902097834](https://github.com/stoicsatvik/NASA/actions/runs/43125278384/artifacts/13902097834).
- The two earlier attempts [#43124512599](https://github.com/stoicsatvik/NASA/actions/runs/43124512599) and [#43124732359](https://github.com/stoicsatvik/NASA/actions/runs/43124732359) failed before acquisition because a seven-position synthetic mask fixture asserted a denominator of six. The test now asserts seven and verifies that both the validity partition and footprint partition sum exactly to the observed denominator. No acquisition result came from the failed runs.
- At the same frozen 346 observed MOLA point centers: 2020 DTM has 256 in-bounds / 164 valid; 2025 DTM has 329 in-bounds / 259 valid. Paired cross-tab: 239 points in both footprints, 17 only in the 2020 footprint, 90 only in the 2025 footprint; 86 valid in both, 61 valid only in 2020 within the shared footprint, 83 valid only in 2025 within the shared footprint, and 9 nodata in both within the shared footprint.
- Total valid-point support differs by **+95** (259−164). Decomposition: **+73** from the footprint imbalance (90−17) and **+22** from the net validity difference inside the shared footprint (83−61). This is a point-support decomposition, not a quality or accuracy advantage. The 2025 mosaic is aligned to CTX and is not an independent horizontal control network.
- Fixed translation sensitivity moves only the 2020 point-index calculation over the nine ±6 m map offsets while keeping the 2025 mask fixed. 2020 valid support varies 164–165; net paired support difference varies 94–95. This is sensitivity only, not fitted registration evidence.
- Bounded transport: 3,055,539 bytes in 97 ranges for 2020 point rows; 676,334,995 bytes in 649 ranges for the 2025 ZIP member under the 850 MiB cap. Only the 2025 DTM member was read; no full archive, FOM raster or orthoimage was downloaded; temporary DTM was deleted. No raw elevations, raster pixels or point coordinates were retained.
- The 2020 TIFF reader emitted a non-fatal tifffile warning while parsing the GDAL_NODATA tag; the experiment's own nodata resolver read the tag and completed. Treat the warning as a parser warning, not as proof of a data error. A separate explicit nodata-sentinel encoding audit remains a possible hardening step.
- Claim boundary: paired point support is MEASURED for this frozen 346-point window; area coverage, vertical datum equivalence, elevation accuracy, independent horizontal registration, route safety, cross-body similarity, known-site recovery and novel analogue discovery remain NOT YET PROVEN/MEASURED or NOT CLAIMED.



## E571 — LOLA 45-degree seam-control result (2026-11-12)

- Draft PR #130, branch `research/e571-lola-seam-control-20261112`, code head `59f8fe849e93a9b5b3948bbf90e3963bc5d60ee2`, stacked on E570 / PR #129.
- Exact-head Actions [#43135464449](https://github.com/stoicsatvik/NASA/actions/runs/43135464449) succeeded: **6/6 deterministic tests** and bounded live PDS acquisition; receipt artifact #13907615759.
- The pinned LOLA GDR label returned HTTP 200 (5,139 bytes). Three 11×11 HTTP Range windows transferred 691,332 range bytes; total transfer was 696,471 / 1,000,000 bytes. Each window had 121/121 finite samples and zero missing values. No full raster or raw pixel values were retained.
- Reacquired 45°S seam relief: 1,662.636876 m, within 0.003124 m of E570's rounded 1,662.64 m.
- Same-longitude controls at 44.5°S and 45.5°S: relief 164.632440 m / 757.747948 m; MAD 31.714439 m / 43.487906 m; median slope 0.560620° / 1.864560°; p90 slope 0.986113° / 7.642094°.
- The seam window exceeds both controls on all four descriptors; relative to the control mean, ratios are 3.605× relief, 11.626× MAD, 4.237× median slope and 2.994× p90 slope.
- Limitation: controls differ substantially (593.116 m relief difference; 6.656° p90-slope difference) and each overlaps the seam window by 3/11 rows. This is a **candidate seam confound**, not proof of causation; natural terrain variation remains viable.
- Claim states: repo operating system SUPPORTED; bounded LOLA ingestion SUPPORTED for this pinned product; local seam/control comparison SUPPORTED for this one location; seam artifact attribution NOT YET PROVEN; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge-selection superiority NOT YET PROVEN.
- Do not repeat another single-longitude seam variant. Next priority is to challenge the current leading alternatives in the 14-challenge screen (Martian Map and MODIS/VIIRS) with their own data/acceptance gates; a multi-longitude seam campaign is justified only if it can change feature admissibility. No UI polish before evidence.


## E572 — independent public analogue-catalogue admissibility (12 November 2026)

The pinned third-party Planetary Analogue Catalogue was audited as a possible independent E001 source. Source: \`rachellelecussan/planetary-analogue-catalogue\`, commit \`62e6339bdf308de3bc987388d0faa7130cf57de9\`, \`data/sites.geojson\`, Git blob SHA-1 \`156edd871599cf9ac9c083658d14d034f660e35d\`, 143,202 bytes, CC BY 4.0.

- 16 total records; 12 primary Mars/Moon records (10 Mars, 2 Moon).
- All 12 are Draft; zero Verified positives.
- 68 in-scope references: 21 peer-reviewed, 20 peer-reviewed references supporting analogue/feature/science claims, 1 marked unverified.
- Four broad type families have at least two records, but none has two Verified positives.
- Zero explicit non-analogue controls.
- Only common numeric fields are \`access_level\` and \`hazard_rating\`, both contributor ratings. Zero common physical numeric descriptors and zero target-body measurement fields.
- Coordinate precision: 8 approximately 10 km, 3 region-only, 1 approximately 1 km.
- Exact aggregate receipt: \`research/results/E572_ANALOGUE_CATALOGUE_ADMISSIBILITY_20261112.json\`. No raw GeoJSON, photos or coordinates were retained.

Result: this catalogue is SUPPORTED as a candidate-site discovery index but REJECTED as a stand-alone E001 labels/features dataset. This does not reject any listed site as a genuine analogue. E001 known-site recovery remains NOT YET MEASURED; cross-body similarity, novel discovery, local validation advantage and challenge-selection superiority remain NOT YET PROVEN.

The planetary-analog challenge remains a research challenger, not the current readiness leader. The all-14 screen still places Martian Map #11 (4.10) and MODIS/VIIRS #9 (4.00) in a provisional top tier; planetary analog #10 remains 2.93. E572 does not justify a numeric score change. No challenge is locked.

Next: acquire analysis-grade, source-pinned Earth measurements and explicit negative controls for one narrow physical family, then construct a matched-support Earth/planetary matrix and run frozen E001 baselines. Do not substitute another catalogue-only audit or polish UI before that evidence exists.


- E572 gate hardening: target-body numeric measurements are counted by record and must be common to every in-scope positive/control record. A one-record-only measurement fails the E001 gate. The pinned catalogue has only `compare` map context (lat/lon/view_km), so target-measurement coverage remains zero and the negative admissibility result is unchanged.


## E573 — exact-head 10.2 m translation sensitivity result (12 November 2026)

- Branch head after nodata/masked-pixel regression: `7f6541e10a823402c2c50bcf6647e425d037ca3a`; exact-head Actions [#43155697664](https://github.com/stoicsatvik/NASA/actions/runs/43155697664) passed **10/10 deterministic tests** and completed bounded live acquisition; receipt [artifact #13916101713](https://github.com/stoicsatvik/NASA/actions/runs/43155697664/artifacts/13916101713).
- Baseline reproduced exactly: 346 observed MOLA point centers; 2020 valid 164/346; 2025 valid 259/346.
- Common-mode 13-offset grid: 2020 valid 164–165; 2025 valid 259; 2025-minus-2020 support margin 94–95 at every offset.
- Differential 2025-only 13-offset grid: 2020 fixed at 164; 2025 fixed at 259; margin +95 at every offset.
- Bounded transport: 2020 6,895,643 bytes in 213 ranges under 32 MiB; 2025 676,334,995 bytes in 649 ranges under 850 MiB. No full archive, FOM, orthoimage or raw pixel/coordinate values retained; temporary DTM deleted.
- A non-fatal tifffile GDAL_NODATA parse warning remains recorded. The experiment's resolver read the pinned nodata value and completed; no warning suppression was added.
- Interpretation: 2025 finite-pixel point support remains higher for this frozen 346-point window under every tested offset. The 10.2 m value is a published 99th-percentile HiRISE-to-CTX alignment statistic, not a hard bound or fitted MOLA registration. This does not establish elevation accuracy, independent horizontal registration, area coverage, route safety or analogue similarity.
- Next: obtain an independent horizontal-control residual or authoritative registration validation. Do not widen the translation grid without a new source-backed uncertainty model.


## E574 — support-gain decomposition (12 November 2026)

- Draft PR #134, branch `research/e574-hirise-support-gain-decomposition-20261112-r1`, stacked on the current E573 exact-head branch.
- Source is pinned to E573 run #43155697664 / artifact #13916101713, receipt JSON SHA-256 `939e3c3b81917f50065f4a1296e909bcfd95144e20257fc8939035ae0f5450a0`, source commit `7f6541e10a823402c2c50bcf6647e425d037ca3a`.
- Zero-offset +95 valid-point difference decomposes into +22 from valid/nodata differences inside the 239-point shared footprint and +73 from footprint-only valid points. Thus 76.84% of the net difference is footprint extent and 23.16% is within-shared-footprint validity.
- Across 13 common-mode offsets, components are +21–22 shared and +73 footprint; across 13 2025-only offsets, +22 shared and +73 footprint. This is point support, not accuracy or registration.
- The initial E574 workflow failure [#43156436125](https://github.com/stoicsatvik/NASA/actions/runs/43156436125) was caused by invoking pytest without installing it; no tests or analysis ran. The workflow now uses standard-library unittest.
- Added fail-closed source provenance checks and arithmetic invariants for the 239-point shared partition, both product valid totals, baseline +22/+73/+95 decomposition, and all offset min/max components.
- Local exact-content validation: **13/13 unittest cases passed**; aggregate runner returned +22 shared / +73 footprint / +95 total and 76.8421% / 23.1579%. GitHub Actions validation on the clean-base branch is pending.
- Independent horizontal registration, terrain accuracy, route safety, cross-body similarity, known-site recovery and novel analogue discovery remain unmeasured/not proven.


## E575 — HiRISE control-source independence audit (12 November 2026)

- The USGS MSR product reports 0.9 m 99th-percentile internal alignment between individual DEMs, 2.3 m vertical offsets between individual DEMs, and 10.2 m 99th-percentile alignment to the CTX reference. The 10.2 m value is CTX-relative, not absolute horizontal accuracy.
- The LPSC 2025 paper states the stereo-pair images were horizontally aligned, DEMs vertically aligned to MOLA shot data, and the preliminary/final mosaic rigidly/affinely aligned to the existing Mars 2020 CTX DEM. The 1 m-at-30th-percentile / 3 m-at-80th-percentile inter-mosaic check uses ASP normalized cross-correlation between orthoimages; it is not an independent ground-control network or a DTM-to-ground-truth residual.
- The USGS HiRISE DTM ARD guidance gives general best-case horizontal accuracy relative to MOLA PEDR of approximately 100 m because a MOLA shot spot is approximately 100 m across, and vertical accuracy approximately ±1.3 m. This is general product-family guidance, not a 2025 product-specific residual.
- Result: no independent horizontal-control residual for the pinned 2025 MSR DTM was found in the public sources reviewed. E573/E574's 10.2 m translation grid remains a sensitivity diagnostic for a CTX-relative statistic, not an absolute-error bound or independent MOLA registration.
- Localized offsets are reported near dune fields, smooth texture and dark regions; unresolved jitter or camera-model intrinsics are candidate causes. No cause or correction is established.
- Challenge ranking remains provisional: Martian Map #11 4.10, MODIS/VIIRS #9 4.00, planetary analog #10 2.93. E575 changes no frozen score factor, so no numeric score change is made. No challenge is locked; planetary analog is not the current readiness-ranked leader.
- Claim states: repo operating system SUPPORTED; internal HiRISE alignment SUPPORTED AS REPORTED; CTX-relative alignment SUPPORTED AS REPORTED; independent horizontal registration NOT YET MEASURED; absolute horizontal accuracy NOT ESTABLISHED; route safety NOT CLAIMED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; planetary-analog challenge superiority NOT YET PROVEN.
- Deterministic source-audit runner, report, receipt and eight standard-library tests: experiments/e575_hirise_control_source_independence_audit.py, research/E575_HIRISE_CONTROL_SOURCE_INDEPENDENCE_AUDIT_20261112.md, research/results/E575_HIRISE_CONTROL_SOURCE_INDEPENDENCE_AUDIT_20261112.json, tests/test_e575_hirise_control_source_independence_audit.py. The CLI receipt is checked for valid JSON and a real trailing newline. No raster acquisition, new elevation sample, route-safety claim, UI work or competition submission.
- Exact-head E575 Actions [#43167818230](https://github.com/stoicsatvik/NASA/actions/runs/43167818230) passed 8/8 tests, CLI JSON generation, semantic receipt equality and aggregate artifact #13920647500. Initial newline and byte-order comparison failures remain preserved in runs #43167610009 and #43167695733. The inherited E572 source audit also passed [#43167818221](https://github.com/stoicsatvik/NASA/actions/runs/43167818221).
- MOLA PEDR is an independent sensor family, but its approximately 100 m shot footprint is too coarse to validate a 10.2 m horizontal residual; held-out tracks are suitable only for gross-error screening.
- Next: acquire a separate control network or independently controlled product with documented horizontal uncertainty materially below 10.2 m; measure held-out multi-patch residuals without fitting corrections to evaluation points.


## E576 — HRSC independent-control admissibility audit (12 November 2026)

- Draft PR #136; branch `research/e576-hrsc-independent-control-admissibility-20261112`, stacked on E575.
- Source-pinned test of Mars Express HRSC as a possible independent horizontal-control product for the pinned 2025 HiRISE mosaic.
- Li & Jiang (2023), DOI 10.1029/2023EA002971, uses MOLA PEDR GCPs (476 calibration GCPs; 125,749 overlapping points across 126 tracks). Reported horizontal positional accuracy: 144.61–145.31 m for calibration and 178.716–301.776 m across validation images. MOLA planimetric accuracy is on the order of 100 m.
- Kirk et al. (2020), DOI 10.5194/isprs-archives-XLIII-B3-2020-1129-2020, uses a mosaicked HiRISE DTM as the reference for HRSC/CTX comparison. Its 10–20 pixel horizontal-resolution estimate is not an independent absolute registration residual.
- **Negative result:** HRSC is a separate sensor family but the retrieved absolute-control evidence is MOLA-GCP controlled and remains hundreds of metres. It does not clear the current 10 m-scale horizontal-control gate. Retain HRSC only for coarse cross-sensor comparison/gross-error screening.
- The 10.2 m E575 value is a CTX-relative P99 alignment statistic, not an absolute-accuracy bound. Ratios in E576 are scale screens only, not formal uncertainty comparisons.
- Exact-head E576 Actions are pending at report time. Eight deterministic standard-library tests and CLI receipt equality are included.
- Claim states unchanged: repo operating system SUPPORTED; independent horizontal registration NOT YET MEASURED; absolute horizontal accuracy NOT ESTABLISHED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; route safety NOT CLAIMED; planetary-analog challenge superiority NOT YET PROVEN.
- No new raster/coordinate sample, field measurement, route-safety result, UI work, or challenge lock.
- Next: identify a separate ground-control network or independently controlled product with documented horizontal uncertainty materially below 10.2 m and no shared CTX/HiRISE/MOLA control dependency.


## E576 exact-head validation completion — 12 November 2026

- The previously pending E576 Actions run [#43176210399](https://github.com/stoicsatvik/NASA/actions/runs/43176210399) completed successfully: **8/8 tests passed**.
- The E572 independent-analogue catalogue workflow also passed on the same E576 branch head.
- The E576 result remains negative for HRSC as 10 m-scale independent horizontal control. No scientific claim state or challenge score changed.

## E577 exact-head live result — 12 November 2026

- Branch head: 316468d3674c71d3903836def1f4992d388fbba7; draft PR #137.
- The exact-head E577 workflow run [#43181807071](https://github.com/stoicsatvik/NASA/actions/runs/43181807071) completed successfully at the workflow level: **7/7 deterministic tests passed**, the compact receipt was generated, and artifact [13927155285](https://github.com/stoicsatvik/NASA/actions/runs/43181807071/artifacts/13927155285) was uploaded.
- The live data decision inside that successful run was **ACQUISITION_ERROR**: metadata_http_status=null, selected_file=null, file_count=null and data_rows=null. No credentials were used and no raw values were stored.
- The first 5 MB metadata response overflow was addressed with the documented ScienceBase fields projection. The projected request still failed before an HTTP status was captured. The logs do not identify the transport exception; do not invent a cause.
- This is **not** evidence that the USGS release contains no data, and it is not a measured scientific null. It is a failed live acquisition attempt. No file was selected or downloaded.

### Consequence for E001 and challenge selection

- E577 does not supply an Earth-side positive-site sample. E001 known-site recovery remains **NOT YET MEASURED**.
- E576 independently rejected HRSC as a 10 m-scale absolute horizontal-control source; retain it only for coarse cross-sensor comparison.
- E572 still leaves the independent analogue catalogue as a candidate-site index, not quantitative labels or negative controls.
- The all-14 challenge screen still ranks Martian Map (4.10) and MODIS/VIIRS (4.00) above planetary analog (2.93). The E531 sensitivity screen is heuristic, but its reported winner frequencies favour Martian Map under the tested perturbations. Planetary analog remains the scientific research thesis under test, **not** the readiness leader and **not** a proven best challenge. No challenge is locked.

### Next move

Do not repeat the same ScienceBase endpoint with more guessed URL variants. Pivot to a different legitimate public Earth-side dataset or a separately controlled published analogue source. Preserve provenance and reject any candidate whose coordinates, physical descriptors, measurement support or non-analogue controls cannot be independently defended. E001 runs only after a positive-site set, matched Mars-side feature family and defensible negative controls exist.

Claim states remain unchanged: repo operating system SUPPORTED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge-selection superiority NOT YET PROVEN.

## E577 null-safe receipt correction — 12 November 2026

- Run [#43185820740](https://github.com/stoicsatvik/NASA/actions/runs/43185820740): 7/7 deterministic tests passed; the live receipt had data_sample=null and the CLI summary formatter raised AttributeError on nested .get access. The sanitized artifact still uploaded. This is a software robustness failure, not a scientific result.
- Run [#43185828498](https://github.com/stoicsatvik/NASA/actions/runs/43185828498): workflow and 7/7 deterministic tests passed; receipt decision remained ACQUISITION_ERROR, with metadata_http_status=null, no file_count, no selected file and no data rows. Artifact 13928595688 uploaded. No credentials or raw values.
- Added a null-safe receipt summarizer and regression tests for null, delimited and ZIP data summaries. The E577 workflow now runs tests on push/PR; the live ScienceBase probe is manual-only to avoid repeating the same external request on documentation/test changes.
- No new data were acquired. This is not evidence that the USGS release contains no data and not a scientific null. E001 remains NOT YET MEASURED.
- Next: pivot to a different independent Earth-side dataset/source. Do not repeat the same ScienceBase endpoint with guessed URL variants.



## E577 current-head deterministic revalidation — 12 November 2026

- Current branch head `f28fad133b9e55a8b84429af7c3fa08756f07d3c`: push workflow [#43186974168](https://github.com/stoicsatvik/NASA/actions/runs/43186974168) passed **7/7 deterministic tests**; inherited E572 audit [#43186974229](https://github.com/stoicsatvik/NASA/actions/runs/43186974229) passed.
- The live-probe job was skipped; no repeat network request was made.
- Last live attempt remains [#43185828498](https://github.com/stoicsatvik/NASA/actions/runs/43185828498): null-safe receipt generation succeeded but data access remained `ACQUISITION_ERROR` with no captured HTTP status, selected file or rows.
- No source absence or scientific null is inferred. Keep E001 NOT YET MEASURED and pivot to a different independent Earth-side source; do not retry the same endpoint using guessed URL variants.


## E578 — independent USGS known-terrestrial-analogue source gate (12 November 2026)

- Isolated branch: \`research/e578-usgs-known-terrestrial-analog-sites-20261112\`, stacked on E577 PR #137; main remains untouched.
- Source: USGS data release DOI 10.5066/P9J72921, ScienceBase item 5f88940b82cebb8c13d912ee. This is distinct from the failed E577 Grand Falls item.
- The frozen probe requests only projected metadata, requires an explicit metadata-linked download URI, caps metadata and any eligible vector package at 5 MB, validates a 4 KiB HTTP Range/Content-Range before a full read, and stores only hashes, file/schema/count/CRS summaries. No raw site rows or coordinates are committed.
- Exact-head deterministic and bounded live results will be recorded after Actions completes.
- Potential positive outcome: an independently sourced known-analogue point index with site/type fields and CRS. Even a successful point layer is not quantitative ground truth and supplies no non-analogue controls by itself.
- Claim states remain: repo operating system SUPPORTED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; planetary-analog challenge superiority NOT YET PROVEN.


## E578 exact-head result — independent USGS known-terrestrial-analogue source (12 November 2026)

- Draft PR #138 on \`research/e578-usgs-known-terrestrial-analog-sites-20261112\`, stacked on E577 PR #137; tested head \`7e1bc6ad64beb9318f2f3d44b8144898fcb5f13f\`.
- Actions #43193280091 completed successfully: 6/6 deterministic tests passed; bounded live-probe artifact #13930469672 was uploaded (SHA-256 ee198cf96f23a1d1b07fd33120392200e95a34949a04b4110814a45c5dc59963).
- The live source decision was ACQUISITION_ERROR, TimeoutError: "The read operation timed out". Metadata HTTP status, file count and selected file are null. No data were acquired; no credentials, raw rows or raw files were used/stored.
- This is a transport/access failure, not evidence that the USGS release contains no records and not a scientific null. Do not retry this item using guessed URL variants.
- E001 known-site recovery remains NOT YET MEASURED; cross-body similarity, novel analogue discovery, local validation advantage and planetary-analog challenge superiority remain NOT YET PROVEN.
- Next: pivot to a different independent public Earth-side source or a literature-backed catalogue with usable coordinates and defensible physical descriptors. No claim promotion.


## E579 challenge-readiness falsification — 12 November 2026

- New isolated branch research/e579-martian-map-stac-readiness-20261112, stacked on E578 PR #138; main remains untouched.
- The official 2026 challenge index lists 14 challenges. The current all-14 scorecard remains Martian Map 4.10, MODIS/VIIRS 4.00 and planetary analog 2.93; the 0.10 gap is below the 0.25 meaningful-difference threshold. E531 sensitivity favours Martian Map under tested perturbations, but challenge-selection superiority remains NOT YET PROVEN.
- A live GET of the official USGS Astrogeology STAC collection metadata for mro_ctx_controlled_usgs_dtms succeeded. It reports Mars, NASA/USGS provenance, CC0-1.0, a 2023-04-18 to 2025-07-04 temporal interval, Mars 2015 ocentric equirectangular WKT2 and GSD range 20.0002065–35.9625866 m. It says the CTX products are controlled to MOLA, while warning that some products have jitter and large nodata regions.
- The STAC items endpoint was not retrievable through this run's browser path. No item, raster, pixel, footprint or terrain measurement was acquired. This is collection metadata access only, not a data-ingestion success.
- Official CTX documentation reports 20 m posting and typical 3–5 m vertical precision but warns about jitter, nodata, long-baseline tilt and effective resolution. Controlled HiRISE DTM products are CC0/MOLA-controlled and are not guaranteed to co-register with uncontrolled RDR imagery.
- The official FIRMS page says Earthdata Login is required for daily text-file downloads and MAP_KEY for API/WMS/WFS. No account or key was created and no credentialless historical MODIS/VIIRS path was verified.
- Planetary analog remains the weakest current data-readiness path: E577/E578 ScienceBase requests acquired no records; E572 is only a candidate site index; E001 remains NOT YET MEASURED.
- Readiness ordering under current evidence: Martian Map > MODIS/VIIRS > planetary analog. This is not a final challenge selection. No challenge is locked.
- Full report: research/E579_MARTIAN_MAP_STAC_READINESS_20261112.md.
- Exact claim states unchanged: repo operating system SUPPORTED; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge-selection superiority NOT YET PROVEN.
- No tests were run because this is a documentation/source-metadata audit and the Actions quota is exhausted. No UI, raster processing, field data, public deployment or competition submission.


## E580 — real CTX item and public DTM byte-range acquisition (12 November 2026)

- Current research branch: `research/e580-stac-search-post-20261112`; draft PR #140, stacked on E579 / PR #139. Main remains untouched.
- The official USGS STAC `POST /search` route returned one item for collection `mro_ctx_controlled_usgs_dtms`, Jezero bbox [76.69, 17.41, 78.69, 19.41], limit 1.
- Item: `P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W`; acquisition datetime 2023-04-18T12:00:00Z; polygon bbox [77.2128114, 17.7577892, 77.9059771, 19.3423089].
- Item metadata: shape [4622, 2013], affine transform [4577133.445008798, 20.162955124498982, 0, 1146178.5021103406, 0, -20.162955124498982], WKT2 present, EPSG field absent. Assets include DTM, orthoimage, intersection error, QA metrics and MOLA control CSV.
- A single anonymous HTTP Range request returned 206 for bytes 0–4095 of the 18,114,156-byte DTM. The 4 KiB response hash is recorded in `research/E580_STAC_SEARCH_ITEM_ACCESS_20261112.md`; no raw bytes, raster or pixel values were stored.
- Exact-head workflow #43212727544 passed 9/9 tests and uploaded receipt artifact #13942396569. The first run's one failure was a test assertion defect about the intentional redaction flag; the live probe was skipped, the assertion was corrected, and the exact-head run passed.
- Claim states: collection metadata access SUPPORTED; pinned item metadata acquisition SUPPORTED; public DTM byte-range access SUPPORTED; actual raster/pixel sampling NOT YET MEASURED; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge-selection superiority NOT YET PROVEN.
- Next: use the pinned item to inspect actual COG band units, nodata, CRS/WKT, transform, data type and QA; extract small deterministic valid pixel windows with provenance and uncertainty. Do not infer elevation units from GSD or treat a successful byte-range request as a terrain measurement.


## E581 — actual CTX COG inspection and pixel windows (12 November 2026)

- Current branch: `research/e581-ctx-cog-pixel-sampling-20261112`, draft PR #141 stacked on E580 / PR #140. Main untouched.
- Exact-head workflow #43213482433 passed 8/8 deterministic tests and acquired the pinned 18,114,156-byte public COG. Artifact #13942017708 contains only the aggregate receipt; full-raster SHA-256 is `2acf3fb601fc9728c88cf9b768cc20c0f51dd6ef143936d429f7ca1623ca1ba0`.
- Raster: 2013×4622, one float32 band, NoData -32767, tiled 512×512, DEFLATE, 20.162955 m horizontal posting. CRS present with metre linear units, no EPSG authority code. Item STAC shape and affine transform match the GeoTIFF; WKT hashes match.
- Five deterministic 64×64 windows yielded 20,480 valid pixels with 0% nodata in each sampled window. Aggregate statistics are in `research/E581_CTX_COG_PIXEL_SAMPLE_20261112.md`; raw raster and pixel arrays were not stored.
- Vertical unit is absent from STAC `raster:bands[].unit` and GeoTIFF band units. Official USGS CTX documentation says heights are relative to the Mars areoid and describes the `dem_geoid` processing stage; ASP `point2dem` documentation says DEM heights are in metres. This supports a source-backed metre inference, not a direct file metadata declaration.
- Slope was deliberately not computed in E581 because the unit metadata was absent. Next: make the documented unit inference explicit, calculate multi-baseline slopes with uncertainty caveats, and inspect the item's QA metrics asset. USGS warns that effective resolution is coarser than 20 m posting and typical vertical precision is around 3–5 m.
- Claim states: public item/COG acquisition SUPPORTED; raster/STAC shape-transform agreement SUPPORTED FOR THIS ITEM; pixel-window sampling SUPPORTED; TIFF/STAC vertical-unit field NOT REPORTED; documented metre inference CANDIDATE; slope and QA analysis NOT YET MEASURED; E001/cross-body/novel analogue/local validation/challenge superiority unchanged.


## E582 — CTX slope-descriptor vertical-error sensitivity (12 November 2026)

- Isolated branch `research/e582-ctx-slope-error-envelope-20261112`, draft PR stacked on E581 / PR #141; main untouched.
- Source: official USGS CTX DTM documentation. It states 20 m post spacing, typical 3–5 m vertical precision, coarser effective resolution, MOLA control with sparse shot support, and per-item QA residual summaries. It explicitly notes that 3 m error can create about 9° apparent slope over 20 m but less than 1° over 200 m.
- Recomputed the one-height perturbation envelope `atan(delta_z / baseline)`: 3 m/20 m = 8.530766°; 3 m/200 m = 0.859372°; 5 m/20 m = 14.036243°; 5 m/200 m = 1.432096°. Local standard-library assertions passed. This is a sensitivity calculation, not a raster slope measurement or confidence interval.
- Decision: reject 20 m slope as the primary robust descriptor for this CTX product under the documented error envelope; retain 200 m as a candidate only. MOLA QA residuals are a quality screen, not independent fine-scale ground truth.
- Exact claim states unchanged: public item/COG and E581 pixel-window acquisition SUPPORTED; direct TIFF/STAC vertical unit NOT REPORTED; metre interpretation only a collection-level processing-documentation inference; 200 m slope and QA residual analysis NOT YET MEASURED; E001, cross-body similarity, novel discovery, local validation advantage and challenge-selection superiority NOT YET PROVEN/NOT YET MEASURED.
- Next: E583 bounded acquisition of `qa_metrics` and MOLA-control CSV, followed by 200 m/400 m slope summaries with valid-pair counts, nodata and detrending sensitivity. No route-safety claim.
- Full report: `research/E582_CTX_SLOPE_ERROR_ENVELOPE_20261112.md`.
