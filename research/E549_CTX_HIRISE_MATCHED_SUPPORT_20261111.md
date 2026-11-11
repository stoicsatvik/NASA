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
