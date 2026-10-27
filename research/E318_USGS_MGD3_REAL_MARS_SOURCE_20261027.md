# E318 — Real USGS MGD3 Mars dune data, with a failed label-harmonization shortcut

**27 October 2026.** Isolated research branch, draft PR #28. Independent official publication: [USGS Open-File Report 2018–1164](https://pubs.usgs.gov/publication/ofr20181164), DOI [10.3133/ofr20181164](https://doi.org/10.3133/ofr20181164).

## Experiment and reproducible evidence

Question: can the independently curated Mars Global Digital Dune Database provide real Mars observations that can be paired with E317's 45 Earth PAAD dune sites for a legitimate E001 analogue-recovery benchmark?

**Actual public archive ingested:** `https://pubs.usgs.gov/of/2018/1164/ofr20181164_dunedatabase.zip`. Bounded read-only GitHub Actions download, **2,982,330 bytes**, SHA-256 `92771c23cfa4a64dfcc38f5ad29de00adfa41b9f321d3665beb2112eefe3485e`. The root [2020 USGS ScienceBase merged release](https://www.sciencebase.gov/catalog/item/5f8a1d2e82ce324187893a97) returned **zero directly attached eligible files** in this particular API response; that negative access result is retained, not misreported as a missing Mars dataset.

The USGS 2018 ZIP contains two readable equatorial/south-polar XLSX workbooks. **Seven worksheet profiles** were parsed in total, excluding two malformed `__MACOSX/._*` metadata members, which are preserved as `TABLE_PARSE_FAILED / BadZipFile` rather than counted as scientific observations.

| Worksheet | Observed nonheader rows |
|---|---:|
| Equatorial: Global Summary, ocks <7000 | 58 |
| Equatorial: Global Summary, all ocks | 59 |
| Equatorial: TES observation data summary | 405 |
| Equatorial: selected mineral worksheet | 50 |
| South polar: Global Summary, ocks <7000 | 51 |
| South polar: Global Summary, all ocks | 53 |
| South polar: TES observation data summary | 329 |

**These are worksheet rows, not unique dune sites.** The same dunes can occur in multiple summary sheets, and observation rows are not necessarily independent sites. The instrument summary fields include source-reported mineral abundances and errors, stability index, nighttime thermal inertia (tiu), and daytime albedo. Raw columns and nonempty counts are retained in the Actions JSON receipt. Source data were not committed.

The first attempted archive parse failed because macOS resource-fork files were named `.xlsx` without being actual workbooks. E318 preserved this negative result, added a synthetic mixed-archive regression, and successfully parsed the valid worksheets without silently swallowing the invalid members.

**Final exact-head validation:** [GitHub Actions run #40439550237](https://github.com/stoicsatvik/NASA/actions/runs/40439550237), **SUCCESS**, 12 deterministic synthetic tests, real USGS source access. [Machine-readable artifact #12706135886](https://github.com/stoicsatvik/NASA/actions/runs/40439550237/artifacts/12706135886) includes both successful and failed source receipts.

## What was falsified / not established

The tempting shortcut **"PAAD Earth dune type codes + MGD3 2018 Mars mineral/thermal columns = matched analogue labels" is invalid**. The datasets have different field semantics, acquisition conditions, measurement support and sampling bias. The MGD3 2018 archive does not, in the profiled worksheets, expose a directly harmonized Earth/Mars dune-morphology target label. Raw climate categories and raw Mars thermal inertia are not interchangeable. MGD3's known dune fields are positives, not evidence that unmapped areas are true negatives.

**SUPPORTED:** real independently sourced Mars workbook ingestion, source SHA, raw schema and negative parse controls.

**NOT YET MEASURED:** E001 known-analogue recovery.

**NOT YET PROVEN:** cross-body similarity, novel analogue discovery, local validation advantage and challenge-selection superiority.

## Highest-value next test

Find the **MGD3 morphology/landform codebook** from the original USGS 2007–2012 mapped dune-field tables and the **PAAD dune-type abbreviation codebook**. Predeclare only genuinely shared, physically justified morphology descriptors, establish nonleaking positive and negative labels, then execute random/majority/physically weighted baselines and leave-one-site-out ablations. If no independent matched labels exist, record that failure and pivot the E001 target rather than fabricating matches. Re-rank all fourteen official 2026 challenges once full statements are available on 28 October.

No competition submission, field data, paid access, outreach, main merge or deployment.
