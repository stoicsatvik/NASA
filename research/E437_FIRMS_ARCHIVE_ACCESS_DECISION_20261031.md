# E437 | NASA challenge-choice access friction, 31 October 2026

## Question
Does discovering real access and science-quality latency constraints in NASA FIRMS overturn the provisional E193 ranking in favor of planetary analogues? This is **pre-event challenge-choice research**, not development of a competition solution.

## New source evidence (official NASA pages, inspected 31 October 2026)

- [NASA FIRMS Archive Download](https://firms.modaps.eosdis.nasa.gov/download/) offers archived MODIS/VIIRS hotspot records but explicitly specifies Earthdata/email authentication and an approximately **five-month** lag before near-real-time observations are replaced by standard science-quality records. A request may require an email-based download workflow. No authenticated download was attempted.
- [NASA FIRMS Active Fire](https://firms.modaps.eosdis.nasa.gov/content/active_fire/) distinguishes near-real-time from standard data and warns scientific users to prefer standard products. An accessible index page is not proof that the underlying files can be downloaded without credentials.
- [NASA GISTEMP v4](https://data.giss.nasa.gov/gistemp/) publishes monthly temperature anomalies in tables and machine-readable forms, with revisions to past records. This is a contrasting access pathway for the Earth Trend challenge; no new GISTEMP bytes were ingested here.
- The official [Lunar Landing Site Navigator](https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/) challenge concerns Sun/Earth horizon visibility, landing sites, dates, power and communication windows. It is **not** the stale `CLPS lunar browser` entry in E193. E411's 13/14 exact-identity gap remains unresolved; E437 does not silently rename or score it.

## Deterministic E193 rating stress test

The existing E193 scorecard is **subjective analyst judgment**, not an empirical win model. Hold every historical rating and penalty fixed except the MODIS/VIIRS **validation** axis, stressed from 8 down to 6, 4, and 0. Compute with exact Decimal arithmetic using the frozen E193 seven weights and existing ratings.

| MODIS validation assumption | MODIS score | Planetary score | Top old-label candidate | Planetary rank in stale 14 |
|---:|---:|---:|---|---:|
| 8 | 5.43 | 4.59 | MODIS/VIIRS | 5 |
| 6 | 5.03 | 4.59 | Earth Trend | 5 |
| 4 | 4.63 | 4.59 | Earth Trend | 5 |
| 0 | 3.83 | 4.59 | Earth Trend | 4 |

Under the **unchanged historical assumptions**, planetary validation must rise from 4.0 to **7.3** to tie Earth Trend and to **8.2** to tie MODIS. The latter threshold was also found in E411. The independent source discovery about FIRMS access does **not** justify any particular new score; the table is a sensitivity calculation only. It shows that penalizing MODIS alone is not enough to make planetary the old-table leader, because Earth Trend remains ahead.

## Interpretation and decisive next move

- **SUPPORTED BY OFFICIAL DOCUMENTATION:** FIRMS archive access requires an authentication/request workflow, and standard science-quality records lag near-real-time data. GISTEMP provides documented machine-readable monthly products.
- **SUPPORTED BY EXACT ARITHMETIC:** The conditional E193 score sensitivity and thresholds above. Five local pure-function tests passed against the exact authored E437 source with a source-equivalent frozen-rating fixture; the full E193 import/CLI and GitHub Actions were not executed.
- **NOT YET PROVEN:** That FIRMS is inaccessible, that the Earth Trend challenge is superior, that planetary analogues can recover known sites, that any entry will win, or that the historical fourteen entries exactly match the current official challenge set.

**Next high-EV test:** Obtain the full official 14 challenge statements/resources and replace the stale CLPS entry with a genuinely evaluated Lunar Navigator, then perform no-cost, legitimate **actual** access/measurement spikes for FIRMS standard MODIS/VIIRS and GISTEMP. For planetary E001, prioritize independent labelled analogue pairs and physically matched Earth/Moon/Mars descriptors rather than further optimizing three unvalidated Earth sites. No credentials, requests requiring email, field observations, deployments, or competition submissions were made.

## Reproduction

`python -m research.e437_firms_access_decision` after E193/E411 dependencies are available; `python -m unittest discover -s tests -p 'test_e437_firms_access_decision.py' -v`. No NumPy required for E437. Exact old 14-label identity remains explicit.
