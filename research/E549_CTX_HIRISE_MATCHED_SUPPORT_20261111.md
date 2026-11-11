# E549 — matched-support Jezero CTX / HiRISE elevation comparison (11 November 2026)

## Question

Can the 2020 Mars 2020 TRN CTX and HiRISE DTMs be shown to share the same physical map definition, then compared over a small, preregistered common-area patch without concatenating mismatched pixels?

## Pinned products

- CTX TRN DTM: USGS DOI 10.5066/P906QQT8, 20 m/pixel, official direct GeoTIFF pinned to the E544 SHA-256.
- HiRISE TRN DTM: USGS DOI 10.5066/P9REJ9JN, 1 m/pixel, official direct GeoTIFF plus its PDS3 label.
- Both official USGS product pages describe equirectangular projection, 3,396,190 m spherical radii, planetocentric latitude, positive-east longitude and metre vertical units.
- HiRISE's GeoTIFF uses user-defined GeoKey code 32767; E549 reconstructs the physical projection from the PDS3 label and projection keys rather than treating 32767 as an EPSG code.

## Frozen comparison

- Centered on the E548 preregistered Jezero sample location.
- 10×10 CTX cells, nominally 200 m × 200 m.
- Each 20 m CTX cell is compared with an area-weighted mean of overlapping 1 m HiRISE pixels.
- Common support requires at least 99% of each CTX cell's physical area to have valid HiRISE samples.
- No raw raster or pixel arrays are committed or uploaded.
- A fixed translation sensitivity grid at −6, 0, +6 m in X and Y is reported. It is not fitted and cannot be called a registration estimate.

## Measurements

The receipt records both source hashes, reconstructed CRS parameters, raster transforms, common-support coverage, per-patch elevation residual statistics, and the preregistered shift-sensitivity grid.

## Interpretation boundary

- This is a local within-Mars cross-instrument consistency experiment, not cross-body similarity or E001 known-site recovery.
- A local vertical residual is not an independent validation of the USGS control network or vertical datum.
- Published USGS metadata reports an approximately 0.4 m median vertical offset between the 2020 HiRISE and CTX DTM mosaics. E549 measures one small local patch and does not assume it must reproduce the global/published statistic.
- Horizontal shift sensitivity is not a measured registration residual.
- No route safety or astronaut navigation claim is made.

## Validation

The dedicated workflow runs deterministic geometry/area-weighting fixtures, then the bounded CTX download and HiRISE byte-range comparison. The first live attempt reached the exact CTX object but failed the TIFF magic check because the fixture implementation over-escaped the byte marker. That implementation failure is preserved in Actions run 43023929608; no raster bytes were interpreted in that attempt. The corrected exact-head result is appended after rerun.


## Exact-head result (11 November 2026)

- Draft PR #109, branch research/e549-ctx-hirise-matched-support-20261111.
- Actions run [#43024094876](https://github.com/stoicsatvik/NASA/actions/runs/43024094876) passed **5/5 deterministic geometry/area-weighting tests** and completed the live comparison.
- CTX source: 9,662,387 bytes, SHA-256 16a1aa66c3f48c1bca252795827db7b417876217aff0f5e1aff18027fab2327b, exactly matching E544. HiRISE label hash matches E548.
- PDS3-derived HiRISE equirectangular CRS is parameter-equivalent to CTX ESRI:103885 under pyproj. Both use radius 3,396,190 m, centre latitude/longitude 0°, 1 m HiRISE pixel scale and the same map units.
- The preregistered 10×10 CTX block (100 cells; 200 m × 200 m) had **100/100 valid CTX cells and 100/100 HiRISE area coverage at 100%** under the ≥99% support rule. HiRISE sampling used 223 exact HTTP Range requests / **353,859 bytes**, under the 1 MB cap.
- Zero-shift residual, defined as CTX minus area-weighted HiRISE (metres): **median −2.7484 m; mean −2.7088 m; SD 1.3677 m; MAE 2.7088 m; RMSE 3.0345 m; 95th percentile absolute residual 4.8544 m; range −6.2199 to −0.1766 m**.
- The fixed ±6 m translation grid retained negative medians from −2.4270 m to −3.0173 m. The sign/magnitude is therefore not removed by this coarse translation sensitivity. This grid is not a fitted registration estimate.
- This local result is **discordant** with the USGS metadata's approximately +0.4 m median vertical offset statement and description of CTX as floating above HiRISE. It is a single 200 m patch, not a global contradiction or proof of a source defect. Plausible explanations include local DTM seam/vertical bias, spatially varying registration, residual terrain/surface differences, or an unrecognized product/metadata interpretation issue. The CTX product's own metadata reports 3.8 m vertical registration between its component DTMs after HRSC alignment, so a local multi-metre difference is not automatically impossible.
- Exact common-area support and local vertical difference are MEASURED for this patch. Local horizontal registration residual, global CTX/HiRISE agreement, cross-body similarity and E001 known-site recovery remain NOT YET MEASURED / NOT YET PROVEN.

Next: E550 will test whether this −2.75 m result is local or spatially systematic using a preregistered 3×3 grid of 100 m patches across the full metadata overlap, preserving all nine patch residuals and a fixed ±6 m translation sensitivity. Do not calibrate the products by fitting away the discrepancy.
