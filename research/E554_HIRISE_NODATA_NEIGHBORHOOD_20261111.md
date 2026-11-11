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

Current code head `d347746f80ee7e01649b58383eedeb6fe7c04704`.

- Exact-head workflow [#43044286332](https://github.com/stoicsatvik/NASA/actions/runs/43044286332) succeeded.
- Deterministic tests: **6/6 passed**.
- All three frozen 128×128 neighborhoods were measured.
- Each neighborhood contained **16,384 finite nodata pixels, zero non-finite pixels, and zero usable pixels**; the central 64×64 diagnostic window also had zero usable pixels.
- All three sampled byte windows had the same SHA-256 `985c185499065102b54acaa4215e54bfa15bb35b3bd172b268638b9b8aec069c`, consistent with the constant declared nodata value rather than a measured surface.
- Total transfer: **368,991 bytes across 394 exact range requests**, below the 1 MB cap.
- The PDS3 label SHA-256 is `99b972f7ea13f9e05e9d3f265435a0566b53dbde4088781673edeb0b6d24cade`.

**Result:** all three positions remain unsupported across at least the sampled 128 m × 128 m neighborhoods. This is stronger evidence for local product-support gaps than the original 113×113 windows, but it still does not identify the physical cause. It does not establish that the locations were outside stereo coverage, nor that they were intentionally masked.

Receipt artifact: [#13865239568](https://github.com/stoicsatvik/NASA/actions/runs/43044286332/artifacts/13865239568) (1,904-byte ZIP; raw pixels not retained).

## Claim boundary

This experiment can establish where valid pixels occur relative to the three frozen coordinates. It cannot distinguish an unsurveyed footprint from a masked/invalid terrain region without independent product-footprint or quality-mask provenance.

Cross-body similarity remains NOT YET PROVEN; known-site recovery remains NOT YET MEASURED; novel analogue discovery remains NOT YET PROVEN; route safety is NOT CLAIMED.

## Next action

Stop repeating local pixel probes around these three coordinates. Seek independent product-footprint or pixel-provenance evidence. The USGS Astrogeology HiRISE DTM documentation identifies a Figure-of-Merit (FOM) image as the definitive per-pixel provenance layer for standard PDS HiRISE DTMs, but the pinned 2020 TRN product's public directory must be checked separately; do not assume the generic FOM asset exists for this flight mosaic. If no product-specific provenance asset is exposed, ask the designated PDS/USGS support contact or preserve the three positions as unsupported.
