# E193 | Falsification attempt: planetary-analogue challenge ranking

**Date:** 2026-10-24. **Scope:** competition preparation and choice analysis only. No competition solution was built. Full official challenge statements and datasets are scheduled for 2026-10-28.

## Question
Is the planetary-analogue challenge *unambiguously* the best of all fourteen published 2026 summaries under the repository's declared multi-criteria objective?

**Result:** NO, under the explicitly subjective assumptions tested. This falsifies a claim of unambiguous ranking superiority, not the value of the planetary challenge.

## Inputs and reproducibility
- All 14 summaries indexed at https://hackathlone.com/challenges with links to official NASA challenge pages; official event https://www.spaceappschallenge.org/2026/.
- The 7 weights are the repository's frozen scorecard: scientific depth .22, validation .20, unique evidence .18, demo .15, local advantage .10, team fit .10, speed .05.
- Each 0–10 score and 0–2 penalty is a **provisional analyst judgment**, not a measured fact. All 14 challenges were included, not merely selected competitors.
- Deterministic script: `python research/e193_challenge_sensitivity.py` (requires NumPy). RNG seed 20261024, 20,000 draws, independent criterion perturbations SD=1, penalty perturbations SD=.30, Dirichlet weights concentration=40.

## Scenario results, NOT competition probabilities

| Candidate | Base weighted score after penalties | Scenario top-rank frequency |
|---|---:|---:|
| MODIS/VIIRS hotspot harmonization | 5.43 | 43.735% |
| Earth System Trend Detective | 5.25 | 30.535% |
| Field Shift farms | 4.73 | 10.820% |
| Dancing with the SARs | 4.63 | 5.820% |
| Planetary analogues | 4.59 | **6.725%** |

Planetary analogues rank **5th of 14** at the stated base ratings, with median simulated rank 5. They rank below MODIS/VIIRS in 82.17% of these *analyst-assumption scenarios*, and below Earth Trend in 76.005%. This is not a posterior or a NASA judging prediction.

Sensitivity grid: across criterion perturbation SD 0.5, 1.0, 1.5 and Dirichlet weight concentration 20, 40, 80 (10,000 seeded draws each), planetary top-rank frequency ranged approximately **5.0%–7.9%**; its scenario frequency of ranking below MODIS/VIIRS ranged approximately **77.0%–87.4%**. These frequencies are conditional on the selected score table and perturbation model.

## Why the uncertainty remains high
- The planetary score is depressed by *unverified* paired lunar/Martian/Earth data access, unresolved instrument comparability, absent known-site recovery and uncertain 48-hour execution cost. These are not empirical failures of planetary-analogue science.
- MODIS/VIIRS and Earth Trend have comparatively straightforward observational validation pathways, but their ratings remain subjective. Existing NASA GISTEMP zonal research in this repo demonstrates accessible Earth trend data, not superior contest outcomes.
- The 14 summaries lack final resource lists and judging-specific technical constraints. Full statements on 28 October can change this ranking substantially.
- Missing planetary geology/remote-sensing expertise and lawful local field access remain unresolved. No local field data were collected.

## Decision and next discriminating test
**Do not lock a challenge.** Preserve planetary analogues as a serious candidate while attempting real paired MOLA MEGT/MEGC and LOLA data-access checks, then revisit all fourteen against the full official statements. Prioritize demonstrable data access and a credible independent validation target over cosmetic demos.

**Claim states:** challenge superiority NOT YET PROVEN; real MOLA raster ingestion NOT YET MEASURED; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN. The scenario ranking itself is SUPPORTED only as reproducible arithmetic over declared assumptions.

**Competition boundary:** preparing/researching is allowed, but the intended competition solution must not be developed before the event, per https://www.spaceappschallenge.org/2026/local-events/santiago-dominican-republic/.
