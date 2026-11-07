# E520 — Contiguous evaluation-block influence (2026-11-07)

## Falsifiable question
Does the lowest retrospective mean-absolute-error baseline from E518 remain unchanged if adjacent evaluation years are excluded together?

## Method
Inherit E519's pinned GISTEMP v4 zonal 2001–2025 snapshot, its 15 expanding-origin 2011–2025 forecast errors, and four fixed methods (trend, persistence, 3-year mean, 5-year mean). Remove only evaluation errors, **never** years from training. For each possible contiguous block of length 1, 2, or 5, calculate each method's MAE over the remaining years and compare the winner with the full 15-year winner. Ties are broken in the declared method order.

Reproduce: `python -m research.e520_gistemp_contiguous_block_influence`. Python stdlib, no external packages.

## Independently executed local results
| Zone | Original winner | One-year flips | Two-year flips | Five-year flips |
|---|---|---:|---:|---:|
| Global | persistence | 2/15 | 4/14 | 5/11 |
| Tropics | mean5 | 6/15 | 7/14 | 4/11 |
| Arctic | trend | 2/15 | 4/14 | 1/11 |

The script prints every flipping block, its dates and replacement winner. Local Python execution completed successfully with these counts, and `python -m compileall -q research` passed in a minimal reconstructed environment containing the exact pinned CSV, E518 OLS function, and E519 error calculation. **Full repository CI and the unmodified upstream E518/E519 modules were not run**. Results are deterministic retrospective sensitivity, not independent trials, uncertainty intervals, physical mechanisms, or evidence of prospective superiority.

## Interpretation and next gate
Ranking invariance under contiguous evaluation-block exclusion is falsified for all three zones. Temporal dependence makes independent-year interpretations especially inappropriate. A truly held-out evaluation period or prospective forecasts are required before claiming model superiority. E001 independent planetary analogue recovery remains the more important mission-aligned validation priority.
