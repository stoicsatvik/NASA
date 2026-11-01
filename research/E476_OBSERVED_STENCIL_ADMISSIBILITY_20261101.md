# E476 | Observed-only terrain stencil admissibility (1 November 2026)

## Question and provenance

Does the E472 result that some approximately 2 km windows contain many *observed* LOLA/MOLA grid cells imply that a centered local slope or 3×3 roughness descriptor can be computed **without interpolated elevations**?

**No, for five of the six selected windows.** This is a post-E472 structural audit of real PDS-derived observation-count masks, not a new planetary analogue experiment or prospective test.

Inputs: original E472 exact-head [Actions artifact 13075465278](https://github.com/stoicsatvik/NASA/actions/runs/41285525743), files e472_mars_source.json and e472_moon_source.json, derived from official MOLA MEGC and LOLA LDEC bounded byte ranges. Exact input SHA-256:

- Mars: 2e70d84ca45cc4730c87e8931194c5ba1cd7a31bdd15e9a7883c5611578c9dfb
- Moon: a4ed427e5996b8ef115e0bf8130f615089248bae8d89ec43cdd6fa2bf80f96c4

These are archived derived count masks, **not full raw PDS products**. E476 verifies input hashes and schemas before calculations. No new field observations, synthetic planetary labels or competition submission.

## Method

For each original Moon 9×9 count-positive mask and central Mars 5×5 count-positive mask at 45°E and the same three preselected latitudes:

1. Count observed bins, and interior centers whose entire 3×3 neighborhood is observed.
2. Count interior centers whose four cardinal neighbors and center are all observed, a conservative 5-point centered-difference support requirement.
3. Count horizontal and vertical observed adjacent pairs separately.
4. As an exploratory **nonphysical structural control**, shuffle the same number of observed cells uniformly across the same window 20,000 times with deterministic seed 476. Compare absolute vertical-minus-horizontal edge anisotropy using a plus-one Monte Carlo tail fraction. This null is not a model of altimeter ground tracks; posthoc p-values are not global scientific inference.

Even fully observed 3×3 support does not guarantee independent measurement footprints or adequate uncertainty.

## Results

| Body | Latitude | Observed cells | Full 3×3 centers | Five-point cross centers | Horizontal / vertical observed pairs | Shuffle anisotropy tail |
|---|---:|---:|---:|---:|---:|---:|
| Moon | 0.5°S | 18/81 | 0/49 | 0/49 | 2 / 12 | 0.000050 |
| Mars | 0.5°S | 11/25 | 0/9 | 0/9 | 2 / 8 | 0.002300 |
| Moon | 20°S | 34/81 | 0/49 | 0/49 | 16 / 29 | 0.000050 |
| Mars | 20°S | 3/25 | 0/9 | 0/9 | 0 / 2 | 0.014499 |
| Moon | 40°S | 80/81 | 48/49 | 49/49 | 71 / 71 | 1.000000 |
| Mars | 40°S | 15/25 | **0/9** | **0/9** | 5 / 11 | 0.004800 |

The two lowest Monte Carlo tails reached the 1/20,001 resolution floor; they do not imply exact zero p-values.

**Decisive negative example:** Martian 40°S contains 15/25 (60%) observed cells but zero complete centered finite-difference stencils. Coverage fraction alone is insufficient to admit an observed-only isotropic local slope descriptor. Five of six windows lack any complete five-point cross or full 3×3 observed neighborhood.

Directional pair counts reveal anisotropic support. Along-track one-dimensional differences may be admissible where a 2D stencil is not. Such descriptors still require physical-distance, track geometry, resolution and datum normalization.

## Validation and limits

Source-equivalent Python ran on the exact downloaded artifact with 20,000 fixed-count shuffles per window (120,000 total). **8/8 local unittest contracts passed**, including source SHA verification, tamper rejection, malformed masks, zero/full controls, stripe counterexample and source-count reconciliation. Python compilation passed. An independently implemented NumPy analysis reproduced all six stencil and edge counts and the qualitative anisotropy finding; Monte Carlo tails were not bitwise identical because RNGs differed.

The committed tests use the E476_ARTIFACT_DIR environment variable for source-backed execution and skip those three artifact-dependent cases when the archive is absent. They do not silently replace source observations with synthetic measurements. **Exact-commit GitHub Actions CI and inherited full suite were not run.**

This is a posthoc selected six-window analysis, not a global coverage estimate. A count-positive bin may represent dependent observations; the shuffle null ignores instrument tracks. The windows have no analogue labels, Earth descriptors or retrieval controls.

## Claim boundary and next experiment

- **SUPPORTED IN LOCAL SOURCE-ARTIFACT ANALYSIS:** observed-bin fraction does not imply complete measured-only five-point or 3×3 stencil support in these windows.
- **REJECTED FOR FIVE OF SIX SAMPLED WINDOWS:** unconditional observed-only centered 2D slope/3×3 roughness admission.
- **NOT YET MEASURED:** E001 known-site recovery.
- **NOT YET PROVEN:** cross-body similarity, novel analogue discovery, local validation advantage, current Space Apps challenge superiority.

**Next:** compare physical-distance-matched directional terrain descriptors using count-positive adjacent pairs, with minimum support and registration/uncertainty gates. Obtain independently sourced analogue-positive/negative sites and run frozen random/Euclidean/physical baselines with leave-one-site-out and ablations. If the descriptors cannot be matched across bodies, preserve the negative result rather than filling holes with unexplained interpolation.

## Reproduce

Download artifact 13075465278 and extract the two source JSON files. From repository root:

    python research/e476_stencil_support.py /path/e472_mars_source.json /path/e472_moon_source.json > e476.json
    E476_ARTIFACT_DIR=/path python -m unittest research.test_e476_stencil_support -v

No paid API, CI rerun, or real-world operation is required.
