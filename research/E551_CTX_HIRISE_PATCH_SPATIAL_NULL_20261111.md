# E551 — exact patch-level spatial null for the Jezero CTX/HiRISE residual (11 November 2026)

## Question

Does the descriptive plane fitted to E550's spatial distribution of CTX-minus-HiRISE residual medians exceed what is expected if the six measured patch values were exchangeable across their fixed positions?

## Frozen input and provenance

E551 uses only the compact patch summaries from E550 Actions run [#43025458917](https://github.com/stoicsatvik/NASA/actions/runs/43025458917), artifact **13855824623**. The artifact ZIP SHA-256 is `a1cd14c272ed122f82edaac5f72e788d799ad7311bd488f8beffd989f487ccb1`; extracted receipt JSON SHA-256 is `bb13f638136d038ec10d683b26fdc48d684fce38957360bc60f121b6d3401123`.

- CTX TRN DTM: USGS DOI [10.5066/P906QQT8](https://doi.org/10.5066/P906QQT8).
- HiRISE TRN DTM: USGS DOI [10.5066/P9REJ9JN](https://doi.org/10.5066/P9REJ9JN).
- Residual definition: CTX elevation minus area-weighted HiRISE elevation, metres.
- No raw rasters or pixel arrays are copied into this branch.

## Coverage audit

E550 evaluated nine preregistered grid positions, but **only six** had common valid support. Six patches had 25/25 CTX cells with 100% HiRISE area coverage; three positions had zero common valid cells:

- Unsupported: `x15_y15`, `x50_y85`, `x85_y85`.
- Measured patch medians (m): `x50_y15` −1.5153; `x85_y15` −3.1523; `x15_y50` −5.0139; `x50_y50` −2.7272; `x85_y50` +2.4249; `x15_y85` −2.4269.

The E550 receipt's 150 common cells therefore represent six patches, not nine fully measured patches. Missingness is preserved, not imputed.

## Exact null experiment

- Fit a descriptive plane to the six patch medians against patch-centre X/Y coordinates.
- Enumerate all **6! = 720** permutations of the six medians across the six fixed measured locations.
- Use plane (R^2) and gradient-vector norm as statistics.
- Treat each patch median as one permutation unit; do not treat the 150 cells as independent.
- Run a two-sided exact sign test for the five negative and one positive patch medians.
- Refit the plane after omitting each measured patch in turn.

## Result

Observed descriptive plane:

- (R^2 = 0.5843)
- X slope = **+0.3526 m/km**
- Y slope = **+0.2559 m/km**
- Gradient norm = **0.4357 m/km**

Exact patch-level permutation:

| Statistic | Observed | Null median | Null 95th percentile | Exact upper-tail p |
|---|---:|---:|---:|---:|
| Plane (R^2) | 0.5843 | 0.3586 | 0.8118 | **0.2444** |
| Gradient norm (m/km) | 0.4357 | 0.2796 | 0.5171 | **0.1500** |

The sign pattern is 5 negative / 1 positive; exact two-sided sign-test (p = 0.21875).

Leave-one-patch-out plane (R^2) ranges from **0.1069 to 0.9145**, so the descriptive fit is sensitive to which patch is removed.

## Interpretation

**Negative result: a spatially coherent residual gradient is NOT SUPPORTED by this six-patch permutation test.**

The apparent (R^2=0.5843) is not unusual under the patch-level exchangeability null (exact (p=0.2444)); the gradient norm is also not unusual ((p=0.15)). Five negative medians out of six are descriptive, not a significant sign pattern. The plane should not be presented as a geophysical trend or used as a correction surface.

This does **not** erase the measured local vertical residuals. It narrows the interpretation: E550 establishes six local common-support comparisons, with three unsupported positions and no statistically supported spatial plane under this limited null.

## Null limitations

The permutation assumes the six measured patch medians are exchangeable under no spatial association. The three unsupported positions are excluded; whether missingness depends on terrain or source coverage remains unknown. Thus these p-values are an exact computational diagnostic under the stated exchangeability null, not a design-based inference for the full nine-position grid. Pixel-level autocorrelation is avoided by permuting patch medians, but six patches remain a small sample.

## Claim states

- CTX/HiRISE projection-parameter equivalence: **SUPPORTED by E550**.
- Common valid support: **SUPPORTED for six patches only; PARTIAL across the nine-position grid**.
- Local vertical residual: **MEASURED for six patches only**.
- Spatially coherent residual gradient: **NOT SUPPORTED by this six-patch permutation test**.
- Global vertical offset reproduction: **NOT ESTABLISHED**.
- Cross-body similarity: **NOT YET PROVEN**.
- Known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Route safety: **NOT CLAIMED**.

## Validation

- Local exact enumeration and deterministic regression suite: **6/6 tests passed**.
- All 720 permutations were enumerated; no Monte Carlo approximation or random seed was used.
- Exact-head GitHub Actions is pending on this draft branch.

## Next decisive action

Do not fit a correction plane. Recover common valid support at the three failed grid positions only if a separately verified product footprint permits it; otherwise preserve the partial-coverage result. The next planetary-analog gate remains independently labelled known-site recovery with physically comparable descriptors and hard negatives. No route-safety claim follows from E550/E551.
