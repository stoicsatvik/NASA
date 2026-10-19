# GISTEMP zonal one-year-ahead predictive falsification (2026-10-19)

Scope: **general NASA climate-data research preparation**, not a Space Apps challenge solution, planetary-analogue recovery, or a submitted project.

## Source and protocol
- Archived manually transcribed NASA GISS GISTEMP v4 zonal annual anomalies, 2001–2025, source `https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts%2BdSST.txt`.
- Existing frozen snapshot: `research/gistemp_zonal_2001_2025_snapshot.csv`, Git blob `0f8109a63a1e3b683a67d83bbb6ef8840ccfad45`.
- Values are 0.01 °C anomalies relative to 1951–1980, **not absolute temperatures**.
- Expanding-origin, one-year-ahead retrospective predictions for 2011–2025 (15 forecast years); models see only earlier observations.
- Fixed baselines: previous year's anomaly, trailing five-year mean, 10-year OLS extrapolation, expanding-history OLS extrapolation. No tuning on future years.

## Measured MAE (°C anomaly)
| Zone | Previous year | Five-year mean | 10-year linear | Expanding linear |
|---|---:|---:|---:|---:|
| Global | 0.1013 | 0.1200 | 0.1039 | 0.1058 |
| Tropics (24°S–24°N) | 0.1873 | 0.1704 | 0.2057 | 0.1709 |
| Arctic (64°N–90°N) | 0.4160 | 0.3536 | 0.3736 | 0.3351 |

Arctic expanding-linear vs persistence MAE improvement: 0.0809 °C, but exploratory circular 3-year-block bootstrap 95% interval for **candidate minus persistence**: **[-0.1919, +0.0180] °C**, crossing zero. The global expanding-linear forecast was slightly worse than persistence.

For 2016–2025 only, Arctic expanding-linear MAE was 0.341 °C versus 0.474 °C persistence, but this is a ten-year descriptive subset and not independent prospective validation.

## Interpretation
- **SUPPORTED:** the frozen, published zonal annual observations allow reproducible rolling-origin baseline comparison.
- **NOT YET PROVEN:** trend extrapolation offers robust predictive improvement. Fifteen annual forecast errors are too few to establish superiority; short-range dependence and changing observation coverage remain.
- **REJECTED as a direct E001 input:** these zonal annual temperature anomalies cannot discriminate specific Earth analogue sites, and they are not comparable to raw LOLA/MOLA/Diviner/THEMIS measurements.
- **NOT YET MEASURED:** planetary E001 known-site recovery, any real lunar/Martian raster ingestion.
- Source limitations: manual transcription previously independently compared against the same mutable NASA text, not a fresh raw download; no NASA observational uncertainty ensemble propagated.

## Next
Retain this as a negative/uncertain generic data-literacy baseline. For the competition, await official full challenge statements and respect the no-pre-event-solution-development boundary. Prioritize legitimate dataset metadata/format preparation and post-start scientifically defensible site-level tests over more zonal climate trend utilities.
