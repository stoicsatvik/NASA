# E369 | Single-feature Earth climate controls saturate public analogue AUC

**28 October 2026 | Independent, pre-event scientific validation audit. Not a competition solution.**

## Question

Can a trivial source-provided Earth vegetation or precipitation predictor match the published comparator's headline *control-catalog separation* (not its full model) without any planetary features? This is a deliberately strong negative control for claims based on editorial humid/vegetated negatives.

## Source, acquisition, and frozen method

Pinned public repository: [Yakiyo/terra-nova@f6c53ba50a9379d1c06f610b0e598395a0a54b43](https://github.com/Yakiyo/terra-nova/tree/f6c53ba50a9379d1c06f610b0e598395a0a54b43). Reacquired the original `data/known_analogs.json` and three 360×720 float32 derived rasters: `vegetation.npy`, `precipitation.npy`, `land_fraction.npy`. Each source passed expected Git blob identity, exact size, and SHA-256 fingerprint checks; no binary data was committed.

Frozen source SHA-256:
- catalog `7485c86971cd538a98cad37b4116f40344645832d770af6356877b1bd92b5e36`
- vegetation `9aa18dcee2323587505aaff1875affabab085d25828d66a2856b11922c6c4f9e`
- precipitation `ac70bfa3f38b7116e16b8f5cf71e535fd6052c4a23a118eaa73aae2ac883c908`
- land fraction `e9a651dc605b33058276e0e753286636b9acbea5ab6f3635083c7c74d5988142`

Use two **predeclared** Earth-only scores, `-vegetation` and `-precipitation`, so less vegetation/rain ranks higher. The source itself describes its negatives as humid or vegetated. For each 360×720 raster, sample the catalogued coordinates using the source's 2-cell nearest-valid policy. Compare finite-only versus land-fraction >= 0.5 masks. Calculate exact pairwise AUC with half credit for ties, for Mars environmental positives (5), Moon environmental positives (3), and the tagged cold-polar subset (3), against the same eight editorial negatives. All 20 source control sites were sampled under both masks. Leave-one-negative-out AUC ranges were also measured. No model fitting, planetary data, invented negative labels or hidden evaluation.

## Real-source result

| Earth-only predictor | Mars 5 vs 8 AUC | Moon 3 vs 8 AUC | Cold-polar 3 vs 8 AUC |
|---|---:|---:|---:|
| **Negative vegetation** | **1.000** | **1.000** | **1.000** |
| Negative precipitation | **1.000** | **0.875** | **1.000** |

Results are identical for the finite-only and land-fraction >= 0.5 masks. Every site was scorable. Leave-one-negative-out minimum AUC was 1.000 for vegetation across all three subsets, 1.000 for Mars and cold-polar precipitation, and 0.857143 for Moon precipitation.

**Decisive interpretation:** Perfect Earth-catalog separation can be achieved using **only the published vegetation raster** and the original editorial negative points, without lunar/Martian measurements, morphology or a cross-body matching model. Therefore **AUC 1.00 on this particular easy Earth-control design is not discriminating evidence of cross-body analogue recovery**. This does not reproduce, refute, or assess the comparator's full five-target score surfaces; its independently self-reported full-model AUC remains NOT INDEPENDENTLY REPRODUCED. It does not imply its product has no other value.

## Validation

- [Exact-head GitHub Actions run 40737403313](https://github.com/stoicsatvik/NASA/actions/runs/40737403313) **SUCCESS** at commit `32c252368e593f1cf2390499e7f2bc54b8c9512b`: deterministic offline controls, source-pinned real public downloads, two byte-identical receipt runs, source and AUC invariants.
- [Machine-readable E369 receipt artifact 12837917264](https://github.com/stoicsatvik/NASA/actions/runs/40737403313/artifacts/12837917264), ZIP SHA-256 `1c254208ae0c0fe63b1415dca8a6676652862170ed6c7b309f625b798cf44dd4`.
- Reproduce with `python -m pytest -q tests/test_e369_single_feature_control_baselines.py tests/test_e367_public_analogue_control_audit.py` and `python -m research.e369_single_feature_control_baselines` (requires public source access and NumPy).

## Scientific limitations and next gate

- Negatives were explicitly selected for humidity/vegetation, so the baseline is **not a blinded or independent dataset**. The 5/3 positive counts are small and the same eight negatives are reused; there is no claim of population-level accuracy or a formal p-value.
- Source rasters are 0.5-degree Earth-derived predictors, not planetary instrument measurements; acquisition, original units, interpolation and site-region representativeness have not been independently calibrated here. The AUC only uses their ordering.
- The catalog includes geology-only sites excluded from this AUC. No independently labelled hard negatives, planetary target measurements, source-independent known Earth–Mars matches or physically normalized descriptors were tested.
- Next: obtain legitimate independently adjudicated **hard negative and positive** analogue pairs with matched physical features; compare frozen random/Euclidean/physically weighted baselines under spatially blocked holdouts. If no labels exist, leave E001 NOT YET MEASURED rather than manufacturing them.
- Challenge-selection superiority remains NOT YET PROVEN; an Earth-only climate AUC is not a reason to lock the planetary-analogue challenge ahead of other official 2026 challenges.

**Claim states:** E369 single-feature Earth catalog AUC SUPPORTED FOR PINNED DATA; headline AUC as cross-body validation REJECTED AS SUFFICIENT EVIDENCE; full third-party model AUC SELF-REPORTED; E001 known-site recovery NOT YET MEASURED; cross-body similarity NOT YET PROVEN; novel discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN; challenge superiority NOT YET PROVEN.

No field work, outreach, private data, competition solution, registration, deployment, spending or main merge.
