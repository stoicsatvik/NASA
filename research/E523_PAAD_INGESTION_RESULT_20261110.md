# E523 — USGS PAAD ingestion and spatial-integrity result

Date: 10 November 2026  
Latest exact-head workflow: [#42879515072](https://github.com/stoicsatvik/NASA/actions/runs/42879515072)  
Branch head: `c49480a2a780af87324f5f1af6de8a5f16f7e86d`  
Artifact: [e523-paad-ingestion, 13792703253](https://github.com/stoicsatvik/NASA/actions/runs/42879515072/artifacts/13792703253)

## Source and acquisition

- Provider: U.S. Geological Survey.
- Dataset: **PAAD: The Planetary Aeolian Analog Database**, release DOI [10.5066/P9IFVZEX](https://doi.org/10.5066/P9IFVZEX), published 20 June 2023.
- ScienceBase item: `64d418c3d34ef477cf3ced10`.
- License stated by the USGS release page: CC0 1.0 Universal.
- Acquisition status: `INGESTED`; primary table is CSV; **45 records**, matching the release metadata.
- Latest download archive SHA-256: `04fd8c98d5a34f482d570ec0156844ea6b7b553001b9eb615faa5c57fc5208ee`.
- ScienceBase item JSON SHA-256: `a3e9572a8d40745a95797890fde0c1e26999ee35d46eb23c4ceb735bab10557b`.
- Normalized CSV SHA-256: `0eb40273f9f685e4fd67181c63fa51e24e2fa348cc850cb1641d5e43af221334`.
- Receipt JSON SHA-256: `ca21a08bf6a851fbc6b3518580fadeffc8ee6a42d466fb7b22a703a20f90ea86`.
- Artifact ZIP SHA-256: `614f5d086e78233cb38e45789cb80304876e1075bfc883f6ccaede850ceb35f0`. Artifact retention expires 10 December 2026.

## Spatial cross-file validation

The release contains a 45-point shapefile in WGS 84 geographic coordinates. The normalized CSV and shapefile point geometry have:

- 45 CSV sites and 45 point geometries.
- 45 matched site names; 0 coordinate mismatches; 0 missing coordinate pairs.
- Bounding box: longitude [-155.3238, 177.5000], latitude [-77.5599, 64.9405].
- Maximum absolute CSV-to-geometry differences: longitude `1.1368683772161603e-13°`, latitude `7.815970093361102e-14°`.

The earlier validator used a 0.00051° tolerance based on the shapefile's three-decimal DBF coordinate *attributes*. It actually compares the full-precision point geometry, not those DBF attributes. That threshold could have admitted a material geometry mismatch. The validator now uses **1e-8°**, reports maximum deltas, and rejects non-POINT geometry.

Regression tests prove that an exact coordinate match passes, a 0.0001° geometry shift is rejected, and a non-POINT layer is rejected. The latest live receipt passes all 45 records under the tighter threshold. I independently re-read the artifact's normalized CSV and shapefile using Python's CSV and PyShp readers and reproduced the 45/45 match and maximum deltas.

This tolerance is only a cross-file consistency check. It is **not** a statement of the sites' absolute positional accuracy.

## Deterministic validation and preserved failure

- Latest exact-head run [#42879515072](https://github.com/stoicsatvik/NASA/actions/runs/42879515072): **12 tests passed**.
- Live USGS acquisition: **45/45 records ingested**, release count matched, CRS WKT present, 45 point geometries checked.
- The original CLI receipt-key failure remains preserved in [run #42869223993](https://github.com/stoicsatvik/NASA/actions/runs/42869223993). It was a software-interface failure: the CLI read the obsolete `count_matches_release_description` key after the receipt schema had moved to `count_matches_release_metadata`. The corrected branch fixes that key.
- The intermediate 0.00051° coordinate threshold is also preserved in earlier run history; it was replaced after inspecting the actual geometry coordinates and recognizing that DBF attribute precision was not relevant to the geometry comparison.

## Data quality and limits

Missing-value counts follow the FGDC metadata convention that literal `NaN` means missing:

| Field | Missing of 45 |
|---|---:|
| Areal coverage | 12 |
| Sand composition | 16 |
| Sand source | 3 |
| Elevation | 1 |
| Latitude / longitude | 0 / 0 |

The 45 sites span 12 country/region labels. The metadata defines 13 bedform codes; the table contains 30 distinct multi-code combinations. All 45 site names and coordinate pairs are unique.

The metadata describes elevation and areal coverage as approximate. Some elevation values were estimated from GMTED2010 where source references did not provide values. Missing values remain missing; no values were imputed.

PAAD is a catalogue of **terrestrial dune-field analog sites**, not a Mars surface raster, not a Jezero terrain model, and not route-safety ground truth. The 45-site release is a literature-derived subset with a US-heavy sampling bias; the source does not establish global representativeness.

## Interpretation and next experiment

PAAD is suitable as a provenance-backed catalogue for studying *Earth analog-site selection*. It cannot support local Mars traversability or hazard claims. A defensible next experiment would define a preregistered, interpretable similarity feature set for comparing terrestrial analog sites with a specific Mars region, preserve missingness and approximate-field flags, and test ranking stability against simple baselines. First establish that each feature is available at compatible spatial resolution and uncertainty. Do not convert this 45-site catalogue into a route-cost surface or claim that its coordinates validate a Martian route.
