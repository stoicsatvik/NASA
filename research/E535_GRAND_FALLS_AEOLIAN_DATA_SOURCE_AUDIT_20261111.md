# E535 — independent Grand Falls aeolian analogue data-source audit (2026-11-11)

## Question

Can a public, independently produced Earth field-data source supply a defensible positive-site candidate and measured aeolian-process evidence for the planetary-analog track?

## Finding

**Yes, as a candidate positive-site data source. No, not yet as E001 ground truth or a cross-body validation result.**

The USGS identifies Grand Falls Dune Field (GFDF), on the Navajo Nation in Arizona, as an active Mars-analogue dune field. The site contains barchans, domes, smaller dunes and ripples, with bimodal mineralogical composition and grain-size distribution. USGS data releases cover field observations from 2013 through November 2024, including wind, sediment flux, time-lapse imagery, photogrammetry-derived DEMs and orthomosaics.

This materially improves the candidate evidence base for a **narrow aeolian-process study**. It does not establish that the planetary-analog challenge is superior to Martian Map or MODIS/VIIRS, and it does not validate a general Earth–Moon–Mars similarity model.

## Source inventory

The machine-readable source registry is `data/grand_falls_source_registry.csv`. It records six dataset/component entries while preserving shared DOI relationships:

1. **2013–2016 sediment transport**, DOI 10.5066/P9Q58J28. Sensit saltation, BSNE samplers and wind measurements were sampled at 20/50/100 cm AGL; the source describes one-second acquisition averaged to one-minute logs and 15-minute xBSNE imagery.
2. **2017–2019 sediment transport**, DOI 10.5066/P9IYGDGQ. MLS4/BSNE/wind measurements were logged at ten-second intervals; xBSNE imagery is 15-minute. The instrument array was placed about 120 m downwind of an active barchan reported to migrate roughly 30 m/year.
3. **December 2022–April 2023 photogrammetry**, DOI 10.5066/P9FRH62D. Raw images, DEMs and an orthomosaic are described; a weather station logged every 15 minutes and seven cameras captured imagery every ten minutes. Catalog bounding box: -111.18636 to -111.14448 longitude, 35.42403 to 35.44501 latitude.
4. **April–July 2023 integrated collection**, DOI 10.5066/P9YQLHHB. Meteorology, time-lapse imagery, photogrammetry and passive sediment catchers are described.
5. **July 2023–November 2024 integrated collection**, DOI 10.5066/P13HPPYM. Weather was logged every 15 minutes in the windy season and hourly in calmer months; cameras captured every ten minutes; passive sediment samplers were retrieved about every two weeks in the windy season; DEMs/orthomosaics were produced.
6. **February–July 2024 photogrammetry component**, also DOI 10.5066/P13HPPYM. Seven dated collections each contain a DEM, orthomosaic, colorized shaded-relief TIFFs and a processing report PDF. This is a component of the parent release, not a separate site or independent DOI.

The USGS release pages identify these data products as public and CC0 1.0. The source registry does not claim that the raw files have been downloaded, hashed or profiled.

## Why this matters scientifically

Grand Falls is a much stronger candidate-positive source than an unverified catalogue row because the USGS source describes both the analogue rationale and direct field measurements. The combination of DEMs/orthomosaics, wind, sediment flux and time-lapse imagery could support within-site estimates of ripple morphology, migration, sediment transport and environmental forcing.

The valid initial scope is **aeolian process comparison**. It is not yet valid to compare these Earth measurements directly with MGD3 thermal inertia, albedo or mineral-abundance summaries. Mars/Earth descriptors must share a physical meaning, units, spatial support and uncertainty. A site-level positive label also does not provide a non-analogue negative population.

## Access and safety boundary

The official USGS/ScienceBase DOI landing path redirects to ScienceBase item pages, but the raw item/file listing could not be retrieved through the current read path. Therefore:
- raw data ingestion: **NOT DONE**;
- source file hashes: **NOT AVAILABLE**;
- raster CRS/resolution/nodata/units: **NOT INSPECTED**;
- time-series missingness and calibration: **NOT INSPECTED**;
- E001 recovery: **NOT RUN**.

This is a data-access task, not a scientific blocker. Do not claim a successful download or substitute catalog metadata for the underlying measurements.

GFDF fieldwork was conducted under Navajo Nation permits. Public data access is not permission for autonomous field visits, sampling or entry. No field activity or contact is proposed.

## Challenge-selection consequence

The new source raises the evidence potential of the planetary-analog track, especially if the project narrows to aeolian morphology/process. It does **not** yet justify changing the 2.93/5 heuristic readiness score or overturning the provisional Challenge 11 / Challenge 9 top tier. Those scores remain heuristic, not judging probabilities. Re-score only after raw files are acquired and a reproducible feature/registration experiment is completed.

## Next decisive experiment

1. Retrieve the ScienceBase file listings for the 2022–2023 photogrammetry and 2023–2024 integrated releases.
2. Download one small DEM/orthomosaic plus its processing report and one matched weather/imagery interval; preserve URL, item/file IDs, byte length and SHA-256.
3. Inspect CRS, horizontal/vertical units, pixel size, nodata, DEM vertical datum, camera geometry and acquisition timestamps.
4. Derive a small set of interpretable Earth-side aeolian descriptors with uncertainty; keep field measurements distinct from remote-sensing products.
5. Seek a Mars-side dune migration/morphology source at compatible physical support, then run transparent baselines and false-positive/contrast-site tests. Unlabelled Earth sites remain UNLABELLED, never negative.

## Claim states

- Grand Falls as a USGS-described Mars-analogue candidate site: **SUPPORTED AS PUBLISHED**.
- Grand Falls raw-data ingestion: **NOT DONE**.
- Aeolian feature comparability to Mars: **NOT YET PROVEN**.
- E001 known-site recovery: **NOT YET MEASURED**.
- Cross-body similarity: **NOT YET PROVEN**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Local Maharashtra validation advantage: **NOT YET PROVEN**.
- Planetary-analog challenge superiority: **NOT YET PROVEN**.

## Primary sources

- USGS 2013–2016 sediment transport: https://www.usgs.gov/data/grand-falls-arizona-dune-field-sand-transport-2013-2016 (DOI 10.5066/P9Q58J28)
- USGS 2017–2019 sediment transport: https://www.usgs.gov/data/grand-falls-arizona-dune-field-sand-transport-2017-2019 (DOI 10.5066/P9IYGDGQ)
- USGS Dec 2022–Apr 2023 photogrammetry: https://www.usgs.gov/data/imagery-photogrammetry-and-meteorological-data-december-2022-april-2023-grand-falls-dune-field (DOI 10.5066/P9FRH62D)
- USGS Apr–Jul 2023 integrated collection: https://www.usgs.gov/data/imagery-sediment-collection-photogrammetry-and-meteorological-data-april-2023-july-2023-grand (DOI 10.5066/P9YQLHHB)
- USGS Jul 2023–Nov 2024 integrated collection: https://www.usgs.gov/data/imagery-sediment-collection-photogrammetry-and-meteorological-data-july-2023-november-2024 (DOI 10.5066/P13HPPYM)
- USGS TADP: https://tadp.astrogeology.usgs.gov/ ; portal supports WMS/WFS/CSW discovery and serves as a USGS terrestrial-analogue data repository.
