# E452 | Does real MOLA 16ppd rescue E446's 2/4-km Earth support? (31 October 2026)

## Question and frozen inputs

Before building E001 or a competition UI, does an already-ingested **real** higher-resolution Mars product change the E446 decision? No new imagery, site labels, field measurements, or competition solution were generated.

Read-only GitHub source receipts, all present on E446's parent:
- E210 NASA PDS MOLA MEG016 16 pixels/degree, `research/results/e210_mola_16ppd_real_data_20261024.json`, blob `f6db61a6f383d1d1f52b9840a88a284a042c5337`; elevation in metres above MOLA areoid, counts are ground returns/bin. Global measured-cell fraction 0.9455320457; equatorial ±16° tile mean observed fraction 0.9604753282 (not per-site coverage).
- E212 real MOLA 4ppd and LOLA-derived lunar 4ppd, `research/results/e212_lola_mola_real_data_20261024.json`, blob `e762981e424186d72b0604b82da266c6d2b4e5ba`. Equatorial north-south pixel spacing Mars 14.7894837491 km and Moon 7.5808376060 km. Lunar source is a derived visualization raster without shot-count mask.
- E214 Mapzen Skadi/SRTM-derived Earth windows, `research/results/e214_earth_skadi_real_data_20261024.json`, blob `ca557aa7ecef53796cfb01515a01cd96cc3291c3`. Three unvalidated research leads (Lonar, Western Ghats, Ladakh), each at 2 km and 4 km; Earth ~30.8875 m north-south sampling. Not official NASADEM and not analogue ground truth.

## Real-receipt sensitivity result

Mars 16ppd equatorial north-south spacing is **3.6973709373 km**, one quarter of the 4ppd Mars spacing. This is a metadata-derived sampling interval, not instrument effective resolution.

| Earth window | Moon 4ppd pixel spans | Mars 4ppd spans | Mars 16ppd spans |
|---|---:|---:|---:|
| 2 km (three sites) | 0.2638 | 0.1352 | **0.5409** |
| 4 km (three sites) | 0.5276 | 0.2705 | **1.0818** |

Thus **3/6** windows cross the one-pixel *spacing* gate for Mars 16ppd, compared with 0/6 for Mars 4ppd, but **0/6** cross the explicitly diagnostic four-pixel gate for Mars 16ppd or Moon 4ppd. A four-pixel north-south support requires 14.7895 km on Mars 16ppd and 30.3234 km on Moon 4ppd. The four-pixel rule is an engineering diagnostic, not a universal scientific threshold.

The higher-resolution Mars data **partially falsify** the overly broad interpretation that all 2/4-km Earth windows must be subpixel for every already available Martian raster. They **do not rescue** within-window, comparable cross-body relief analysis. A 4-km Earth window contains just ~1.08 Mars 16ppd pixel spacings; lunar 4ppd remains subpixel. A footprint exceeding one pixel spacing does not guarantee a sufficient number of independent samples or known instrument point-spread/vertical-datum comparability.

## Validation and boundaries

- The full three source JSON receipts were fetched and independently evaluated in JavaScript: six site-window records, 3 one-pixel Mars16 passes, zero four-pixel Mars16/Moon4 passes.
- Seven targeted Python unittests on frozen source-derived numeric fixtures PASS; Python compilation PASS. Git blob hashes of source/tests were verified against the locally executed files.
- The committed Python CLI was **not run on the full remote JSON files** in the local environment; full repository suite and exact-head GitHub Actions were not run.
- Global MOLA observed fraction is **not** site-specific quality. MOLA interpolation, LOLA visualization smoothing, latitude-dependent east-west support, Earth data blending, and unequal planetary datums remain unresolved. No physically matched per-site rasters, independent positive/negative analogue labels, or blind retrieval scores were computed.

**SUPPORTED:** real-receipt equatorial resolution sensitivity and limited one-pixel Mars16 rescue.
**REJECTED FOR CURRENT PRODUCTS:** treating these six 2/4-km Earth windows as comparable four-sample Moon/Mars relief supports.
**NOT YET MEASURED:** E001 known-site recovery.
**NOT YET PROVEN:** cross-body similarity, novel analogue discovery, local validation advantage, and superiority of the planetary-analogue challenge.

## Next decisive experiment

Select published, independently labelled Earth–Moon/Mars analogue pairs and hard negatives; obtain per-site high-resolution planetary terrain with measured-cell masks and documented effective resolution. Alternatively preregister larger Earth windows, re-extract at matched physical support, and explicitly test scale sensitivity. Then freeze random, Euclidean, physically weighted, leave-one-site-out, ablation, and null controls. Keep the 2026 challenge ranking open; avoid UI investment before the evidence gate.
