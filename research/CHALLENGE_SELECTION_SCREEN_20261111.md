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

1. Its official brief requires identifying and characterizing **new terrestrial analogs** from open Earth, Moon and Mars data. The current NASA branch has a source-pinned Mars MGD3 spatial-ingestion path, but the official archive has not yet been ingested in this run.
2. The E527→E528 integration defect just corrected was a producer/consumer identifier mismatch. The correction makes a future join possible; it is not evidence of a successful 2018 join, cross-body similarity or analogue recovery.
3. Cross-body descriptors remain **NOT YET PROVEN** and E001 known-site recovery remains **NOT YET MEASURED**. No leave-one-site-out result, identity-leakage audit or physically weighted baseline has been run.
4. The challenge has the highest novelty score but depends most heavily on an Earth-science / planetary-geology / remote-sensing expert, who is not yet present. Maharashtra/Lonar/Deccan/Western Ghats/Ladakh remain research leads, not discoveries.
5. By contrast, the Martian Map preparation repository is explicitly preparation-only, not a solution, but it already records MOLA, CTX and HiRISE source families and geospatial validation requirements. The MGD3 dune layer being prepared in NASA can become a directly relevant Mars feature layer. A bounded map can be evaluated for CRS, coverage, resolution, missingness, layer registration and route-profile correctness without claiming a route is safe.
6. MODIS/VIIRS and CLPS are serious alternatives. MODIS/VIIRS has the clearest multi-sensor validation path; CLPS has a clean site/date geometry deliverable. Neither currently has more verified portfolio reuse than the Martian Map path.

## Conditional decision gate

- **Provisional top tier: Challenge 11, Interplanetary Survival Guide: Martian Map (4.10), and Challenge 9, MODIS/VIIRS Hot Spots (4.00), are effectively tied.** Their 0.10 difference is below the stated 0.25 meaningful-difference threshold. Martian Map receives only a weak portfolio-reuse tie-breaker from existing MOLA/CTX/HiRISE preparation and the possible MGD3 dune layer; this is not evidence of scientific superiority or judging advantage.
- **Challenge 10 remains a conditional challenger.** It stays viable only if E527 produces a valid, provenance-complete MGD3 spatial layer and a subsequent E001 experiment recovers held-out known analog sites above transparent random/Euclidean/physically weighted baselines without identity leakage.
- If known-site recovery fails or the cross-body representation is dominated by instrument/site identity, reject the analog thesis for this event rather than polishing the UI.
- Before the event, run the official MGD3 archive acquisition and schema/CRS audit. Then test whether the MGD3 dune layer can be registered with a Mars base layer. If that integration is not reproducible, the Martian Map score falls and MODIS/VIIRS or CLPS should be rescored.
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
