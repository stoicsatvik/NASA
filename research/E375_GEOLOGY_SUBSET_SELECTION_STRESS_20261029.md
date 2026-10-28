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

## Measured pinned-source results | exact-head E375 CI

[Workflow #40788352455](https://github.com/stoicsatvik/NASA/actions/runs/40788352455) **SUCCESS** at commit `66d261ce60edab9a094163f79914a5225838ad42`. The source-pinned public data were downloaded, checked and scored twice with byte-identical JSON receipts. [Artifact #12860656448](https://github.com/stoicsatvik/NASA/actions/runs/40788352455/artifacts/12860656448), ZIP SHA-256 `e05c61a8780398acb2ff49f36d23c1004fdcba2c7e9aa5e488414f93758a022a`, independently downloaded and parsed. Offline E375 + inherited E369 tests passed. The original source commit is `f6c53ba50a9379d1c06f610b0e598395a0a54b43`.

The following exact pairwise AUCs use **finite-only** masking. Land-fraction >= 0.5 gives identical environment/geology/pooled-versus-editorial AUCs for all rows.

| Earth-only score | Source body | Environment vs editorial | Geology vs editorial | Pooled analogue vs editorial |
|---|---|---:|---:|---:|
| Negative vegetation | Mars | 1.000000 | 1.000000 | 1.000000 |
| Negative vegetation | Moon | 1.000000 | **0.791667** | **0.895833** |
| Negative vegetation | All | 1.000000 | **0.843750** | **0.947917** |
| Negative precipitation | Mars | 1.000000 | 1.000000 | 1.000000 |
| Negative precipitation | Moon | 0.875000 | **0.666667** | **0.770833** |
| Negative precipitation | All | 0.953125 | **0.750000** | **0.885417** |

Source counts: 5 Mars environment + 1 Mars geology, 3 Moon environment + 3 Moon geology, 8 editorial negatives. The score comparison between geology and environment is strongly ordered toward environment: negative vegetation geology-vs-environment AUC 0.03125 with finite-only and 0.00000 with land-fraction mask; precipitation 0.09375 in both. These values diagnose **source role selection**, not which analogues are scientifically better.

**Measured falsification:** The perfect E369 Earth-only vegetation AUC is **not invariant** to including the source's own geology-labelled analogue examples, particularly Moon cases. The original easy-control AUC cannot be used as universal analogue-recovery evidence. Mars-only source subset stays perfect under this stress, showing the conclusion is specific to the source composition rather than a universal model failure.

**Claim states:** catalog-subset sensitivity SUPPORTED ON PINNED EARTH-ONLY SOURCE; general cross-body retrieval NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel analogue discovery, local field advantage and 2026 challenge superiority NOT YET PROVEN. This experiment does not refute TerraNova's full model or treat source-labelled geology analogues as hard negatives.
