# E293 | Real Diviner spatial missingness versus fixed-count exchangeability

**Executed:** 2026-10-26. Pre-event source-quality research, NOT E001 or a Space Apps solution.

## Falsifiable question
E291 measured the missing-value fractions in three authentic Diviner nighttime
temperature-deviation rows. If missing positions were exchangeable across
longitude conditional on each row's total missing count, would the observed
contiguous gaps and 4-degree moving-window concentrations be typical?

**Result: NO for the three sampled rows under the stated fixed-count permutation null.**
Each of the six preregistered row/metric tests exceeded all 199 seeded
permutations (one-sided Monte Carlo p = 1/200 = 0.005; this is the resolution
floor, not an exact tail probability). These tests share pixels and are not
six independent confirmations.

## Real-source measurements
Official PDS Diviner Level 3 `DGDR_STN_AVG_CYL_032` is a 32px/degree,
11,520-longitude-pixel simple-cylindrical raster of nighttime rock-free
regolith **temperature deviation** in K, not absolute temperature or thermal
inertia. Detached PDS label SHA-256:
`254aade12b81b51560bbcce0501948acfe91ea61d878e06f7c66256ff28c20ad`.
Each 23,040-byte row was retrieved by exact HTTP 206 range and checked against
its independent E291 SHA-256. No full raster or raw row was committed.

| Approx latitude | Missing / 11,520 | Longest circular missing run | Null max (199) | Max missing in any 128-px longitude window | Null max (199) |
|---|---:|---:|---:|---:|---:|
| +39.984° | 600 (5.208%) | **9** | 4 | **22** | 20 |
| −0.016° | 1,973 (17.127%) | **9** | 8 | **54** | 42 |
| −40.016° | 708 (6.146%) | **9** | 6 | **28** | 22 |

The 128-pixel window spans 4 degrees of longitude, **not a fixed kilometre
footprint** across latitude. The equatorial observed window has 54/128 =
**42.1875% missing**, versus row-wide 17.1267%. This is a local missingness
concentration, not a global or cross-body terrain result.

## Null and controls
The null holds each row's exact missing count fixed and uniformly shuffles
longitude positions 199 times with a seeded PRNG. The statistics are circular
longest missing run and the maximum over **all** circular 128-pixel windows,
so there is no cherry-picked longitude window. Four deterministic controls
cover all-valid/all-missing masks, seam-spanning clusters, fixed-count null
reproducibility, and invalid inputs.

[Exact-head GitHub Actions 40295290708](https://github.com/stoicsatvik/NASA/actions/runs/40295290708):
**SUCCESS**; four deterministic tests and all three genuine PDS row retrievals.
Machine-readable numerical artifact: [12637609079](https://github.com/stoicsatvik/NASA/actions/runs/40295290708/artifacts/12637609079).

## Interpretation and decision
**REJECTED for these three rows:** missing positions are exchangeable across
longitude conditional only on the total row missing count. Any retrieval
pipeline using STN must retain local valid-pixel fractions and explicitly
exclude or sensitivity-test poorly observed candidate windows.

**NOT ESTABLISHED:** missingness mechanism, global missingness pattern,
instrument shot counts, spatial independence of observations, physical
temperature comparability to THEMIS/Earth LST, known-site recovery or analogue
discovery. A fixed-count random-mask null is intentionally simplistic;
instrument geometry and geological/illumination context can produce structured
missingness. The three rows are not independent global samples.

## Next decisive experiment
Obtain calibrated Mars THEMIS and Earth thermal observations with explicit
time-of-day, physical footprint, atmosphere, units and coverage metadata.
Only compare physically defensible descriptors, then attempt independently
labelled E001 recovery against random, Euclidean and weighted baselines.
Stop extending single-instrument missingness tests unless they change the
candidate representation or exclusion rule. Re-rank all 14 challenge statements
when the full official text arrives 28 October. No pre-event competition
solution or submission.

**Claim states:** real-source spatial clustering relative to the stated null
SUPPORTED; E001 known-site recovery NOT YET MEASURED; cross-body similarity,
novel analogue discovery, local validation advantage and challenge-selection
superiority NOT YET PROVEN.
