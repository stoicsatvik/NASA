# E469 | Independent LOLA 128ppd observed-bin support (bounded real-source experiment)

Date: 2026-11-01. **Status: source probe implemented, remote real-data outcome PENDING.** Never report coverage percentages until exact-head source execution succeeds.

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
