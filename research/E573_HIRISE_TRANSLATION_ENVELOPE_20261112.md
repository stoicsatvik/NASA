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

- Zero-shift 2020/2025 point-support counts: NOT YET RE-MEASURED.
- 2025 support advantage under common-mode translation: NOT YET MEASURED.
- 2025 support advantage under differential translation: NOT YET MEASURED.
- Independent horizontal registration: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Route safety: NOT CLAIMED.

## Next decision

If the 2025 support advantage survives both tested translation modes, keep the 2025 mosaic as a higher-coverage candidate but retain the published localized-misalignment caveat. If it fails either mode, prefer the more conservative 2020 coverage for any event-day map and keep the 2025 layer visibly conditional. In either case, independent horizontal-control residuals remain required before any safety-relevant routing claim.
