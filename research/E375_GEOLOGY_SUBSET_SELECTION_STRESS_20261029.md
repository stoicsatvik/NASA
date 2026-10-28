# E375 | Does editorial-control AUC survive the geology-labelled analogue subset?

29 October 2026. Independent **pre-event validation audit**, not a competition solution.

## Question and frozen design

E369 found Earth-only negative-vegetation AUC 1.000 for the source catalogue's eight *environment*-labelled analogues versus eight explicitly editorial humid/vegetated negative sites. The same pinned source also contains four *geology*-labelled analogues, excluded from that headline AUC. Are the simple scores equally discriminating for those different legitimate analogue examples?

Re-use E369's source-identity-verified 360x720 Earth vegetation/precipitation/land-fraction rasters and its exact nearest-valid-cell scoring. No model tuning, no new labels, no new planetary observations. Compute exact pairwise AUC for environment-only, geology-only, and pooled source-labelled analogues versus the same eight editorial negatives, and geology versus environment as a *score distribution diagnostic*. Stratify by Mars/Moon/all and retain both predeclared land masks.

**Critical label boundary:** The four geology sites are **alternative source-labelled analogue positives**, not independently adjudicated hard negatives. AUC changes would reveal catalog-subset dependence, not cross-body retrieval failure or success.

## Reproduction

```bash
python -m pytest -q tests/test_e375_geology_subset_stress.py tests/test_e369_single_feature_control_baselines.py
python -m research.e375_geology_subset_stress > e375_receipt.json
```

The dedicated Actions workflow downloads the pinned public files read-only, checks source blob identity, repeats the experiment, compares byte-identical receipts and uploads the JSON. No raw raster is committed.

## Evidence and claim boundary

Measured real-source results must come from a successful workflow receipt; do **not** substitute the synthetic unit-test values for measurements. E001 known-site recovery NOT YET MEASURED. Cross-body similarity, novel analogue discovery, local validation advantage and challenge-selection superiority NOT YET PROVEN. Next step remains independent physically comparable Earth/Moon/Mars descriptors, legitimate source-independent site labels and spatially blocked recovery with random/Euclidean/weighted baselines.

No outreach, fieldwork, competition submission, deployment, spending or main merge.
