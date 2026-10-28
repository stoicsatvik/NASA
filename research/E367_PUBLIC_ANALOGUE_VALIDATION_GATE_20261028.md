# E367 | Independent public baseline and validation-control audit

**28 October 2026. Scope: pre-event research and challenge selection, not competition solution development.**

## Falsifiable question

Is the 2026 planetary-analogue challenge still differentiated by a global Earth scoring map and a headline known-analogue ROC-AUC? Does a publicly reported AUC of 1.00 establish cross-body Earth–Moon/Mars analogue recovery?

**A public comparator already describes a similar global screening product.** [Yakiyo/terra-nova](https://github.com/Yakiyo/terra-nova) reports 78,247 scorable Earth land cells, five Moon/Mars target profiles, a 3D globe, weighted scoring and known-site validation. These are **third-party self-reported capabilities**, not independently reproduced by this Foundry. The public code is a relevant existing baseline for cloneability and product differentiation, not a reason to accuse its authors of error.

Source commit frozen before this audit: [`f6c53ba50a9379d1c06f610b0e598395a0a54b43`](https://github.com/Yakiyo/terra-nova/tree/f6c53ba50a9379d1c06f610b0e598395a0a54b43). Public files independently audited via read-only, bounded requests:
- `data/known_analogs.json`
- `src/compute/validation.py`
- `README.md`

## What the source actually tests

The catalog defines 12 terrestrial analogue sites: **8 environmental positives** (5 Mars-tagged, 3 Moon-tagged) and **4 geology-only sites**. It also includes **8 editorial humid/vegetated negative reference points**, without source URLs. The validation function excludes geology-only sites from the headline AUC and compares target-appropriate Earth environmental positives against the same eight negative points.

For a generic body-level Mars target that is **5 × 8 = 40 positive-negative score pairs**; for a generic Moon target **3 × 8 = 24 pairs**. A target with an explicit `validation_tag` can use a different positive subset. Pair counts are not independent site counts and are not E001 recovery.

The repository README reports AUC **1.00** for five built-in targets. **We have not reproduced the score surface or this AUC**, and its interpretation must be limited to the declared Earth positive/editorial-negative controls. The catalog has no independently blinded Earth–Mars matched physical descriptors and does not establish planetary analogue retrieval accuracy. The negative labels were chosen for contrasting humidity/vegetation, which are directly scored features; this is a straightforward screening sanity check, not an adversarial cross-body validation.

## Why this changes the challenge decision

- A 3D map, transparent weighted Earth screening, source citations and site cards are **already publicly described**. UI-only novelty is therefore a weaker moat than assumed.
- Source-catalog ROC-AUC 1.00 is not a credible substitute for physically comparable Moon/Mars/Earth descriptors, independent positive/negative matches, spatially blocked held-out evaluation and ablations.
- This audit does **not** prove that the third-party system is scientifically invalid or that it has no stronger unexamined data. Nor does it prove our own challenge ranking.
- The alternative Lunar Navigator and Earth-data challenges remain live candidates; their own independent validation cost and data accessibility must be measured before selection.

## Reproduce and exact evidence boundary

```bash
python -m pip install pytest
python -m pytest -q tests/test_e367_public_analogue_control_audit.py
python -m research.e367_public_analogue_control_audit
```

The script requests only three public files at the pinned Git commit, records SHA-256 for each, validates site identities and coordinates, verifies the source's positive/negative AUC policy, and emits a machine-readable source-control receipt. It **does not** fetch private data, execute the competitor's code, reproduce its 78,247-cell predictor cube, compute AUC, train a model or build a contest entry.

**Claim states:** Public comparator and source-control design SUPPORTED BY SOURCE AUDIT once exact-head CI passes; third-party AUC SELF-REPORTED / NOT INDEPENDENTLY REPRODUCED; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel discovery, local validation advantage and planetary challenge superiority NOT YET PROVEN.

**Next decisive experiment:** Obtain independently defined physical cross-body analogue positives and credible hard negatives, then freeze descriptors and split before label exposure. Do not optimize UI or promote the editorial-negative AUC into scientific evidence.
