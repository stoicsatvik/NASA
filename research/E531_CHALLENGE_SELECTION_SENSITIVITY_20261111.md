# E531 — challenge-selection score sensitivity (2026-11-11)

## Question

Does the provisional Martian Map lead over MODIS/VIIRS survive reasonable perturbations to the subjective scorecard, or is the 0.10-point gap an artifact of chosen weights/scores?

## Frozen source

Input is the five-column, 14-challenge scorecard in `research/CHALLENGE_SELECTION_SCREEN_20261111.md`:

- public-data readiness: 25%
- measurable validation: 25%
- portfolio reuse: 20%
- technical differentiation: 15%
- 48-hour feasibility: 15%

The baseline weighted scores are Martian Map 4.10, MODIS/VIIRS 4.00, CLPS 3.85, Earth System Trend Detective 3.80 and planetary analog 2.93. The scorecard itself states that differences below about 0.25 are not meaningful.

## Experiment

For each of 0.25, 0.50 and 0.75 score-point perturbation amplitudes:

1. Run 200,000 deterministic draws with seed 526.
2. Perturb each criterion weight independently by a multiplicative uniform factor in [0.8, 1.2], then renormalize weights to sum to one.
3. Perturb every challenge/criterion score independently by uniform [-a,+a], clipping the score to [1,5].
4. Recompute all 14 weighted totals and count the top-ranked challenge.
5. Record the 5th, 50th and 95th percentiles of the Martian Map minus MODIS/VIIRS score difference.

This is a scorecard robustness diagnostic. It is **not** a probability model for judging outcomes, challenge quality or project success. Perturbations are hypothetical and not calibrated from inter-rater data.

## Results

| Score perturbation | Martian Map top | MODIS/VIIRS top | CLPS top | Earth Trend top | Median Map–MODIS gap | 5th–95th percentile gap |
|---|---:|---:|---:|---:|---:|---:|
| +/-0.25 | 83.97% | 15.88% | 0.13% | 0.02% | +0.1010 | -0.0645 to +0.2646 |
| +/-0.50 | 65.40% | 27.46% | 4.75% | 2.38% | +0.1012 | -0.2146 to +0.4152 |
| +/-0.75 | 54.34% | 28.55% | 10.48% | 6.32% | +0.1041 | -0.3497 to +0.5595 |

Field Shift and the other lower-ranked challenges are rarely top under these perturbation families. Their low frequency here is not evidence of poor judging potential; it reflects the frozen baseline scores and chosen perturbation distribution.

The complete deterministic result is stored at `research/results/E531_CHALLENGE_SELECTION_SENSITIVITY_20261111.json`; the executable is `experiments/e531_challenge_selection_sensitivity.py`.

## Interpretation

- Martian Map remains the most frequent top choice under all three tested perturbation families.
- Its lead over MODIS/VIIRS is **not robust to moderate score uncertainty**: the 5th-percentile Map–MODIS gap is already negative at +/-0.25 and becomes more negative at +/-0.50 and +/-0.75.
- The result supports a **provisional shortlist**, not a locked selection. The ranking's direction is often stable under small perturbations, but the margin is not decisive when subjective criterion scores are uncertain.
- The sensitivity percentages must not be described as probabilities that NASA judges will prefer one challenge.

## Current evidence update

The data situation changed after the original screen:

- E527 acquired the official 2007 MGD3 spatial package: 547 polygons/IDs. E528 linked 535/547 unique IDs to the 2018 MGD3 workbook. Exact-head E527 Actions run [#42904750899](https://github.com/stoicsatvik/NASA/actions/runs/42904750899) passed.
- E530 then tested actual PAAD/MGD3 artifacts and found no directly admissible shared quantitative physical-feature family. PAAD contains 45 known-analogue records but lacks target-body/family labels and a non-analogue control population. Strict dune-type overlap is S/SS; L remains a candidate and B is ambiguous. Naively admitting B inflates apparent coverage 1.81x on PAAD and 1.93x on MGD3. E001 known-site recovery remains NOT YET MEASURED.
- This strengthens the evidence base for a Mars dune context layer, but it does not validate a route-safety model. The separate `martian` repository remains preparation-only; it explicitly does not contain a competition solution or validated Mars navigation product.
- Planetary analog remains conditional and scientifically unready for E001 until independent Earth positive sites, defensible non-analogue controls and physically comparable features exist.

## Decision

Keep **Martian Map and MODIS/VIIRS as a provisional top tier**. Martian Map retains the current portfolio-reuse/data-readiness tie-breaker, now supported by an actual MGD3 spatial acquisition and ID join. Do not lock it: the margin remains sensitive to subjective score perturbations, and no route-safety validation exists. Keep planetary analog as a research stream, not the default competition choice; E530 is a negative admissibility result, not a reason to polish its UI.

## Claim states

- All-14 challenge screen: **SUPPORTED as a provisional evidence-readiness screen**.
- Martian Map superiority: **NOT YET PROVEN**.
- MODIS/VIIRS superiority: **NOT YET PROVEN**.
- Planetary-analog challenge superiority: **NOT YET PROVEN**.
- Cross-body similarity: **NOT YET PROVEN**.
- Known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Local validation advantage: **NOT YET PROVEN**.

## Validation

The branch workflow runs the deterministic unit tests, recompiles the experiment, recomputes the full 200,000-draw-per-scenario campaign and byte-compares the result with the committed JSON. No competition submission, team contact, deployment or live infrastructure change was made.
