# E533 — source audit of a predeclared Mars/Moon candidate subset (2026-11-11)

## Question

Do the primary sources cited by a predeclared subset of the independent analogue catalogue actually support the narrow Mars/Moon candidate-label claims attached to those Earth sites?

This is a provenance/label audit, not an expert verification of the sites, a cross-body similarity test, or an E001 recovery benchmark.

## Frozen source and selection

- Candidate catalogue: `rachellelecussan/planetary-analogue-catalogue`
- Immutable revision: `62e6339bdf308de3bc987388d0faa7130cf57de9`
- File: `data/sites.geojson`
- Selection: six Mars/Moon primary-label records for which the catalogue supplies a peer-reviewed DOI with a directly inspectable source record and a narrow target-feature claim.
- This is a **purposeful evidence-availability subset**, not a random or representative sample of all 12 Mars/Moon candidates. Six other in-scope candidates remain unaudited.
- All six catalogue records remain `Draft`; none is promoted to `Verified`.

## Source-by-source findings

| Earth candidate | Target | Primary source evidence | Decision and scope |
|---|---|---|---|
| Atacama Yungay | Mars | Navarro-González et al. (2003), DOI [10.1126/science.1089143](https://doi.org/10.1126/science.1089143), explicitly frames Atacama soils as Mars-like and studies the dry limit of microbial life. | **Candidate label supported** for hyperarid soil/habitability questions; not a general topographic or spectral analogue. |
| Río Tinto | Mars | Amils et al. (2014), DOI [10.3390/life4030511](https://doi.org/10.3390/life4030511), explicitly describes a geochemical/mineralogical Mars analogue; Gómez et al. (2011), DOI [10.1017/S147355041100005X](https://doi.org/10.1017/S147355041100005X), documents a multidisciplinary field campaign. | **Candidate label supported** for acidic, iron/sulfur-rich geochemistry; not whole-site equivalence. |
| Holuhraun / Krafla region | Mars | Voigt et al. (2025), DOI [10.3847/PSJ/adb5f1](https://doi.org/10.3847/PSJ/adb5f1), directly compares the 2014–2015 Holuhraun flow field with young volcanic terrains in Elysium Planitia. | **Candidate label supported** for fissure-fed lava morphology and emplacement processes. The paper itself reports major scale differences, including Martian flow-field volumes orders of magnitude larger. |
| Lava Beds National Monument | Moon | Primary study DOI [10.1029/2021JE007140](https://doi.org/10.1029/2021JE007140) measures magnetic anomalies over terrestrial lava tubes and explicitly relates them to lunar lava-tube exploration. | **Candidate label supported** for lava-tube detection/geometry methods; not a claim of identical terrestrial and lunar magnetic environments. |
| Mauna Kea | Moon | ten Kate et al. (2013), DOI [10.1061/(ASCE)AS.1943-5525.0000200](https://doi.org/10.1061/(ASCE)AS.1943-5525.0000200), documents a field campaign testing and calibrating instruments developed for in-situ lunar research. | **Candidate label supported** as an operational/instrument-test analogue; this is not proof of complete geological equivalence. |
| Haughton impact structure | Mars | Lee & Osinski (2005), DOI [10.1111/j.1945-5100.2005.tb00144.x](https://doi.org/10.1111/j.1945-5100.2005.tb00144.x), describes the Haughton-Mars Project; Tornabene et al. (2005), DOI [10.1111/j.1945-5100.2005.tb00149.x](https://doi.org/10.1111/j.1945-5100.2005.tb00149.x), applies remote-sensing lithologic mapping at Haughton to Mars. | **Candidate label supported** for Mars-relevant impact geology and remote-sensing methods; not one-to-one equivalence of every landform or mineral unit. |

The evidence supports six **narrow candidate-positive labels**. It does not independently verify exact site coordinates, current access, field safety, or all descriptive fields in the catalogue.

## Reconciliation: the official USGS 2020 point layer was already ingested

The E532 note proposed acquiring the USGS 2020 *Known Terrestrial Analog Sites for Planetary Science* layer (DOI [10.5066/P9J72921](https://doi.org/10.5066/P9J72921)). That would duplicate prior work.

NASA PR #33 / E326 already queried the same ScienceBase item `5f88940b82cebb8c13d912ee` and its anonymous public ArcGIS layer on 27 October 2026. The recorded result was four feature rows, all `AnalogType=Volcanic`; `AnalogBody` was empty/null-like in all four. No dune positives or negatives were present. The source is therefore not a missing acquisition task and does not supply a Moon/Mars-labelled validation cohort.

The E326 receipt and limitations remain in [NASA PR #33](https://github.com/stoicsatvik/NASA/pull/33). E533 does not repeat that acquisition.

## Reproducibility

- `experiments/e533_candidate_label_source_review.py` fetches the exact pinned E532 GeoJSON, enforces URL/byte limits, verifies the six site IDs, target-body labels, Draft statuses and catalogue DOI membership, and emits a JSON receipt.
- `research/E533_CANDIDATE_LABEL_SOURCE_REVIEW_20261111.csv` records the manual source-to-claim mapping and limitations.
- `experiments/test_e533_candidate_label_source_review.py` checks source pinning, six-record selection, DOI membership, no status promotion and no negative-control inference.
- The workflow stores a 30-day receipt artifact; no source photos, sensitive coordinates or raw external catalogue are copied.

## Result

- Six of 12 Mars/Moon primary candidates were source-audited in a purposeful subset.
- All six cited sources support the corresponding narrow candidate-label claim.
- All six catalogue records remain Draft.
- Six in-scope candidates remain unaudited.
- No non-analogue controls were created.
- No E001 ranking or leave-one-site-out recovery was run.

**Decision:** candidate-positive source support is **SUPPORTED for these six narrow claims**. The catalogue as a whole remains **NOT E001-READY**. Known-site recovery remains **NOT YET MEASURED**; cross-body similarity remains **NOT YET PROVEN**.

## Next decisive work

1. Review the remaining six Mars/Moon candidates using the same explicit source-to-feature criteria.
2. Build a defensible, predeclared control universe without treating absence from a positive catalogue as a negative.
3. Obtain matched-support physical descriptors from real Earth and planetary products.
4. Re-run E001 only when the label and descriptor gates are met.

The official USGS 2020 layer must not be reacquired as if it were new; its E326 result is already part of the evidence ledger.
