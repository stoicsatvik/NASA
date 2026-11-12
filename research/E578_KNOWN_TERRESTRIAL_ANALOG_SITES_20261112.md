# E578 — independent USGS known-terrestrial-analogue layer access and schema audit

Date: 12 November 2026

## Question

Does the separate USGS data release "Known Terrestrial Analog Sites for Planetary Science" expose a bounded, anonymous, machine-readable point layer with a defensible site count, schema, geometry type and coordinate reference system?

This is a different ScienceBase item and DOI from the failed E577 Grand Falls release. It is not a retry of the same endpoint or a guessed URL variant.

## Pinned source

- USGS DOI: https://doi.org/10.5066/P9J72921
- ScienceBase item: \`5f88940b82cebb8c13d912ee\`
- Public catalog record: https://catalog.data.gov/dataset/known-terrestrial-analog-sites-for-planetary-science
- USGS landing page: https://www.usgs.gov/data/known-terrestrial-analog-sites-planetary-science
- Catalog description: a point layer of known planetary-science analogue sites, including impact craters, dunes, volcanoes and other processes.
- Catalog license: CC0 1.0 Universal.

## Frozen acquisition limits

- Anonymous HTTPS only; no credentials, tokens, cookies, contact or access-control bypass.
- One projected metadata request, capped at 5 MB.
- Only a metadata-linked, explicit download URI is eligible.
- Only a supported vector package at or below 5 MB is eligible for a full read.
- A 4 KiB HTTP Range request must return HTTP 206 and an exact Content-Range matching the catalogued file size before any full-file read.
- Full file cap: 5 MB. No raw feature rows, site coordinates or source files are committed.
- Preserve source hash, file inventory, feature/record count, schema, geometry type, aggregate spatial bounds and CRS authority candidates only.

## Discriminating outcomes

1. A verified point layer with site-name/type fields and a usable CRS is a candidate positive-site index, not numeric physical ground truth.
2. A layer with no useful site identity or coordinate reference is not E001-ready.
3. An access or size failure is an acquisition result, not evidence that the source contains no useful records.

## Claim boundary

This audit cannot establish cross-body physical similarity, known-site recovery, novel analogue discovery, non-analogue controls or planetary-analog challenge superiority. It can only establish whether an independent public Earth-side candidate-site source is accessible and structurally usable.

## Validation

Deterministic tests and the bounded live probe run on the isolated branch. Exact-head outcomes are appended after Actions completes.


## Exact-head result — 12 November 2026

- Branch head tested: \`7e1bc6ad64beb9318f2f3d44b8144898fcb5f13f\`; draft PR #138, stacked on E577 PR #137.
- Actions run [#43193280091](https://github.com/stoicsatvik/NASA/actions/runs/43193280091) completed successfully. Deterministic tests: **6/6 passed**. The bounded live-probe job completed and uploaded artifact [#13930469672](https://github.com/stoicsatvik/NASA/actions/runs/43193280091/artifacts/13930469672), SHA-256 \`ee198cf96f23a1d1b07fd33120392200e95a34949a04b4110814a45c5dc59963\`.
- Actual source decision: **ACQUISITION_ERROR**, \`TimeoutError: The read operation timed out\`. Metadata HTTP status, file count and selected file are all null. No rows or raw files were acquired; no credentials were used.
- The workflow's green status means the bounded runner handled and preserved the failure correctly. It does **not** mean the USGS data were acquired or that the source contains no records.
- This is an access/transport failure, not a scientific null. E001 known-site recovery remains **NOT YET MEASURED**; cross-body similarity, novel analogue discovery, local validation advantage and challenge-selection superiority remain **NOT YET PROVEN**.
- One-shot guard: the live probe is now pinned to the tested head so later documentation/test updates do not repeat the same external request.



## Geometry/schema gate hardening — 12 November 2026

Code review found that the first E578 classifier treated any non-empty DBF+SHP package as a schema-verified point layer, without checking the SHP geometry type or whether the DBF/PRJ exposed the minimum site identity, analogue type and CRS evidence. That could false-admit a polygon or line layer as a point-site index.

- Added an explicit ESRI point-family allowlist (Point, MultiPoint, PointZ, MultiPointZ, PointM, MultiPointM).
- A non-empty DBF/SHP package with another shape type is now classified as `PUBLIC_VECTOR_LAYER_ACQUIRED_NON_POINT_GEOMETRY`.
- A point geometry is only `PUBLIC_ANALOG_POINT_LAYER_ACQUIRED_SCHEMA_VERIFIED` when the DBF contains a recognized site-identity field and analogue-type field and the PRJ exposes an EPSG authority candidate. Missing evidence remains `PUBLIC_ANALOG_POINT_LAYER_ACQUIRED_SCHEMA_INCOMPLETE`.
- Added three regression tests: admissible point schema, polygon rejection, and incomplete point schema.
- Commit: `e2427ce046f3f864cfaf8f914e40f33aef8870b8`.
- Exact code/test workflow [#43194344911](https://github.com/stoicsatvik/NASA/actions/runs/43194344911) passed **9/9 tests**. The live-probe job was skipped by the one-shot SHA guard; the original bounded attempt remains a timeout, with no source records acquired.

This is an admissibility-classifier correction only. It does not change the USGS source result: E578 remains an access failure, not a source-absence finding or scientific null. E001 known-site recovery remains NOT YET MEASURED.
