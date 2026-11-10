# E522 — NASA Analog Explorer catalogue admissibility gate

Date: 2026-11-10  
Branch: research/e522-analog-explorer-admissibility-20261110  
Base: E001 spatial-scale sensitivity PR #83 head d8362fd43e35983f5669ba94a6a91d42742c89f3  
Question: Can NASA's official Planetary Analog Explorer gallery be used directly as the independently labelled site matrix required by E001?

## Source inventory

NASA's gallery lists 11 curated Earth/other-world pairs. Nine target the Moon or Mars: three Moon pairs and six Mars pairs. Two additional pairs target Venus and Enceladus and are excluded from this challenge-specific inventory. The nine in-scope Earth sites are Medicine Lake Volcano lava caves, Kilauea, Utah's Pilot Valley, the Atacama Desert, Iceland's Vikursundar/Askja region, Death Valley, Lake Salda, Arizona's Verde Valley, and the Askja subsurface-ice field site.

Primary source: https://science.nasa.gov/solar-system/analog-explorer/ (accessed 2026-11-10). The page gives qualitative descriptions and images; several image comparisons explicitly state that images are not to scale.

## Executed admissibility experiment

experiments/e522_analog_catalogue_admissibility.py parses the frozen 11-pair transcription and evaluates two possible E001 family definitions:

- Target body: Mars has 6 positives and Moon has 3, satisfying the raw minimum count but mixing distinct mechanisms (salts, hyperaridity, ripples, rocky hazard reconnaissance, lake sediments, biosignature preservation; and caves, basalt, subsurface ice). A single body-level centroid would combine physically different targets.
- Analogue mechanism: all 9 in-scope mechanism families are singletons, so no held-out positive can be compared with another independently labelled same-family positive.

The gallery records do not supply numeric site-feature vectors, analysis coordinates/footprints, or negative controls. The E001 evaluator therefore cannot run on this source alone. The test deliberately fails closed instead of inventing feature values or treating arbitrary locations as negatives.

## Independent source discovery

1. USGS PAAD — Planetary Aeolian Analog Database, DOI https://doi.org/10.5066/P9IFVZEX. The USGS release describes 45 dune-field analog sites and core attributes including bedform type, climate class, sand source/composition, latitude, longitude, average elevation, and approximate areal coverage; it is CC0. Actual ingestion and source-fingerprinted analysis already exist in earlier stacked PRs #27-#32, so E522 does not repeat that acquisition. The prior work rejects direct raw-code joining to the Mars 2007 codebook and shows that 100 km spatial blocking changes Earth-only lexical agreement. Source: https://www.usgs.gov/data/paad-planetary-aeolian-analog-database.
2. USGS Terrestrial Analogs Data Portal (TADP) provides ScienceBase-backed discovery and OGC WMS/WFS/CSW services. Source: https://tadp.astrogeology.usgs.gov/how-to-contribute.
3. A separate public catalogue at https://github.com/rachellelecussan/planetary-analogue-catalogue contains 16 candidate site records and extensive references, but all 16 records are marked Draft in the inspected data/sites.geojson. It is a discovery lead only, not independent verified ground truth.

## Result and claim boundary

- NASA gallery pair inventory: SUPPORTED as a curated qualitative source.
- Gallery directly usable as E001 feature/label matrix: REJECTED for this source's current schema.
- USGS PAAD 45-site Earth dune ingestion: SUPPORTED in prior E317-E319 work; cross-body semantic equivalence and E001 recovery: NOT YET PROVEN.
- E001 known-site recovery: NOT YET MEASURED.
- Cross-body similarity, novel analogue discovery, local validation advantage, and challenge-selection superiority: NOT YET PROVEN.

This is a source-admissibility falsification, not an analogue-recovery score and not evidence that the planetary-analog challenge is inferior. The planetary-analog challenge remains a candidate, not a locked choice.

## Next decisive move

Do not repeat PAAD acquisition: the source-pinned 45-site CSV and the independent 2018 Mars MGD3 workbooks are already preserved in E317-E318. The next gate is an independently adjudicated semantic crosswalk between Earth and Mars dune descriptors plus predeclared non-analogue controls, followed by E001 leave-one-site-out and spatially blocked evaluation. E319's raw-token overlap is insufficient, E320/E323/E325 are Earth-only lexical/spatial diagnostics, and the source climate descriptions are not valid Köppen codes. No matched Earth-Mars positive/negative set or known-site recovery is established.
