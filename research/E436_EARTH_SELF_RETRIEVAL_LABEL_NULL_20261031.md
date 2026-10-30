# E436 | E430 Earth self-retrieval: exact candidate-label null and scaler leakage ablation

**31 October 2026. Retrospective, pre-event source-data audit. Not a Space Apps solution or E001.**

## Falsifiable question

E430 found that 2 of 3 two-kilometre Earth DEM windows selected the matching four-kilometre window using four physical terrain summary descriptors. Does this remain true without pooling the held-out query features into the standardization? And how unusual is 2/3 under a *strictly artificial*, globally permuted candidate-label null, accounting for inspection of multiple distance/ablation variants?

## Frozen inputs and protocol

The **only observed data** are six real SRTM-derived Mapzen Skadi summary records from E214, source blob `ca557aa7ecef53796cfb01515a01cd96cc3291c3` in `research/results/e214_earth_skadi_real_data_20261024.json`. Three unvalidated research leads (Lonar, Western Ghats, Ladakh), two overlapping 2/4-km windows per lead. Four descriptors: detrended relief SD (m), median slope, 90th-percentile slope (dimensionless), elevation range (m). No Moon/Mars data or independent analogue labels enter this experiment.

For each 2-km query, rank the three 4-km candidate windows. Freeze four transparent feature treatments: pooled six-row z-score (E430); candidate-catalogue-only z-score; z-score fitted on the *other two* candidate sites (deliberately unstable small-sample control); and scale-free log ratio. In each, evaluate all four features plus each single-feature deletion, yielding 20 *retrospectively inspected* configurations.

For each frozen prediction vector, enumerate all **3! = 6** permutations of candidate site labels **jointly**, not one permutation per query. The count of correct site identities under the identity permutation is the observed score. An additional best-of-20 calculation applies the **same** candidate-label permutation across all 20 configurations, preserving dependence between the inspected models.

This is an exact *combinatorial sensitivity diagnostic*, **not** a valid p-value for geological generalization: sites were selected, not randomly sampled or exchangeable; supports overlap; feature/variant choices were inspected after E430.

## Independently reproduced numerical result

| Four-feature treatment | Predicted targets for Lonar / Ghats / Ladakh queries | Same-site matches | Exact artificial-label tail |
|---|---|---:|---:|
| Pooled six-row z-score | Lonar / Ghats / Ghats | 2/3 | 2/6 = **1/3** |
| Candidate-catalogue z-score | Lonar / Ghats / Ghats | 2/3 | **1/3** |
| Other-two-sites z-score | Lonar / Ghats / Ghats | 2/3 | **1/3** |
| Log ratio | Lonar / Ghats / Ghats | 2/3 | **1/3** |

Across the **20 inspected configurations**, 18 scored 2/3, one scored 1/3 and one scored 0/3; none scored 3/3. The best observed score was 2/3. Under the joint candidate-label permutation, the best-of-20 null scores were `[2, 2, 1, 1, 2, 2]`; **4/6 = 2/3** of these artificial permutations did at least as well as the observed best. This is not a prospective multiple-testing correction with calibrated error rates.

The E430 2/3 outcome is **not caused solely by pooled-query z-score leakage**, because catalog-only and leave-query-site-out scaling give the same three predictions. That does not make it evidence of a deployable similarity model: Ladakh still retrieves Ghats, 2/3 is unpersuasive under even this tiny artificial null, and overlapping windows make the exercise easier than independent held-out recovery.

## Reproducibility and limitations

- `research/e436_e430_permutation_null.py`: standard-library, source-fail-closed 20-configuration audit and six joint label permutations.
- `tests/test_e436_label_null.py`: five offline deterministic tests for exact combinatorics, frozen source predictions, best-of-20, malformed provenance, nonfinite input and invalid arguments.
- Local Python 3 `unittest`: **5/5 PASS** using a source-equivalent six-record fixture; a separately authored JavaScript implementation independently fetched and analyzed the **actual full GitHub E214 JSON** and reproduced every configuration and all six best-of-20 null counts.
- The Python tests on the **exact committed GitHub source** and full repository CI remain pending; no new raw DEM files were downloaded.
- The E214 derived data have dataset-level provenance but do not provide original per-pixel SRTM void/fill provenance. None of the three site names is a validated positive or negative.

## Claim boundaries and next gate

- **SUPPORTED FOR FROZEN SIX REAL-DERIVED RECORDS:** the 2/3 four-feature self-retrieval survives three alternative scaler choices; exact six-permutation combinatorial results and ablation outcomes reproduced independently.
- **REJECTED AS EVIDENCE:** interpreting 2/3 overlapping Earth support self-retrieval as independent known Earth–Moon/Mars analogue recovery.
- **NOT YET MEASURED:** E001 known-site recovery.
- **NOT YET PROVEN:** cross-body similarity, novel analogue discovery, local field-validation advantage, planetary-analogue challenge superiority.

**Highest-EV next experiment:** stop reusing these three unvalidated leads as a validation set. Acquire independently defined physical Earth–Moon/Mars analogue matches, hard negatives and instrument/footprint-compatible descriptors, then freeze leave-one-site-out or spatial-group holdouts and compare random, geography-only, Euclidean and physically weighted baselines. Independently challenge-rank all official 2026 statements. No UI polishing, field sampling, competition submission, outreach or main merge.
