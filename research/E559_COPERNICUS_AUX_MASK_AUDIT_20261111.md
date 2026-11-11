# E559 — Copernicus GLO-30 quality-mask and source-lineage audit (11 November 2026)

## Question

Does the exact public Copernicus GLO-30 tile used by E557 expose its documented quality layers (EDM, FLM, WBM, HEM) and source/accuracy KML objects? If so, do those layers show whether the flat Lonar-centre DSM patch is water-edited, filled, or based on another elevation source?

## Source-backed path contract

- The E557 public tile is `Copernicus_DSM_COG_10_N19_00_E076_00_DEM` in the anonymous `copernicus-dem-30m` AWS bucket, region `eu-central-1`.
- The Copernicus DEM Product Handbook v5.0 (29 November 2022), section 1.2.8.1, documents the DGED package structure: `AUXFILES/` contains `EDM.tif`, `FLM.tif`, `WBM.tif`, `HEM.tif`, and `ACM.kml`; `PREVIEW/` contains `SRC.kml`.
- The filename stem is derived from the handbook's DGED convention: product level DSM, spacing 10, lower-left geocell N19_00_E076_00. The script lists the exact tile's two documented prefixes before touching any object. It does not guess alternative paths.
- The Earth Engine Copernicus GLO-30 catalogue documents the mask bands and class meanings. The product handbook is authoritative for product structure and lineage semantics.

## Frozen access and safety limits

- Anonymous HTTPS ListObjectsV2 only; no credentials, AWS account, API key, redirects, or pagination.
- Maximum 100 keys and 2 MB XML per prefix.
- Only objects actually returned by the exact prefix listing can be inspected.
- GeoTIFF headers are limited to a 16 KiB range. Only tiled masks may be sampled, using two 17×17 windows (Lonar literature lead and nearby comparison point) with an 8 MB uncompressed-block cap.
- KML is read only if it is at most 1 MB; only placemark names and metadata fields are retained.
- No raw DEM, mask pixels, or full KML is retained. The two locations remain neither positive nor negative analogue labels.

## Layer semantics

- WBM: 0 no water, 1 ocean, 2 lake, 3 river.
- FLM: 0 void, 1 edited except filled, 2 not edited/not filled, 3–9 and 100–101 identify fill-source classes.
- EDM: 0 void, 1 not edited, 2 external elevation infill, 3 interpolated, 4 smoothed, 5 airport, 6 raised negative elevation, 7 flattened, 8 ocean, 9 lake, 10 river, 11 shoreline, 12 morphed, 13 shifted.
- HEM: height-error standard deviation; edited areas may use -32767 and must be interpreted with EDM/FLM.
- SRC: source-scene KML with acquisition identifiers, dates/times and height-of-ambiguity metadata.
- ACM: geocell accuracy KML; its global/geocell statistics are not site-specific field validation.

## Result

The exact-head live run completed; detailed measurements follow. The experiment distinguished:
1. masks present and sampled;
2. masks present but not safely sampleable;
3. complete public-prefix listing with no expected masks/lineage objects;
4. incomplete listing/access failure.

A missing object in the complete public prefix is a negative source-access result, not evidence that the product itself lacks the layer.

## Exact-head result (11 November 2026)

- Code/test head `905e6d91e3876b66146c64ea3de9bbf994857ed6`; dedicated Actions [#43064153053](https://github.com/stoicsatvik/NASA/actions/runs/43064153053) succeeded with **11/11 tests** and the bounded live audit. Duplicate push run [#43064147215](https://github.com/stoicsatvik/NASA/actions/runs/43064147215) also succeeded.
- Both exact public prefixes were fully enumerated: AUXFILES 5 objects / 1,753 XML bytes; PREVIEW 8 objects / 2,610 XML bytes. All six actual layers/lineage objects were found. Public COG raster basenames differ from the handbook's simplified DGED names for EDM/FLM/HEM/WBM; listing-driven selection succeeded. ACM/SRC names matched.
- At the frozen Lonar literature-lead coordinate (19.9750 N, 76.5090 E), all 289 WBM samples are `lake`, all 289 EDM samples are `lake`, all 289 FLM samples are `edited_except_filled`, and all 289 HEM samples are sentinel `-32767` (zero valid values). The E557 flat 479.500 m patch is water-edited lake surface, not usable bare-earth/topographic morphology evidence. Exclude it from terrain descriptors; it is not a positive analogue label.
- At the nearby comparison point (19.8000 N, 76.3000 E), all 289 WBM samples are `no_water`, all EDM samples `not_edited`, all FLM samples `not_edited_not_filled`; HEM has 289 valid samples, median 0.4560666 m, range 0.2976013–1.2218320 m. This remains an unlabelled nearby comparison, not a negative analogue.
- ACM KML contains one tile placemark, 16,172 ICESat points and tile-level LE68 1.415 m / LE90 1.665 m statistics; these are not Lonar-specific validation. SRC KML contains 37 source-scene placemarks. Raw mask pixels and full KML were not retained.

## Claim ceiling

- E557 public GLO-30 DSM tile access: SUPPORTED.
- Public availability and bounded sampling of this tile's quality masks/lineage: SUPPORTED.
- Water-edited lake status at the frozen Lonar coordinate: SUPPORTED.
- Bare-earth/topographic interpretation of the E557 flat Lonar patch: REJECTED for this sample.
- Local bare-earth elevation at that coordinate: NOT MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Local validation advantage: NOT YET PROVEN.

## Next gate

If WBM/EDM identifies the flat centre patch as water-edited and FLM/HEM/SRC provide source lineage, classify the E557 centre sample as an edited-water DSM observation and sample a coordinate-uncertainty-aware annulus over unedited terrain. If the exact public prefixes contain no masks, stop guessing paths and seek another independently documented source endpoint or terrain product.
