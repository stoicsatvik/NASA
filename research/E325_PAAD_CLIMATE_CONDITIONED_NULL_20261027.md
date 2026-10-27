# E325 | Is E323 spatial raw-token dependence explained by Earth climate categories?

**27 October 2026. Research-only, pre-event.** Falsifiable hypothesis: the E323 Earth-only geographic raw-dune-token association may be partly explained by the source's Köppen–Geiger climate metadata, not independent geological structure.

The experiment downloads the official USGS PAAD 45-site CSV (DOI 10.5066/P9IFVZEX) and checks its frozen SHA-256, then repeats E323's nearest-site Jaccard and 25/50/100 km connected-component blocking. It compares three deterministic 999-permutation nulls: unrestricted whole-site token shuffling, shuffling within exact climate labels, and shuffling within only unambiguous first-letter climate families. Entire per-site token sets move together; site coordinates, labels, site identity and group sizes are fixed. Degenerate/singleton strata are reported explicitly.

**Important limitation:** the first-letter climate family is only a coarse analyst-defined stratum when the source code is unambiguous. It is *not* a Mars climate descriptor. Climate may correlate with geography and dune morphology, so conditional permutation differences do not establish causality. All p-values are exploratory, one-sided Monte Carlo statistics under specified exchangeability nulls; multiple thresholds/strata were inspected. Source abbreviations remain unharmonized.




## Source-pinned measured results (exact-head CI)

[GitHub Actions #40474399735](https://github.com/stoicsatvik/NASA/actions/runs/40474399735) **SUCCESS**, 28 deterministic tests passed, USGS PAAD source SHA-256 verified, full [JSON artifact #12720186077](https://github.com/stoicsatvik/NASA/actions/runs/40474399735/artifacts/12720186077). This result is from **45 real published Earth sites**, not synthetic coordinates.

- Raw nearest-site dune-token Jaccard **0.35005291**. With 100 km connected-component exclusion it falls to **0.23523810**, drop **0.11481481**. At 25/50 km the drop is **−0.00555556**, i.e. no reduction.
- **Global 999-permutation null:** nearest-site upper-tail p **0.001**, 100 km drop p **0.001** (different RNG seed from E323, whose p was 0.006).
- **Within exact source climate-description strata:** 10 groups, 40/45 sites in permutable groups, 5 singletons. Nearest p **0.001**, 100 km drop p **0.004**, 25/50 km drop p **0.466**.
- **Within explicitly analyst-grouped source descriptors:** ARID 37, EQUATORIAL 2, POLAR 2, SNOW 4. Nearest p **0.001**, 100 km drop p **0.002**, 25/50 km drop p **0.442**.
- **Failed coarse-code assumption preserved:** all 45 source climate entries are descriptive English text, not unambiguous Köppen alphanumeric codes. The strict first-letter climate-code parser therefore returned **45 UNCLASSIFIED**; its nominal "family" null is just unrestricted shuffling and **must not be cited as a climate-adjusted result**.

**Interpretation:** The specific Earth-only spatial raw-token association survives two source-description-conditioned exchangeability nulls. This makes a simple climate-label-only explanation insufficient *under these assumptions*. It does not prove causal geology, true climate adjustment, statistical independence of sites, or any cross-body similarity. The analyst descriptor groups are coarse, dominated by 37 arid sites, and not a canonical Köppen taxonomy. The exact-climate null has five immovable singleton sites. Multiple exploratory tests and spatially dependent source records limit inference.

The first CI run failed one deliberate free-text-label control: an overbroad parser misclassified "desert" as a D-family code. The parser was corrected to fail closed before any real-data claim; subsequent exact-head CI succeeded. The negative control remains in tests.

**Next decisive gate:** independently validate source dune morphology definitions, identify non-overlapping Earth/Mars physical descriptors and true positive/negative labels, then run blinded E001 recovery with spatially blocked holdouts. Do not spend on geospatial UX. Reassess all official 2026 challenge statements after their 28 October release.

**Claim states:** Earth-only lexical association E323 SUPPORTED under its original null; E325 conditional raw-label association SUPPORTED under tested source-preserving permutation nulls; E001 known-site recovery NOT YET MEASURED; cross-body similarity, novel analogue discovery, local validation advantage and challenge superiority NOT YET PROVEN.

No competition submission, field sampling, deployment, outreach, spending or main merge.
