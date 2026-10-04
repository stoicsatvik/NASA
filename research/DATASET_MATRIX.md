# Dataset Matrix — Planetary Analog Track

Status values:
- **verified** = official source identified
- **access-test** = source identified but ingestion not yet reproduced in this repo
- **research** = feature/data choice still needs scientific justification

| Body | Variable | Mission/product | Official source | Status | Why it may matter |
|---|---|---|---|---|---|
| Moon | topography / altimetry | LRO LOLA | https://pds.nasa.gov/ds-view/pds/viewDataset.jsp?dsid=LRO-L-LOLA-3-RADR-V1.0 | access-test | terrain geometry / relief / roughness derivation |
| Moon | thermal / solar reflectance | LRO Diviner GDR | https://pds.nasa.gov/ds-view/pds/viewProfile.jsp?dsid=LRO-L-DLRE-5-GDR-V1.0 | access-test | temperature and surface/mineral-related comparison |
| Mars | global topography | MGS MOLA MEGDR | https://pds.nasa.gov/ds-view/pds/viewDataset.jsp?dsid=MGS-M-MOLA-5-MEGDR-L3-V1.0 | access-test | planetary terrain reference |
| Mars | thermal infrared | Mars Odyssey THEMIS IR RDR | https://pds.nasa.gov/ds-view/pds/viewProfile.jsp?dsid=ODY-M-THM-3-IRRDR-V1.0 | access-test | thermal/spectral behavior |
| Mars | projected thermal imagery | THEMIS IR GEO | https://pds.nasa.gov/ds-view/pds/viewDataset.jsp?dsid=ODY-M-THM-5-IRGEO-V2.0 | access-test | map-aligned thermal comparison |
| Earth | land surface temperature | ECOSTRESS | https://www.earthdata.nasa.gov/data/instruments/ecostress | access-test | Earth thermal behavior |
| Earth | terrain / elevation | NASA Earthdata elevation products | https://www.earthdata.nasa.gov/ | research | Earth topography baseline |
| Earth | geology / lithology | non-NASA geological sources likely required | TBD | research | physical substrate constraint |

## Important warning

Cross-body comparison is not a normal machine-learning feature table.

A Moon Diviner temperature value, an Earth ECOSTRESS surface temperature and a Mars THEMIS measurement differ in:
- instrument response;
- acquisition geometry;
- atmosphere;
- illumination;
- time of day;
- spatial resolution;
- calibration;
- physical environment.

Do **not** concatenate them and normalize columns as though they came from one sensor.

The first technical task is to determine which **derived, physically comparable descriptors** are legitimate.

Examples that may be safer than direct raw-value matching:
- dimensionless terrain morphology;
- standardized local relief;
- slope distributions;
- roughness statistics at matched physical scales;
- landform geometry.

Spectral/thermal comparisons require substantially more care.

## Resolution policy

Any comparison must record:
- native resolution;
- resampled resolution;
- interpolation method;
- projection;
- spatial footprint;
- uncertainty introduced by resampling.

The lowest-resolution/least-trustworthy source may set the useful comparison scale.

## Access spike acceptance criteria

For each priority dataset:
1. fetch a small real sample;
2. verify file format;
3. parse coordinates;
4. render or summarize values;
5. document units;
6. document missing-data conventions;
7. record spatial resolution;
8. store provenance, not giant raw files, in Git.

Large source rasters should not be committed directly unless justified.
