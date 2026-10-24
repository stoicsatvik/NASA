# E221 | Real Earth coordinate-jitter falsification (24 October 2026)

## Question and frozen design
Does moving an unvalidated research-lead coordinate by up to ±500 metres change terrain descriptors and the ordering of three candidate sites? **Pre-registered** five east and five north offsets (-0.5, -0.25, 0, +0.25, +0.5 km), two physically defined windows (2 km and 4 km), three sites. This gives **150 overlapping real raster windows**, not 150 independent samples.

## Sources and validation
Read-only Mapzen Skadi SRTM-derived HGT N19E076 (Lonar area), N18E073 (Western Ghats), N34E077 (Ladakh); all source URLs and SHA-256 checksums are in the JSON receipt. These are **not direct NASADEM observations**. The three coordinates are research leads, not positive/negative analogue labels. Exact-code-head [GitHub Actions 40099007353](https://github.com/stoicsatvik/NASA/actions/runs/40099007353) passed inherited and five new deterministic tests, downloaded real HGT tiles, and produced 150 per-window numerical records.

## Measured rank sensitivity
| Descriptor and footprint | Distinct site orders among 25 shifts | Shifts changing the unshifted ranking |
|---|---:|---:|
| Detrended relief SD, 2 km | 3 | 24.0% |
| Detrended relief SD, 4 km | 2 | 36.0% |
| Slope p90, 2 km | 3 | 76.0% |
| Slope p90, 4 km | 1 | 0.0% |

Maximum absolute change in 2-km detrended relief SD from the unshifted center: **Lonar 29.3%; Western Ghats 44.0%; Ladakh 39.4%**. At 4 km the corresponding values were 1.3%, 17.4%, and 16.0%.

**Falsification:** Coordinate selection can materially alter local descriptor magnitudes and site ordering. This effect is **feature- and footprint-dependent**, not universal: 4-km slope p90 preserved the same ordering for all 25 shifts. A single chosen coordinate/scale is not sufficient to claim a robust ranking.

## Boundaries and next discriminating experiment
The ±500m shift is an analyst sensitivity choice, not a measured location-error distribution. Windows overlap, so frequencies are descriptive, **not confidence intervals or probabilities**. Source mosaicking and per-pixel instrument coverage are unresolved. No Earth–Moon–Mars similarity or known-site recovery was measured. E001 known-site recovery **NOT YET MEASURED**; cross-body similarity, novel analogue discovery, local validation advantage and challenge superiority **NOT YET PROVEN**.

Next: obtain independent legitimate known-analogue labels and negative controls, then test leave-one-site-out retrieval under physical-footprint, source and coordinate perturbations against transparent random/Euclidean/weighted baselines. Do not use these three lead identities as training labels.
