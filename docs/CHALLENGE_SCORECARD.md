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

**Current status: provisional lead, not locked.**

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

Current provisional lead: **planetary analog identification**. Challenge-selection superiority remains NOT YET PROVEN.

The next research sprint should try to *disprove* that choice rather than defend it.


## 2026-11-11 evidence-based falsification update

All 14 official challenge summaries are now tracked against current repo evidence. Missing audits remain UNKNOWN, not zero. No numeric re-ranking is justified until each candidate's decisive data/validation gate is executed.

| Official challenge | Current evidence | Missing decisive gate |
|---|---|---|
| Abandoned but not Forgotten | No validated historical-source pipeline in the current portfolio audit | Provenance-backed mission-history reconstruction and factual evaluation |
| Be An Earth System Trend Detective! | E515 reconciled 75/75 NASA GISTEMP values and ran OLS plus block/circular-shift diagnostics | Broader regional tool, calibrated inference and independent acceptance test |
| Build a Junior Astronaut Mission Trainer | No tested trainer in the current portfolio audit | Frozen resource constraints and learner/usability validation |
| Create Health Monitoring Software for Astronauts | No empirical astronaut-health dataset or validated model in this stream | Safe nonclinical scope, real data and domain review |
| Dancing with the SARs | No paired NISAR time-series experiment in this stream | Georegistered NISAR pairs, change controls and uncertainty |
| Field Shift: Adapting Farms with NASA Data | kaggriculture-argus exists, but no farmer/soil evidence was found in this audit | Local agronomy partner, legitimate soil/crop inputs and held-out recommendation validation |
| Flame in Freefall | No microgravity combustion dataset/experiment ingested | Genuine microgravity measurements and controlled comparison |
| Harmonization of MODIS and VIIRS Hot Spots | No paired cross-sensor calibration experiment in this stream | Co-located observations and independently verified event ground truth |
| Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars | E523 PAAD and E318 MGD3 workbook ingestion; E524 zero directly admissible descriptors in the current pair; E525 documents a separate MGD3 spatial source but it is not ingested | Verified spatial download, Dune ID join, matched Earth features, independent labels/controls and E001 recovery |
| Interplanetary Survival Guide: Martian Map | MOLA numeric ingestion and a martian preparation repo exist; MGD3 spatial data may add dune context | Hyperlocal multisensor route model, hazard layers and route-safety validation |
| Lunar Landing Site Navigator | LOLA numeric ingestion exists | Tested Sun/Earth horizon windows, illumination constraints and landing-site validation |
| Planet X and SPHEREx | No multi-epoch SPHEREx detection/validation campaign in this stream | Source-pinned multi-epoch spectra and false-positive controls |
| Space Mission Design Game | No validated resource-constrained game simulation in this stream | Frozen physical constraints, deterministic scenarios and user tests |
| The Earth Information Jukebox | No source-pinned sonification/interaction evaluation in this stream | Accessible NASA imagery/audio mapping and listener tests |

Planetary analog still has the most assembled cross-body source pipeline, but its core comparison is not scientifically admissible yet: E524 found zero directly comparable descriptors in the current PAAD/2018-workbook pair and E001 recovery is NOT YET MEASURED. E525 identifies a separate official MGD3 spatial route but does not ingest it. Earth Trend has a real source-verified numerical path; Martian Map has MOLA ingestion but no route-safety validation. Field Shift lacks local domain evidence. The remaining challenges are not ranked inferior where their audits are absent.

**Conclusion: challenge-selection superiority remains NOT YET PROVEN.** Do not lock planetary analog until the spatial join and E001 baseline are run, and do not discard Earth Trend or Martian Map without their own acceptance gates.

## E572 independent analogue-catalogue admissibility (2026-11-12)

A second public catalogue was pinned and quantitatively audited: Rachelle Le Cussan's Planetary Analogue Catalogue, v0.1 (CC BY 4.0), commit \`62e6339bdf308de3bc987388d0faa7130cf57de9\`.

It contains 12 primary Mars/Moon records (10 Mars, 2 Moon), all Draft; 68 references (21 peer-reviewed, 20 peer-reviewed label/feature-supporting, 1 unverified); zero explicit negative controls; zero common physical numeric descriptors; and zero target-body measurement fields. The only numeric fields shared across all records are contributor access/hazard ratings. Eleven of twelve coordinates are region-only or approximately 10 km precision.

**Decision:** the catalogue is useful as a candidate-site index, not as E001 labels/features. No numeric challenge score changes. The planetary-analog challenge remains NOT YET PROVEN and below the provisional readiness pair: Martian Map #11 (4.10) and MODIS/VIIRS #9 (4.00). E001 remains NOT YET MEASURED. See \`research/E572_ANALOGUE_CATALOGUE_ADMISSIBILITY_20261112.md\` and its pinned aggregate receipt.
