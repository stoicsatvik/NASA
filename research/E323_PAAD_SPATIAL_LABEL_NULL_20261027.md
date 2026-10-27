# E323: Does spatial blocking change real PAAD raw-token agreement? (27 October 2026)

## Frozen question and sources

On the 45 Earth dune-site records from the USGS Planetary Aeolian Analog Database (PAAD), DOI `10.5066/P9IFVZEX`, does the nearest *separately named* site tend to share source-reported dune-type **raw string tokens** more than a geographic-label-exchangeability null predicts? Does excluding whole connected spatial components at 25, 50 or 100 km materially change that overlap?

The CSV was re-downloaded read-only from the official ScienceBase item and SHA-256 checked against E317/E319:
`5be67b4da584987d9ce5207f2ee3c90b5b3b5849469461847111eaab5aafcecd`.
No raw CSV was committed. Names, coordinates and per-site raw code tokens were used; no physical/geological meaning was assigned to unverified abbreviations.

Predeclared metric: mean per-site Jaccard overlap of raw token sets with its nearest eligible other site. Spatial blocking excludes every member of the same **connected component** at each distance threshold, not just directly nearby neighbors. 999 deterministic permutations (seed 323) shuffle intact per-site token sets over fixed coordinates, preserving row cardinalities and global token frequencies. One-sided p-values are Monte Carlo upper-tail counts including the observed sample correction, not posterior probabilities or external validation.

## Exact-head real-data result

[GitHub Actions #40467944124](https://github.com/stoicsatvik/NASA/actions/runs/40467944124) **SUCCESS**, 28 deterministic synthetic/inherited tests passed, official source fingerprint verified, real-data computation completed. [Full machine-readable artifact #12717605849](https://github.com/stoicsatvik/NASA/actions/runs/40467944124/artifacts/12717605849).

- **45 sites**, **13 distinct raw dune-type tokens**.
- Name-only nearest-site mean Jaccard **0.3500529101**, upper-tail **p = 0.001** against 999 whole-site label permutations.
- **25 km** component-blocked nearest mean **0.3556084656**, difference name-only minus blocked **−0.0055555556**, permutation **p = 0.572**.
- **50 km** same mean and difference as 25 km, **p = 0.572**.
- **100 km** component-blocked nearest mean **0.2352380952**, difference **+0.1148148148**, permutation **p = 0.006**.
- All **45/45** holdouts retained at every threshold because another component remained available. The blocked nearest neighbors can be distant and unrepresentative, so these differences are not causal estimates.

## What changed our belief

**SUPPORTED WITHIN THIS CATALOG:** Raw dune-type token assignments are not exchangeable across source-reported Earth coordinates under this specified permutation null; name-only nearest-site agreement is unusually high. At the **100 km** connected-component threshold, the observed nearest-neighbor overlap falls by about **0.115 Jaccard**, unusually large under the same null. At **25/50 km**, blocking does **not** reduce measured overlap; the small difference is opposite sign and not unusual. The 100 km result is threshold-specific, exploratory and does not validate any cross-body model.

**REJECTED AS A GENERAL CLAIM:** “Every spatial-blocking radius reduces raw-token agreement.” The 25/50 km controls falsify that universal statement.

**NOT ESTABLISHED:** Whether the PAAD abbreviations have harmonized geological semantics; shared site provenance or geodetic accuracy; the source of geographic token correlation; out-of-catalog generalization; Earth–Mars labels, independent negative sites, or physical analogue recovery. This is an **Earth-only lexical-label** audit, not E001. No empirical effect size confidence interval was inferred from permutation p-values.

**Claim states:** E001 known-site recovery **NOT YET MEASURED**. Cross-body similarity **NOT YET PROVEN**. Novel analogue discovery **NOT YET PROVEN**. Local field-validation advantage **NOT YET PROVEN**. Challenge-selection superiority **NOT YET PROVEN**.

## Next discriminating experiment

Obtain the authoritative PAAD codebook and actual MGD3 morphology definitions/linked observations; independently validate source relationships and physically comparable descriptors. Only then test known-site recovery under site-name and 100 km blocked holdouts with random/majority/physically weighted baselines. Also test whether the apparent 100 km dependence survives codebook harmonization and a genuinely independent source. Reassess all 14 official challenge statements after the 28 October release.

No competition submission, deployment, outreach, field sampling, spending or main merge.
