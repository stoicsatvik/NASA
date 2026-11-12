# E570 — bounded real LOLA GDR sample and seam audit

**Date:** 12 November 2026  
**Branch:** `research/e570-lola-gdr-window-20261112`  
**Parent:** E569 paired HiRISE support  
**Status:** exact-head bounded acquisition and metadata controls passed

## Question

Can the official PDS3 LOLA GDR product be ingested as a small real lunar sample while preserving units, reference-sphere semantics, grid registration, missing-value behavior, provenance and transport bounds?

## Pinned source

- Product: `LRO-L-LOLA-4-GDR-V1.0 / LDEM_16_FLOAT`
- PDS archive directory: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/float_img/
- PDS label: https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/cylindrical/float_img/ldem_16_float.lbl
- Product page: https://pds-geosciences.wustl.edu/missions/lro/lola.htm
- Dataset DOI: https://doi.org/10.17189/1520642
- Bundle DOI: https://doi.org/10.17189/tnyt-7007
- Label SHA-256: `b39b1e1ec3d7dbd0ec451f1d4df0304ab383f6ebbc52601b8bf819e0a8d5111a`

The pinned label declares a 2,880 × 5,760 pixel-registered simple-cylindrical grid, 16 pixels/degree, 1.89521 km/pixel at the equator, 32-bit `PC_REAL`, kilometre units, scaling factor 1, a 1,737.4 km reference-sphere offset, and the `MEAN EARTH/POLAR AXIS OF DE421` coordinate system. The data spans 13 July 2009 through 29 November 2016; the product was created 15 March 2019.

Important value semantics from the product label:
- `HEIGHT = DN × SCALING_FACTOR`.
- `PLANETARY_RADIUS = DN × SCALING_FACTOR + OFFSET`.
- The label says topography is `PLANETARY_RADIUS − GEOID_RADIUS`, with geoid radius derived from a gravitational equipotential model.
- Therefore the sampled DN-derived values are reference-sphere-relative heights, not absolute planetary radius and not geoid-corrected topography.
- The label declares no `MISSING_CONSTANT` or `MISSING_VALUE`; the parser now fails closed if either appears in a future label. Non-finite samples are counted as missing.

The label also warns that the grid files were produced in 45° latitude bands and that edge artifacts may occur at those boundaries. This warning materially changes interpretation of window C below.

## Frozen acquisition and safety controls

- Three analyst-selected 11 × 11 windows; they are not geological labels, known analogues or ground truth.
- Exactly three HTTP byte-range requests; each requested 230,444 bytes.
- Label transfer: 5,139 bytes. Range payload: 691,332 bytes. Total body transfer: **696,471 bytes**, below the 1,000,000-byte cap.
- Full IMG size is 66,355,200 bytes; the full IMG was not downloaded.
- Each response is streamed with `stream=True`; HTTP 206 and the exact `Content-Range` are validated before reading any body bytes. The body reader stops at the requested byte count and rejects short/oversized bodies.
- The PDS label is independently capped at 64 KiB. The total-transfer receipt includes label plus raster range payloads.
- Projection center, offsets, rotation, pixel extent, geographic bounds, dimensions, type, units and scaling are pinned and validated before pixel indexing.
- Raw pixel values are used in memory only. The receipt retains source/range hashes and aggregate descriptors, not raw pixels or coordinates beyond the three analyst-selected centers.

## Exact-head validation

- Code/test head: `3625a95acf4df69a5d1ccb0181790d6939c16327`.
- Exact-head Actions: https://github.com/stoicsatvik/NASA/actions/runs/43133147310
- Result: **19/19 deterministic tests passed**; bounded live acquisition completed.
- Compact receipt artifact: https://github.com/stoicsatvik/NASA/actions/runs/43133147310/artifacts/13905583586
- Final outcome: `LOLA_METADATA_AND_THREE_REAL_WINDOWS_ACQUIRED`.
- Earlier acquisition run #43129825676 is preserved as the initial 11-test result. Subsequent commits added streaming range guards, exact projection checks and a latitude-band seam warning; intermediate concurrency-cancelled runs were superseded by the final successful exact-head run.

## Bounded sample results

| Window | Centre (lat, east lon) | Zero-based pixel | Valid / missing | p95–p05 reference-height range | Median / p90 gradient proxy | 45° seam flag |
|---|---:|---:|---:|---:|---:|---|
| A | (32.8°, 344.4°) | (915, 5510) | 121 / 0 | 179.60 m | 0.210° / 2.344° | No |
| B | (8.5°, 31.4°) | (1304, 502) | 121 / 0 | 418.61 m | 0.765° / 4.033° | No |
| C | (−45.0°, 90.0°) | (2160, 1440) | 121 / 0 | 1,662.64 m | 5.138° / 12.918° | **Yes, −45°** |

All three windows had 121 finite samples and zero non-finite samples. The three range hashes are retained in the compact receipt.

### Critical seam caveat

Window C is centered exactly at −45° and spans approximately −45.3125° to −44.6875°. It crosses a PDS-documented 45° latitude-band boundary. Its much larger reference-height range and gradient proxy **must not be interpreted as natural terrain roughness** until a boundary-sensitivity experiment is run. The PDS warning makes a seam artifact plausible, but this sample does not prove that the seam caused the observed values.

Windows A and B are off the documented 45° seams, but remain arbitrary analyst-selected windows without geological labels. Their descriptors are ingestion diagnostics only.

## Engineering changes

- Replaced buffered HTTP range reads with bounded streaming. A server that ignores Range is rejected before its body is read; a server that sends a mismatched/oversized body is stopped at the explicit cap.
- Counted label bytes inside the 1 MB total-transfer cap and retained partial receipts on failure.
- Added fail-closed checks for a declared missing-value sentinel until its semantics are implemented.
- Pinned projection center, offsets, rotation, pixel bounds, geographic extent and coordinate-system name to the source label.
- Added an explicit diagnostic for windows intersecting the documented 45° latitude-band seams.

## Interpretation boundary

**Supported:** bounded ingestion of this pinned PDS3 LOLA product, its declared metadata, and three real 11 × 11 windows under a measured transfer cap.

**Not established:** geoid-corrected topography, terrain accuracy, seam-free morphology, cross-body similarity, known-site recovery, geological classification, route safety, or novel analogue discovery. No cross-body feature table or model score is produced.

## Next falsifiable experiment — E571

Use the existing −45° receipt as the seam-crossing baseline. Acquire two additional 11 × 11 windows at the same longitude, centred at −44.5° and −45.5°, which lie on opposite sides and do not cross the boundary. Retain row-level aggregate summaries only and test whether the boundary-centred window shows a discontinuity relative to the off-boundary windows. Preserve the result even if no discontinuity is detected. This will be a seam-sensitivity diagnostic, not proof of the true lunar surface.

After that, choose a separate Diviner or Mars MOLA bounded sample only when its spatial support, units, temporal semantics and physical meaning can be recorded independently. Do not combine raw Moon/Mars values or claim analogue recovery from these three arbitrary windows.