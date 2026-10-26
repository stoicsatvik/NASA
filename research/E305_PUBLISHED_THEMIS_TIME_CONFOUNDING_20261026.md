# E305 — Published THEMIS time-of-observation confounding (exploratory)

**Date:** 2026-10-26. **Type:** independent computation on **secondary published real observations**, not raw PDS ingestion, instrument calibration, E001 analogue retrieval, or a competition solution.

## Source and provenance

Ahern, Rogers, Edwards & Piqueux (2021), *Thermophysical Properties and Surface Heterogeneity of Landing Sites on Mars From Overlapping Thermal Emission Imaging System (THEMIS) Observations*, *JGR: Planets* 126, e2020JE006713, DOI [10.1029/2020JE006713](https://doi.org/10.1029/2020JE006713). **Table 4, Bagnold Dunes (BD)**, Gale crater. The 24 image IDs, solar longitudes, local times, Mars years, temperatures (K) and VIS optical depths were manually transcribed into `research/data/e305_ahern_gale_bagnold_table4.csv`. The SHA-256 receipt fingerprints the transcription, **not the publisher's original data**. The paper estimates brightness temperature from calibrated THEMIS radiance; these are published derived observations, not downloaded PBT pixels.

## Discriminating question

Can raw brightness temperatures from distinct observations of the *same named geological surface* be treated as comparable physical descriptors without conditioning on observation time?

13 observations occur around local 03:19–05:59 and 11 around local 18:04–19:23. The early-morning group mean is **189.709769 K**, evening group **209.095727 K**, difference **19.385958 K**. This descriptive comparison is **not a controlled causal estimate**.

To reduce the most obvious seasonal mismatch, a deterministic maximum-cardinality, minimum-total-circular-solar-longitude-distance one-to-one matcher uses **only** solar longitude (not temperature). At ±10° tolerance it identifies seven disjoint pairs; **all seven** evening observations are warmer. The differences in K are **15.003, 31.573, 25.256, 27.071, 11.000, 20.393, 18.931**, mean **21.318143 K**. These are distinct images but often different Mars years. No significance or independence claim is made: selection is exploratory, data are small, and the observation schedule is not randomized.

Sensitivity to solar-longitude tolerance:

| Max circular separation | Disjoint pairs | Positive evening-minus-morning | Mean difference |
|---:|---:|---:|---:|
| 5° | 5 | 5 | 24.645 K |
| 10° | 7 | 7 | 21.318 K |
| 15° | 8 | 8 | 21.338 K |
| 20° | 9 | 9 | 21.464 K |

The original paper documents local-time, seasonal, atmospheric/dust and model limitations. The present comparison cannot isolate local time from Mars year, dust opacity, atmospheric conditions or sampling selection. It **does** demonstrate a large within-site observational nuisance in the cited sample, making naive unstratified cross-scene Kelvin distance scientifically unjustified.

## Validation and boundaries

Four deterministic source/matching/tamper tests; byte-for-byte two-run JSON comparison in isolated Actions workflow. No raw planetary imagery or field measurements collected. No raw datasets or personal information committed.

**SUPPORTED:** published same-site brightness-temperature observations vary markedly across the two local-time groups; descriptive ±5° to ±20° season-matched comparisons preserve the sign in this finite sample.

**NOT YET PROVEN:** independent PBT pixel calibration, attribution of the difference to local time alone, cross-instrument thermal harmonization, Moon/Mars/Earth similarity, novel analogue discovery or superiority of the planetary challenge.

**E001 known-site recovery: NOT YET MEASURED.**

**Next:** obtain independent PBT scene labels/pixels, acquisition-time masks and positive/negative analogue geology labels. Do not convert these 24 repeated within-site observations into independent Earth/Mars analogue examples. Re-rank all official 2026 challenges when full statements arrive October 28.
