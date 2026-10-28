# 2026 Challenge Scorecard

Status: **provisional research ranking**. This document is designed to change as evidence improves.

## Scoring

Each axis is 0–10.

| Axis | Weight | Question |
|---|---:|---|
| Scientific depth | 0.22 | Does success require real reasoning rather than presentation? |
| Validation strength | 0.20 | Can we prove that the result is correct/useful? |
| Proprietary evidence potential | 0.18 | Can we create evidence others do not automatically have? |
| Demo quality | 0.15 | Can judges understand the value in under a minute? |
| Local access advantage | 0.10 | Can India/Maharashtra give us unusual access or context? |
| Technical fit | 0.10 | Can the current team build the hard parts fast? |
| Execution speed | 0.05 | Can a credible MVP be completed inside the hackathon? |

Subtract:
- cloneability penalty: 0–2
- dependency risk: 0–2

## Current candidates

### 1. Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars

**Current status: primary research target.**

Why:
- inherently geospatial/scientific;
- requires combining Earth + planetary datasets;
- validation can use published analog sites;
- India contains candidate terrains discussed in planetary-analogue literature;
- field observations can become a real evidence layer;
- strong visual demo is possible.

Main risk:
- an unsophisticated cosine-similarity map would be easy to clone and scientifically weak.

What would make it strong:
- explicit physical variables;
- uncertainty;
- reference-site calibration;
- field validation;
- literature-backed reasoning;
- side-by-side spectral/topographic/morphological evidence.

---

### 2. Field Shift: Adapting Farms with NASA Data

**Current status: high-potential, domain-access dependent.**

Why:
- explicitly combines NASA observations with local soil information, crop properties and farmer priorities;
- interviews/soil observations could create proprietary evidence;
- clear real-world user.

Main risk:
- without a farmer/agronomy partner, it degenerates into a generic recommendation dashboard.

Kill criterion:
- if we cannot recruit a credible agriculture/domain person or obtain legitimate local input quickly, deprioritize.

Official challenge:
https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/

---

### 3. Harmonization of MODIS and VIIRS Hot Spots

**Current status: technically respectable, weaker moat by default.**

Why:
- real data harmonization problem;
- useful to emergency managers/scientists;
- strong opportunity for statistics, geospatial engineering and anomaly detection.

Main risk:
- the core data are public and many teams can build a dashboard.

Possible defensibility:
- independently verified event ground truth;
- robust cross-sensor calibration;
- quantified uncertainty and false-positive analysis.

---

### 4. Planet X and SPHEREx

**Current status: interesting science, high cloneability pressure.**

Why:
- rich astronomical data;
- change detection across repeated all-sky observations;
- strong visualization potential.

Main risk:
- challenge explicitly asks for a public-facing web tool; many teams will converge on similar UX + image-difference pipelines.

Choose only if:
- we recruit a serious astrophysics/spectral-data teammate and discover a scientifically differentiated analysis layer.

---

### 5. Be An Earth System Trend Detective!

**Current status: good statistics challenge, moderate moat.**

Why:
- forces actual time-series/statistical reasoning;
- possible to distinguish rigorous significance analysis from visual trend lines.

Main risk:
- mostly public data; defensibility comes from methodology rather than exclusive evidence.

---

### 6. Earth Information Jukebox / Connected Earth

**Current status: creative, lower priority for the current strategy.**

These can produce beautiful entries, but presentation and interaction are relatively reproducible. They are attractive only if paired with exceptional sonification/visualization talent.

---

### 7. Astronaut health-monitoring software

**Current status: low priority.**

Why:
- software-heavy and therefore easy to imitate;
- credible validation is difficult without appropriate physiological data/domain expertise;
- health-related claims require extra care.

---

### 8. Lunar Landing Site Navigator (new official-source counterexample, 28 Oct 2026)

**Status: serious falsification candidate, NOT selected.** The official 2026 statement asks for a tool comparing Moon south-pole sites and dates using Sun/Earth positions relative to the horizon, to evaluate illumination/power and direct-to-Earth communication. Source: https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/

Why it challenges the current leader:
- **Potentially stronger independent validation:** predicted Sun/Earth geometry could be checked against published ephemerides and established mission-planning calculations. This has **not yet been run**.
- **Potentially lower execution risk:** the objective has well-defined physical quantities, whereas Earth/Moon/Mars analogue similarity still lacks a measured known-site-recovery baseline.
- **Weaker proprietary moat:** no obvious unique local evidence advantage, and other teams may reproduce an ephemeris visualization.
- **Unresolved blocker:** actual lunar DEM horizon data, SPICE kernel compatibility, error bounds and validation reference cases have not been checked.

#### Explicit score-reversal witness (assumptions, NOT measured scores)

Use the predeclared weights above. The following 0–10 vectors are *illustrative scenario inputs*, not evaluator scores, observations or rankings of all official challenges. Order: science, validation, proprietary evidence, demo, local access, technical fit, execution speed.

| Candidate | Assumed vector | Weighted score | Assumed penalties | Scenario final |
|---|---|---:|---:|---:|
| Planetary analogue | (9,3,8,8,7,7,4) | 6.82 | 1.00 | 5.82 |
| Lunar navigator | (8,9,2,8,2,8,8) | 6.52 | 0.60 | 5.92 |

This **0.10-point reversal** is a sensitivity counterexample: current leadership is not robust to a plausible change in validation strength and execution risk. Raising the analogue validation score from 3 to 4 alone adds 0.20, reversing this example again. Therefore it is **not evidence** that the lunar navigator is actually superior.

**Discriminating next measurement:** independently verify one published lunar south-pole illumination/visibility reference case and its error tolerance, then compare its reproducibility and 48-hour feasibility with a blinded E001 analogue-recovery attempt. Both must comply with pre-event competition rules; do not develop the actual entry prematurely.

**Coverage limitation:** this is one additional official challenge checked, **not** a verified exhaustive audit of all 14 statements. The full challenge-selection superiority claim remains NOT YET PROVEN.

---

## Decision gate

Do not lock a challenge until the leading candidate clears all five:

1. **Dataset gate** — required data can actually be accessed and processed.
2. **Science gate** — at least one credible scientific method can be reproduced.
3. **Validation gate** — we know what evidence would falsify our output.
4. **Team gate** — missing expertise can realistically be recruited.
5. **Demo gate** — the core result can be understood visually in <60 seconds.

## Next decision

Current working target: **planetary analog identification**.

The next research sprint should try to *disprove* that choice rather than defend it.
