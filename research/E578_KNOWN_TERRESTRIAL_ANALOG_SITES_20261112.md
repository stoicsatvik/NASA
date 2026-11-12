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
