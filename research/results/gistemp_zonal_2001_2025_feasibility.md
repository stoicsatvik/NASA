# GISTEMP zonal trend feasibility (retrospective, 2026-10-10)

**Claim:** Accessible real NASA zonal observations permit a bounded spatial trend test. This is NOT planetary-analogue recovery, a new climate discovery, or a competition submission.

Source: NASA GISS GISTEMP v4 annual zonal Land-Ocean Temperature Index, https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts%2BdSST.txt (accessed 2026-10-10). NASA source uses 0.01 °C anomalies relative to 1951–1980. Manual 2001–2025 transcription (25 annual rows), SHA-256 `73c38e1b52bf70764445ec9fb7bb8f9273486a81b93fea5afe26198e944705f4`. Source is mutable; values must be independently rechecked before use.

Method: regress 25 annual zonal means against centered calendar year; multiply slope by 10; OLS with Newey-West HAC lag 3, 95% normal intervals; Theil–Sen sensitivity; paired Arctic minus tropical anomaly series; remove each possible consecutive five-year window.

| Zone (2001–2025) | Trend °C/decade | HAC 95% interval |
|---|---:|---:|
| Global | 0.2588 | [0.1946, 0.3230] |
| Tropics (24S–24N) | 0.1939 | [0.1205, 0.2673] |
| Arctic (64N–90N) | 0.6787 | [0.5267, 0.8307] |
| Arctic minus tropics (paired) | 0.4848 | [0.3038, 0.6658] |
| Arctic minus tropics, 2011–2025 only | 0.2268 | [-0.0960, 0.5495] |

All 21 leave-five-consecutive-year-out Arctic-minus-tropics slopes stayed positive (0.3001 to 0.6410 °C/decade). The shorter 2011–2025 interval includes zero, a useful sensitivity limit.

**Boundaries:** These are already published aggregate observations, not independent gridded sites. HAC does not propagate NASA's observational uncertainty ensemble, Arctic coverage differs from tropical coverage, and manual transcription requires independent verification. No E001 known-site recovery was performed. The alternative Earth trend challenge has demonstrably accessible zonal data, but comparative challenge superiority is NOT YET PROVEN. Do not use these data to infer a planetary analogue.

**Next:** Check NASA zonal source snapshot independently and test spatial 2°×2° grids with missing-data masks and observational uncertainty. In parallel, continue MOLA/LOLA data acquisition for E001.