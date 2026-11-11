# E553 — exact missingness sensitivity for the E550 CTX/HiRISE grid (11 November 2026)

## Question

Does E551's six-patch spatial null remain informative for the full nine-position grid when the three unsupported locations are considered explicitly?

## Frozen input

E553 uses only the durable E550 patch summaries, not raw rasters:

- CTX TRN DTM: USGS DOI [10.5066/P906QQT8](https://doi.org/10.5066/P906QQT8).
- HiRISE TRN DTM: USGS DOI [10.5066/P9REJ9JN](https://doi.org/10.5066/P9REJ9JN).
- Six measured medians remain unchanged.
- Unsupported positions remain `x15_y15`, `x50_y85`, and `x85_y85`.

E551's exact 6! test remains valid for its six measured locations. It does not cover the three unsupported positions.

## Companion E552 nodata-provenance result

The sibling draft PR [#112](https://github.com/stoicsatvik/NASA/pull/112) independently matched the three unsupported E550 windows to the product's declared all-nodata digest. All six other windows are valid. The physical cause of those nodata windows remains **NOT DETERMINED**. E553 does not reclassify them or acquire new raster data; it asks how much the full-grid null could change under hypothetical completions.

## Discriminating sensitivity experiment

For each unsupported position, assign one of five values from the empirical quantile grid of the six observed patch medians: minimum, Q1, median, Q3, maximum. Keep all six measured values fixed.

This produces **5³ = 125 hypothetical nine-position completions**. For each completion, enumerate all **9! = 362,880** permutations of its nine values across the fixed grid. Compute the same plane-R² and gradient-norm statistics used in E551.

Total: **45,360,000 exact permutation evaluations**. No Monte Carlo sampling is used.

The empirical quantile range is a sensitivity envelope only. It is not a physical bound, a missing-data model, or a probability distribution. Imputed values never become measurements.

## Result

- Plane R² across hypothetical completions: **0.0056–0.7614**.
- Gradient norm: **0.0329–0.4137 m/km**.
- Exact R² p-value range: **0.0183–0.9898**.
- Exact gradient-norm p-value range: **0.0180–0.9897**.
- **4 of 125** completions produce p<0.05 for both statistics.

All four low-p completions assign the unsupported west/south position `x15_y15` the observed minimum (−5.0139 m) and the unsupported east/north position `x85_y85` the observed maximum (+2.4249 m); the remaining unsupported position `x50_y85` takes Q1, median, Q3 or maximum. This is a hypothetical pattern, not a recovered terrain measurement.

## Interpretation

**The six-patch null is not invalidated. The full nine-position conclusion is not identifiable from current support.**

E551 still supports: no spatial plane was detected among the six measured patches under the stated six-patch exchangeability null.

E553 adds: the three unsupported positions can change the conditional exact-null outcome. Within the declared empirical sensitivity grid, some hypothetical completions are non-significant and a small subset is significant. The count 4/125 is not a probability and is not evidence that a real gradient exists.

Do not fit a correction plane, impute the three locations into the science product, or claim a spatial trend. The correct next step is to recover common valid support at those positions from a separately verified footprint, or preserve the partial-coverage result.

## Claim state

- Six-patch spatial gradient: **NOT SUPPORTED BY E551 SIX-PATCH NULL**.
- Nine-position spatial gradient: **NOT IDENTIFIABLE; THREE POSITIONS UNSUPPORTED**.
- Missingness sensitivity as a conditional computational diagnostic: **SUPPORTED**.
- Cross-body similarity: **NOT YET PROVEN**.
- Known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Route safety: **NOT CLAIMED**.

## Reproducibility

- Executable: `experiments/e553_missingness_sensitivity.py`
- Tests: `tests/test_e553_missingness_sensitivity.py`
- Machine-readable result: `research/results/E553_MISSINGNESS_SENSITIVITY_20261111.json`
- Exact nulls: 9! permutations per completion, 125 completions.

No field data, new sensor measurements, route-safety validation, destructive sampling, or restricted-area access was performed.


## Exact-head validation

- Tested implementation/workflow head: `ac9d07aa594102899812b79cd7e0d850172a4758`.
- Dedicated pull-request Actions run [#43033652738](https://github.com/stoicsatvik/NASA/actions/runs/43033652738): **SUCCESS**; all five deterministic tests, the full 125 × 9! exact sensitivity grid and artifact upload passed.
- Dedicated push Actions run [#43033646927](https://github.com/stoicsatvik/NASA/actions/runs/43033646927): **SUCCESS**.
- Machine-readable durable receipt: `research/results/E553_MISSINGNESS_SENSITIVITY_20261111.json`; original Actions artifact **13862081912**.
- Companion nodata provenance audit: draft PR [#112](https://github.com/stoicsatvik/NASA/pull/112). It identifies all three unsupported windows as all-nodata; physical cause remains NOT DETERMINED.

The later receipt/report/state commits do not change the tested experiment code. Main remains unchanged.
