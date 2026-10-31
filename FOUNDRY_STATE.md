# FOUNDRY_STATE — NASA

Updated: 2026-10-05
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

1. verify ingestion of real LOLA / Diviner / MOLA / THEMIS / Earth datasets;
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

**Dataset access + known-analogue recovery.**

The next substantive run should reduce one of these uncertainties, not add another planning document.

## 2026-10-23: MOLA interpolation evidence gate

Official maintained MEGDR labels establish that the 720×1440 MEGT median-topography raster **interpolates cells without MOLA observations** and that only ~55% of equatorial bins contain shots; the paired MEGC counts raster is needed to distinguish measured from interpolated cells. See `research/MOLA_MEGDR_COUNTS_INTERPOLATION_GATE_20261023.md`.

**No raw MEGT/MEGC bytes were ingested**. Dataset access remains unverified and E001 remains NOT YET MEASURED. Next preparation gate is checksum + counts-mask QC on official data, not geospatial UI. Full 2026 challenge statements are expected 28 Oct; actual competition solution development is reserved for 14–15 Nov under official guidance. Planetary challenge ranking remains NOT YET PROVEN.

## 2026-10-24: E193 challenge-ranking falsification

All 14 official 2026 challenge summaries were included in a seeded sensitivity audit using the repository's declared scoring weights and explicitly subjective analyst ratings. Under those assumptions, planetary analogues ranked 5/14 (base score 4.59) and topped 6.725% of hypothetical score/weight perturbation scenarios. These scenario frequencies **are not competition success probabilities** and must not be presented as empirical evidence. MODIS/VIIRS and Earth Trend ranked higher under the stated assumptions. Reproducible script and limitations: `research/e193_challenge_sensitivity.py` and `research/E193_CHALLENGE_RANKING_FALSIFICATION_20261024.md`.

**Decision:** challenge-selection superiority NOT YET PROVEN; do not lock the planetary track. Reassess all fourteen when full statements/resources arrive 2026-10-28. Continue real paired MOLA/LOLA data-access preparation, but do not begin developing the competition solution before 14 November. No new raster ingestion or E001 recovery was performed.

## 2026-10-24: E209 real MOLA MEG004 counts-mask ablation

**First real Mars raster ingestion achieved on an isolated research branch.** Official PDS3 MEGT and MEGC 4-pixel/degree (720 × 1440, signed 16-bit big-endian) binaries and labels were downloaded in read-only GitHub Actions run 40074383215, passed the existing metadata/geometry reader and five new synthetic ablation controls, and were SHA-256 fingerprinted. Raw rasters were not committed. Full exact-head JSON is `research/results/e209_mola_real_data_20261024.json`; numerical evidence is from the real PDS bytes, not synthetic measurements.

- MEGC > 0 in **1,027,663 / 1,036,800** cells (99.1187%); 9,137 cells (0.8813%) have zero observations and MEGT supplies interpolated values.
- At global 16 × 16-pixel tiles, the top-decile ranking by uncorrected elevation standard deviation had **100% overlap** with a measured-only ranking (ordinal rank correlation 0.999808). At 4 × 4-pixel tiles overlap was **99.892%**.
- Within ±16° latitude, measured coverage was 99.9995%, and top-decile overlap was 100% at 16 × 16 tiles. Missingness was concentrated in polar bands (85–90°N: 86.00% observed; 85–90°S: 82.27% observed).
- This **fails to support a large global top-decile mask effect at coarse MEG004 resolution**, under these particular descriptors. It does **not** establish that interpolated data are harmless in small areas, polar regions, higher-resolution products or physically normalized morphology.
- The PDS label's approximate 55% equatorial-shot coverage statement is not a measured coverage estimate for the coarse 4ppd product used here; do not generalize it without resolution context.
- Dataset bytes: MEGT SHA-256 `25f16fb7aaf857898dcf98bc4f841341a24f8b9f7e98453ca083bc45d897ca2c`; MEGC SHA-256 `7e920ec43497b4beddf974650471600c7afd4916e2a8dd3500d6b14714365661`.

**Claim states:** real Mars MEG004 ingestion SUPPORTED; this coarse mask-sensitivity result SUPPORTED for the tested metric; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local field-validation advantage NOT YET PROVEN; challenge superiority NOT YET PROVEN.

**Next highest-value experiment:** test the same counts-mask sensitivity on higher-resolution MOLA MEG016/MEG032 products, then ingest real LOLA and Earth terrain at matched physical scales. Do not optimize UI or infer planetary analogues from one Mars dataset. Re-rank all 14 challenges after full statements on 28 October.

## 2026-10-24: E210 higher-resolution real MOLA falsification

Read-only exact-head GitHub Actions run 40074587339 successfully downloaded official **16 pixels/degree** MEGT/MEGC 2880×5760 signed-big-endian PDS3 rasters (33,177,600 bytes each), checked labels/units/projection and source SHA-256, and executed the same masked-vs-all-cell tile-rank experiment at 16/32/64-pixel scales. Full immutable numerical receipt: `research/results/e210_mola_16ppd_real_data_20261024.json`; no raw rasters committed.

**Measured evidence:** 15,685,242/16,588,800 cells (94.5532%) have counts>0; 903,558 cells (5.4468%) are interpolated. At global 16×16 tiles, 1,304 of 64,800 tiles failed the >=25% measured coverage gate; among 63,496 eligible tiles the top-decile overlap was **99.213%**, ordinal rank correlation 0.999453. In ±16° latitude, observed coverage was 96.0475% and 16×16 top-decile overlap **99.306%**. Polar 5° bands have only ~53.96% observed at 85–90°N and ~51.19% at 85–90°S.

**Falsification:** The E209 coarse-resolution finding of strong *global top-decile rank stability* largely survived the independent 16ppd test, but finer resolution revealed more missing bins, coverage-gated exclusions and larger individual rank displacements. This is **not** a demonstration that interpolation is harmless in polar or local patches, nor that elevation standard deviation is a physically comparable cross-body descriptor. The source label's generic equatorial 55% note must not be mistaken for a measured coverage fraction of these particular products.

**Claim states:** real Mars MEG004+MEG016 ingestion SUPPORTED; 4ppd/16ppd masked-rank sensitivity SUPPORTED under tested synthetic metric; E001 known-site recovery NOT YET MEASURED; cross-body similarity NOT YET PROVEN; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; planetary challenge superiority NOT YET PROVEN.

**Next:** target polar/high-missingness sensitivity and independent 32ppd count/raster geometry only if it can change the representation decision; prioritize obtaining actual lunar LOLA and Earth terrain and matching physical footprint before E001. Full official 2026 challenge statements on 28 October may change project selection. No UI/demo polish.

## 2026-10-24: E212 real LOLA/MOLA cross-body scale gate

**First independently ingested real lunar topography.** Read-only GitHub Actions run 40078234718 downloaded NASA Scientific Visualization Studio's LOLA-derived global 4ppd floating TIFF (1440x720), paired with official MOLA MEGT/MEGC 4ppd PDS rasters and labels. The workflow passed synthetic geometry/missingness controls, validated raster shape/type and MOLA PDS metadata, and preserved SHA-256 fingerprints. NASA SVS TIFF SHA-256: `330afa2556a86fd05ac6ba2f912f246600fdade35de2a0d90593d50d07b01b65`. Full numerical receipt: `research/results/e212_lola_mola_real_data_20261024.json`. Raw rasters were not committed.

**Decisive representation result:** at the equator, an equal-angle 4x4 tile spans ~30.323 km north-south on the Moon but ~59.158 km on Mars, a **1.9509x linear footprint mismatch**. A Moon 4px / Mars 2px comparison narrows the north-south span to 30.323/29.579 km, but leaves different sample counts (16 vs 4) and different instrument smoothing. Observed equatorial MOLA fraction was 0.999991 in the +/-10-degree window. Median within-tile elevation SD was 353.23 m (Moon 4px), 58.95 m (Mars 2px), 140.87 m (Mars 4px); these are **diagnostic, NOT comparable terrain similarity scores**. The large change between Mars 2px and Mars 4px demonstrates why equal-angle or naive raw-value comparisons are unsuitable.

**Claim states:** real Mars MOLA and real lunar LOLA-derived raster ingestion SUPPORTED; equal-angle cross-body physical-scale mismatch PROVEN by spherical geometry; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge superiority NOT YET PROVEN.

**Next evidence gate:** ingest legitimate Earth terrain with known geodetic datum, reproject all three bodies to comparable *physical* support and instrument-aware descriptors, obtain LOLA shot/coverage metadata rather than treating derived TIFF as raw observations, then attempt independent known-analogue recovery against random/Euclidean/physical baselines. The full 2026 challenge statements (expected Oct 28) may force a challenge pivot. No UI polish or competition submission.

## 2026-10-24: E214 real Earth SRTM-derived terrain ingestion and footprint ablation

The first NASADEM OpenTopography mirror URL failed HTTP 404 in read-only CI; **do not claim NASADEM was ingested**. The next isolated experiment successfully downloaded three real **Mapzen Skadi SRTM-derived** HGT Earth tiles (Lonar-area N19E076, Western Ghats N18E073, Ladakh N34E077), validated CRS, dimensions, hashes, nodata and metric pixel spacing, and measured 2-km versus 4-km physical windows. Exact-head CI [40082499487](https://github.com/stoicsatvik/NASA/actions/runs/40082499487) SUCCESS; complete immutable receipt `research/results/e214_earth_skadi_real_data_20261024.json`, memo `research/E214_EARTH_DEM_FOOTPRINT_ABLATION_20261024.md`.

**Falsification:** window enlargement changed detrended-relief SD by −29.3% (Lonar lead), +24.8% (Western Ghats lead), and +103.4% (Ladakh lead); 90th-percentile slopes also changed markedly. A fixed angular image tile or arbitrary physical window is not a stable analogue descriptor. The three coordinates are **unvalidated research leads**, not positives or negatives. Mapzen is a derived SRTM-based mosaic, not official NASADEM, and 100% valid delivered pixels do not prove original instrument coverage.

**Claim states:** Real Earth SRTM-derived raster ingestion SUPPORTED; 2/4-km footprint sensitivity SUPPORTED for the tested windows; direct NASADEM ingestion NOT YET PROVEN; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; planetary challenge superiority NOT YET PROVEN. Next gate: independent known-site labels, explicit source/void uncertainty, fixed physically comparable descriptors and E001 holdouts. No competition solution or submission before the official event.

## 2026-10-24: E221 real Earth geolocation-jitter ablation

Read-only Actions [40099007353](https://github.com/stoicsatvik/NASA/actions/runs/40099007353) at code head `dc24e08a357f587b92f80babbddccaa17876f01b` passed and evaluated **150 real Mapzen Skadi SRTM-derived Earth raster windows** (3 research leads × 2/4-km windows × 25 preregistered ±500m coordinate shifts). Complete source-hashed per-window numerical receipt: `research/results/e221_earth_geolocation_jitter_20261024.json`; analysis: `research/E221_GEOLOCATION_JITTER_ABLATION_20261024.md`.

**Falsification:** 2-km detrended relief site ordering changed on 24% of offsets, 4-km relief on 36%; 2-km slope p90 on 76%, while 4-km slope p90 ordering remained unchanged. Largest 2-km relief change from the unshifted coordinate: 29.3% Lonar, 44.0% Western Ghats, 39.4% Ladakh. These overlapping offsets are descriptive sensitivity checks, not independent observations, confidence intervals or measured geolocation uncertainty. No independent analogue labels or cross-body recovery. **E001 NOT YET MEASURED; cross-body similarity, novel discovery, local validation and challenge superiority NOT YET PROVEN.** Next: independent known-site labels and physical/coordinate uncertainty in held-out recovery; no UI or competition submission.


## 2026-10-24: E223 exact independent-site coordinate-jitter stress test

**Question:** E221 shifted all three unvalidated Earth research leads synchronously. Does the same full-rank stability hold if each site is allowed an independently selected offset from the 25 previously measured real SRTM-derived windows?

**Result:** Exhaustively enumerated 25³ = **15,625 exact combinations per descriptor/footprint**, without treating overlapping windows as independent observations. Central full ordering preserved: 2-km relief **77.5488%**, 2-km slope-p90 **16.8%**, 4-km relief **65.6%**, 4-km slope-p90 **100%**. Crucially, at 2-km slope-p90, Western Ghats still ranks top in **95.52%** despite full-order instability. Common-offset E221 audit hides some site-specific possible rank reversals; top-site stability and complete-order stability are different claims.

**Evidence:** `research/e223_independent_jitter_rank.py`, five deterministic tests, `research/E223_INDEPENDENT_SITE_JITTER_20261024.md`; exact-head CI [40103028365](https://github.com/stoicsatvik/NASA/actions/runs/40103028365) SUCCESS at `ee7bed88de398741647f3612b2bde397870cf237`. The source remains E221's 150 real Earth windows; no new planetary rasters or analogue labels. Uniform independent-offset scenario fractions are **NOT empirical probabilities or confidence intervals**. The sites remain unvalidated leads.

**Claims:** Real terrain descriptor sensitivity SUPPORTED for finite tested windows. E001 known-site recovery **NOT YET MEASURED**; cross-body similarity **NOT YET PROVEN**; novel discovery **NOT YET PROVEN**; local field advantage **NOT YET PROVEN**; challenge superiority **NOT YET PROVEN**.

**Next:** Stop extending coordinate-only sensitivity without new external labels. Obtain independently established planetary analogue positives and negative controls, then execute E001 with blind holdouts and random/Euclidean/physically weighted baselines. Reassess official challenges on 28 Oct; no competition solution build before the permitted event window.


## 2026-10-24: E226 exploratory cross-footprint site-identity sanity gate

Read-only reuse of E221's **150 real SRTM-derived overlapping Earth windows** from three *unvalidated* site leads. The experiment held out the exact central coordinate from 72 query windows per case, used one central reference per site, and compared 2-km and 4-km footprints using reference-only normalized relief/slope nearest-neighbor scores, ablations and exact 3! label permutations.

**Measured two-feature site-identity correct counts:** 2km→2km **50/72**; 4km→2km **47/72**; 2km→4km **30/72**; 4km→4km **68/72**. Slope-only 4km→2km **4/72** versus uniform random expected **24/72**. The six 2km→4km two-feature reference-label permutations yield [30, 3, 17, 16, 26, 52], so do not claim statistical significance. This is an exploratory source-site recognition test, **not** independent analogue-label recovery or independent sample inference. Overlapping windows and site selection create substantial leakage risk. See `research/E226_CROSS_FOOTPRINT_SITE_IDENTITY_20261024.md` and branch-scoped deterministic workflow.

**Claim:** footprint-transfer failure in this tiny Earth site-identity sanity check SUPPORTED CONDITIONAL ON RECORDED MEASUREMENTS. **E001 known-analogue recovery NOT YET MEASURED**; cross-body similarity, novel discovery, local validation advantage and challenge superiority **NOT YET PROVEN**. Next: independently sourced known positive/negative analogue labels and blinded recovery against transparent baselines. No new rasters, field data, competition solution or submission.


## 2026-10-24: E227 independent NASA/USGS analogue-label evidence gate

**Real public-source ingestion, not E001.** Official NASA Planetary Analog Explorer has 11 descriptive analogue pairs (9 Moon/Mars); their primary evidence spans terrain, lithology, geochemistry, subsurface ice, astrobiology, operations and temporal landforms. Five of eleven were analyst-tagged as having a plausible static surface-morphology component; these are not NASA-authored machine-learning labels.

USGS Astrogeology DOI `10.5066/P9J72921` was accessed read-only via ScienceBase metadata and an unauthenticated public ArcGIS FeatureServer. The currently returned single point layer contained **4 volcanic points**, all **4/4 missing a populated `AnalogBody`**, with one geometry/Lat-Lon attribute discrepancy >100 m: **Baugur 3,534.10 m** (maximum). Raw GeoJSON SHA-256 `0d0b61a5663f3cb2c00de5a02dfb6bf4599195a4dd28d81514af4d52351f0f1e`. Embedded source URL token parameters were redacted; no token used. Exact-head Actions E227 passed and uploaded raw receipt and source-QC outputs. See `research/E227_USGS_ANALOGUE_LABEL_ACCESS_20261024.md` and draft PR #16.

**Falsification:** This accessible USGS point service **cannot by itself supply Moon/Mars known-site labels or independent negative controls**. The coordinate disagreement is an unresolved source ambiguity, not proof which coordinate is correct. Do not treat the NASA gallery as a binary similarity benchmark.

**Claims:** official-source metadata and four real points SUPPORTED; source missingness/disagreement SUPPORTED; cross-body similarity NOT YET PROVEN; E001 NOT YET MEASURED; novel discovery, local advantage, challenge superiority NOT YET PROVEN.

**Next:** Seek explicit site-to-target geological analogue pairs with validated coordinates/process and independent negative controls. Attempt E001 only with compatible measured descriptors. Re-rank all official challenge statements after 28 Oct; no competition solution build before event.

## 2026-10-25: E242 real Earth sampling-density falsification

**Executed, not merely proposed.** [Read-only exact-head workflow 40151130273](https://github.com/stoicsatvik/NASA/actions/runs/40151130273) downloaded two public Mapzen Skadi SRTM-derived Earth tiles and compared 30-km support windows at Western Ghats and Ladakh leads. The initial workflow [40151021226](https://github.com/stoicsatvik/NASA/actions/runs/40151021226) failed because E214's geometry helper deliberately caps windows at 20 km; E242 added an independently validated 30-km helper without weakening E214. Five deterministic synthetic controls and inherited tests passed.

High-resolution plane-detrended relief SD was 144.09 m (Ghats) and 436.64 m (Ladakh). Under idealized **2×2 cell averaging**, the same descriptor fell to **5.3% and 26.0%** of the high-resolution reference; under **4×4 averaging**, to **36.2% and 69.5%**. Sixteen coarse point-sampling phases per grid also produced wide min/max ranges, including overestimates. The 2×2 planar-fit residual has only one degree of freedom; this is partly an **estimator identifiability failure**, not proof of actual instrument smoothing. The study does NOT emulate LOLA/MOLA point-spread functions.

Provenance, source SHA-256s, full numerical receipt and limitations: `research/results/e242_real_earth_sampling_aliasing_20261025.json` and `research/E242_EARTH_SAMPLING_ALIASING_20261025.md`. No raw DEMs, field observations or invented analogue labels committed.

**Claim states:** real Earth sampling-density sensitivity SUPPORTED for these two sites and this descriptor; physically comparable Earth/Moon/Mars similarity NOT YET PROVEN; **E001 known-site recovery NOT YET MEASURED**; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; planetary challenge superiority NOT YET PROVEN.

**Next:** avoid treating 2×2 Mars, 4×4 Moon and dense Earth roughness as comparable. Test instrument-aware common spatial-frequency descriptors, obtain independently sourced positive/negative geological labels, and attempt blinded E001. Re-rank all 14 official challenges when full statements arrive on October 28.


## 2026-10-25: E243 exact Earth sampling-phase rank reversal

Isolated research branch `foundry/e243-earth-rank-phase-stress-20261025`, draft PR #18. E242's same two source-fingerprinted real 30-km Earth DEM patches were compared at 2×2, 4×4, 8×8 and 16×16, with 16 phase registrations per site and all 256 independent cross-site phase combinations per grid. [Exact-head workflow 40155160144](https://github.com/stoicsatvik/NASA/actions/runs/40155160144) **SUCCESS (69 tests)**, numerical artifact `12584127859`. The dense-resolution relief ranking (Ladakh above Western Ghats) **reversed in 27/256** independent phase combinations for the **2×2 separately plane-detrended** metric, versus **0/256** for 4×4/8×8/16×16. A raw elevation-range alternative had 0/256 reversals at every grid but includes broad-scale slope, so is not an equivalent roughness feature. The 27/256 ratio is a finite analyst-chosen scenario fraction, **not an empirical probability**.

Mathematical control: the 2×2 planar-detrended population SD is exactly `|z00-z01-z10+z11|/4`; it retains only one checkerboard interaction degree of freedom and can vanish on arbitrarily steep planar surfaces. This exposes a **representation identifiability failure** for 2×2 roughness. Details: `research/E243_EARTH_RANK_PHASE_STRESS_20261025.md`. Do not promote this Earth-only finding to a LOLA/MOLA instrument claim. **E001 NOT YET MEASURED; cross-body similarity NOT YET PROVEN; novel discovery NOT YET PROVEN; challenge superiority NOT YET PROVEN.** Next: physically comparable common-band descriptors and independently established positive/negative geological labels, not UI.


## 2026-10-25: E247 common physical-lag terrain descriptor (Earth-only)

On top of E243, an independent 15-km-lag RMS elevation-contrast descriptor was tested against the same two SHA-256-fingerprinted public Earth terrain windows. At 2x2, combined RMS had **0/256** independent-phase site-rank reversals versus E243 plane-detrended relief SD **27/256**; east-west RMS still reversed **5/256**. At 4x4, 8x8 and 16x16, all three new metrics had 0/256 reversals. Exact-head Actions 40162430995 passed **74 tests** and produced numerical artifact 12587210698. This is finite Earth-only diagnostic evidence, NOT a measured planetary sensor error probability or validated analogue retrieval. The contrast includes broad slope and only four directional pairs at 2x2. See `research/E247_COMMON_LAG_TERRAIN_20261025.md`.

**Decision:** The E243 ranking instability is descriptor-dependent, but the new apparently stable descriptor is NOT YET PROVEN geologically discriminative or transferable across instruments. E001 remains NOT YET MEASURED; cross-body similarity, novel discovery, local validation advantage and challenge superiority remain NOT YET PROVEN. Highest-EV next step: independent geological labels, actual instrument response/QC, and blinded known-site recovery, not further two-site feature tuning.


## 2026-10-25: E258 synthetic planar-slope nuisance on real Earth terrain

Two SHA-256-gated real Earth DEM windows (Western Ghats and Ladakh leads), 48 predeclared synthetic planar tilts (2 sites × 6 slopes × 4 directions), 256 independent phase comparisons at each of 2×2/4×4/8×8/16×16. Exact-head CI [40185139599](https://github.com/stoicsatvik/NASA/actions/runs/40185139599) passed 78 tests and emitted [artifact 12595447715](https://github.com/stoicsatvik/NASA/actions/runs/40185139599/artifacts/12595447715). Six of 48 synthetic-tilt configurations yielded at least one 2×2 rank reversal (140/12,288 total artificial comparisons), while zero dense, 4×4, 8×8 or 16×16 configurations reversed. Plane-detrended relief was unchanged. This demonstrates slope-nuisance sensitivity of E247's combined contrast, **not** an empirical sensor error rate or a planetary similarity score. See `research/E258_SLOPE_NUISANCE_FALSIFICATION_20261025.md`.

**Claims:** Earth-only descriptor sensitivity SUPPORTED; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge superiority NOT YET PROVEN. **Next:** stop two-site descriptor tuning; obtain independent geological positive/negative labels and run blinded E001 with physically comparable observables.


## 2026-10-26: E273 real LOLA sampling-support falsification

Read-only [Actions 40235733739](https://github.com/stoicsatvik/NASA/actions/runs/40235733739) succeeded (83/83 tests), using source-fingerprinted real NASA SVS LOLA-derived 4ppd lunar TIFF and official MOLA MEGT/MEGC 4ppd rasters. The median within-tile lunar elevation SD **fell 37.23%** when 4×4 lunar patches were reduced to four 2×2 spatial block means, while the approximately equal-distance native MOLA 2×2 support was unchanged. Moon/Mars median roughness contrast shifted **5.99167 → 3.76077**; only **638/720** native top-decile lunar windows survived aggregation. See `research/E273_LOLA_SAMPLING_SUPPORT_20261026.md` and workflow artifact 12615070896.

**Interpretation:** equal physical tile width does not harmonize measurement sampling. Spatial block means are a synthetic aggregation operator, not a measured instrument point-spread function. This is a **real-data representation sensitivity result**, NOT cross-body similarity, known-site recovery or analogue discovery.

**Claim states:** real lunar/Mars sampling-support sensitivity SUPPORTED; E001 known-site recovery NOT YET MEASURED; cross-body similarity NOT YET PROVEN; novel analogue discovery NOT YET PROVEN; local field advantage NOT YET PROVEN; challenge superiority NOT YET PROVEN.

**Next gate:** independently labelled analogue positives and negatives plus source-grounded observation geometry. Do not continue optimizing two unvalidated Earth leads. Reassess all 14 challenge statements when complete resources are released October 28; no pre-event competition solution work.

## 2026-10-26 E291: first real Diviner thermal-anomaly sample

On isolated `foundry/e291-diviner-thermal-source-access-20261026`, draft PR #22, official PDS GDR_L3 `DGDR_STN_AVG_CYL_032` metadata was verified and three 23,040-byte HTTP 206 equatorial/midlatitude rows were ingested, **not** the entire 88 MB raster. Source is a **nighttime regolith temperature deviation in K** (DN × 0.02, missing DN −32768), **not** absolute temperature or THEMIS thermal inertia. Valid cells at approx +40°, 0°, −40°: **10,920/11,520; 9,547/11,520; 10,812/11,520**. The 0° row has 1,973 missing cells versus 600/708 in the two other sampled rows. These are three descriptive rows, **not global coverage**. Exact-head [CI 40287923992](https://github.com/stoicsatvik/NASA/actions/runs/40287923992) SUCCESS with four deterministic controls and real PDS byte ranges; final documentation-head CI requires separate verification. Full hashes, source/units and limitations in `research/E291_DIVINER_THERMAL_SOURCE_GATE_20261026.md`.

Two separate UCLA Level 4 `.xyz` sources failed TLS chain verification on the runner; **no TLS bypass** and no false ingestion claim. Alternative official PDS source worked.

**Claim:** PDS Diviner STN bounded real-source ingestion SUPPORTED; cross-body thermophysical similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel discovery, local field advantage and challenge superiority NOT YET PROVEN. Next: quantitative THEMIS and legitimate Earth thermal observables with physically justified calibration and masks; independently labelled E001 recovery before UX.


## 2026-10-26: E293 real Diviner STN spatial-missingness null

Three source-hash-verified genuine PDS STN rows (11,520 cells each) were tested against 199 fixed-count seeded longitude permutations. Observed longest circular missing runs were 9/9/9 pixels versus permutation maxima 4/8/6; observed maximum missing pixels in any circular 128-pixel window were 22/54/28 versus null maxima 20/42/22. Each comparison reached Monte Carlo resolution floor p=0.005. Equatorial row-wide missingness 17.127% contrasted with local maximum 42.188%. **REJECTED:** longitude missingness exchangeability under the simplistic fixed-count null for these three rows. **SUPPORTED:** locally clustered missing pixels requiring candidate-window coverage QC. No physical missingness mechanism or global inference established. See `research/E293_DIVINER_SPATIAL_MISSINGNESS_20261026.md`, exact-head Actions 40295290708 and artifact 12637609079. E001 NOT YET MEASURED; cross-body similarity, novel discovery, local validation advantage and challenge superiority NOT YET PROVEN. Next: independently labelled analogues and physically comparable THEMIS/Earth observations, not more single-instrument null scaffolding.


## 2026-10-26 E295: reject visual THEMIS mosaics for quantitative thermal comparison

Official USGS documentation explicitly says the global nighttime THEMIS mosaic is visually stretched and blended, **not** a calibrated Kelvin raster. E295's strictly monotone synthetic display transform reverses a nearest-neighbor ranking (physical 5 K vs 15 K; displayed 90 vs 10 arbitrary units), proving such rankings are not invariant to unknown display stretches. A fail-closed source gate distinguishes projected IR-PBT **brightness temperature** from Diviner STN **nighttime temperature deviation**, despite both being in K. See `research/E295_THEMIS_THERMAL_ADMISSIBILITY_20261026.md`, `research/e295_thermal_product_admissibility.py` and six deterministic tests.

**Claim:** source-product exclusion SUPPORTED by USGS metadata; mathematical counterexample PROVEN for synthetic anchors. **No new real THEMIS measurements**, no physically harmonized cross-body descriptors, no E001. E001 NOT YET MEASURED; cross-body similarity, novel analogue discovery, local validation advantage and challenge superiority NOT YET PROVEN. Next: read genuine calibrated IR-PBT observation labels/bytes with band/time/projection/mask, independently labelled analogue recovery; revisit 14 full challenge statements on 28 October. No pre-event competition solution.


## 2026-10-26 E305: published THEMIS local-time nuisance audit

**Executed exploratory secondary-source experiment**, not new raw PDS ingestion. Manually transcribed 24 real THEMIS-derived Bagnold Dunes temperatures from Ahern et al. (2021), DOI 10.1029/2020JE006713 Table 4; 13 early-morning and 11 evening observations. Group means **189.709769 K** and **209.095727 K** (19.385958 K difference). Maximum-cardinality one-to-one solar-longitude matching at ±10° yielded **7/7 warmer evening observations**, mean +21.318143 K; ±5°/±15°/±20° sensitivity yielded 5/5, 8/8 and 9/9 positive signs. This is a finite, nonrandomized, exploratory within-site source audit, **not** a causal estimate: different Mars years, atmospheric opacity and acquisition schedules remain confounded. Manual transcription hash does not authenticate publisher pixels. See `research/E305_PUBLISHED_THEMIS_TIME_CONFOUNDING_20261026.md`, `research/e305_published_themis_time_audit.py` and branch-scoped Actions.

**SUPPORTED:** strong observational nuisance across local-time groups in this published sample. **NOT YET PROVEN:** raw PBT pixel verification, physical harmonization, Moon/Mars/Earth analogue similarity, local validation, novel discovery and challenge superiority. **E001 known-site recovery NOT YET MEASURED.** Next: genuine PBT pixels/labels and independently sourced positive/negative analogue labels, not UI. Reassess challenge ranking October 28.


## 2026-10-27 E317: independent USGS PAAD Earth dune-site ingestion

**Real data access achieved.** Isolated draft PR #27 ingested a source-fingerprinted **33,976-byte** USGS PAAD public CSV (DOI `10.5066/P9IFVZEX`; SHA-256 `5be67b4da584987d9ce5207f2ee3c90b5b3b5849469461847111eaab5aafcecd`) in read-only GitHub Actions. **45 rows, 45 distinct named sites, 45/45 numeric coordinate pairs in valid ranges**, 45/45 dune type and reference entries, 44/45 sand composition/source and elevation entries, 33/45 areal coverage entries. Exact-head CI #40433261440 SUCCESS, seven synthetic controls; receipt artifact #12703186381. The raw CSV is not committed. Details: `research/E317_USGS_PAAD_EARTH_DUNE_SOURCE_20261027.md`.

**Evidence change:** a previously missing *independently curated Earth-side dune analogue site catalog* is now legitimately accessible and machine-readable. It does NOT supply matched Mars/Moon targets, independently verified geodetic accuracy, negatives or a validated shared dune-type codebook. E001 known-analogue recovery **NOT YET MEASURED**; cross-body similarity, novel analogue discovery, local validation advantage and challenge superiority **NOT YET PROVEN**.

**Next:** inspect PAAD codebook and independent USGS Mars Global Digital Dune Database labels; attempt a small, predeclared, physically comparable aeolian cross-body baseline only if common observable/target labels are defensible. Otherwise preserve a negative feasibility finding. Reassess all 14 official challenges after full statements on 28 Oct; do not lock the planetary track or build the competition submission early.


## 2026-10-27 E318: independent real Mars dune-source ingestion

Official USGS OFR 2018-1164 ZIP (2,982,330 bytes, SHA-256 `92771c23cfa4a64dfcc38f5ad29de00adfa41b9f321d3665beb2112eefe3485e`) was downloaded read-only and **seven real Mars worksheet profiles** were parsed from equatorial/south-polar XLSX workbooks. The 2020 ScienceBase merged-release root returned no eligible directly attached files, so the 2018 publication ZIP supplied the actual evidence. Two malformed macOS resource-fork pseudo-workbooks initially caused a parse failure; E318 now preserves these negative controls and profiles the valid tables. Exact numerical receipt: [Actions #40439550237](https://github.com/stoicsatvik/NASA/actions/runs/40439550237), 12 synthetic controls PASS, real download SUCCESS; artifact #12706135886.

**Scientific boundary:** MGD3 2018 summary sheets contain source-reported mineral/thermal/stability variables, not automatically harmonized PAAD Earth dune-type labels. Sheet row totals are not distinct sites, and mapped Mars dune positives do not provide verified negatives. **E001 NOT YET MEASURED**, cross-body similarity NOT YET PROVEN, novel discovery NOT YET PROVEN, local validation advantage NOT YET PROVEN, challenge superiority NOT YET PROVEN. Full source and limitations: `research/E318_USGS_MGD3_REAL_MARS_SOURCE_20261027.md`.

**Next:** obtain both official dune-type codebooks and independent positive/negative matched-site labels; test shared morphology descriptors with transparent random/majority baselines and held-out sites. Re-rank all fourteen 2026 challenges after full statements on October 28. No UI polishing or invented field observations.


## 2026-10-27: E319 real PAAD↔Mars dune-codebook lexical gate

Isolated research draft PR #29, `foundry/e319-paad-mars-codebook-overlap-20261027`. Exact-head read-only [Actions #40444987424](https://github.com/stoicsatvik/NASA/actions/runs/40444987424) SUCCESS: **14 synthetic/inherited tests passed** and the 45-site real PAAD CSV was independently re-downloaded with the E317 frozen SHA-256. Comparison against **Hayward et al. (2007), Table 1** source-documented Mars morphology codes (SS,D,B,Bd,T,L,S,U) was strictly case-sensitive and lexical.

**Measured:** 21/45 PAAD sites have one dune-type token; 24/45 are multi-token. Only **8/45** have every raw token present in the published Mars code set; **21/45** have partial overlap, and **16/45** have no overlap. Nine distinct unsupported tokens were preserved (C,G,MG,P,R,RP,TIB,TR,WB), not guessed. Full source receipt and limitations: `research/E319_PAAD_MARS_CODEBOOK_GATE_20261027.md`.

**Falsification:** direct PAAD↔Mars string-code joining is **REJECTED AS A VALIDATED BENCHMARK**. Exact code overlap is not semantic equivalence, and the 2018 Mars workbook data are mineral/thermal rather than verified linked 2007 morphology labels. No known-positive Earth↔Mars matched pairs or independent negatives exist in this experiment. This does **not** falsify aeolian analogy as a physical phenomenon.

**Claim states unchanged:** E001 known-site recovery **NOT YET MEASURED**; cross-body similarity, novel analogue discovery, local field-validation advantage and challenge-selection superiority **NOT YET PROVEN**. Next: find the independent PAAD codebook and actual MGD3 dune-field morphology table with provenance, establish comparable physical descriptors and independent labels, or pivot the retrieval benchmark. Re-rank all 14 official challenges when full statements arrive 28 Oct. No competition solution work or submission.

## 2026-10-27: E320 real PAAD geographic holdout-dependence audit

Official SHA-256-pinned USGS PAAD 45-site CSV was independently re-downloaded in exact-head read-only CI #40450688890 (SUCCESS; 21 tests). Among 990 unordered site pairs, 10 are within 25 km, 12 within 50 km and 19 within 100 km by spherical great-circle distance. Connected proximity groups contain **9/45** separately named sites at 25 km and **16/45** at 100 km; nearest named pair is **6.824912 km**. Full receipt and interpretation: `research/E320_PAAD_SPATIAL_HOLDOUT_20261027.md`; draft PR #30.

**Decision:** Site-name-only leave-one-out is **NOT GUARANTEED geographically independent** for the PAAD catalog. This is an audit of source-reported coordinates, not independent geodetic verification, same-geology proof or cross-body similarity. PAAD is still positive-only; do not infer negative sites or label equivalence. E001 known-site recovery **NOT YET MEASURED**; cross-body similarity, novel discovery, local validation advantage and challenge superiority **NOT YET PROVEN**.

**Next:** After independent cross-body morphology/physical descriptor and positive/negative label harmonization, compare name-only versus spatial-group held-out performance and preserve failures. Reassess all 14 full official challenge statements when published October 28. No UI polish or competition submission.

## 2026-10-27 E323: real PAAD raw-label spatial dependence and null

**Real source-pinned Earth-only label experiment:** 45 USGS PAAD sites and 13 raw dune-type tokens; 999 whole-site token-set permutations at seed 323. Exact-head read-only [Actions #40467944124](https://github.com/stoicsatvik/NASA/actions/runs/40467944124) SUCCESS, 28 tests passed; [artifact #12717605849](https://github.com/stoicsatvik/NASA/actions/runs/40467944124/artifacts/12717605849). Name-only nearest-site Jaccard **0.350053**, upper-tail permutation p **0.001**. Component-blocked 25/50 km Jaccard **0.355608** (name-only minus blocked **-0.005556**, p **0.572**), whereas 100 km blocked Jaccard **0.235238** (difference **+0.114815**, p **0.006**). All 45 sites had eligible outside-component neighbors. **SUPPORTED:** spatial structure in source-reported Earth *raw lexical token* agreement under the declared exchangeability null; 100 km blocking changes this within-catalog overlap. **REJECTED:** the generic claim that every blocking threshold lowers overlap (25/50 km do not). No causal/geological inference, codebook harmonization or external validation. Full evidence: `research/E323_PAAD_SPATIAL_LABEL_NULL_20261027.md`.

**Scientific boundaries unchanged:** E001 known-site recovery **NOT YET MEASURED**; cross-body similarity, novel analogue discovery, local field advantage and challenge-selection superiority **NOT YET PROVEN**. Next: authoritative PAAD/MGD3 codebooks and physically comparable independent positives/negatives, then blinded spatial-blocked recovery with transparent baselines. Re-rank all official 2026 challenge statements after October 28. No competition solution or submission.


## 2026-10-27 E325: climate-conditioned real PAAD spatial-label null

Source-fingerprinted 45-site USGS PAAD experiment re-ran E323 raw-token nearest-site Jaccard (0.35005291) and 100 km component-block drop (0.11481481) with 999 permutations within fixed source climate strata. Exact 10 source-description groups (40/45 permutable, 5 singleton) yielded one-sided p=0.001 for nearest agreement and p=0.004 for the 100 km drop. Explicit analyst descriptors (ARID 37, EQUATORIAL 2, POLAR 2, SNOW 4) yielded p=0.001 and p=0.002 respectively. At 25/50 km the drop remains negative (−0.00555556) with descriptor-group p=0.442. Strict alphanumeric Köppen-family parsing correctly rejected all 45 free-text source descriptions, so its "family" null is NOT an independent climate adjustment. This failure was preserved.

[Exact-head CI 40474399735](https://github.com/stoicsatvik/NASA/actions/runs/40474399735) SUCCESS, 28 tests; source fingerprint verified; [artifact 12720186077](https://github.com/stoicsatvik/NASA/actions/runs/40474399735/artifacts/12720186077). Full limitations in research/E325_PAAD_CLIMATE_CONDITIONED_NULL_20261027.md, draft PR #32.

**Claim:** Earth-only spatial raw-token association survives two specified conditional permutation nulls, SUPPORTED for this dataset/analysis. Causal geology, independent validation, Earth–Mars comparability and challenge superiority NOT YET PROVEN. E001 known-site recovery NOT YET MEASURED. Next: authoritative morphology codebooks, matched positive/negative cross-body descriptors and blinded spatial holdouts, plus full challenge reassessment 28 October. No competition submission, fieldwork, outreach or main merge.


## 2026-10-27 E326: independent terrestrial analogue inventory source falsification

Hunter (2020) USGS `Known Terrestrial Analog Sites for Planetary Science` DOI 10.5066/P9J72921 was ingested through anonymous public ArcGIS FeatureServer reads. ScienceBase metadata itself has no downloadable tabular files (first negative access-path result). The linked ArcGIS URL contained a query credential; the research code discarded the entire query string and did not use any credential. Exact-head CI #40482249632 SUCCESS, 16 tests, machine-readable artifact #12723207792.

**Measured source result:** exactly **4 public feature records**, all `AnalogType=Volcanic`; `AnalogBody` missing/null-like in 4/4; geometry present 4/4 but independent geodetic accuracy not verified. No dune positive/negative labels. This is an **independent publication**, not a scientifically independent dune recovery cohort, and does not validate the 45-site PAAD raw-code association. See `research/E326_INDEPENDENT_USGS_ANALOG_INVENTORY_20261027.md`.

**Decision:** E001 known-site recovery NOT YET MEASURED; cross-body similarity, novel analogue discovery, local validation advantage, and planetary challenge superiority NOT YET PROVEN. Do not relabel these four volcanic sites as dune negatives or Mars matches. Next: independently defined cross-body morphology and true controls, plus full official challenge statement comparison after 28 Oct. No fieldwork, spending, deployment, outreach, or submission.


## 2026-10-27 E330: competition pre-event rule/provenance gate

Primary official NASA Space Apps local-event guidance (Santiago 2026) explicitly distinguishes allowed learning/preparation from prohibited development of the solution intended for submission before 14–15 November. Rewari's official event page also describes building during the event. This is **local guidance, not independently verified global-rule text**; final global/selected-local terms must be checked. The Ajmer event states 18+ eligibility, but that is **not** a global age restriction. The existing NASA repo contains timestamped pre-event research; do not present it as 48-hour competition work, disguise its provenance, or assume reuse is allowed. Conservative gate: no competition-specific solution development until the event starts. Independent scientific research and general skill preparation must be kept clearly separate. See `research/E330_SPACE_APPS_PRE_EVENT_ELIGIBILITY_GATE_20261027.md`.

E001 known-site recovery **NOT YET MEASURED**; cross-body similarity, novel analogue discovery, local validation advantage and challenge superiority **NOT YET PROVEN**. Next: independently verify official global and selected-local pre-work/under-18 rules, then re-rank all official challenge statements after 28 October. No registration, outreach, submission, deployment or main merge.


## 2026-10-28 E340: independent published Ibex/Gale morphology mismatch

New primary scientific source: Bretzfelder et al. (2026), *Aeolian Research* 75, DOI 10.1016/j.aeolia.2026.101032, NASA NTRS record 20260000452. Their accepted manuscript reports **0.71 m** mean wavelength for measured Ibex (Earth) large ripples versus **2.20 m** for two Gale crater (Mars) example bedforms: Mars/Earth ratio **3.09859155** and difference **1.49 m**. The authors explain longer Martian wavelengths in a different atmospheric regime while noting similarities in ripple height and grain armoring. Earth LiDAR measurements were reported accurate to ±2 cm, but this is **not a confidence interval for the mean**; the Mars mean uncertainty was not supplied for this audit. An illustrative Earth-only ±2 cm perturbation gives conditional ratio 3.01370–3.18841, **not** a scientific uncertainty interval. Deterministic decimal arithmetic and three tests passed locally; CI exact-head status must be checked separately. Source, script, tests, receipt workflow and limitations: `research/E340_IBEX_GALE_PUBLISHED_MORPHOMETRY_GATE_20261028.md`.

**Decision:** raw wavelength equality as a necessary analogue condition is REJECTED for this published exemplar. This is a source-supported positive *case study*, not an independent blinded recovery cohort; Earth and Mars sampling differ and no negatives are provided. **E001 known-site recovery NOT YET MEASURED; cross-body similarity, novel discovery, local validation advantage, and challenge superiority NOT YET PROVEN.** Next: independently labeled, untouched matched morphology and true controls with instrument uncertainties; do not leak this already-read pair into a holdout. Competition-specific solution development remains gated until the event.


## 2026-10-28: E369 real public Earth-only AUC falsification

Read-only independent reproduction of a **single-feature control baseline** on the pinned public TerraNova catalogue and three source-derived Earth rasters (vegetation, precipitation, land fraction). All four downloaded source blobs passed Git-blob ID, size and SHA-256 checks; all 20 catalogue controls were scorable. [Exact-head CI 40737403313](https://github.com/stoicsatvik/NASA/actions/runs/40737403313) SUCCESS, with [receipt 12837917264](https://github.com/stoicsatvik/NASA/actions/runs/40737403313/artifacts/12837917264).

**Measured:** using only **negative vegetation**, the original editorial humid/vegetated negative controls are perfectly separated from Mars environment positives (5/5 versus 8 negatives), Moon environment positives (3/3 versus 8) and cold-polar tagged positives (3/3 versus 8): **AUC 1.000** for all three subsets. Negative precipitation AUC: Mars 1.000, Moon 0.875, cold-polar 1.000. Finite-only versus land-fraction >=0.5 masks do not change these results. This is an **Earth-only catalog negative control**, not an independent reproduction of TerraNova's five-target model AUC, not a blinded benchmark, and not physical Earth–Mars recovery. The editorial-negative AUC alone is insufficient evidence of cross-body analogue validity.

**Claim states:** source-pinned Earth-only AUC SUPPORTED; E001 known-site recovery NOT YET MEASURED; cross-body similarity, novel analogue discovery, local validation advantage and challenge superiority NOT YET PROVEN. Full report: `research/E369_SINGLE_FEATURE_AUC_FALSIFICATION_20261028.md`. Next high-EV gate is independent matched physical Earth/Moon/Mars descriptors with legitimate hard positives/negatives and spatially blocked E001; do not manufacture labels or build competition-specific solutions before permitted event time.


## 2026-10-29 E397: exact geography-only editorial-control null

Pinned public Earth analogue catalogue (Yakiyo/terra-nova commit f6c53ba5, verified Git blob d75240ce) contains 12 source-labelled analogue positives and eight editorial humid/vegetated negatives. Five simple geographic-only features were evaluated with exact AUC and exhaustive 125,970 label allocations. Absolute latitude AUC=0.7604167, nominal one-sided p=0.028689; westward longitude AUC=0.75, nominal p=0.034548. **Max-of-five familywise exact p=0.131357**: apparent geographic separation exists, but the specified family does not reject conditional label exchangeability at 5%. Source-selected editorial negatives are not independent scientific labels, and the null's exchangeability assumption is hypothetical. Independent Python and JavaScript enumeration agreed. Exact-head GitHub Actions #40922637245 SUCCESS, four offline tests, pinned-source deterministic repeat and artifact #12919006534. See research/E397_GEOGRAPHIC_CONTROL_NULL_20261029.md, stacked draft PR #41.

**Claim states:** geographic-source confounding CANDIDATE / NOT PROVEN; E001 known-site recovery NOT YET MEASURED; cross-body similarity, novel discovery, local validation advantage and challenge-selection superiority NOT YET PROVEN. **Next:** independent identity-disjoint analogue/non-analogue labels and spatially blocked physically matched Earth/Moon/Mars baselines; no UI work or pre-event competition solution development.


## 2026-10-30 E411: challenge-index mismatch and validation-axis decision gate

The 2026 HackAthlone local-event index lists 14 challenges. E193's historical score table matches 13 canonical titles after short-name normalization but contains stale `CLPS lunar browser` instead of the official `Lunar Landing Site Navigator`. The historical 14-entry ranking is therefore **NOT an exhaustive current official challenge ranking**; no navigator rating was silently inherited. Frozen E193 arithmetic still gives planetary analogues 4.59 (5th) versus MODIS/VIIRS 5.43. Removing the validation axis alone and renormalizing other weights raises planetary analogues to 1st; none of the other six single-axis removals does. With all other historical assumptions fixed, the analogue validation rating would need to rise from 4 to 8.2 merely to tie MODIS/VIIRS. This is **analyst-assumption sensitivity, NOT empirical win probability**. Offline four-test exact-head CI and deterministic receipt are in `research/E411_CHALLENGE_VALIDATION_ABLATION_20261030.md`.

The official Space Apps legal page specifies parent/guardian registration and continuous accompaniment for under-18 participants; verify selected local-event implementation. All 14 full official challenge statements/resources were not independently fetched (several direct requests failed HTTP 502). No competition solution was developed. **E001 known-site recovery NOT YET MEASURED; cross-body similarity, novel analogue discovery, local field advantage and challenge superiority NOT YET PROVEN.** Next: independently assess the actual lunar navigator and full statements, test empirical MODIS/Trend validation costs, and execute a legitimate held-out E001 when physical labels exist.


## 2026-10-30 E416: lunar challenge title mismatch does not prove different task

Fresh search-indexed **official Space Apps** pages revealed that `Lunar Landing Site Navigator` and `CLPS Lunar Mission Browser` describe the same Moon south-pole Sun/Earth horizon, landing-date/site, solar power and communication-window task features. The official navigator page uses the former name, while multiple official-platform team pages use the latter challenge label with the same platform-rendered task description. A third-party local event listing includes both names, introducing possible alias/duplicate ambiguity. Direct full-page retrieval of official pages returned HTTP 502; canonical challenge IDs and resource-list equality are **NOT VERIFIED**. See `research/E416_LUNAR_CHALLENGE_ALIAS_AUDIT_20261030.md`.

**Correction to E411 interpretation:** 13/14 *literal title* coverage SUPPORTED, but the stronger conclusion that E193's `CLPS lunar browser` is a substantively *different* challenge is **NOT SUPPORTED** by this source evidence. Treat lunar identity as CANDIDATE ALIAS / UNRESOLVED, not a proven stale task. E193's complete semantic coverage and lunar rating remain NOT YET PROVEN. E411 numerical sensitivity remains valid as arithmetic on frozen subjective ratings.

**Next:** verify canonical IDs/redirects, full statements and resource links before relabeling; independently validate competing challenges and E001 physical analogue recovery. E001 known-site recovery NOT YET MEASURED; cross-body similarity, novel discovery, local validation advantage and challenge-selection superiority NOT YET PROVEN. No competition-specific solution developed.


## 2026-10-30 E418: editorial negative deletion sensitivity

- Branch `research/e418-geographic-negative-deletion-20261030`, stacked on E416 draft PR #43.
- Pinned 12-positive/8-editorial-negative TerraNova source from E397. Deleting each negative in turn leaves 12/7 sites; exact C(19,12)=50,388 label allocations per deletion, max over the same five geographic scores.
- Measured max geographic AUC range 0.726190–0.821429; eight exact conditional max-of-five p values range 0.052671–0.258752, none below 0.05. This is a **source-selection sensitivity**, not a randomized test, independent label set or cross-body model.
- Three independent local implementations (two JavaScript, one Python) agreed on all eight exceedance counts; the committed Python source and offline tests were **not** executed under the repository runner. GitHub Actions quota reported exhausted; no paid CI triggered.
- **SUPPORTED:** editorial-control deletion sensitivity. **NOT YET MEASURED:** E001 known-site recovery. **NOT YET PROVEN:** cross-body similarity, novel discovery, local advantage, planetary challenge superiority.
- Next: independent physically characterized analogue pairs and credible hard negatives, frozen site-disjoint/spatial-blocked split and random/Euclidean/physically weighted controls. Avoid further circular tuning on editorial labels. See `research/E418_GEOGRAPHIC_NEGATIVE_DELETION_20261030.md`.


## 2026-10-30 E425: NASA official illustrated analogue labels are not blind E001 ground truth

Official NASA Science [Planetary Analog Explorer](https://science.nasa.gov/solar-system/analog-explorer/) provides 11 independently published **curated analogy leads** (9 Moon/Mars, 2 Venus/Enceladus), but zero independently sampled hard negatives and no complete paired physical descriptor vectors/georeferenced blind cohort. NASA's Vikursundar/Mars illustration explicitly shows a tenfold ridge-scale difference; raw equality is not a necessary condition for its illustrated analogy. Source-transcribed JSON and limitations: `research/data/e425_nasa_editorial_analogue_pairs_20261030.json` and `research/E425_NASA_OFFICIAL_ANALOGUE_LABEL_AUDIT_20261030.md`. This is source evidence, **not a new E001 numerical test**. Known-site recovery NOT YET MEASURED; cross-body similarity, novel analogue discovery, local validation advantage and challenge superiority NOT YET PROVEN. Next: independent matched geospatial/instrument descriptors, hard negatives and identity-disjoint held-out evaluation; no pre-event competition solution development.

## 2026-10-31: E436 E430 exact three-site label-null and scaler-leakage audit

Using only the six real-derived E214 Earth summary records, 20 retrospective distance/feature-ablation configurations were evaluated. The four-feature E430 2/3 same-site retrieval persists under pooled, catalog-only, other-site-only and log-ratio scaling, so pooling query features was not solely responsible for this specific outcome. The best of all 20 variants was still 2/3. Under six *artificial joint candidate-label permutations*, the single four-feature configuration has tail 2/6 and the best-of-20 has tail 4/6. These are combinatorial diagnostics, **not scientifically calibrated p-values**: three selected unvalidated leads, overlapping windows, no independent positives/negatives, no planetary measurements. A separately authored JavaScript calculation on the full source JSON reproduced all 20 configurations; five local Python source-equivalent tests passed. Exact committed-head CI remains pending. Research: `research/E436_EARTH_SELF_RETRIEVAL_LABEL_NULL_20261031.md`, script `research/e436_e430_permutation_null.py`.

**Claim states unchanged:** E001 known-site recovery NOT YET MEASURED; cross-body similarity NOT YET PROVEN; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge superiority NOT YET PROVEN. **Next:** stop optimizing these three Earth leads as a validation set; obtain independently labelled physically comparable Earth–Moon/Mars pairs and hard negatives, then run frozen random/Euclidean/physically weighted E001 with spatial holdouts. Reassess all official 2026 challenge statements. No competition solution development before the event.

## 2026-10-31 E446: real-data cross-body support falsification

Read-only analysis of existing real E212 LOLA/MOLA 4ppd and E214 Earth SRTM-derived receipts found all six 2/4-km Earth windows span <1 equatorial north-south pixel in both planetary products (Moon 7.58084 km/pixel; Mars 14.78948 km/pixel). A four-pixel-per-axis diagnostic would require ~30.323 km Moon / ~59.158 km Mars, changing the Earth support. Six local tests passed; independent JavaScript read of the full real receipts reproduced all six spans. New Python CLI on full remote receipts and exact-head CI not run. See `research/E446_REAL_DATA_SUPPORT_INCOMPATIBILITY_20261031.md` and draft PR #49. **Claim:** current 2/4-km site-scale E001 comparison with these coarse products REJECTED; real-data support mismatch SUPPORTED; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED. **Next:** obtain higher-resolution planetary coverage/instrument metadata or preregister larger matched Earth windows plus independent analogue labels. No pre-event competition solution developed.


## 2026-10-31 E452: real MOLA 16ppd partial resolution rescue

Source-pinned E210 MOLA MEG016 16ppd, E212 LOLA/MOLA 4ppd, and E214 Earth Skadi receipts were compared without inventing imagery or analogue labels. Mars 16ppd equatorial north-south pixel spacing is 3.69737 km; the three 4-km Earth windows now exceed **one** Mars pixel spacing (1.08185), but all three 2-km windows remain subpixel (0.54092). **0/6** Earth windows reach the declared four-pixel Mars16 or Moon4 diagnostic; Moon4 remains 7.58084 km/pixel. This partially rejects an across-all-available-Mars-products subpixel generalization, but does not establish matched relief support. MOLA global measured fraction 0.94553 is not per-site coverage. Seven local source-identical-fixture tests PASS, independent full-receipt JavaScript calculation confirms six rows; full Python CLI on remote receipts and exact-head CI NOT RUN. See `research/E452_MOLA16_RESOLUTION_RESCUE_20261031.md`.

**Claims:** support-resolution sensitivity SUPPORTED; E001 known-site recovery NOT YET MEASURED; cross-body similarity, novel analogue discovery, local validation advantage and challenge-selection superiority NOT YET PROVEN. **Next:** independently labelled pairs/hard negatives and instrument-aware higher-resolution per-site planetary data, or preregistered larger Earth support, then E001 random/Euclidean/physical baselines and nulls. No competition submission, fieldwork or UI work.
