# E554 — bounded HiRISE nodata-neighborhood audit (11 November 2026)

## Question

Do the three E550 all-nodata positions sit inside a larger local support gap, or does valid HiRISE support occur immediately around the sampled windows?

This is a support-geometry diagnostic only. It does not replace the original E550 measurements or reinterpret nodata as a physical measurement.

## Frozen inputs

- E550 compact patch summary: `data/e550_patch_summaries.json`.
- Three positions: `x15_y15`, `x50_y85`, `x85_y85`.
- USGS Mars 2020 TRN HiRISE DTM, DOI [10.5066/P9REJ9JN](https://doi.org/10.5066/P9REJ9JN).
- E548-pinned PDS3 label and GeoTIFF nodata semantics.
- No alternative product, fitted registration, imputation or new candidate site.

## Experiment

For each missing E550 position, acquire one 128×128 float32 neighborhood (nominally 128 m × 128 m) centered on its frozen map coordinate using exact HTTP byte ranges.

- Summarize valid/nodata/non-finite counts.
- Retain an 8×8 grid of 16×16-pixel valid counts.
- Separately report the central 64×64 support.
- Persist only counts, hashes, georeferencing and transport receipts. Raw pixels are not committed or uploaded.
- Transfer budget: 1 MB.

## Exact-head result

- Draft PR #114, branch `research/e554-hirise-nodata-neighborhood-20261111`.
- GitHub Actions run [#43044286332](https://github.com/stoicsatvik/NASA/actions/runs/43044286332): SUCCESS; deterministic mask-summary tests and the bounded live source probe passed.
- Pinned source: USGS 2020 Mars 2020 TRN HiRISE DTM, DOI 10.5066/P9REJ9JN.
- Nodata semantics: GeoTIFF `GDAL_NODATA = -3.4028226550889045e+38`; no conflict with the E548 PDS3 label.
- All three 128×128 neighborhoods were **16,384/16,384 nodata pixels**, with **0 usable pixels** and **0 valid pixels in the central 64×64**.
- Exact byte-range transport: **394 requests / 368,991 bytes**, below the 1 MB cap.
- The local support gap therefore extends across each sampled 128 m neighborhood. This does **not** establish why the product is nodata there.

## Interpretation

Outcome: **THREE_NEIGHBORHOODS_ALL_NODATA**.

The nearby-support-boundary explanation is not supported within the sampled 128 m neighborhoods. Remaining explanations include:
1. the product's actual surveyed/compiled footprint excludes the locations;
2. a quality or terrain mask excludes the locations despite the raster bounding box;
3. another product-specific nodata rule applies.

The current experiment cannot distinguish these explanations. Do not move the patch centers, impute elevations, or fit a correction surface to manufacture common support.

## Claim boundary

- Local 128 m nodata neighborhoods: MEASURED.
- Physical cause of nodata: NOT DETERMINED.
- Common valid support at the three E550 positions: NOT RECOVERED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

## Next action

Stop repeating local pixel probes. Obtain independent official USGS footprint/quality-mask provenance or a separate validated source layer. If no defensible common support can be established, preserve the six-patch partial-coverage result and return compute to independent Earth positive-site/control discovery before E001.
