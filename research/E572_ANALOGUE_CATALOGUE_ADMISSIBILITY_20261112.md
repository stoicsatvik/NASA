# E572 — independent public analogue-catalogue admissibility

Date: 12 November 2026

## Question

Can an independent public catalogue supply a defensible E001 cohort: independently reviewed Mars/Moon analogue positives, explicit non-analogue controls, and physically comparable numeric descriptors?

## Source and provenance

- Repository: [Rachelle Le Cussan, Planetary Analogue Catalogue](https://github.com/rachellelecussan/planetary-analogue-catalogue)
- Pinned commit: \`62e6339bdf308de3bc987388d0faa7130cf57de9\`
- File: \`data/sites.geojson\`
- Git blob SHA-1: \`156edd871599cf9ac9c083658d14d034f660e35d\`
- Exact file size: 143,202 bytes
- Dataset license: CC BY 4.0; attribution retained in the result receipt.
- Catalogue README describes 16 sites, 96 references and 42 photos. The source data were generated 2026-10-12.

The catalogue is a separate public candidate inventory. It is not treated as NASA ground truth, and its own review-status field is respected. No source GeoJSON, photos or coordinates are copied into this repository.

## Method

1. Fetch only the pinned raw GitHub file, with a 200 kB cap, 20-second timeout and final-host validation.
2. Verify the exact Git blob SHA-1 and byte count before parsing.
3. Reject duplicate site IDs, non-Point geometry, invalid/non-finite coordinates and out-of-range longitude/latitude.
4. Restrict the audit to primary Mars/Moon analogue records.
5. Count review states, analogue-type families, reference support, coordinate precision and numeric-field coverage.
6. Distinguish contributor access/hazard ratings from physical descriptors.
7. Apply a minimal E001 input gate: at least one family with two Verified positives, an explicit negative control, a common physical numeric descriptor, and a numeric target-body measurement field.

This is a source-admissibility test, not a recovery experiment. No ranks, accuracy, p-values or analogue discoveries are computed.

## Exact result

| Measure | Result |
|---|---:|
| Total catalogue features | 16 |
| Primary Mars/Moon records | 12 |
| Mars / Moon | 10 / 2 |
| Verified in-scope positives | 0 / 12 |
| Draft in-scope positives | 12 / 12 |
| In-scope references | 68 |
| Peer-reviewed references | 21 |
| Peer-reviewed references supporting analogue/feature/science claims | 20 |
| Unverified references | 1 |
| Explicit non-analogue controls | 0 |
| Common numeric fields | \`access_level\`, \`hazard_rating\` |
| Common physical numeric descriptors | 0 |
| Numeric target-body measurement fields | 0 |
| Minimum E001 input gate | **FAIL** |

Primary analogue-type counts:

- Mineralogical: 3
- Habitability / biological: 2
- Volcanic: 2
- Operational (instrument, rover or crew testing): 2
- Geochemical: 1
- Impact: 1
- Geological / geomorphological: 1

Four broad catalogue types have at least two records, but these labels are not sufficiently specific to establish physically homogeneous reference families. More importantly, none of the records is marked Verified.

Numeric site-property coverage is incomplete:

| Field | Records with a numeric value |
|---|---:|
| access_level | 12/12 |
| hazard_rating | 12/12 |
| altitude_max_m | 5/12 |
| altitude_min_m | 2/12 |
| extent_km2 | 6/12 |
| ph_min / ph_max | 3/12 each |
| temp_min_c | 4/12 |
| temp_max_c | 6/12 |

The only fields shared by all 12 records are access and hazard ratings. They are contributor ratings, not physical terrain/material/environment descriptors. The catalogue's \`compare\` blocks provide planetary map context, not measured planetary feature vectors.

Coordinate precision:

- Approximately 10 km: 8 records
- Region only: 3 records
- Approximately 1 km: 1 record

Thus 11/12 records are too coarse for direct local high-resolution raster sampling without a better, independently sourced footprint. They can seed regional searches, not pixel-level extraction.

## Interpretation

**The catalogue is useful as a candidate-site discovery index, but it is not E001-ready.**

It does add 12 traceable Mars/Moon candidate leads and 68 references. It does not provide verified labels, non-analogue controls, a shared physical feature matrix, or planetary measurement vectors. Treating its broad analogue-type labels or subjective access/hazard ratings as physical similarity features would introduce label and construct leakage.

This is a negative result and is preserved as such. No E001 run was attempted because the required input matrix does not exist. The result does not reject the sites as analogues; it rejects this catalogue snapshot as a stand-alone E001 training/evaluation dataset.

## Claim states

- Repo operating system: SUPPORTED
- This catalogue as a candidate-site discovery source: SUPPORTED
- This catalogue as E001 labels/features by itself: REJECTED
- Cross-body similarity: NOT YET PROVEN
- Known-site recovery: NOT YET MEASURED
- Novel analogue discovery: NOT YET PROVEN
- Local validation advantage: NOT YET PROVEN
- Planetary-analog challenge superiority: NOT YET PROVEN

## Next move

Stop searching for another catalogue-only substitute. Acquire one analysis-grade, source-pinned Earth dataset for a narrow physical family (the previously identified Grand Falls aeolian source is a candidate), with actual raster/point data, footprints, units, resolution, nodata and uncertainty. Add defensible non-analogue controls from an independent source, then construct a matched-support Earth/planetary feature matrix and run frozen random, Euclidean and physically weighted leave-one-site-out E001 baselines. Preserve nulls; do not tune to rescue named sites.

India/Maharashtra leads remain literature leads, not discoveries. No field measurements, permissions, site access or local validation are claimed.


## E001 target-measurement completeness hardening (12 November 2026)

The minimum E001 gate now requires at least one numeric target-body measurement field to be populated for **every** in-scope positive/control record. A field appearing on only one candidate is reported as partial coverage and cannot satisfy a matched feature-matrix requirement. The synthetic regression explicitly rejects that sparse-field case while retaining the fully matched positive/control fixture. The pinned live catalogue still has no target measurement fields: its `compare` values are only map-context latitude, longitude and view radius. The source-level conclusion is unchanged: candidate-site index SUPPORTED; stand-alone E001 labels/features REJECTED; known-site recovery NOT YET MEASURED.
