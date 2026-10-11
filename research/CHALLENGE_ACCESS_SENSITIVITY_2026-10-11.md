# Pre-event challenge data-access sensitivity | 2026-10-11

Status: **research preparation only**. No hackathon submission or project implementation. Full challenge statements/resources remain pending. This memo does not assert an empirically calibrated probability of winning.

## Frozen scorecard and falsification

The 14-challenge subjective scoring exercise (2026-10-11) assigned MODIS/VIIRS fire harmonization 6.09, Earth System Trend Detective 5.96, Field Shift 5.88, and planetary analogues 4.94. The seven-axis weights were inherited from the repository's challenge scorecard. These are analyst scores, **not** measurements.

The fire challenge's lead is only **0.13 points** over Earth trends and **0.21** over Field Shift. Any combined increase in fire-specific dependency/cloneability penalties greater than 0.13 changes the first-place ranking. This is an arithmetic threshold, not an estimated real-world penalty.

## New independent access and competition evidence

- NASA FIRMS active-fire page: https://firms.modaps.eosdis.nasa.gov/active_fire . It lists MODIS and VIIRS products, distinct spatial resolutions and 24-hour/48-hour/7-day downloads, and registration for data access.
- NASA FIRMS archive: https://firms.modaps.eosdis.nasa.gov/download/ . Archive retrieval requires Earthdata Login or email workflow; near-real-time products can later be replaced by science-quality standard data.
- NASA official challenge summary: https://www.spaceappschallenge.org/2026/challenges/harmonization-of-modis-and-viirs-hot-spots/ .
- Publicly visible independent implementation: https://github.com/Hisernberg/ignis-public . Its existence is evidence that a generic fire-calendar UI is already reproducible, not proof of its claimed performance or eligibility.

**Access gate result:** No authenticated MODIS/VIIRS sample pairs were downloaded in this run. No Earthdata account/API key was created, and no cross-sensor calibration was measured. The source exists, but the dataset validation gate is **NOT YET MEASURED**.

## Counterfactual stress test

Using the frozen scorecard, vary the additional fire access-friction penalty and visible-competition penalty independently over {0, 0.2, 0.4, 0.6, 0.8}. The fire challenge remains first in 1 of 25 hypothetical scenarios and falls to third or below in 22 of 25. This is sensitivity to deliberately selected penalties, **not** a posterior probability of success.

The official Earth trend and Field Shift summaries remain plausible alternatives:
- https://www.spaceappschallenge.org/2026/challenges/be-an-earth-system-trend-detective/
- https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/

## Decision

No challenge is locked. Fire harmonization's prior rank #1 is fragile under new data-access and cloneability evidence. Do not substitute a polished web interface for scientific calibration. Continue independent dataset access and validation preparation; re-rank against full official statements when released.

Planetary claim boundaries unchanged: repo operating system **SUPPORTED**; cross-body similarity **NOT YET PROVEN**; E001 known-site recovery **NOT YET MEASURED**; novel analogue discovery **NOT YET PROVEN**; local validation advantage **NOT YET PROVEN**.
