# E411 | Frozen challenge-ranking ablation and 2026 source-index mismatch

**30 October 2026.** Pre-event decision/eligibility research only; no competition solution, data fabrication, deployment or submission.

## Falsifiable questions

1. Does E193's set of 14 analyst-scored challenges correspond one-to-one to the currently published 2026 local-event challenge index?
2. Is the provisional planetary-analogue ranking sensitive to one specific declared scoring axis?
3. Is under-18 eligibility a concrete operational gate, rather than a speculative local restriction?

**Source scope:** [HackAthlone 2026 challenge index](https://hackathlone.com/challenges), a local-event page reproducing NASA Space Apps challenge summaries, accessed 30 October 2026. The [official 2026 event](https://www.spaceappschallenge.org/2026/) confirms the 14–15 November dates; [official legal terms](https://www.spaceappschallenge.org/legal/) were searched for under-18 conditions. Direct fetches of several official full challenge pages returned HTTP 502, so **all fourteen full official statements/resources have NOT been independently verified**. This audit does not satisfy NASA issue #1's full-statement acceptance criterion.

## Source-index mismatch (new)

The local-event index has 14 distinct challenge titles. Thirteen map unambiguously to E193's 14 scored labels after harmless short-name normalization. E193 contains **`CLPS lunar browser`**, while the published index contains **`Lunar Landing Site Navigator`**. The latter asks for Moon south-pole Sun/Earth horizon geometry and illumination/communication comparisons; it must not silently inherit ratings for a different CLPS browser. The official navigator URL is https://www.spaceappschallenge.org/2026/challenges/lunar-landing-site-navigator/.

**Result:** E193's claim to cover the complete current official set is **REJECTED AS EXACT TITLE/CHALLENGE COVERAGE**. Its historical arithmetic remains valid *conditional on its historical analyst score table*. No historical E193 files or ratings were rewritten. A fresh navigator assessment is needed before claiming an exhaustive current ranking.

## Exact leave-one-criterion-out sensitivity (new arithmetic, not measured competition evidence)

The experiment parses the frozen E193 score vectors and weights directly from the historical Python source with the standard library; it neither re-fits nor edits them. For each of seven criteria, remove its weight and renormalize the other six, leaving all original analyst ratings and cloneability/dependency penalties unchanged.

- Original provisional planetary score **4.59**, rank **5/14**.
- Highest original competitor: MODIS/VIIRS **5.43**; difference **0.84**.
- Removing **validation** alone makes planetary analogues rank **1/14** among the *old fourteen entries*. Removing any other single criterion does **not**.
- At unchanged weights and all other scores/penalties fixed, the planetary validation rating must rise from **4.0 to 8.2** to *tie* MODIS/VIIRS, or exceed 8.2 to win.

This is a precise diagnosis of **the analyst ranking's dependence on validation**, not evidence that planetary science is worse, that MODIS will win, or that a future validation experiment can earn a score of 8.2. The official index mismatch makes even this old-table ranking non-exhaustive for the current challenge set.

## Independent eligibility gate

The [official Space Apps legal terms](https://www.spaceappschallenge.org/legal/) state that participants **under 18 must be registered by a parent or legal guardian and accompanied by a parent or legal guardian throughout the event**. This is an important practical requirement, not a universal 18+ ban. Local venue rules and implementation should be checked independently. No registration, contact or commitments were made.

## Reproducibility

- `research/e411_challenge_validation_ablation.py`
- `tests/test_e411_challenge_validation_ablation.py`
- `python -m unittest discover -s tests -p 'test_e411_challenge_validation_ablation.py' -v`
- `python -m research.e411_challenge_validation_ablation`
- Dedicated read-only Actions workflow repeats byte-identical receipts and uploads JSON.

## Claims and decision

- E193 current challenge coverage: **REJECTED AS EXACT COVERAGE** (13/14 aliases, one stale entry).
- E193 numerical sensitivity: **SUPPORTED AS REPRODUCIBLE ARITHMETIC ON SUBJECTIVE RATINGS**.
- Planetary-analogue challenge superiority: **NOT YET PROVEN**.
- NASA repo operating system: **SUPPORTED**.
- E001 known-site recovery: **NOT YET MEASURED**.
- Cross-body similarity, novel analogue discovery, local field advantage: **NOT YET PROVEN**.

**Next decisive gate:** obtain the actual full official 14 statements/resources and independently score the lunar navigator rather than inheriting CLPS assumptions; test empirical data/validation cost for MODIS/VIIRS and Earth Trend against a blinded E001 known-site recovery attempt. No geospatial UI or pre-event competition solution work.
