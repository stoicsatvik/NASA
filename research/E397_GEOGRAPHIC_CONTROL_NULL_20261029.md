# E397 | Does geography alone separate a public analogue catalogue's editorial controls?

29 October 2026. Independent pre-event catalogue validation audit, not a competition solution.

## Falsifiable question

E369/E375 show high Earth-only vegetation/precipitation AUCs when the source's analogue sites are compared against eight deliberately humid/vegetated editorial negatives. Could even a trivial geography-only score achieve apparently meaningful AUC on those source labels, indicating selection dependence?

Source: Yakiyo/terra-nova, commit f6c53ba50a9379d1c06f610b0e598395a0a54b43, path data/known_analogs.json, Git blob SHA-1 d75240ce203ddb00b2d9186e7981ab90720ff9a3 (6,500 bytes). All 12 source-labelled analogue sites (eight environmental, four geological) remain positives; eight editorial humid/vegetated sites remain negatives. No geology positives were re-labelled as negatives.

Five intentionally simplistic fixed geographic scores: absolute latitude, signed northern latitude, negative absolute latitude, westward longitude, absolute longitude. No model fitting, no raster values, no planetary observations. Compute pairwise AUC with half-credit ties, then enumerate **all C(20,12) = 125,970** fixed-score label allocations. Report exact conditional one-sided p-values and a max-of-five familywise selection correction. The five scores were explored together, so the corrected statistic is primary.

## Reproduced calculations (source-pinned catalogue)

| Geographic-only score | AUC | Exact one-sided p |
|---|---:|---:|
| Absolute latitude | 0.760416667 | 3614/125970 = 0.028689370 |
| Northern latitude | 0.635416667 | 21613/125970 = 0.171572597 |
| Negative absolute latitude | 0.239583333 | 122988/125970 = 0.976327697 |
| Westward longitude | 0.750000000 | 4352/125970 = 0.034547908 |
| Absolute longitude | 0.604166667 | 29771/125970 = 0.236334048 |

**Max-of-five familywise exact p = 16547/125970 = 0.131356672.** Geographic proxies produce nontrivial apparent separation on this editorial catalogue, but the five-feature familywise test does **not** reject the exchangeable-label null at 5%. A stronger claim that geography explains E369's vegetation AUC is not supported. Independent Python pairwise enumeration and JavaScript rank-sum enumeration agreed on all five AUCs, exceedance counts and the max statistic.

## Important limitations

- Source-selected editorial negatives are not a random or independent scientifically adjudicated non-analogue sample; label-exchangeability is a hypothetical sensitivity null, not an actual randomized experimental design.
- Five geographic scores were exploratory, not a preregistered scientific family. The max statistic corrects only for this specified family, not arbitrary post-hoc choices.
- Source coordinates include point representatives of large geographic regions; longitude is not physically comparable across all site geometries.
- No cross-body topographic, thermal, geological or instrument-aware descriptors were evaluated. This is not E001 known-site recovery and not evidence of a planetary-analogue model.
- The Space Apps pre-event development boundary remains respected: only public source-audit mathematics and reproducibility are added.

**Claim states:** geography-only apparent AUC SUPPORTED FOR THIS SOURCE; geographic confounding CANDIDATE / NOT PROVEN after familywise correction; E001 known-site recovery NOT YET MEASURED; cross-body similarity, novel analogue discovery, local field advantage and challenge-selection superiority NOT YET PROVEN.

**Next decisive experiment:** obtain independent geology-labelled and environment-labelled site/non-site controls from legitimate sources, freeze identity-disjoint and spatially blocked splits, and compare simple geography-only/Euclidean/physically weighted descriptors on matched Earth/Moon/Mars physical support. Preserve nulls; no UI polish.

**Reproduction:** python -m unittest discover -s tests -p test_e397_geographic_control_null.py -v; python -m research.e397_geographic_control_null. Dedicated Actions workflow verifies pinned blob, repeats output and uploads numerical receipt. No private data, fieldwork, outreach, spending, deployment or submission.
