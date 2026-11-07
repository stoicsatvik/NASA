# E001 baseline evaluation harness

Run from repository root:

```bash
python -m unittest experiments.test_e001_baseline -v
python -m experiments.e001_baseline data/independently_sourced_sites.csv --features slope,roughness,aridity --output e001_results.json
```

Input columns: `site_id` (unique), `family` (e.g. Mars basalt), `is_analog` (0/1), and numeric feature columns. Do not use site identity, analog label, or derivatives of either as features.

**Status:** evaluation implementation and synthetic unit tests only. No independently sourced site-feature matrix has been supplied; no planetary recovery claim or empirical metric is justified. Every fold excludes the test site from feature standardization and reference centroid construction. Candidates are the withheld positive plus all negative controls, so reported top-1 rates must be interpreted against the printed random expectation. The controls are not automatically representative of the world; selection bias and spatial autocorrelation remain unresolved.

**Known limitations:** the current implementation treats numeric features as equally important, performs no uncertainty propagation, uses population-standard-deviation scaling, and cannot evaluate families with fewer than two independently documented positives. Per-feature ablation is exploratory; it is not a substitute for preregistered feature-family ablation or geographically blocked evaluation. Missing and nonfinite feature values fail rather than silently impute.

**Next falsifiable experiment:** curate at least two independently documented positives per planetary family and several negative comparison sites, with source URLs, native resolution, spatial footprint, measurement units, and acquisition date for each feature. Freeze candidate selection and feature definitions before examining ranks. Record failures without adjusting weights to rescue known sites.
