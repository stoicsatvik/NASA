# E515 — Challenge-selection falsification via real NASA GISTEMP trend data

**Date:** 2026-11-03. **Scope:** research-only, no submission, no change to main.

## Question

The 2026 planetary-analogue challenge is the current leading thesis, **NOT YET PROVEN** to be the best challenge. Can a rival official challenge already produce more independently checkable evidence? This is a challenge-selection test, **not E001 known-site recovery**.

## Source verification

Existing `research/gistemp_zonal_2001_2025_snapshot.csv` was transcribed on 2026-10-10 from the official [NASA GISS GISTEMP v4 annual zonal table](https://data.giss.nasa.gov/gistemp/tabledata_v4/ZonAnn.Ts%2BdSST.txt). On 2026-11-03, all **25 years × 3 selected columns = 75/75 numeric values** were independently compared against the current NASA text, with zero mismatches. This was a read-only check, not a cryptographically pinned NASA server response. The source may be revised.

Units: hundredths of °C anomaly relative to 1951–1980. CSV Git blob `0f8109a63a1e3b683a67d83bbb6ef8840ccfad45`; SHA-256 `dc5d81e433b4687143e06b7f35471105aa9f12e9c9e1c6ea5304436ff48b44a2`.

## Executed experiment

`research/e515_gistemp_block_null.py` uses exact integer centered covariance to calculate OLS trends for 25 annual values (2001–2025). It exhaustively enumerates **120 permutations** of five consecutive five-year blocks and **25 circular shifts**.

| Series | OLS °C/decade | Two-sided block extremes /120 | Circular extremes /25 |
|---|---:|---:|---:|
| Global | +0.258769 | 1/120 | 1/25 |
| Tropics (24S–24N) | +0.193923 | 2/120 | 1/25 |
| Arctic (64N–90N) | +0.678692 | 2/120 | 1/25 |
| Arctic minus tropics | +0.484769 | **6/120** | 1/25 |

The contrast's block-null tail fraction is **5%**, weaker than the global trend's **0.83%** under this diagnostic. This does not reject Arctic amplification, contradict established climate science, or constitute a calibrated significance test: the five-year blocks are **not known exchangeable** under warming, and circular shifts are likewise not an established null. The window and block length are fixed descriptive choices. No causal attribution or future forecast.

Six deterministic local tests passed, using the exact Git blobs of the committed code and tests. Native CI pending at creation.

Reproduce:

```sh
python -m unittest discover -s research -p 'test_e515_gistemp_block_null.py' -v
python -m research.e515_gistemp_block_null
```

## All 14 official 2026 challenge alternatives

Inventory and summaries: [2026 local-event challenge list](https://hackathlone.com/challenges), which links to [official NASA Space Apps challenge pages](https://www.spaceappschallenge.org/2026/challenges/). This is an **evidence-readiness audit**, not a ranking based on fabricated competition odds. `Not audited` is not evidence of infeasibility.

| Challenge | Present evidence and missing gate |
|---|---|
| Abandoned but not Forgotten | Not audited; verified historical source and narrative evaluation needed |
| Be An Earth System Trend Detective! | **E515 source-reconciled numerical trend + temporal null**; full regional time-series tool and broader variables absent |
| Build a Junior Astronaut Mission Trainer | Not audited; resource-balance mechanics and learner validation needed |
| Create Health Monitoring Software for Astronauts | Not audited; safe nonclinical indicator/evaluation boundary needed |
| Dancing with the SARs | Not audited; georegistered NISAR time pairs and change controls needed |
| Field Shift: Adapting Farms with NASA Data | Not audited here; ARGUS repo is not proof of challenge readiness |
| Flame in Freefall | Not audited; genuine microgravity combustion measurements needed |
| Harmonization of MODIS and VIIRS Hot Spots | Not audited; paired satellite sensor calibration needed |
| Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars | **E514:** real Earth/Mars nominal equal support; 3/5 rankings changed, 4/5 survived spatial shuffles; **independent analogue labels absent** |
| Interplanetary Survival Guide: Martian Map | MOLA numeric ingestion established; no validated hyperlocal multisensor Marswalk routing |
| Lunar Landing Site Navigator | LOLA numeric ingestion established; no tested Sun/Earth horizon windows |
| Planet X and SPHEREx | Not audited; multi-epoch SPHEREx provenance/data needed |
| Space Mission Design Game | Not audited; frozen resource constraints and user tests needed |
| The Earth Information Jukebox | Not audited; legitimate imagery and accessible sonification needed |

## Decision

**SUPPORTED:** A rival challenge, Earth System Trend Detective, already has a source-verified retrospective quantitative baseline and an executed falsification control. This weakens any claim that the planetary-analogue challenge is **automatically** the strongest choice.

**NOT YET PROVEN:** Overall Earth Trend superiority, challenge submission readiness, comparative performance across all 14 challenges, or scientific novelty.

**NOT YET MEASURED:** E001 independent known-analogue recovery. Cross-body similarity, new analogue discovery, local field advantage and planetary-analogue superiority remain **NOT YET PROVEN**.

**Next decisive gate:** Run E001 with independently established known analogue and non-analogue sites, held-out by site, on georegistered equal-footprint data against random/histogram/physical baselines. If independent labels cannot be obtained, run a genuine Martian Map hyperlocal data/route gate and an Earth Trend regional time-series gate before committing the final sprint. No automatic pivot or competition submission.
