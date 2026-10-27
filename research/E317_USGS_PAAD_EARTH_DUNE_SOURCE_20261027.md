# E317 — First independently published Earth dune-analogue table ingested

**27 October 2026.** Read-only retrieval from USGS ScienceBase item `64d418c3d34ef477cf3ced10`, DOI [10.5066/P9IFVZEX](https://doi.org/10.5066/P9IFVZEX), published by Gullikson, Titus and Hunter (2023). This is independent of the NASA gallery's descriptive eleven examples and the incomplete four-point 2020 USGS layer tested in E227.

## Falsifiable question and measured result

Can a public, independently curated geological analogue catalog provide actual geolocated Earth sites and interpretable process descriptors, rather than only metadata or unverifiable site leads?

**Yes, for Earth dune-site source access.** The source-fingerprinted public CSV was downloaded by GitHub Actions, not simulated. The result is a **data-access and completeness gate**, not planetary similarity or a matched-label benchmark.

- CSV: `Planetary Aeolian Analog Database_core attributes.csv`, **33,976 bytes**; SHA-256 `5be67b4da584987d9ce5207f2ee3c90b5b3b5849469461847111eaab5aafcecd`.
- **45 data rows; 45 distinct nonempty site names; 45/45 latitude/longitude pairs numeric and in valid geographic ranges**. This does not independently geodetically verify coordinates.
- **45/45** rows have nonempty `Dune_Type`, `References`, and `Köppen_Geiger_Climate_Classification`. **44/45** have `Sand_Source`, `Composition_of_Sand`, and `Elevation`. **33/45** have `Areal_Coverage`.
- The source contains **12 fields**: country, field site, location description, dune type, sand source, sand composition, center latitude/longitude, elevation, areal coverage, Köppen-Geiger climate class and references.
- Dune-type values are combinations of abbreviations such as `B`, `L`, `P`, `MG`, `SS`, `TR`; **the codebook and comparability with Mars dune taxonomy have NOT been independently validated**. Do not assign semantics by guessing abbreviations.

[Exact-head CI #40433261440](https://github.com/stoicsatvik/NASA/actions/runs/40433261440) **SUCCESS**, seven synthetic controls and a real read-only ScienceBase download. [Machine-readable receipt artifact #12703186381](https://github.com/stoicsatvik/NASA/actions/runs/40433261440/artifacts/12703186381). The raw dataset is not committed.

Earlier CI failures were test-fixture errors (an overbroad string assertion and literal newline escaping), corrected before final successful validation. They were not evidence of a USGS source failure.

## What this changes

**Previously:** E227's accessible 2020 USGS service yielded only four points with missing planetary-body labels. NASA gallery examples were descriptive, not a machine-readable benchmark.

**Now:** An independent USGS catalog supplies 45 real geolocated Earth dune analogues with dune-type, composition and climate metadata. This removes one **Earth-side labelled-site acquisition** uncertainty for a restricted aeolian-analogue research track.

**Still missing:** explicit matched Moon/Mars targets, independently sourced negative sites, harmonized instrument measurements, comparable dune-type codebooks, and blind held-out recovery. PAAD alone does not establish a correct cross-body match.

The [USGS Mars Global Digital Dune Database](https://www.usgs.gov/centers/astrogeology-science-center/science/mars-global-digital-dune-database) is a potential *independent* Martian dune-label source, but no MGD3 records were downloaded or matched in this experiment.

## Next decisive experiment

Read the PAAD dune-type codebook and Mars MGD3 attribute definitions. Identify any **physically comparable, predeclared features** (e.g. dune morphology category) without conflating Earth climate with Mars climate. Then ingest a small source-pinned Martian sample, build random/majority/nearest-category baselines and perform held-out site tests. If the datasets do not share a scientifically defensible target label, record the negative result and seek an independent matched-analogue study.

**Claim states:** independent Earth dune-site ingestion **SUPPORTED**; E001 known-site recovery **NOT YET MEASURED**; cross-body similarity **NOT YET PROVEN**; novel discovery **NOT YET PROVEN**; local field-validation advantage **NOT YET PROVEN**; challenge-selection superiority **NOT YET PROVEN**. No competition solution, submission, field collection or contact.
