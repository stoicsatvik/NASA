# E310 | Published THEMIS time/year identifiability falsification

**Date:** 2026-10-27. **Evidence:** same 24 manually transcribed, published THEMIS-derived Bagnold Dunes temperatures from Ahern et al. (2021), [DOI 10.1029/2020JE006713](https://doi.org/10.1029/2020JE006713), Table 4. No new raw PDS scenes, independent measurements, field data or analogue labels.

## Question that could change the interpretation

E305 found an evening-minus-morning group-mean difference of **19.385958 K**, and all seven solar-longitude-matched pairs at ±10° were warmer in the evening. Could this isolate the contribution of local observation time, after controlling for Mars year?

**No, not from these observations.** Every morning image is from Mars years **26, 28–32**, and every evening image is from years **33–35**. There is **no Mars year with both time groups**. The seven season-matched pairs therefore all compare *different Mars years*. Solar-longitude matching does not fix the year or atmospheric conditions.

A year-indicator design has exact rational rank **9**; adding the morning/evening indicator leaves its rank at **9**. The time-group column is an exact linear combination of year indicators. The coefficient for local-time group is therefore **not identifiable conditional on unrestricted Mars-year effects**.

For any assumed local-time coefficient (the audit uses **−30, 0 and +30 K**), one can shift the nine year intercepts to produce **exactly the same fitted values and residual sum of squares**. This is an algebraic observational-equivalence construction, **not evidence that those year effects are physically plausible**. A synthetic positive control moving one evening observation into a morning-observed Mars year restores the design rank, verifying that the test detects within-year overlap.

## Claim revision

- **SUPPORTED:** the published observations show a descriptive ~19.39 K between-group difference; the current 24-row sample has exact time/year aliasing.
- **REJECTED for this sample:** a uniquely estimable local-time temperature coefficient while allowing unrestricted Mars-year effects. E305's matched signs cannot be used as a controlled causal time-of-day estimate.
- **NOT YET PROVEN:** physical explanation of the observed difference, calibrated raw THEMIS/PBT cross-scene normalization, cross-body thermal comparability, analogue retrieval, novel analogue discovery, local validation advantage or superiority of this challenge.

**E001 known-analogue recovery: NOT YET MEASURED.**

## Next discriminating measurement

Acquire real THEMIS/PBT observations with documented acquisition metadata and **overlapping morning/evening sampling within the same Mars years and comparable solar longitude**, plus atmospheric optical depth/uncertainty and surface masks. Test within-year contrasts and physically grounded normalization before including thermal features in an Earth/Moon/Mars similarity metric. If such observations are unavailable, exclude absolute temperature as a cross-scene similarity feature rather than manufacturing a correction.

## Reproducibility

Run `python -m unittest discover -s tests -p 'test_e310_*.py' -v` and `python -m research.e310_themis_year_aliasing`. The receipt records the source transcription SHA-256, exact design ranks, matched-pair year gaps and three observationally equivalent model SSEs. All computations are deterministic and standard-library-only.
