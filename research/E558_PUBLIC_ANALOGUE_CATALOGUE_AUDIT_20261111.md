# E558 — external terrestrial analogue catalogue audit (2026-11-11)

## Purpose

Identify whether a second public catalogue adds candidate-positive sites, usable provenance and defensible controls beyond the existing USGS PAAD / 2007 MGD3 material.

## Source pinned

- Repository: https://github.com/rachellelecussan/planetary-analogue-catalogue
- Source commit: `62e6339bdf308de3bc987388d0faa7130cf57de9`
- GeoJSON path: `data/sites.geojson`
- Git blob SHA-1: `156edd871599cf9ac9c083658d14d034f660e35d`
- Generated date in source: 2026-10-12
- Citation: Rachelle Le Cussan, *Planetary Analogue Catalogue*, v0.1 (2026), as recorded in `CITATION.cff`
- Data licence: CC BY 4.0; code licence MIT. This audit uses only the data fields, not photographs or map assets. Any redistribution must retain attribution, licence link and change notice.

## Dataset audit

- **16 site records**, **96 references**, **33 peer-reviewed references**, **1 reference marked unverified**.
- **All 16 site records are Draft**; none is Verified by a second reviewer.
- Primary target distribution: Mars 10, Early Earth 2, Moon 2, Enceladus 1, Europa 1.
- Primary analogue types: Habitability/biological 6, Mineralogical 3, Volcanic 2, Operational 2, Geochemical 1, Impact 1, Geological/geomorphological 1.
- Coordinate precision: approximately 10 km for 10 sites, approximately 1 km for 2, and region-only for 4.
- All 16 records have coordinates, a target feature, a comparison location and at least one reference. Seven records omit the `analogue_limitations` field.
- No India/Maharashtra site is present.
- No non-analogue controls are present.

| Site | Country/region | Primary target | Primary type | Coordinate precision | References (peer-reviewed) |
|---|---|---|---|---|---:|
| Río Tinto | Spain | Mars | Mineralogical | ~10 km | 4 (2) |
| Atacama Desert – Yungay | Chile | Mars | Habitability/biological | ~10 km | 3 (2) |
| Dallol | Ethiopia | Mars | Geochemical | ~1 km | 4 (2) |
| McMurdo Dry Valleys | Antarctica | Mars | Habitability/biological | Region only | 5 (2) |
| Haughton impact structure | Canada | Mars | Impact | ~10 km | 10 (3) |
| Iceland volcanic fields | Iceland | Mars | Volcanic | Region only | 6 (2) |
| Pilbara Craton: Strelley Pool/Dresser | Australia | Early Earth | Habitability/biological | ~10 km | 9 (4) |
| Hamelin Pool / Shark Bay | Australia | Early Earth | Habitability/biological | Region only | 6 (1) |
| Arkaroola | Australia | Mars | Mineralogical | ~10 km | 5 (1) |
| Lanzarote | Spain | Mars | Volcanic | Region only | 6 (2) |
| Bockfjord Volcanic Complex | Svalbard, Norway | Mars | Mineralogical | ~10 km | 8 (1) |
| Mauna Kea | United States | Moon | Operational | ~10 km | 5 (1) |
| Boulby Mine | United Kingdom | Mars | Operational | ~10 km | 4 (2) |
| Lost City Hydrothermal Field | Mid-Atlantic Ridge | Enceladus | Habitability/biological | ~1 km | 5 (2) |
| Lake Vostok | Antarctica | Europa | Habitability/biological | ~10 km | 8 (5) |
| Lava Beds National Monument | United States | Moon | Geological/geomorphological | ~10 km | 8 (1) |

The source's coordinate-precision field is a constraint, not a decorative note: a 0.5 km DEM window centred on a coordinate labelled “approximately 10 km” cannot be treated as a precise sample of the named site. Four region-only records cannot be sampled at point scale from this file.

## Interpretation

This is a **candidate-positive catalogue**, not ground truth:
- The all-Draft review status prevents treating its analogue assertions as independently validated labels.
- Peer-reviewed references support many fields, but the record itself has not passed a second-person review.
- Seven records lack an explicit analogue-limitations field.
- No negative/control sites or matched background samples are supplied.
- The catalogue is a separate compilation from PAAD; record overlap and source overlap have not yet been measured.
- It contains no India/Maharashtra sites, so it does not validate the Lonar/Deccan track.

Use it to broaden candidate discovery and to follow per-site references. Do not train or evaluate a model as if these 16 records were verified positive labels. Preserve each site's target feature, comparison limitations, coordinate precision and reference-level provenance.

## Second independent public source located, not yet acquired

USGS, *Known Terrestrial Analog Sites for Planetary Science*, DOI [10.5066/P9J72921](https://doi.org/10.5066/P9J72921), published 2020-12-18, is a public point layer and CC0 1.0 data release. Its metadata describes impact craters, dunes, volcanoes and other planetary-process analogs. The actual vector file has **not** yet been downloaded or parsed, so its feature count, schema and overlap with PAAD / this catalogue remain UNKNOWN. It is another candidate-positive source, not a control set.

## Next discriminating action

Acquire the USGS point layer from its ScienceBase data release, verify the archive checksum and schema, then compare names/coordinates/analogue types against PAAD and this catalogue without treating missing catalogue entries as negatives. Only after candidate provenance is reconciled should the pipeline construct uncertainty-aware DEM windows and matched background/control samples.


## Access-route audit (2026-11-11)

### USGS point-layer release

The official USGS landing page identifies the release as a point layer, authored by Marc A. Hunter, and marked CC0 1.0. The Data.gov record classifies access as public, but its `Digital Data` distribution points only to the DOI landing page; the second distribution is the original metadata XML. It does not expose a direct vector-file URL in the harvested distribution record.

- USGS landing page: https://www.usgs.gov/data/known-terrestrial-analog-sites-planetary-science
- Data.gov record: https://catalog.data.gov/dataset/known-terrestrial-analog-sites-for-planetary-science
- ScienceBase item ID resolved from the DOI redirect: `5f88940b82cebb8c13d912ee`
- ScienceBase API documentation: https://www.usgs.gov/sciencebase-instructions-and-documentation/api-and-web-services
- Contact in the catalog record: Marc A. Hunter (`mahunter@usgs.gov`).

A metadata-only web retrieval attempt in this research session did not return the ScienceBase item JSON (the browser fetch was unavailable) and the Data.gov metadata XML endpoint returned HTTP 403 to the retrieval client. These are client-side retrieval outcomes, **not** proof that the public data release is inaccessible to ordinary clients. No file was downloaded. Feature count, geometry schema, CRS, checksum, file size and overlap remain UNKNOWN.

Marc A. Hunter was already contacted on 2026-11-10 about a separate PAAD codebook question and has not replied. No second message was sent about this release; this would be a follow-up to a nonresponder.

### Copernicus mask-band lead

The Google Earth Engine catalogue for `COPERNICUS/DEM/GLO30_2024_1` documents five bands: DEM, EDM, FLM, HEM and WBM. It defines FLM as the filling/lineage mask and WBM values as no-water, ocean, lake or river. The same catalogue describes the source as DGED and the elevation surface as a DSM in the EGM2008 vertical datum.

- Catalogue: https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_DEM_GLO30_2024_1
- Copernicus Data Space collection/access description: https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM
- AWS Open Data registry for the anonymous GLO-30 Public COG bucket: https://registry.opendata.aws/copernicus-dem/

This is a **discovery lead, not a mask acquisition**. The Earth Engine 2024_1 collection must not be conflated with E557's pinned 2021 GLO-30 Public AWS COG. No WBM/FLM pixel values were requested or retrieved, and no anonymous direct WBM/FLM object URL was verified. If an Earth Engine route is pursued, it must use a separately authorized account/project; no credentials were used in this audit.

### Revised next gate

1. Retrieve the USGS ScienceBase item JSON through a verified public client route; enumerate file names, sizes and content types before downloading anything.
2. If a vector file exists, download only that release asset, verify its byte length and SHA-256, parse the geometry/schema/CRS, and preserve its source attributes.
3. Compare the USGS layer with PAAD and the 16-site catalogue using provenance-aware name/coordinate matching. Absence from any catalogue is not a negative label.
4. Keep E557's anonymous 2021 DSM sample separate from any future mask layer unless exact product version, tile identity, grid, transform and datum are verified.
