# E524 — PAAD / MGD3 physical-feature admissibility (2026-11-11)

## Question

Can the currently ingested PAAD Earth CSV and 2018 MGD3 Mars global-summary workbooks support a physically comparable feature matrix for E001?

## Frozen source receipts

- E523 USGS PAAD normalized CSV: SHA-256 `0eb40273f9f685e4fd67181c63fa51e24e2fa348cc850cb1641d5e43af221334`; 45 rows; 45 unique site names; 45 unique coordinate pairs; 13 raw dune-type tokens.
- E318 2018 MGD3 database ZIP: SHA-256 `92771c23cfa4a64dfcc38f5ad29de00adfa41b9f321d3665beb2112eefe3485e`.

PAAD missingness (the literal string `NaN` is treated as missing): composition 16/45, approximate areal coverage 12/45, sand source 3/45, elevation 1/45, climate description 0/45. Climate values are source-language descriptions, not validated Köppen codes.

## MGD3 workbook profile

| Profile | Worksheet rows, not unique sites | Thermal inertia | Albedo | Mineral fields nonempty |
|---|---:|---:|---:|---:|
| Equatorial, ocks <7000 | 58 | 58 | 58 | 42 |
| Equatorial, all ocks | 59 | 58 | 58 | 52 |
| South Polar, ocks <7000 | 51 | 51 | 51 | 37 |
| South Polar, all ocks | 53 | 51 | 51 | 48 |

The profiled 2018 summary tables contain dune IDs, ordinal area ranks, mineral abundances/errors, stability index, thermal inertia and albedo. They do not expose coordinate or footprint fields. Worksheet row counts are not unique-site counts and must not be summed as such.

## Executed strict-comparability test

Nine descriptor families were checked: morphology, mineral composition, thermal inertia, albedo, elevation, area, climate, coordinates and sand source. **Zero are directly admissible** from the current PAAD CSV plus the profiled 2018 workbook summaries:

- PAAD morphology tokens and MGD3 stability classes use different taxonomies; raw-token overlap is not a semantic crosswalk.
- PAAD composition is heterogeneous narrative text; MGD3 reports instrument-derived mineral abundance and errors. Detection limits, units and mineral basis are not harmonized.
- PAAD has no thermal-inertia or albedo fields.
- The 2018 summary workbook exposes area rank, not Mars physical area; no coordinates/footprints or elevation appear in the profiled summary tables.
- PAAD climate values are free text, not validated Köppen codes.

No independent non-analogue labels are present. No distance metric, E001 ranking or recovery score is admissible from these two sources alone.

## Scope correction discovered during source audit

This is explicitly a **2018 workbook-summary-only** conclusion, not a conclusion that the full MGD3 project lacks spatial data. The official USGS 2007 MGD3 release separately documents dune polygons and a 37-column spatial attribute table. That source is recorded in E525 as documented but not yet ingested.

## Result and claim state

- PAAD live ingestion: SUPPORTED (E523).
- MGD3 2018 workbook ingestion: SUPPORTED (E318).
- Direct shared physical descriptors in the currently profiled PAAD/2018-workbook pair: **0**.
- E001 known-site recovery: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- Novel analogue discovery and local validation advantage: NOT YET PROVEN.

## Validation

The source-pinned command produced 45 PAAD rows, four MGD3 global-summary profiles, and zero directly admissible descriptors. Eight local unit tests passed, including source-hash gates, duplicate-site rejection, literal-NaN missingness, worksheet-row semantics, no-negative-label inference and the documented-not-ingested spatial-source boundary. Exact-head GitHub CI has not yet run.

## Next decisive experiment

Acquire the official MGD3 spatial layer, record its source hash and CRS, inspect the 37-column schema, and attempt a Dune ID join to the 2018 workbook. Only then compare polygon area, MOLA elevation, dune type and orientation against PAAD with matched spatial support and uncertainty. Keep unlabeled sites unlabeled; do not manufacture negatives.