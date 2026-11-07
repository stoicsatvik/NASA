# E506: Cross-body raster-resolution confound (2 Nov 2026)

**Claim:** A raw per-pixel terrain-roughness nearest-neighbour heuristic is not physically comparable across the currently ingested LOLA, MOLA and ETOPO2022 grids. **SUPPORTED on the 13 inherited numerical 5×5 patches.** This is a methodological negative control, **NOT E001 known-analogue recovery**, not a geologically validated Earth/Moon/Mars similarity result, and not a finding about Lonar's actual analogue status.

## Reproducible inputs

Read only the numerical JSON receipts from the previous exact-head CI artifacts; the E506 script checks the SHA-256 of the unzipped JSON bytes, not merely a filename.

| Body | Prior experiment | Receipt JSON SHA-256 | Raw-data identity |
|---|---|---|---|
| Moon | E501, [PR #60](https://github.com/stoicsatvik/NASA/pull/60) | `84b72b67c9ea81bbccf6d0c6a301579a33925cb009ef7801b9a2076ee14bf7ae` | NASA SVS LOLA TIFF `330afa2556a86fd05ac6ba2f912f246600fdade35de2a0d90593d50d07b01b65` |
| Mars | E502, [PR #61](https://github.com/stoicsatvik/NASA/pull/61) | `eaa499260b4d15899e4a28c609b71f300e8669d00201bdbe55c2591b4020072d` | MOLA topography `25f16fb7aaf857898dcf98bc4f841341a24f8b9f7e98453ca083bc45d897ca2c`, shot-count `7e920ec43497b4beddf974650471600c7afd4916e2a8dd3500d6b14714365661` |
| Earth | E505, [PR #63](https://github.com/stoicsatvik/NASA/pull/63) | `db8c94a161c392626459f4032a40a850007e3b42d9f971ad6fdf5cc9009c6476` | NOAA ETOPO2022 tile `cbb763175d331ed0222da35f357d3837aa8218aeda72e586974ef2a53f9027d4` |

Five LOLA samples, five MOLA samples (each 25/25 cells has positive ground-return count), and three georeferenced Earth samples. Prior receipts were supplied to this run; the original full raster binaries were **not redownloaded** for E506.

Run:

```bash
python research/e506_scale_confounds.py --lola e501_lola_numeric_receipt.json \
  --mola e502_mola_paired_receipt.zip --earth e505-earth-dem-final-head.zip
python -m unittest discover -s research -p 'test_e506_scale_confounds.py' -v
```

## Physical resolution gate

Assuming spherical local spacing, north-south distance is `radius * delta_lat_rad`; east-west is `radius * cos(latitude) * delta_lon_rad`. These are **approximations**, not actual georegistration for the planetary TIFF samples.

| Source | Nominal angular step | Approx north-south km per pixel |
|---|---:|---:|
| Earth ETOPO | 15 arcsec | 0.4633 |
| Moon LOLA | 0.25 degrees | 7.5808 |
| Mars MOLA | 0.25 degrees | 14.7895 |

A single pixel step spans ~16.36 times the Earth distance on the Moon and ~31.92 times on Mars. Absolute adjacent elevation differences are therefore not a fair physical roughness metric.

## Descriptive ranking stress test

For each of ten planetary 5×5 patches, choose the nearest of the three *unverified* Earth sample locations under (A) median absolute adjacent pixel difference in metres and (B) median of east/west and north/south absolute elevation gradients divided by approximate physical pixel spacing.

| Assumed planetary absolute latitude | Nearest Earth choice changed / 10 |
|---|---:|
| 0 degrees | 5 |
| 30 degrees | 5 |
| 60 degrees | 5 |

At assumed 0 degrees, raw pixel-difference matching picks the **Lonar_candidate** for all ten targets. Gradient-adjusted matching instead picks Northern_control for LOLA tile 2 and MOLA tiles 0 and 1, and Deccan_control for MOLA tiles 2 and 4. The other five choices remain Lonar_candidate. At 60 degrees, the LOLA tile 2 adjusted choice changes to Deccan_control; the count remains five.

Example: Mars tile 2 has a median adjacent difference of **69 m** at ~14.79 km/pixel (equatorial gradient ~0.004665). Earth Lonar has **20.913 m** at ~0.46 km/pixel (gradient ~0.046654). Comparing raw differences favors Lonar; comparing dimensionless gradients favors the Deccan_control. **Neither selection is a validated analogue.**

## Falsification and boundaries

- **REJECTED:** naive pixel-adjacency matching is a stable, physically interpretable cross-body analogue ranking on these inherited samples.
- **SUPPORTED:** numerical sample-scale confounding and five nearest-choice reversals across three assumed planetary latitudes.
- **NOT YET MEASURED:** E001 known-site recovery, with independent positive and hard-negative labels.
- **NOT YET PROVEN:** cross-body analogue similarity, novel discovery, local field-validation advantage, or superiority of the planetary-analogue challenge.

This adjusted median gradient is **not itself a fair equal-footprint descriptor**. The Moon and Mars patches cover far larger physical areas than the Earth patches; planetary pixel orientation and latitude remain unregistered; all three instruments have different vertical datums, sampling kernels and coverage. The sample selection is not random or independent ground truth. Latitude sensitivity is a stress test, not a substitute for coordinate metadata.

**Next decisive experiment:** georegister actual planetary reference sites, resample all three DEMs to matched physical footprints and effective spatial frequencies (with MOLA shot-count masks), then run E001 with externally established analogue labels, independent hard negatives, leave-one-site-out, random/Euclidean/physically weighted baselines, nulls and ablations. If those fail, pivot rather than polishing a similarity map.
