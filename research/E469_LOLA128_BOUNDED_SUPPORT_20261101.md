# E469 | Independent LOLA 128ppd observed-bin support (bounded real-source experiment)

Date: 2026-11-01. **Status: REAL LOLA SOURCE EXECUTED.** Initial fail-closed label rejection and final successful source run are documented below; do not generalize beyond three nonrandom windows.

## Falsifiable question

Does the official lunar LDEC_128 count raster provide direct-observation support at three predeclared 9×9 locations? This is the lunar counterpart to E463's measured Mars MEGC128 counts. The count masks can establish **observed versus zero-count bins**, not independent effective resolution or Earth/Moon/Mars analogue recovery.

## Official sources and provenance

- NASA PDS Geosciences LRO LOLA GDR cylindrical IMG directory: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/img/
- `ldec_128.lbl` and `ldec_128.img`: gridded elevation observation counts, NOT the albedo-count `LDAC` product.
- `ldem_128.lbl` and `ldem_128.img`: lunar elevation data, whose DN and datum MUST NOT be naively concatenated with Mars MOLA topography.
- PDS ODE GDRDEC documentation: https://ode.rsl.wustl.edu/mercury/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20%28LRO%29/LOLA/GDR/GDRDEC.htm
- PDS ODE GDRDEM documentation: https://ode.rsl.wustl.edu/mars/pagehelp/Content/Missions_Instruments/LRO/LOLA/GDR/GDRDEM.htm

## Fixed experiment

Before reading lunar raster bytes, freeze longitude **45°E**, latitude **0.5°S, 20°S, 40°S**, and **9×9** windows. These are not known analogue sites. Source labels must pass geometry/type checks (23040×46080, 128ppd, signed or unsigned MSB 16-bit counts, 16-bit MSB elevations). Each sample fetch requests only nine contiguous raster rows and requires exact HTTP 206 Content-Range, no full multi-GB downloads.

`research/e469_lola128_bounded.mjs` records source-label SHA-256, each sampled count/elevation byte-range SHA-256, count>0 versus zero-count bins, and raw elevation DN extrema. The exact source outcome should be archived by `.github/workflows/e469_lola128_coverage.yml` as a machine-readable artifact. Six synthetic deterministic controls test label admission, product identity, range bounds and big-endian signed decoding.

## Important limitations and failure states

- Source HTTP 200 instead of 206 is **SOURCE ACCESS UNVERIFIED**, not zero observations. Do not download the full ~2.1GB file.
- The PDS label's latitude registration and row order must be independently confirmed before asserting precise geographic sample coordinates. Raster geometry alone does not prove orientation.
- Positive counts do not establish independent spatial resolution; tracks and interpolation can correlate samples.
- LOLA 128ppd has ~237m nominal north-south pixel spacing near the lunar equator, while Mars MOLA 128ppd has ~463m; matching ppd is NOT matching physical scale.
- Raw lunar elevation DN requires its own label scaling, offset and reference datum. The experiment does not claim physically comparable terrain descriptors.
- These 243 cells are nonrandom and cannot estimate global lunar coverage.
- No independent analogue labels, Earth matched descriptors, E001 retrieval, field observations or competition submission.

## Decision gate

If official ranges succeed, inspect the numerical receipt and label orientation, compare observed-bin fractions with E463 *only as descriptive instrument support*, then design physically matched windows and execute blinded known-site recovery with random/Euclidean/physical baselines. If ranges fail, preserve exact HTTP failure and pursue a legitimate independent PDS mirror or smaller LDEC product.

**Claim states:** Mars E463 measured-bin coverage SUPPORTED; lunar high-resolution coverage NOT YET MEASURED until actual source success; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge-selection superiority NOT YET PROVEN.

## 2026-11-01: Actual official lunar raster outcome

**Executed real data:** [GitHub Actions #41273612028](https://github.com/stoicsatvik/NASA/actions/runs/41273612028) completed **SUCCESS** at experiment head `6c10352805531d922fec107315f5648c133a41be`. All **8/8** deterministic offline Node controls passed; official count and elevation label requests and six exact HTTP 206 bounded row-range requests passed; artifact `13069334715` preserves the original machine-readable receipt. A checked normalized transcription is committed as `research/results/e469_lola128_real_data_20261101.json`.

| Preselected 45°E center | LOLA LDEC observed count>0 | Zero-count bins | Observed fraction | LDEM raw DN range |
| --- | ---: | ---: | ---: | ---: |
| 0.5°S | 18/81 | 63/81 | 22.22% | -3117 to -3091 |
| 20°S | 34/81 | 47/81 | 41.98% | -2010 to -1266 |
| 40°S | 80/81 | 1/81 | 98.77% | 943 to 2191 |
| **Nonrandom pooled** | **132/243** | **111/243** | **54.32%** | Not pooled |

The two official PDS3 labels both declare `SAMPLE_TYPE = LSB_INTEGER`, 16-bit little-endian signed samples, 23040×46080 pixels and 128 pixels/degree. The initial code mistakenly expected big-endian samples: [Actions #41273491100](https://github.com/stoicsatvik/NASA/actions/runs/41273491100) failed on the label gate; a diagnostic [Actions #41273568697](https://github.com/stoicsatvik/NASA/actions/runs/41273568697) exposed the actual `LSB_INTEGER` declaration. The code was corrected and additional little-endian tests were added. This failure is retained as evidence, not silently erased.

**Interpretation:** LOLA 128ppd count support is highly site-dependent across these three windows. The observed fractions differ from E463 MOLA 128ppd (40.74%, 18.52%, 46.91%), but the samples are on *different planets* and at different physical pixel scales. Lunar nominal equatorial spacing ≈236.90m versus Martian ≈463.08m, a 1.955× difference; 128ppd is not a physical matching criterion. Do not interpret these fractions as relative instrument quality, global coverage or analogue similarity.

**Remaining unknowns:** independently verify precise PDS pixel-registration/latitude orientation; normalize LDEM scaling/datum; quantify footprint/track correlation and effective resolution; obtain independent Earth known-analogue labels and E001 leave-one-site-out retrieval. The three windows are not established analogue locations. Cross-body similarity and challenge-selection superiority **NOT YET PROVEN**; E001 known-site recovery **NOT YET MEASURED**.
