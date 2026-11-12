# E596 — independent public planetary-analogue catalogue provenance audit

Date: 12 November 2026  
Branch: \`research/e596-analogue-catalogue-provenance-audit-20261112\`, stacked on E594.  
Source: Rachelle Le Cussan, *Planetary Analogue Catalogue* v0.1, repository commit \`62e6339bdf308de3bc987388d0faa7130cf57de9\`, GeoJSON blob \`156edd871599cf9ac9c083658d14d034f660e35d\`. Data licence: CC BY 4.0; code licence: MIT.

## Question

Can an independent public catalogue provide a defensible, geospatially usable set of known analogue labels for the E001 leave-one-site-out recovery benchmark?

## Exact snapshot audit

- 16 site records.
- 16/16 records have \`review_status = Draft\`; 0 are Verified.
- 96 references and 42 photos are present in the snapshot.
- Coordinate precision: 10 records approximately 10 km, 2 approximately 1 km, 4 region-only.
- 7 records are marked sensitive.
- Primary target bodies: Mars 10, early Earth 2, Moon 2, Enceladus 1, Europa 1.
- Primary analogue types: habitability/biological 6, mineralogical 3, volcanic 2, operational 2, geochemical 1, impact 1, geological/geomorphological 1.

The source README explicitly says new entries start Draft and become Verified only after someone other than the author checks science, references and ratings. The current snapshot therefore supplies a useful candidate index and references, but **zero records are admitted as E001 ground-truth labels**. The audit retains site names and categorical metadata only; no coordinates or geometry are copied.

## Candidate index (no coordinates retained)

| Site | Primary target | Type | Coordinate precision | Review | References |
|---|---|---|---|---|---:|
| Río Tinto | Mars | Mineralogical | ~10 km | Draft | 4 |
| Atacama Desert – Yungay area | Mars | Habitability / biological | ~10 km | Draft | 3 |
| Dallol | Mars | Geochemical | ~1 km | Draft | 4 |
| McMurdo Dry Valleys | Mars | Habitability / biological | Region only | Draft | 5 |
| Haughton impact structure | Mars | Impact | ~10 km | Draft | 10 |
| Iceland volcanic fields (Holuhraun and Krafla) | Mars | Volcanic | Region only | Draft | 6 |
| Pilbara Craton: Strelley Pool and Dresser formations | Early Earth | Habitability / biological | ~10 km | Draft | 9 |
| Hamelin Pool Marine Nature Reserve, Shark Bay | Early Earth | Habitability / biological | Region only | Draft | 6 |
| Arkaroola | Mars | Mineralogical | ~10 km | Draft | 5 |
| Lanzarote | Mars | Volcanic | Region only | Draft | 6 |
| Bockfjord Volcanic Complex | Mars | Mineralogical | ~10 km | Draft | 8 |
| Mauna Kea | Moon | Operational | ~10 km | Draft | 5 |
| Boulby Mine | Mars | Operational | ~10 km | Draft | 4 |
| Lost City Hydrothermal Field | Enceladus | Habitability / biological | ~1 km | Draft | 5 |
| Lake Vostok | Europa | Habitability / biological | ~10 km | Draft | 8 |
| Lava Beds National Monument | Moon | Geological / geomorphological | ~10 km | Draft | 8 |

## Independent source cross-check

NASA's official Analog Explorer gallery lists 11 Earth/planet pairs, including Kilauea/Moon, Atacama/Mars, Iceland/Mars and Iceland/Moon. The USGS official terrestrial-analogs page identifies Meteor Crater, Cinder Lake, SP Mountain, Sunset Crater, Grand Falls, San Francisco Volcanic Field, Lava River Cave, Verde Valley and Grand Canyon, with stated use cases. These are useful independent candidate sources, but their page text does not expose a ready coordinate-bearing site-feature matrix. The USGS TADP/ScienceBase route remains a possible structured source; the prior metadata probe timed out.

## E001 decision

**E001 remains NOT YET MEASURED.** The catalogue cannot be used as ground truth in its current state: all records are Draft, and several site geometries are too coarse for a point sample without primary-source extent resolution. A 16-site list is not a labelled benchmark. The two-point Lonar/NASADEM sample remains descriptive only; neither Lonar nor its nearby comparison point is a validated positive/negative label.

No draft labels were promoted, no sensitive coordinates were copied, no raw data was committed, and no author was contacted. This source audit does not prove cross-body similarity, known-site recovery, novel discovery or local validation advantage.

## Next gate

Independently review primary references for one narrow family (for example volcanic or impact analogues), establish site extents and coordinate uncertainty from primary geospatial sources, and then obtain matched-footprint DEM/MOLA descriptors. Keep candidate controls distinct from known negatives. Only then run E001 random, Euclidean and physically weighted baselines with leave-one-site-out folds, null/permutation tests and false-positive inspection.
