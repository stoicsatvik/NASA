# E523: PAAD public-data ingestion result (2026-11-10)

## Objective

Acquire the public USGS Planetary Aeolian Analog Database (PAAD) release reproducibly, preserve source metadata, and validate that the normalized table is consistent with the release's spatial file without overstating coordinate accuracy or global representativeness.

## Source and provenance

- Provider: U.S. Geological Survey, Astrogeology Science Center
- Release: [PAAD: The Planetary Aeolian Analog Database](https://www.usgs.gov/data/paad-planetary-aeolian-analog-database)
- DOI: [10.5066/P9IFVZEX](https://doi.org/10.5066/P9IFVZEX)
- ScienceBase item: `64d418c3d34ef477cf3ced10`
- Release date: 2023-06-20
- License: CC0 1.0 Universal
- Primary source file: `Planetary Aeolian Analog Database_core attributes.csv`
- Coordinate CRS: WGS 84 geographic coordinates

The workflow retains the original archive, FGDC metadata, normalized CSV, and a JSON receipt with source/item/archive hashes.

## Exact-head acquisition result

- Commit: `b80027910fa7c850407e8a69ce1e1c91f2da615f`
- Workflow: [#42902679796](https://github.com/stoicsatvik/NASA/actions/runs/42902679796)
- Deterministic parser/provenance tests: **10 passed**
- Live status: `INGESTED`
- Primary table: CSV
- Records: **45**
- CSV count matches FGDC release metadata: **true**
- CSV/shapefile consistency: **45 matched, 0 mismatches, 0 missing coordinate pairs**
- Coordinate comparison tolerance: 0.00051 degrees
- Artifact: `e523-paad-ingestion`, ID `13801934866`

The coordinate tolerance accounts only for the CSV's four decimal places versus the shapefile's three. This is a cross-file consistency check, not a positional-accuracy estimate.

## Field metadata and uncertainty semantics

Units are extracted from the FGDC attribute definitions rather than inferred solely from field names.

| Field | Unit | Approximation basis |
|---|---|---|
| Center_Latitude | decimal degrees | Not marked approximate |
| Center_Longitude | decimal degrees | Not marked approximate |
| Elevation | m | FGDC definition says elevation may be estimated; at least three GMTED2010 measurements are reduced to a site median where cited elevation is unavailable |
| Areal_Coverage | km2 | USGS release description explicitly calls the core attribute approximate |

The release description is the basis for the areal-coverage approximation flag; the FGDC field definition supplies km2 but does not itself use the word “approximate”.

## Missingness and sampling limitations

| Field | Missing records |
|---|---:|
| Areal_Coverage | 12 / 45 |
| Composition_of_Sand | 16 / 45 |
| Sand_Source | 3 / 45 |
| Elevation | 1 / 45 |
| Center_Latitude | 0 / 45 |
| Center_Longitude | 0 / 45 |

USGS describes the first release as a subset of terrestrial analog sites, with more US-based sites because the initial literature search and source authors were predominantly US-based. It is not a balanced global sample. Most sites currently have only one reference. The table is a discoverability dataset, not a validated ranking of planetary-analog suitability.

## Implementation repairs

1. The first v2 acquisition successfully fetched and parsed the source but exited with a `KeyError`: the console summary still read the v1 field `count_matches_release_description` after the receipt schema changed to `count_matches_release_metadata`. A schema-bound summary helper and regression test now guard this contract.
2. The first FGDC metadata parser used field-name lookups for units. It now parses decimal degrees, metres, and km2 from attribute definitions. Synthetic tests deliberately use unrelated field labels to ensure units come from the metadata text.
3. Approximation provenance is explicit: elevation uses the FGDC definition; areal coverage uses the USGS release description.
4. Intermediate failures remain visible in GitHub Actions history. They were not deleted or rewritten.

## Next research gate

Crosswalk PAAD site attributes and locations with the MGD3 spatial release only after matching definitions, spatial scales, and coverage. Test whether the added descriptors provide useful, independently documented analog context. Do not turn the 45-site subset into a global suitability score or a Mars traverse recommendation without additional evidence.
