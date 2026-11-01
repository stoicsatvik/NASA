# E478 | Exact fixed-count null for measured-only terrain stencils (1 November 2026)

## Decision question

E476 found **zero complete centered 5-point terrain stencils** in all three approximately 2 km Martian windows, even at 40°S where **15/25 bins** had a positive MOLA observation count. Is the 40°S absence itself unusual once the number of observed cells is held fixed?

**No.** Under the exact, explicitly nonphysical null of uniformly placing the same number of observed cells in a 5×5 grid, **1,995,810 of 3,268,760** masks with 15 observed cells also have zero complete 5-point stencils (**61.0571%**). The zero-stencil result is not evidence of anomalously poor geometry relative to this null. It remains a valid **data-admissibility failure** for measured-only centered 2D slopes at this selected site.

## Evidence and procedure

Inputs were downloaded directly from archived [E472 exact-head Actions artifact #13075465278](https://github.com/stoicsatvik/NASA/actions/runs/41285525743), generated from official PDS-derived MOLA/LOLA count ranges. The two source JSON files were verified before analysis by SHA-256:

- Mars `e472_mars_source.json`: `2e70d84ca45cc4730c87e8931194c5ba1cd7a31bdd15e9a7883c5611578c9dfb`
- Moon `e472_moon_source.json`: `a4ed427e5996b8ef115e0bf8130f615089248bae8d89ec43cdd6fa2bf80f96c4`

The same three preselected locations at 45°E were used, with Mars restricted to the physically matched central 5×5 window. For each fixed observed count k, E478 exhaustively enumerated every one of `C(25,k)` binary masks and counted the fraction with no complete center-plus-four-neighbors stencil and no full 3×3 stencil. No sampling approximation was needed. The Moon masks were checked for consistency but were not assigned infeasible exact 81-cell enumeration probabilities.

| Mars latitude | Observed bins | Exact masks | P(zero 5-point stencils) | P(zero full 3×3) |
|---|---:|---:|---:|---:|
| 0.5°S | 11/25 | 4,457,400 | 92.4924% | 99.9758% |
| 20°S | 3/25 | 2,300 | 100% | 100% |
| 40°S | 15/25 | 3,268,760 | **61.0571%** | **97.9023%** |

All three observed Mars windows had zero complete 5-point and 3×3 centers. An independently implemented C++20 Gosper-bitmask enumerator agreed exactly on all three total counts, zero-5-point counts and zero-3×3 counts. Four local pytest tests passed against the real archived source files, including SHA tamper rejection, malformed masks, empty/full controls and the independent exact integer oracle. Python compilation passed. **No GitHub Actions CI was run**, because prior project notes report included Actions minutes exhausted; do not spend money to rerun this test.

## Falsification and limits

- **REJECTED relative to the stated fixed-count null:** interpreting zero complete 5-point stencils at 40°S as unusual spatial incompleteness *beyond* the 15/25 observed-cell count. The null probability is 0.61057, not a small tail.
- **SUPPORTED for these six selected windows:** observed-bin percentage does not ensure admissible centered measured-only slope/roughness estimates. E476's original observed counts and stencil counts remain intact.
- **NOT ESTABLISHED:** real MOLA track-geometry causation, independence/effective resolution, geodetic registration, physical slope differences, Moon/Mars/Earth descriptor comparability, or population-level global coverage. E476's separate directional anisotropy result tests a different statistic and cannot be substituted for this stencil-null result.
- **NOT YET MEASURED:** E001 independently labelled known-site recovery.
- **NOT YET PROVEN:** cross-body similarity, novel analogue discovery, India local-validation advantage, and superiority of the 2026 planetary-analogue challenge.

This is a finite, exact structural control on real-source masks, **not** a new planetary observation or analogue discovery. Its highest-value implication is to stop interpreting the zero-stencil statistic as a surprising track-pattern effect. Invest next in observed-pair, physical-lag directional elevation descriptors with units, datum, independent-resolution and uncertainty gates; then obtain independent positive/negative analogue labels and run E001 frozen baselines. If comparable descriptors are unavailable, preserve that negative gate.

## Reproduce offline

Extract the two source JSON files from the named archived E472 artifact into a local directory:

```bash
python research/e478_exact_stencil_null.py /path/e472_mars_source.json /path/e472_moon_source.json
E478_ARTIFACT_DIR=/path python -m pytest -q research/test_e478_exact_stencil_null.py
```

Numerical receipt: `research/results/e478_exact_fixed_count_stencil_null_20261101.json`. Source hashes are checked before any numerical analysis. The exact enumerator takes approximately 15 seconds in the local Python environment; the independent C++ oracle is a separate validation, not a replacement source.
