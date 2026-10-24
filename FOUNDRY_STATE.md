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
