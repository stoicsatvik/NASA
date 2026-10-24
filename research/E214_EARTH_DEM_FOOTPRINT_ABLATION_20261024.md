# E214 — Real Earth terrain access and physical-footprint falsification (2026-10-24)

## Research question
Can a legitimately accessible Earth elevation source be ingested for the India planetary-analogue **research leads**, and are local terrain descriptors stable when a physical observation window doubles from 2 km to 4 km?

## Access result and provenance
1. An initial read-only Actions attempt at NASADEM from the OpenTopography public mirror returned **HTTP 404** ([failed CI 40082382097](https://github.com/stoicsatvik/NASA/actions/runs/40082382097)). This is a failed **specific URL/access attempt**, not evidence that NASADEM is unavailable globally.
2. A preregistered fallback used **Mapzen Skadi SRTM-derived HGT tiles** from the public AWS terrain archive. [Exact-head CI 40082499487](https://github.com/stoicsatvik/NASA/actions/runs/40082499487) downloaded N19E076, N18E073 and N34E077 and passed the existing lunar/Mars tests plus seven new synthetic geometry/nodata tests. Real 2-km and 4-km windows were processed at three sites.
3. SHA-256 fingerprints, source URLs, CRS, tile extents, physical pixel dimensions, void coverage and all numerical results are in `research/results/e214_earth_skadi_real_data_20261024.json`. Raw tiles were not committed. The Mapzen product is a **derived mosaic**, not an official NASADEM Earthdata download; it is not shot-level or per-pixel source-provenance evidence.

Official dataset context: NASA's [NASADEM description](https://data.nasa.gov/dataset/nasadem-merged-dem-global-1-arc-second-v001); [Mapzen public S3 archive](https://registry.opendata.aws/terrain-tiles/); [Mapzen terrain data-source/format documentation](https://www.mapzen.com/blog/terrain-tile-service/). This run's actual measurements came only from Mapzen Skadi.

## Measured physical-window sensitivity
The coordinates are **leads**, not confirmed positives, negatives or independent known-site labels.

| Lead | Detrended relief SD at 2 km | SD at 4 km | Change | 90th-percentile slope at 2 km | At 4 km |
|---|---:|---:|---:|---:|---:|
| Lonar area | 43.426 m | 30.718 m | **−29.3%** | 0.4827 | 0.1418 |
| Western Ghats area | 75.819 m | 94.619 m | **+24.8%** | 0.7508 | 0.5654 |
| Ladakh area | 48.249 m | 98.162 m | **+103.4%** | 0.4665 | 0.6657 |

The effect is **not a consistent scaling factor**: enlarging the physical window decreases detrended relief around the Lonar coordinate while increasing it around Ladakh. The 90th-percentile slope likewise changes in different directions. All six windows had 100% valid pixels *in the delivered derived product*; that does not prove original SRTM shot completeness.

**Interpretation:** A cross-body analogue model must define a physical observation footprint *before* comparing terrain descriptors. The same Earth location changes markedly when its observation window changes, so arbitrary image-tile dimensions are not defensible.

## Claim boundaries
- **SUPPORTED:** Real SRTM-derived Earth raster ingestion, source fingerprinting, and numerical footprint sensitivity for these six delivered windows.
- **NOT YET PROVEN:** The underlying site's scientific analogue status, original-source observation completeness, direct NASADEM ingestion, Earth/Moon/Mars descriptor comparability, or any cross-body similarity.
- **E001 KNOWN-SITE RECOVERY: NOT YET MEASURED.** No positive/negative ground truth or independent held-out known analogue was ranked.
- **Novel analogue discovery: NOT YET PROVEN. Local field-validation advantage: NOT YET PROVEN. Challenge selection superiority: NOT YET PROVEN.**

## Next decisive gate
Acquire an Earth DEM with explicit per-pixel provenance/void handling and independently validated known-analogue labels. Normalize fixed physical footprints across Earth/Moon/Mars, use robust topographic descriptors, and run random/Euclidean/physically weighted leave-one-site-out E001 baselines with ablations and false-positive inspection. Preserve all negative results. No UI work, field work or competition submission occurred.
