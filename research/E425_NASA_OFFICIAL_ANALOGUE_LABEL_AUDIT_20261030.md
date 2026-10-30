# E425 | Official NASA planetary-analogue gallery: independent label and scale audit

**30 October 2026. Source evidence only, not competition solution development.**

## Question

Can an independently published NASA planetary-analogue gallery immediately supply the frozen, blind, physically matched positive/negative cohort required by E001? If not, which parts of it are legitimate positive-control leads?

## Primary source

[NASA Science, Planetary Analog Explorer](https://science.nasa.gov/solar-system/analog-explorer/), page last updated **4 March 2026**. The gallery contains **11 illustrated Earth/other-world comparisons** and identifies their analogy mechanisms. It is a NASA-authored source independent of the TerraNova editorial controls used in E397/E418. The curated identities are now exposed to this research stream.

Source-transcribed structured inventory: `research/data/e425_nasa_editorial_analogue_pairs_20261030.json`.

## Source-backed inventory result

- **11** gallery comparisons: **9** involve the Moon or Mars, **2** involve Venus or Enceladus.
- **0** are independently sampled hard negative controls on the source page.
- **0** provide a complete paired, physically comparable numeric descriptor vector with matched instrument metadata and an independently fixed geospatial holdout.
- Many analogies are **mechanism-specific**, not globally similar terrain: perchlorate chemistry (Pilot Valley / Martian northern plains), biosignature preservation (Verde Valley / Mount Sharp), operational field geology (Kilauea / Hadley Rille), and icequake/subsurface detection (Gulkana Glacier / Enceladus).
- Candidate *positive-control leads*, not validated E001 examples: Lake Salda / Jezero Crater for lakebed/mineral context, Vikursundar / Martian ridges for aeolian morphology, and Death Valley / Utopia Planitia for rocky hazard appearance. Georeferencing and paired instrument comparability remain unverified.

### Independent scale counterexample

For its **Vikursundar Iceland / Mars ridges** illustration, NASA explicitly states the Martian ridges shown are **ten times** the size of the Icelandic ridges (300 m versus 3 km field of view). This is an illustrated scale comparison, **not** a calibrated ratio with uncertainty. Nevertheless, the NASA source itself treats them as analogous while showing that literal raw spatial-scale equality is **not necessary** for the gallery's analogy judgement. It independently reinforces E340's warning against naive equality of cross-world ripple wavelengths. No morphology normalization formula is inferred from this caption.

## Falsification / decision

**REJECTED:** treating all 11 NASA gallery comparisons as blind quantitative E001 ground truth, or treating gallery illustrations as proof of a learned cross-body similarity model.

**SUPPORTED:** existence of 11 NASA-curated analogy leads, nine Moon/Mars, two other worlds; the illustrated 10x ridge-scale contrast.

**NOT YET MEASURED:** E001 known-site recovery, any leave-one-site-out score, independent hard-negative performance or random/Euclidean/physically weighted baseline win.

**NOT YET PROVEN:** physically comparable cross-body descriptors, novel analogue discovery, local Maharashtra validation advantage or superiority of the planetary-analogue Space Apps challenge.

The labels are public and already inspected, so they can serve as **declared positive controls only**, not untouched blind holdouts. A model can appear to recover these sites simply by learning site names, latitude, climate or editorial selection.

## Next discriminating experiment

1. Select a *mechanism-specific* pair and obtain actual site coordinates, image footprints, acquisition geometry, resolution, units, missingness and uncertainty from independent official data sources.
2. Freeze physically meaningful descriptors and a spatially separated set of independent non-analogues **before** inspecting model scores.
3. Run random, Euclidean and physically weighted baselines on an identity-disjoint holdout, with leave-one-site-out, feature ablations and false-positive inspection.
4. Preserve failure and pivot if no signal survives. Do not train on or call the inspected NASA gallery a blind test.

No competition solution code, fieldwork, outreach, deployment, paid API, main merge or competition submission occurred.
