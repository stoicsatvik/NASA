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

Interpretation:
- valid pixels only near the edge: local nodata core with nearby support;
- valid pixels in the central diagnostic window: support reaches the frozen center;
- no valid pixels in the full neighborhood: local support gap of at least the sampled extent, with physical cause still undetermined.

## Exact-head result

Pending GitHub Actions exact-head execution.

## Claim boundary

This experiment can establish where valid pixels occur relative to the three frozen coordinates. It cannot distinguish an unsurveyed footprint from a masked/invalid terrain region without independent product-footprint or quality-mask provenance.

Cross-body similarity remains NOT YET PROVEN; known-site recovery remains NOT YET MEASURED; novel analogue discovery remains NOT YET PROVEN; route safety is NOT CLAIMED.

## Next action

If valid support reaches the frozen centers, inspect the exact boundary and determine whether a separately preregistered common-support sample is defensible. If all three neighborhoods remain all-nodata, stop repeating local pixel probes and seek independent USGS footprint/quality-mask provenance or preserve partial coverage.
