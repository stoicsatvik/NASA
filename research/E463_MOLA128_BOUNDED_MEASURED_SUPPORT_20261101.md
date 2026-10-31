# E463 — Actual MOLA 128ppd measured-bin support (preregistered source spike)

Date: 2026-11-01. Status: **PENDING ACTUAL SOURCE EXECUTION**. Do not report numerical coverage until the GitHub Actions receipt exists and is inspected.

## Falsifiable question
E458 established that a 4-km window at 128 pixels/degree has enough **nominal** Mars grid cells. Does a predeclared set of real MOLA 128ppd windows contain sufficient **observed** (MEGC > 0) cells to support any terrain descriptor? High nominal grid density is not an instrument-resolution guarantee.

## Official data and fixed sampling
Official PDS4-maintained MGS MOLA derived MEG128 directory:
https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg128/

PDS3 labels shipped alongside the PDS4 product:
- `megc00n000hb.lbl`: 5632 rows × 11520 columns, unsigned 8-bit observation counts, 128ppd, 0 to -44 degrees latitude, 0–90 E longitude.
- `megt00n000hb.lbl`: same grid, signed big-endian 16-bit median topography, **metres** relative to MOLA areoid. Topography in count-zero cells is interpolated.
- The PDS label explicitly states ~55% of equatorial bins contain observations and gaps up to 12 km. This statement is not a measured percentage for our three windows.

Before observing any bytes, choose longitude 45 E, center latitudes **-0.5, -20, -40 degrees**, and **9×9** grid windows, using zero-based center row floor(-lat×128) and column floor(lon×128). These are deliberately not alleged analog sites. No site or label is selected by inspecting outcomes.

`research/e463_mola128_range_coverage.mjs` downloads only six exact HTTP 206 contiguous row ranges (counts + topography for each window), verifies Content-Range and PDS label metadata, records SHA-256 for each sampled range and both labels, counts measured/interpolated bins, and reports observed elevation extrema. **Full product checksums are not available from these partial ranges.** `research/test_e463_mola128_range_coverage.mjs` checks geometry, fail-closed admission and signed decoding.

## Prespecified interpretation
- A low measured-bin fraction at the equator would falsify any assumption that 128ppd nominal pixels are all independent measured samples.
- A high measured-bin fraction at one location would support only local observed-bin coverage, not a global fraction, effective independent resolution, or cross-body comparability.
- Even 81/81 observed cells would not prove absence of instrument smoothing, correlated tracks or aliasing.
- If the server refuses exact byte ranges, record **SOURCE ACCESS NOT VERIFIED**, do not silently download >100MB full tiles or fabricate coverage.

## Gates still outstanding
Real LOLA high-resolution effective-resolution/spot-count masks, matched physical-scale terrain descriptors, independent known analogue positives and hard negatives, leave-one-site-out recovery and null/permutation/ablation tests. E001 **NOT YET MEASURED**; cross-body similarity **NOT YET PROVEN**; challenge-selection superiority **NOT YET PROVEN**. No UI work, fieldwork, competition submission, spending or main merge.
