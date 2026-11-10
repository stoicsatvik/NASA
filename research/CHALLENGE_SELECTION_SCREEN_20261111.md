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
