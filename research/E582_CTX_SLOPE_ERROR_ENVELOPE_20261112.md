# E582-S companion — CTX slope-descriptor vertical-error sensitivity

Date: 12 November 2026  
Branch: `research/e582-ctx-slope-error-envelope-20261112`  
Base: E581 / PR #141. Draft research only; `main` untouched.

## Question

Given the actual E581 CTX raster posting and the documented vertical-error envelope, is a 20 m slope descriptor stable enough to use, or should the first candidate descriptor use a longer baseline?

This is a source-backed sensitivity calculation. It is **not** a new raster measurement and does not compute a slope from the five E581 pixel windows.

## Pinned data context

E581 acquired the public CTX COG for item `P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W`:

- Raster posting: 20.162955 m × 20.162955 m.
- Five deterministic 64×64 windows; 20,480 valid pixels; no raw pixel arrays retained.
- TIFF/STAC vertical-unit field: absent. The metre interpretation is a collection-level processing-documentation inference; the exact item-specific processing command is not independently verified.
- No slope was calculated in E581.

Official USGS CTX documentation states that these DTMs use 20 m post spacing, are controlled to individual MOLA shot tracks, and typically have approximately 3–5 m vertical precision. It warns that effective resolution is coarser than posting, MOLA shots are spaced about 300 m along track with often kilometre-scale gaps near the equator, and the per-item `qa_metrics.txt` contains CTX–MOLA maximum, minimum, mean, median and standard deviation differences. Large mean/median/standard-deviation residuals can indicate broad quality problems. The same documentation explicitly warns that a 3 m topographic error can create about a 9° apparent slope over 20 m but less than 1° over 200 m.

Source: https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/  
Relevant source sections: processing, available assets, accuracy/errors/issues, general usability.

## Frozen sensitivity model

For a single vertical perturbation magnitude `delta_z` over horizontal baseline `L`, compute the apparent slope angle:

```
theta_error_degrees = degrees(atan(delta_z / L))
```

This is a simple one-height-error envelope, not a full covariance model and not a statistical confidence interval. It deliberately does not assume independent endpoint errors or a distribution that USGS has not supplied.

| Vertical perturbation | Baseline | Apparent angle |
|---:|---:|---:|
| 3 m | 20 m | 8.530766° |
| 3 m | 200 m | 0.859372° |
| 5 m | 20 m | 14.036243° |
| 5 m | 200 m | 1.432096° |

The 3 m results reproduce the USGS qualitative example (approximately 9° at 20 m and below 1° at 200 m). The 5 m rows extend the same calculation to the upper end of the documented typical precision range.

## Decision

- **Reject 20 m slope as the primary robust terrain descriptor** for this CTX product under the documented 3–5 m vertical-precision envelope. It remains useful as a diagnostic, not as a route-safety or fine-scale terrain claim.
- **Retain 200 m as a candidate first baseline**, not as a validated descriptor. At 5 m vertical perturbation its simple one-height envelope is still about 1.43°.
- Do not equate 20 m posting with 20 m effective resolution.
- Do not treat MOLA control residuals as independent fine-scale ground truth: MOLA is much coarser and sparsely sampled. Use `qa_metrics.txt` to screen item quality and identify broad disagreement, not to certify local slopes.
- Long-baseline tilt, spacecraft jitter, nodata, edge outliers and unresolved small features remain separate error modes; this calculation addresses only a simple vertical-error component.

## Reproducibility

The four values above were recomputed locally with Python's standard-library `math.atan` and `math.degrees`. Assertions confirmed the 3 m values, monotonic increase with vertical perturbation, and reduction with longer baseline. No external package, API, credential, paid service or Actions run was used.

## Next decisive experiment

The parallel E582 QA/MOLA audit is now complete on PR #143. It acquired both assets but found a +27.3687 m mean and +26.7783 m median CTX–MOLA difference (SD 10.934 m), which is a quality warning under the official USGS guidance. E583 should first screen several additional Jezero CTX items by their QA metrics. Only if an item has defensible residuals should a later experiment calculate 200 m/400 m slope summaries with explicit vertical-unit provenance, valid-pair counts, nodata masks and detrending sensitivity. Do not claim route safety from this single DTM.

## Claim states

- Public CTX item/COG acquisition: SUPPORTED.
- E581 raster/STAC shape and transform agreement: SUPPORTED FOR THIS ITEM.
- E581 pixel-window sampling: SUPPORTED.
- Direct TIFF/STAC vertical-unit field: NOT REPORTED.
- Metre-valued areoid interpretation: SUPPORTED AS A COLLECTION-LEVEL PROCESSING-DOCUMENTATION INFERENCE; item-specific command not independently verified.
- 20 m slope as a robust primary descriptor: REJECTED UNDER THE DOCUMENTED ERROR ENVELOPE.
- 200 m slope descriptor: CANDIDATE / NOT YET MEASURED.
- QA residual analysis: NOT YET MEASURED.
- Cross-body similarity, E001 known-site recovery, novel analogue discovery, local validation advantage and challenge-selection superiority: unchanged / NOT YET PROVEN or NOT YET MEASURED as previously stated.

No raw raster, pixel arrays, field measurements, route-safety conclusion, challenge lock, competition submission or public deployment is asserted.
