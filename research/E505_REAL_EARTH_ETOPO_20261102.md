# E505 | Real Earth DEM access and georeference falsification (2 November 2026)

## Question
Can an independent, legitimate Earth terrain grid be numerically acquired and georeferenced near the literature-backed Lonar candidate before any Earth↔Moon/Mars analogue recovery is attempted?

## Source and reproducibility
- NOAA NCEI ETOPO 2022 surface elevation, 15 arc-second GeoTIFF, **N30E075** tile: https://www.ngdc.noaa.gov/mgg/global/relief/ETOPO2022/data/15s/15s_surface_elev_gtif/ETOPO_2022_v1_15s_N30E075_surface.tif
- Official dataset: https://www.ncei.noaa.gov/products/etopo-global-relief-model
- Dataset DOI: https://doi.org/10.25921/fd45-gt74
- Source SHA-256: `cbb763175d331ed0222da35f357d3837aa8218aeda72e586974ef2a53f9027d4`
- Actual source bytes: **30,871,200**; decoded **3600 × 3600 float32**; **12,960,000 finite gridded cells**.
- Native exact-code-head [Actions #41455099916](https://github.com/stoicsatvik/NASA/actions/runs/41455099916): **SUCCESS**, five synthetic georeference controls PASS, real download and TIFF decoding PASS. Numerical receipt artifact **#13146198485**, downloaded and independently parsed after CI; source and numeric values are not inferred from job status alone.
- Source tile min/max **−3,988 / +8,585.716 m**, not an independent vertical-accuracy estimate.
- TIFF pixel scale **1/240°** in both axes, tiepoint **(75° E, 30° N)**, raster type PixelIsArea.

## Actual registered 5×5 samples
| Research location | Requested lat/lon | Actual center lat/lon | 5×5 min/max elevation (m) |
|---|---|---|---|
| Lonar candidate | 19.976°N, 76.508°E | 19.977083°N, 76.506250°E | 479.500 / 590.097 |
| Deccan comparison | 19.5°N, 75.5°E | 19.497917°N, 75.502083°E | 453.076 / 467.298 |
| Northern comparison | 27.5°N, 78.5°E | 27.497917°N, 78.502083°E | 169.799 / 173.567 |

These are **actual gridded elevation samples**, not field observations, independent known-analogue labels, measured crater dimensions or novel discoveries. The comparison locations were not independently labelled as negatives.

## Falsification and recovery
The initial file-name assumption was wrong. NOAA `N15E075` has a real TIFF upper-left tiepoint at **15°N**, not 30°N, and cannot contain the 19.976°N candidate under the source's north-up pixel convention. Exact-head [run #41454792208](https://github.com/stoicsatvik/NASA/actions/runs/41454792208) rejected the unexpected tiepoint. [Run #41454901700](https://github.com/stoicsatvik/NASA/actions/runs/41454901700) confirmed the numeric tiepoint, and a subsequent N30E075 run exposed the missing floating-point predictor decoder. Installing `imagecodecs` resolved decoding; no fabricated data were substituted.

## Physical comparability warning
Earth ETOPO is a terrestrial elevation model; MOLA is metres above the Mars areoid; LOLA is kilometres above a lunar reference radius. Absolute elevation is **not** a cross-body similarity feature. At ~20°N, one Earth 15-arcsecond pixel spans roughly **0.44 km east-west × 0.46 km north-south**, while 4-pixels/degree lunar and Martian cells span many kilometres. Resample to a **common physical footprint**, handle observed-shot masks, and compute relief/roughness/slope only after registration and uncertainty checks.

## Claim state
- Real Earth DEM numeric ingestion and bounded GeoTIFF georegistration: **SUPPORTED** by exact-head native CI and downloaded artifact.
- Real lunar LOLA and Martian MOLA ingestion: **SUPPORTED** by E501/E502; Earth sample provenance is distinct.
- Cross-body physically comparable descriptors: **NOT YET PROVEN**.
- E001 known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery, local validation advantage, challenge-selection superiority: **NOT YET PROVEN**.

## Highest-EV next experiment
Source independent analogue labels from planetary-geology literature, align DEMs to equal physical support, exclude MOLA zero-shot bins, and run E001 random/Euclidean/physically weighted baselines with leave-one-site-out, hard negatives, ablations and rank sensitivity. Do not tune to the Lonar identity or polish UI first.
