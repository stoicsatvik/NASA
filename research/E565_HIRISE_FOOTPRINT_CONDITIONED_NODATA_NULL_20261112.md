# E565 — Footprint-conditioned HiRISE nodata clustering reference

Date: 12 November 2026  
Branch: `research/e565-footprint-conditioned-nodata-null-20261112`  
Draft PR: [#124](https://github.com/stoicsatvik/NASA/pull/124)  
Code head at exact-head validation: `0ff4527b195e2df28d1992e5c8d35b7acfd863b7`

## Question

Does the clustering of the 92 observed MOLA points that fall inside the pinned HiRISE raster but map to nodata persist when the null is conditioned on the actual HiRISE raster footprint?

E564's all-observed reference randomized labels across all 346 observed MOLA bins. That mixes deterministic outside-raster geometry with internal nodata. Its upper-tail fraction is descriptive only.

## Frozen source and geometry

The workflow reacquired the same bounded Jezero masks and retained no raw raster samples or point coordinates.

- Observed MOLA bins: 346 / 1,089.
- CTX-valid observed MOLA centers: 346 / 346.
- HiRISE in-bounds observed MOLA centers: 256 / 346.
- HiRISE finite, non-nodata observed MOLA centers: 164 / 346.
- Three-way common point support: 164 / 346 = **47.3988%**.
- HiRISE outside bounds: 90.
- HiRISE inside but nodata: 92.

## E564 descriptive clustering baseline

- 422 four-neighbor edges among the 346 observed MOLA nodes.
- Inside-nodata class: 8 components with sizes [44, 16, 10, 7, 7, 3, 3, 2]; 96 same-category edges.
- Outside-bounds class: 6 components with sizes [59, 11, 8, 4, 4, 4]; 113 same-category edges.
- All-observed fixed-count reference for inside nodata: mean 29.5876 edges, 95th percentile 37, upper-tail reference fraction 0.0001.

The all-observed reference is not inferential: it does not preserve the deterministic HiRISE footprint geometry.

## E565 footprint-conditioned reference

The new reference fixes the 256 in-bounds observed MOLA nodes and their 299 cardinal adjacency edges, then reassigns the 92 nodata labels only among those in-bounds nodes.

| Quantity | Result |
|---|---:|
| Eligible in-bounds nodes | 256 |
| In-bounds adjacency edges | 299 |
| Nodata labels preserved | 92 |
| Observed nodata adjacency edges | 96 |
| Permutations | 9,999 |
| Reference mean edges | 38.3311 |
| Reference 95th percentile | 46 |
| Upper-tail reference fraction | 0.0001 |

The nodata clustering remains pronounced after conditioning on the actual raster footprint. This is a stronger descriptive comparison than E564's all-observed reference, but **0.0001 is not an inferential p-value**. The null still assumes exchangeability of nodata labels within the footprint; spatially correlated processing gaps or other nodata-generation mechanisms can violate that assumption.

## Validation

Exact-head workflow [#43104583925](https://github.com/stoicsatvik/NASA/actions/runs/43104583925) succeeded:

- 13/13 deterministic tests passed.
- Bounded MOLA/CTX/HiRISE acquisition and receipt generation completed.
- Artifact [13892504439](https://github.com/stoicsatvik/NASA/actions/runs/43104583925/artifacts/13892504439).
- Artifact ZIP SHA-256: `36ad0ecfe853dc5f27b552ed9803d40a7b34e56775cf826ff55f86143b8cbf7a`.

The live reader emitted the existing nonfatal GDAL_NODATA-to-float32 parsing warning; the explicit nodata resolver handled the sentinel and retained all 92 nodata points as invalid. The warning was not suppressed.

## Claim boundary

- Bounded three-way point support: **PARTIAL FOR THIS WINDOW**.
- Nodata spatial clustering under a fixed-footprint random-label reference: **DESCRIPTIVELY SUPPORTED**.
- Physical cause of nodata: **NOT IDENTIFIED**.
- Independent horizontal registration residual: **NOT YET MEASURED**.
- Cross-body similarity: **NOT YET PROVEN**.
- Known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Route safety: **NOT CLAIMED**.

No pixels were imputed, no correction was fitted, no route-risk score was generated, and no analogue recovery was claimed.

## Next decisive move

Inspect the pinned HiRISE DTM's nodata/quality-mask semantics and seek an overlapping or independent DTM coverage source for the same area. Avoid further same-window permutation variants unless they preserve a materially stronger spatial null. Reassess Martian Map against MODIS/VIIRS only if a predeclared score factor changes. The all-14 challenge ranking remains provisional; no challenge is locked.
