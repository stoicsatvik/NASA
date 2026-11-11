# 2026 Space Apps challenge-selection screen — 2026-11-11

Status: **provisional pre-event triage, not a final challenge selection or competition submission**.

## Scope and method

Screened all 14 challenge titles listed by the 2026 Space Apps India/partner challenge index and cross-checked the principal candidate descriptions against official Space Apps challenge pages. The score is a decision aid, not a prediction of judging outcomes.

Weights (1–5, higher is better): public-data readiness 25%; measurable validation within the 48-hour event 25%; reuse of current portfolio/preparation 20%; technical differentiation 15%; execution feasibility 15%. A score difference below roughly 0.25 is not meaningful. Human expertise and hidden data-access constraints remain uncertain.

## All 14 challenges

| # | Official challenge | Data | Validation | Reuse | Differentiation | 48h feasibility | Weighted score | Fit / falsification note |
|---|---|---:|---:|---:|---:|---:|---:|---|
| 1 | Abandoned but Not Forgotten | 4.5 | 3.0 | 2.0 | 1.5 | 4.5 | 3.18 | Easy source-led storytelling; lower computational/scientific leverage and weak reuse |
| 2 | Be An Earth System Trend Detective | 4.5 | 4.0 | 3.5 | 2.5 | 4.0 | 3.80 | Strong public time-series and statistical tests; risk of variable fishing and multiple testing |
| 3 | Junior Astronaut Mission Trainer | 3.0 | 2.5 | 2.0 | 2.0 | 3.0 | 2.53 | Buildable game, but engineering realism and learning outcomes are hard to validate quickly |
| 4 | CLPS Lunar Mission Browser | 4.0 | 4.0 | 4.0 | 3.0 | 4.0 | 3.85 | Clear site/date geometry and power/communications outputs; good map reuse, but lunar-specific data work remains |
| 5 | Astronaut Health Monitoring Software | 2.5 | 2.0 | 1.5 | 2.5 | 2.0 | 2.10 | Sensitive health domain and risk of unsafe clinical interpretation; deprioritize |
| 6 | Dancing with the SARs | 3.0 | 3.5 | 3.0 | 4.0 | 2.5 | 3.20 | High technical differentiation; SAR calibration, processing and expert burden are substantial |
| 7 | Field Shift: Adapting Farms with NASA Data | 3.5 | 3.5 | 4.0 | 3.5 | 3.0 | 3.53 | Kaggriculture gives conceptual reuse, but its game data are not agronomic evidence; needs local soil/crop records |
| 8 | Flame in Freefall | 4.0 | 3.0 | 2.0 | 2.0 | 4.0 | 3.05 | Literature retrieval/synthesis is feasible; lower differentiation unless retrieval accuracy is independently evaluated |
| 9 | Harmonization of MODIS and VIIRS Hot Spots | 4.5 | 4.5 | 3.5 | 3.0 | 4.0 | 4.00 | Strong measurable sensor-harmonization problem with long public record; little existing portfolio code and likely crowded |
| 10 | Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars | 2.0 | 1.5 | 5.0 | 5.0 | 2.0 | 2.93 | Highest novelty and current research reuse, but no cross-body descriptor validity or known-site recovery yet |
| 11 | Interplanetary Survival Guide: Martian Map | 4.0 | 4.0 | 4.5 | 3.5 | 4.5 | **4.10** | Best first-pass execution fit: MOLA/CTX/HiRISE preparation plus the MGD3 dune layer can support a source-backed layered map; no route-safety claim is needed |
| 12 | Planet X and SPHEREx | 3.0 | 2.5 | 2.0 | 4.0 | 2.0 | 2.68 | Billion-object, 102-band time-series scale and astrophysics burden are too high for current evidence/time |
| 13 | Space Mission Design Game | 3.5 | 2.5 | 3.0 | 2.0 | 3.0 | 2.85 | A credible game needs coupled mass, energy, orbit, communications and budget constraints; easy to fake, hard to validate |
| 14 | The Earth Information Jukebox | 4.0 | 2.5 | 2.0 | 2.0 | 4.0 | 2.93 | Creative sonification is feasible, but scientific value and accessibility need user testing |

## Falsification of the current planetary-analog default

The analog challenge is not currently the highest-readiness choice.

1. Its official brief requires identifying and characterizing **new terrestrial analogs** from open Earth, Moon and Mars data. E527 acquired the official 2007 MGD3 spatial package (547 polygons/IDs); E528 linked 535/547 unique IDs to the 2018 workbook. E530 then found no directly admissible shared quantitative physical-feature family in the current PAAD/MGD3 pair. The Mars layer is useful map context, not evidence of cross-body similarity.
2. E527/E528 completed the producer/consumer identifier correction and actual 2018 join; exact-head E527 Actions run #42904750899 passed. The 535/547 ID join is codebook linkage, not physical-feature comparability, cross-body similarity or analogue recovery. E530 is the subsequent negative admissibility result.
3. Cross-body descriptors remain **NOT YET PROVEN** and E001 known-site recovery remains **NOT YET MEASURED**. No leave-one-site-out result, identity-leakage audit or physically weighted baseline has been run.
4. The challenge has the highest novelty score but depends most heavily on an Earth-science / planetary-geology / remote-sensing expert, who is not yet present. Maharashtra/Lonar/Deccan/Western Ghats/Ladakh remain research leads, not discoveries.
5. By contrast, the Martian Map preparation repository is explicitly preparation-only, not a solution, but it already records MOLA, CTX and HiRISE source families and geospatial validation requirements. The MGD3 dune layer is now source-pinned and joined to the 2018 workbook, so it can support a Mars context layer. It does not validate a route-safety model. A bounded map can be evaluated for CRS, coverage, resolution, missingness, layer registration and route-profile correctness without claiming a route is safe.
6. MODIS/VIIRS and CLPS are serious alternatives. MODIS/VIIRS has the clearest multi-sensor validation path; CLPS has a clean site/date geometry deliverable. Neither currently has more verified portfolio reuse than the Martian Map path.

## Conditional decision gate

- **Provisional top tier: Challenge 11, Interplanetary Survival Guide: Martian Map (4.10), and Challenge 9, MODIS/VIIRS Hot Spots (4.00), are effectively tied.** Their 0.10 difference is below the stated 0.25 meaningful-difference threshold. Martian Map receives only a weak portfolio-reuse tie-breaker from existing MOLA/CTX/HiRISE preparation and the possible MGD3 dune layer; this is not evidence of scientific superiority or judging advantage.
- **Challenge 10 remains a conditional challenger.** E527/E528 have produced a provenance-complete MGD3 spatial layer and 535/547 ID joins, but E530 found no directly admissible shared quantitative features and E001 remains NOT YET MEASURED. It stays viable only if independent Earth positive sites, defensible non-analogue controls and physically comparable features are acquired, then held-out known sites are recovered above transparent random/Euclidean/physically weighted baselines without identity leakage.
- If known-site recovery fails or the cross-body representation is dominated by instrument/site identity, reject the analog thesis for this event rather than polishing the UI.
- The official MGD3 archive acquisition, schema audit and 2018 ID join are complete. Next test geometry/CRS registration and actual map coverage against MOLA/CTX/HiRISE source support without making a route-safety claim. If registration or coverage is insufficient, the Martian Map score falls and MODIS/VIIRS or CLPS should be rescored.
- For a Mars map, separate observed elevation/slope/thermal/radiation proxies from assumed crew fatigue, oxygen budgets and mission rules. RAD/REMS are local rover observations, not a global safety forecast. Never label a route safe without a validated risk model.

## Sources

- 2026 Space Apps challenge index and event dates: https://www.spaceappschallenge.org/2026/
- 2026 partner index listing the 14 challenge titles: https://spaceapps.conocimiento.gob.ar/
- Analog challenge brief: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/
- Martian Map challenge: https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/
- Earth System Trend Detective: https://www.spaceappschallenge.org/2026/challenges/earth-system-trend-detective/
- MODIS/VIIRS Hot Spots: https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/
- Field Shift: https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/
- Dancing with the SARs: https://www.spaceappschallenge.org/2026/challenges/dancing-with-the-sars/
- CLPS Lunar Mission Browser challenge description (official team page): https://www.spaceappschallenge.org/2026/find-a-team/orbitforge1/
- SPHEREx: https://www.spaceappschallenge.org/2026/challenges/planet-x-and-spherex/
- Health Monitoring: https://www.spaceappschallenge.org/2026/challenges/health-monitoring-software/
- Junior Astronaut Mission Trainer: https://www.spaceappschallenge.org/2026/challenges/junior-astronaut-mission-trainer/
- Flame in Freefall: https://www.spaceappschallenge.org/2026/challenges/flame-in-freefall/
- Mission Design Game: https://www.spaceappschallenge.org/2026/challenges/space-mission-design-game/
- Earth Information Jukebox: https://www.spaceappschallenge.org/2026/challenges/the-earth-information-jukebox/
- Abandoned Equipment storytelling: https://www.spaceappschallenge.org/2026/challenges/nasas-discarded-equipment-storytelling/

The challenge-selection claim remains **NOT YET PROVEN**. No team contact, registration change, project submission or competition commitment was made.


## E531 scorecard sensitivity update (2026-11-11)

The five-weight, 14-challenge scorecard was stress-tested with 200,000 deterministic draws per scenario (seed 526). Each weight was independently multiplied by a uniform [0.8, 1.2] factor and renormalized; each criterion score was independently perturbed by +/-0.25, +/-0.50 or +/-0.75 and clipped to [1, 5].

| Score perturbation | Martian Map top | MODIS/VIIRS top | CLPS top | Earth Trend top | Median Map–MODIS gap |
|---|---:|---:|---:|---:|---:|
| +/-0.25 | 83.97% | 15.88% | 0.13% | 0.02% | +0.1010 |
| +/-0.50 | 65.40% | 27.46% | 4.75% | 2.38% | +0.1012 |
| +/-0.75 | 54.34% | 28.55% | 10.48% | 6.32% | +0.1041 |

Martian Map remains the most frequent top choice under these perturbation families, but its 5th-percentile gap versus MODIS/VIIRS is negative even at +/-0.25 and becomes more negative as score uncertainty grows. This is a robustness diagnostic, not a probability of judging success. Keep Martian Map and MODIS/VIIRS as a provisional top tier; challenge-selection superiority remains NOT YET PROVEN. Full method and results: `research/E531_CHALLENGE_SELECTION_SENSITIVITY_20261111.md` and `research/results/E531_CHALLENGE_SELECTION_SENSITIVITY_20261111.json`.

## E535 independent Earth aeolian dataset discovery (2026-11-11)

USGS source review identified the Grand Falls Dune Field, Navajo Nation, Arizona, as a candidate positive site with independent public field-data releases from 2013–2024. The release family includes wind/sediment-flux measurements, time-lapse imagery, photogrammetry-derived DEMs and orthomosaics; USGS explicitly describes the active dune field as a Mars analogue. The 2022–2023 and 2023–2024 products provide DEM/orthomosaic and meteorological/imagery components; 2023–2024 weather is 15-minute in the windy season and hourly in calmer months, cameras are 10-minute, and passive sediment samplers are retrieved about every two weeks in the windy season.

This raises the evidence potential of the planetary-analog track for a narrow **aeolian-process** experiment. It does not yet make the data E001-ready: raw files have not been downloaded or hashed, CRS/resolution/nodata/units are uninspected, and no non-analogue controls or Mars/Earth matched-support descriptors exist. The heuristic score is unchanged; Martian Map and MODIS/VIIRS remain the provisional top tier pending data ingestion and validation.

Source report: `research/E535_GRAND_FALLS_AEOLIAN_DATA_SOURCE_AUDIT_20261111.md`; registry: `data/grand_falls_source_registry.csv`. Public data access is not field-access permission; the site is on Navajo Nation land and new geological fieldwork requires applicable permits. No fieldwork, sampling or contact was performed.


## E541 leave-one-factor-out challenge-ranking falsification (2026-11-11)

The frozen five-factor scorecard was rescored across **all 14 challenges**, removing one factor at a time and renormalizing the remaining weights. This is a sensitivity experiment, not a probability of winning.

| Removed factor | Martian Map #11 | MODIS/VIIRS #9 | Gap (#11 − #9) | Leader |
|---|---:|---:|---:|---|
| None | 4.100 | 4.000 | +0.100 | #11, below meaningful threshold |
| Data readiness | 4.133 | 3.833 | +0.300 | #11 |
| Validation | 4.133 | 3.833 | +0.300 | #11 |
| Portfolio reuse | 4.000 | 4.125 | −0.125 | #9, below meaningful threshold |
| Differentiation | 4.206 | 4.176 | +0.029 | #11, effectively tied |
| Feasibility | 4.029 | 4.000 | +0.029 | #11, effectively tied |

All 14 were rescored. The top five for each ablation and the exact method are in `research/E541_CHALLENGE_SELECTION_FACTOR_ABLATION_20261111.md`.

**Falsification:** the Martian Map lead reverses when the 20% portfolio-reuse factor is removed. MODIS/VIIRS leads by 0.125, still below the predeclared 0.25 meaningful-difference threshold. The two remain a provisional top tier; neither is proven superior. No other challenge enters the top two under a single-factor removal. Challenge #10 planetary analog does not enter the top five under any single-factor ablation.

**Analog threshold:** with challenge #10's current reuse/differentiation/feasibility scores fixed, matching MODIS/VIIRS 4.00 requires `Data + Validation ≥ 7.8` (currently 3.5). Matching Martian Map 4.10 requires `Data + Validation ≥ 8.2`. This confirms that novel-site recovery and defensible cross-body data are the actual missing evidence, not UI polish.

Claim states remain unchanged: challenge-selection superiority NOT YET PROVEN; cross-body similarity NOT YET PROVEN; known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN.

Next decisive experiment remains MOLA/CTX/HiRISE geometry/CRS registration and actual coverage on one pinned Mars area. If that fails, lower #11 and reassess #9. No challenge is locked.


## E562 data-access addendum (2026-11-12)

The official FIRMS sample endpoint is anonymously accessible and yielded 74,605 VIIRS SNPP records for 2023-07-12 (14 fields, zero missing values, SHA-256 `edf79f62b35ba4485d7c85e01be5f6f61d30ab7b4addcf2eea00e2581982c30f`). This is a static VIIRS-only sample, not a current or historical paired MODIS/VIIRS cohort.

A pinned South Asia daily VIIRS file returned HTTP 303 without credentials; a bounded FIRMS area request with placeholder `NO_KEY` returned HTTP 400 / MAP_KEY_REQUIRED. The official Active Fire page requires Earthdata Login for daily text downloads and the API requires a free MAP_KEY. No credentials were created or used.

**Scoring decision:** do not change the 14-challenge numeric scores from this one access audit. MODIS/VIIRS (#9) remains viable if a legitimate participant credential is available, but its no-credential data path is not established. Keep #9 and Martian Map (#11) as a provisional top tier; their 0.10 baseline gap and reversal when portfolio reuse is removed remain below the predeclared 0.25 meaningful-difference threshold. Challenge-selection superiority remains NOT YET PROVEN.

Next factor-changing test: measure actual CRS registration, pixel support and nodata overlap for MOLA/CTX/HiRISE over one pinned Mars footprint. If the common support or registration fails, reduce Martian Map data readiness and rerun the all-14 screen.
