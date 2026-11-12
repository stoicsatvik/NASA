# E573 — HiRISE support sensitivity under a 10.2 m translation envelope

Date: 12 November 2026  
Branch: \`research/e573-hirise-translation-envelope-20261112\`  
Parent: E572 / PR #131  
Status: bounded live validation retry after range-plan preflight correction

## Question

Does the apparent 2025 HiRISE DTM point-support advantage over the 2020 HiRISE DTM persist when the same frozen 346 observed MOLA point centers are tested under coherent translations up to the published 10.2 m, 99th-percentile 2025 HiRISE-to-CTX alignment statistic?

This is a data-readiness sensitivity gate for the Martian Map alternative, not a route-safety or analogue-recovery experiment.

## Frozen inputs and design

- Reuse the E563/E569 33×33 MOLA window at 18.3995°N, 77.27025°E; only the 346 bins with positive MOLA shot counts enter the denominator.
- Re-acquire the 2020 Mars 2020 TRN HiRISE DTM through the bounded row-range reader.
- Re-acquire only the pinned 2025 MSR HiRISE DTM ZIP member; the full archive and orthoimage/confidence members are not downloaded.
- Compare 13 deterministic map translations: zero; four cardinal shifts at 5.1 m; four cardinal shifts at 10.2 m; and four diagonal shifts whose radial magnitude is 10.2 m.
- Compute two distinct scenarios:
  1. common-mode: apply the same shift to both products relative to the MOLA point grid;
  2. differential-2025: hold the 2020 product at zero and shift only the 2025 product.
- Reconcile the zero-shift aggregates against E563/E568: 346 observed points, 164 valid 2020 samples and 259 valid 2025 samples.
- Retain masks only in memory. Persist aggregate counts, metadata and hashes; no raw elevations or point coordinates.

## External alignment evidence

The USGS 2025 MSR HiRISE product metadata and the LPSC 2025 paper report HiRISE-to-CTX alignment below 6 m at the 93rd percentile and below 10.2 m at the 99th percentile. This is a percentile statistic, not a hard bound, and it is not an independent MOLA tie or pointwise registration field.

Sources:
- USGS product: https://astrogeology.usgs.gov/search/map/mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic
- LPSC 2025 paper: https://www.hou.usra.edu/meetings/lpsc2025/pdf/1627.pdf
- 2020 HiRISE product: https://astrogeology.usgs.gov/search/map/Mars/Mars2020/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40

## Exact-head result and preserved failure

Initial exact-head workflow [#43152358641](https://github.com/stoicsatvik/NASA/actions/runs/43152358641) passed all 4 deterministic tests, then failed before any 2020 point samples or 2025 DTM member were read. The receipt artifact [#13913928464](https://github.com/stoicsatvik/NASA/actions/runs/43152358641/artifacts/13913928464) records `RuntimeError: 2020 HiRISE point-window plan exceeds the 4 MiB range cap`; inspection of the exact branch showed E573 had raised the inherited reader cap to 16 MiB, so the failure was that the 13-offset union plan exceeded 16 MiB. The stale 4 MiB text in the exception was misleading and has been replaced with the actual planned byte count and configured cap. The TIFF `GDAL_NODATA` parser warning was non-fatal and was not the failure cause.

The safe correction raises only the explicit 2020 point-window cap from 16 MiB to 32 MiB. This remains a hard bounded-range budget; it does not permit whole-file TIFF download. The deterministic test now asserts the 32 MiB cap. Exact-head bounded acquisition is pending. No support-sensitivity result is claimed until the live receipt reproduces the frozen zero-shift aggregates.

The first corrected live retry [#43153122730](https://github.com/stoicsatvik/NASA/actions/runs/43153122730) passed **5/5 deterministic tests** and passed the 32 MiB range-plan preflight, but then failed at the first paired cross-tab with `ValueError: paired point masks must have equal lengths`. Artifact [#13914279372](https://github.com/stoicsatvik/NASA/actions/runs/43153122730/artifacts/13914279372) preserves the error. The 2020 reader returns a 1-D vector in boolean-indexed observed-point order (346 entries), while the new 2025 sampler initially returned the full 33×33 lattice masks (1,089 entries). The 2025 sampler now applies the identical `observed` boolean selection before returning masks. A deterministic fake-raster regression verifies the output length and observed-point ordering. No support counts or translation conclusion were produced by the failed retry.

## Interpretation boundary

- A positive 2025-minus-2020 count means more of these MOLA point centers land on finite, non-nodata pixels in the 2025 raster. It does not mean the 2025 elevation is more accurate.
- Common-mode and differential shifts answer different questions and must not be conflated.
- The translation grid is deterministic sensitivity analysis, not a probability distribution, confidence interval or fitted correction.
- The 2025 product is aligned to CTX, not an independent horizontal control network.
- No elevation residual, terrain morphology, route cost, hazard threshold, astronaut safety or E001 recovery is evaluated.

## Claim states

- Zero-shift 2020/2025 point-support counts: REPRODUCED EXACTLY (346 observed; 164 valid in 2020; 259 valid in 2025).
- 2025 support advantage under common-mode translation: SUPPORTED FOR ALL 13 TESTED OFFSETS; net support margin 94–95 points.
- 2025 support advantage under differential translation: SUPPORTED FOR ALL 13 TESTED OFFSETS; net support margin +95 points at every offset.
- Independent horizontal registration: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

## Next decision

The exact-head run reproduced the frozen zero-shift baseline and retained a positive 2025 point-support margin at every tested common-mode and differential translation. Keep the 2025 mosaic as a higher-coverage candidate for this 346-point Jezero window, with the published localized-misalignment caveat. This is not a fitted registration, accuracy comparison, or safety result. Independent horizontal-control residuals remain required before any safety-relevant routing claim.


The next exact-head run [#43153663740](https://github.com/stoicsatvik/NASA/actions/runs/43153663740) passed the other **5/6 deterministic tests**, but the new fake-raster regression failed while constructing a PROJ transformer: its fixture used EPSG:4326 (Earth) against the production Mars-sphere source CRS, and PROJ correctly rejected a cross-celestial-body transform. The live acquisition was skipped. This is a test-fixture CRS mismatch, not a data or production-sampler result. The fixture now uses the same Mars reference sphere as the frozen MOLA transform; the production code remains unchanged by this correction. Exact-head validation is pending.


A subsequent exact-head test run [#43153757855](https://github.com/stoicsatvik/NASA/actions/runs/43153757855) again passed 5/6 tests. The Mars-CRS fixture then reached the sampler but omitted the GeoTIFF `nodata` attribute; the test failed with `AttributeError` before the live acquisition. The fake raster now declares `nodata = None`, matching a valid GeoTIFF with no nodata metadata. This is a test-fixture completeness correction only; no production code or scientific result changed. Exact-head validation remains pending.


## Fixture hardening and nodata regression — 12 November 2026

The latest failed test run [#43153757855](https://github.com/stoicsatvik/NASA/actions/runs/43153757855) stopped before live acquisition because the fake raster did not expose the `nodata` attribute expected by the sampler. The failure was a fixture-interface defect, not a raster or support result. The fixture now exposes `nodata = None` for the no-sentinel case.

The test was strengthened beyond the immediate fixture correction. A parameterized regression now checks four pixel states at an in-bounds observed point: ordinary finite value (valid), explicit -9999 nodata sentinel (invalid), masked pixel (invalid), and NaN (invalid). This tests the actual validity contract rather than only making the fake object satisfy the sampler interface.

Test update commit: [0919521](https://github.com/stoicsatvik/NASA/commit/0919521cc01c498fe8c001ca650d049716c81a78). Exact-head workflow [#43155697664](https://github.com/stoicsatvik/NASA/actions/runs/43155697664) completed successfully: **10/10 deterministic tests passed**, the bounded 2020/2025 acquisition completed, and aggregate receipt artifact [#13916101713](https://github.com/stoicsatvik/NASA/actions/runs/43155697664/artifacts/13916101713) was uploaded.


## Exact-head result — E573 run 21 (12 November 2026)

- Validated branch head: `7f6541e10a823402c2c50bcf6647e425d037ca3a`.
- Baseline reconciliation: all frozen aggregates reproduced exactly — 346 observed MOLA point centers; 2020 valid 164/346; 2025 valid 259/346.
- Common-mode translation: 13 deterministic offsets applied to both product lookups; 2020 valid support 164–165, 2025 259, net 2025-minus-2020 margin 94–95 at every offset.
- Differential translation: 13 offsets applied to 2025 only while 2020 remained fixed; 2020 valid 164, 2025 valid 259, margin +95 at every offset.
- The 10.2 m envelope is the published 99th-percentile HiRISE-to-CTX alignment statistic used to define a sensitivity grid. It is not a hard bound, a fitted MOLA tie, or a probability distribution.
- Bounded transfer: 2020 point-row reads 6,895,643 bytes in 213 ranges under the 32 MiB cap; 2025 ZIP-member reads 676,334,995 bytes in 649 ranges under the 850 MiB cap. No full archive, FOM confidence member or orthoimage was read; temporary DTM was deleted. No raw elevations, pixels, point coordinates or shot counts were retained beyond aggregate counts.
- The 2020 GeoTIFF parser emitted a non-fatal warning while interpreting the GDAL_NODATA tag. The pinned nodata value was independently read by the experiment's resolver and the acquisition completed; the warning remains recorded rather than suppressed.
- Interpretation: 2025 finite-pixel support is higher at every tested offset for this frozen 346-point window. This does not establish better elevations, independent registration, area coverage, route safety, or analogue similarity.
