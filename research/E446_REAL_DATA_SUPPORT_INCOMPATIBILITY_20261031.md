# E446 | Real-data physical-support incompatibility, 31 October 2026

**Pre-event research only.** No Space Apps competition solution, geospatial UI, fieldwork, or novel-analogue claim was produced.

## Discriminating question
Can the six real 2-km/4-km Earth site windows ingested in E214 be compared at the **same physical support** to the existing real 4-pixel/degree lunar LOLA-derived and Martian MOLA rasters from E212, without inventing unresolved within-pixel morphology?

## Pinned, independently retrieved evidence
- E212 real LOLA/MOLA receipt: `research/results/e212_lola_mola_real_data_20261024.json`, Git blob `e762981e424186d72b0604b82da266c6d2b4e5ba`. The official-derived Moon 4ppd pixel is 7.580837606 km north-south at the equator; MOLA 4ppd is 14.789483749 km. Grid is 720×1440. Raw acquisition, interpolation, shot-count, smoothing and vertical-datum differences persist.
- E214 real SRTM-derived Mapzen Skadi Earth receipt: `research/results/e214_earth_skadi_real_data_20261024.json`, Git blob `ca557aa7ecef53796cfb01515a01cd96cc3291c3`. Six windows cover Lonar, Western Ghats and Ladakh research leads at 2 and 4 km; Earth north-south pixel spacing is 30.887522 m. These are **not** validated analogue labels.
- Both receipts were independently read from the existing E437 branch; the six real-record calculations were reproduced in JavaScript independently of the new Python source.

## Falsification result

| North-south physical span | Earth samples (approx.) | Moon 4ppd pixel spans | Mars 4ppd pixel spans |
|---|---:|---:|---:|
| 2 km | 65 | 0.2638 | 0.1352 |
| 4 km | 130 | 0.5276 | 0.2705 |

All six Earth windows span **less than one** equatorial north-south pixel in both existing planetary global products. This does **not** mean that a window necessarily contains zero pixel centers; it means within-window topographic variability cannot be resolved at the chosen support. Even the minimal, deliberately declared four-pixel-per-axis diagnostic would require ~30.323 km Moon and ~59.158 km Mars, versus E214's 2–4 km.

The Moon and Mars products have equatorial north-south pixels about 245.43× and 478.82× larger than E214 Earth pixels. Enlarging Earth windows by an order of magnitude would change the phenomenon under comparison; E214 already measured material descriptor changes from only 2→4 km.

## Interpretation
- **REJECTED FOR CURRENT PRODUCTS:** that E214's 2–4 km Earth relief descriptors can be compared at equivalent within-window spatial support to E212's global 4ppd Moon/Mars rasters.
- **SUPPORTED:** the metadata-derived scale mismatch and deterministic fail-closed support gate on these six real-data receipts.
- **NOT YET PROVEN:** physically comparable cross-body descriptors, known-site recovery E001, new analogue identification, local field advantage, or challenge-selection superiority.
- The four-sample threshold is a diagnostic choice, **not** an established scientific resolution requirement. The stronger less-than-one-pixel result does not depend on it. Latitude-dependent east-west resolution, source smoothing, coverage and vertical datums require separate analysis.

## Validation
Six local unittest controls passed against source-equivalent E212/E214 fixtures; Python compilation and the standalone audit passed. The new Python source and test Git blobs were read back and matched the locally executed files. Independent JavaScript calculations on both **full real-receipt JSONs** confirmed all six subpixel spans and the 30.323/59.158 km four-pixel thresholds. The new Python CLI was **not** run against the full remote receipts in this local environment, and no exact-head GitHub Actions were requested.

Reproduce on the stacked branch:

```bash
python -m research.e446_cross_body_support_gate
python -m unittest discover -s tests -p 'test_e446_cross_body_support_gate.py' -v
```

## Highest-EV next experiment
Do **not** perform E001 using these coarse raster windows as if they were physically matched. Either obtain legitimate higher-resolution LOLA/MOLA/THEMIS products with known per-site coverage and instrument resolution, or preregister much larger Earth windows and re-extract all descriptors at matched support. Obtain independently published analogue-positive/negative labels before retrieval. Only then run random, Euclidean, physically weighted, leave-one-site-out, ablation and sensitivity baselines. Challenge choice remains open; the November 14–15 event deadline is unchanged.
