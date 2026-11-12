# E570 — bounded real LOLA GDR sample

**Date:** 12 November 2026  
**Branch:** \`research/e570-lola-gdr-window-20261112\`  
**Parent:** E569 paired HiRISE support  
**Status:** acquisition and exact-head validation pending

## Question

Can the official PDS3 LOLA GDR product be read as a small, bounded real lunar sample with its units, reference sphere, grid geometry, missing-value semantics and provenance preserved?

## Pinned source

- PDS product: \`LRO-L-LOLA-4-GDR-V1.0 / LDEM_16_FLOAT\`
- Product page: https://pds-geosciences.wustl.edu/missions/lro/lola.htm
- Dataset DOI: https://doi.org/10.17189/1520642
- Bundle DOI: https://doi.org/10.17189/tnyt-7007
- Label: \`ldem_16_float.lbl\`
- Image: \`ldem_16_float.img\`

The PDS label declares a 2,880 × 5,760 pixel-registered simple-cylindrical grid, 16 pixels/degree, 1.89521 km/pixel at the equator, 32-bit \`PC_REAL\`, values in kilometres, and a 1,737.4 km reference-sphere offset. The data spans 13 July 2009 through 29 November 2016 and was created 15 March 2019.

## Frozen acquisition

- Three analyst-selected 11 × 11 windows; these are not analogue labels or geological ground truth.
- Three HTTP byte-range requests only; the full 66,355,200-byte IMG is never downloaded.
- Hard transfer cap: 1,000,000 bytes.
- Preserve the label hash and each range hash; retain only aggregate descriptors.
- Derive radial-height p05/median/p95, p95–p05 relief, median absolute deviation and local slope summaries.
- Longitude pixel spacing is adjusted by cos(latitude); latitude spacing remains the equatorial map scale.
- Reject servers that ignore HTTP Range or return a mismatched Content-Range.

## Interpretation boundary

The PDS label says each sample is radial height relative to a 1,737.4 km reference sphere. This experiment does **not** apply a lunar geoid correction. It therefore reports radial-height texture, not geoid-corrected elevation. No cross-body distance, analogue recovery, geological classification or novel discovery is claimed.

## Validation

Pending deterministic tests and exact-head bounded live acquisition. The final receipt will be appended only after the actual workflow completes. Failed acquisition attempts will remain recorded.
