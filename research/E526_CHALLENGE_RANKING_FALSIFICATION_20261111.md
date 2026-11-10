# E526 — 2026 Space Apps challenge-selection falsification update (2026-11-11)

## Decision boundary

The planetary-analog challenge remains a leading candidate, not a locked choice. This update compares current repository evidence against all 14 official challenge summaries previously screened in E515. No numeric score is assigned where the evidence gate has not been executed; unknown is not zero.

## Fourteen-challenge evidence matrix

| Official challenge | Current repo/source evidence | Missing decisive gate |
|---|---|---|
| Abandoned but not Forgotten | No validated historical-source pipeline in the current portfolio audit | Provenance-backed mission-history reconstruction and factual evaluation |
| Be An Earth System Trend Detective! | E515 reconciled 75/75 NASA GISTEMP values and ran OLS plus block/circular-shift diagnostics | Broader regional tool, calibrated inference and independent acceptance test |
| Build a Junior Astronaut Mission Trainer | No tested trainer in the current portfolio audit | Frozen resource constraints and learner/usability validation |
| Create Health Monitoring Software for Astronauts | No empirical astronaut-health dataset or validated model in the current stream | Safe nonclinical scope, real data and domain review |
| Dancing with the SARs | No paired NISAR time-series experiment in the current stream | Georegistered NISAR pairs, change controls and uncertainty |
| Field Shift: Adapting Farms with NASA Data | kaggriculture-argus exists, but no farmer/soil evidence was found in this audit | Local agronomy partner, legitimate soil/crop inputs and held-out recommendation validation |
| Flame in Freefall | No microgravity combustion dataset/experiment ingested | Genuine microgravity measurements and controlled comparison |
| Harmonization of MODIS and VIIRS Hot Spots | No paired cross-sensor calibration experiment in the current stream | Co-located MODIS/VIIRS observations and independently verified event ground truth |
| Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars | E523 PAAD 45-site live ingestion; E318 MGD3 workbook ingestion; E524 finds zero directly admissible features in the current PAAD/2018-workbook pair; E525 documents a separate MGD3 spatial layer but has not ingested it | Verified 2007 spatial download, Dune ID join, Earth-side matched features, independent labels/controls and E001 leave-one-site-out recovery |
| Interplanetary Survival Guide: Martian Map | MOLA numeric ingestion and a martian preparation repo exist; MGD3 spatial source may add dune context | Hyperlocal multisensor route model, hazard layers and route-safety validation |
| Lunar Landing Site Navigator | LOLA numeric ingestion exists | Tested Sun/Earth horizon windows, illumination constraints and landing-site validation |
| Planet X and SPHEREx | No multi-epoch SPHEREx detection/validation campaign in the current stream | Source-pinned multi-epoch spectra and false-positive controls |
| Space Mission Design Game | No validated resource-constrained game simulation in the current stream | Frozen physical constraints, deterministic scenarios and user tests |
| The Earth Information Jukebox | No source-pinned sonification/interaction evaluation in the current stream | Accessible NASA imagery/audio mapping and listener tests |

## Falsification result

Planetary analog has the strongest currently assembled cross-body data pipeline, but the core comparison is not yet scientifically admissible: E524 found zero direct shared descriptors in the current Earth/Mars tables, and E001 recovery remains unmeasured. E525 improves the path by identifying a separate official spatial MGD3 release with polygons, area, MOLA elevation, dune type and orientation, but it is not ingested or joined.

Two rivals remain real rather than hypothetical: Earth System Trend Detective has a source-reconciled numerical experiment (E515), while Martian Map can reuse MOLA/MGD3 geospatial data but lacks a validated route-safety model. Field Shift has an ARGUS codebase but no domain evidence. The other challenges remain unknown where the required data/validation experiments have not been run.

**Conclusion:** challenge-selection superiority remains NOT YET PROVEN. Do not lock planetary analog until the MGD3 spatial join and an E001 baseline are run, and do not discard Earth Trend or Martian Map without their own acceptance gates.