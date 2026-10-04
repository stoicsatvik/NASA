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
