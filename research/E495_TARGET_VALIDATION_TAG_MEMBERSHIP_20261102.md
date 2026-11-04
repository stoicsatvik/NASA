# E495 | Validation-tag override changes effective planetary analogue controls (2026-11-02)

## Falsifiable question and evidence

Does the E493 audit's body-level positive count identify the **actual** environmental positive sites used by every target in the public `Yakiyo/terra-nova` benchmark?

**No.** The pinned `src/compute/validation.py` applies `validation_tag` in preference to target body. When a target has a tag, it selects sites carrying that tag across bodies, then counts `kind == "environment"` as positives. This is explicitly documented upstream, not a hidden implementation defect.

Read-only inspection of public upstream commit `7128cc5363e916e422f7c770db9983981c0716f2`, with exact Git blobs:
- `data/known_analogs.json`: `d75240ce203ddb00b2d9186e7981ab90720ff9a3`
- `data/targets.json`: `ed326364e2ba4bad3e05a0bb48d06c23d7c87d4c`
- `src/compute/validation.py`: `ad44aca36f95a739af819f5e99ed8bfffa59a65c`

## Source-exact effective memberships

| Target | Target body | Override | Environmental positives | Positives from a different body | Possible positive-negative pairs |
|---|---|---|---:|---:|---:|
| lunar_south_pole | Moon | none | 3 Moon | 0 | 24 |
| malapert_massif | Moon | none | 3 Moon | 0 | 24 |
| haworth_psr | Moon | cold_polar | 3 Mars-labelled | 3 | 24 |
| jezero_crater | Mars | none | 5 Mars | 0 | 40 |
| gale_crater | Mars | none | 5 Mars | 0 | 40 |

For `haworth_psr`, the three positives are **Haughton impact crater, Devon Island; Axel Heiberg Island; and McMurdo Dry Valleys**. All are catalogued under `bodies: ["mars"]` but carry `tags: ["cold_polar"]`. The ordinary Moon positives (Meteor Crater, Craters of the Moon, Askja) are *not* the Haworth validation positives. The 8 negative reference sites are unchanged.

Thus the old count of 3 positives and 24 possible pairwise comparisons remains numerically correct for Haworth but is **semantically misleading** if called "Moon-positive" evidence. Cross-body control selection is not automatically invalid: a polar analog can be physically relevant across bodies. The important requirement is to report exactly which sites were used and why.

## Change and falsification controls

Extended `research/e493_benchmark_audit.mjs` with a pure `effectiveControls()` audit matching the published validation membership rule. The source-pinned CLI asserts one target with cross-body positives and three cross-body assignments, and checks the Haworth site names. It still refuses to report or infer an AUC from labels alone.

Added seven synthetic Node regression tests covering body-only selection, tag override, cross-body controls, geology exclusion, unknown-tag no-fallback, aggregate reporting, and editorial-proxy invariance. Local Node 22 syntax check and **7/7 tests passed**. The source-exact five-target membership table was independently evaluated against the pinned upstream JSON via GitHub source reads. An offline GitHub Actions workflow runs the seven synthetic tests; exact-head CI status must be checked separately.

## Limits and next decisive experiment

- The E495 result is **label provenance**, not a numerical rerun of the upstream reported 1.00 AUC. Pairwise counts assume every selected control has a finite score; the published `validate()` can exclude unscored controls.
- The three polar controls may be legitimate analogues for a lunar cold trap, but they do not independently validate general Moon-site recovery. Their overlap with Mars validation positives is a dependence to disclose.
- The eight humid/vegetated negatives remain easy controls. No independent same-biome hard negatives, DEM registration, held-out field labels, or E001 known-site recovery were measured.
- Do not compare models on this source-defined positive set and claim independent physical generalization. Next gate remains measured LOLA/MOLA/Earth terrain windows plus independently curated, mission-specific hard negatives and leave-one-site-out tests.

No upstream code or data was modified or redistributed, no emails sent, and no competition submission, production deployment or merge occurred.
