# E418 | Does one editorial negative determine the geography-only null?

**Date:** 30 October 2026. **Scope:** pre-event source-selection sensitivity, not a competition solution or known-analogue recovery.

## Decision question
E397 reported an exploratory geography-only maximum AUC of 0.760416667 across five fixed scores on 12 source-labelled Earth analogues versus eight source-selected humid/vegetated editorial negatives. Its exact max-of-five conditional label-exchangeability p was 16547/125970 = 0.131356672. Is the apparent geographic separation stable when *each* editorial negative is deleted in turn, without choosing the deletion after seeing a favorable result?

## Frozen design and provenance
Use the same source-pinned [Yakiyo/terra-nova](https://github.com/Yakiyo/terra-nova/tree/f6c53ba50a9379d1c06f610b0e598395a0a54b43), `data/known_analogs.json`, commit `f6c53ba50a9379d1c06f610b0e598395a0a54b43`, Git blob SHA-1 `d75240ce203ddb00b2d9186e7981ab90720ff9a3` (6,500 bytes), already verified by E397. Keep all 12 source-positive sites including four geology positives. Remove each of eight negatives *once*, leaving 12 positives and seven editorial controls. Retain E397's five scores: absolute latitude, northern latitude, negative absolute latitude, westward longitude and absolute longitude. No fitting or new planetary measurements.

For each deletion calculate pairwise half-tie AUC and exact conditional maximum-of-five p by enumerating **all C(19,12)=50,388** label allocations. The max statistic accounts for choosing the strongest of the five fixed geographic features within that deletion; it does **not** adjust for a post-hoc choice among the eight deletions. Report all eight, not only the smallest p.

## Measured source-pinned results

| Editorial negative omitted | Maximum geographic AUC | Exact max-of-five p |
|---|---:|---:|
| Amazon rainforest | 0.761905 | 7808/50388 = 0.154958 |
| Congo Basin rainforest | 0.726190 | 13038/50388 = 0.258752 |
| Borneo rainforest | 0.726190 | 12765/50388 = 0.253334 |
| Iowa cropland | 0.809524 | 3404/50388 = 0.067556 |
| Dhaka, Bangladesh | 0.738095 | 11048/50388 = 0.219259 |
| West Siberian taiga | 0.821429 | 2654/50388 = 0.052671 |
| South-eastern US forest | 0.785714 | 5283/50388 = 0.104846 |
| Western Europe farmland | 0.809524 | 3384/50388 = 0.067159 |

The maximum AUC ranges **0.726190–0.821429** and the eight conditional p-values **0.052671–0.258752**. **None** is below 0.05, even before accounting for looking across eight deletions. The apparent geography-only separation depends on which editorial controls remain, and no robust geographic confounding conclusion is established.

## Independent computational checks
1. The pinned 6,500-byte public JSON was retrieved through the GitHub connector and contained 12 positive / 8 negative records.
2. Independent JavaScript recursive-combination and bitmask-combination enumerators agreed on all eight exceedance counts.
3. An independently written Python `itertools.combinations` enumeration, using the exact coordinates retrieved from that source, matched all eight counts. Direct pairwise AUC agreed with rank-sum AUC.
4. Repository script `research/e418_geographic_negative_deletion.py` reuses E397's pinned-source SHA guard, midranks and fixed score definitions; offline toy regression tests were committed.
5. **Not executed:** the newly committed Python script against the source, the repository's pytest suite or exact-head GitHub Actions. Included Actions minutes were reported exhausted on 29 October; no paid CI was initiated. The measured counts come from the three independent local calculations above, not a claimed CI run.

## Evidence boundary
- **SUPPORTED:** source-specific deletion sensitivity of geography-only AUC and conditional null p.
- **NOT SUPPORTED:** declaring geographic confounding established at 5%, treating editorial negatives as independently adjudicated non-analogues, or using source-catalog AUC as cross-body recovery evidence.
- **NOT YET MEASURED:** E001 known-site recovery.
- **NOT YET PROVEN:** cross-body similarity, novel analogue discovery, local field-validation advantage and 2026 challenge superiority.

The deletion experiments are highly dependent because they share 12 positives and six or seven controls. Their p-values are conditional sensitivity diagnostics, **not** independent confirmatory hypothesis tests. Label-exchangeability is not a valid sampling model for intentionally chosen editorial negatives.

## Highest-value next move
Stop trying to extract scientific validity from the same editorial-control catalogue. Obtain source-independent, physically characterized Earth/Moon/Mars analogue pairs with legitimate negative controls and compatible spatial supports. Freeze site identities and split before scoring; compare random, geography-only, standardized Euclidean and physically weighted baselines with spatial blocking and ablations. If such labels cannot be acquired before the deadline, reassess Lunar Navigator and Earth-data challenge alternatives rather than investing in UI.

No fieldwork, outreach, competition submission, spending, deployment, main merge or paid API usage.
