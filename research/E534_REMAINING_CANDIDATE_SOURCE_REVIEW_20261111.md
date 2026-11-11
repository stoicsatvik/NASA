# E534 — source audit of the six remaining Mars/Moon candidates (2026-11-11)

## Question

Do primary sources support the narrow candidate-label claims for the six Mars/Moon records not reviewed in E533, when checked against the same immutable catalogue revision?

E534 is the complement of E533's six-record purposeful subset. It does not rewrite E533 or promote catalogue statuses.

## Frozen source and selection

- Catalogue: rachellelecussan/planetary-analogue-catalogue
- Immutable revision: 62e6339bdf308de3bc987388d0faa7130cf57de9
- File: data/sites.geojson
- Source revision and URL are imported from the E533 pinned-source module.
- New frozen IDs: dallol-et, mcmurdo-dry-valleys-aq, arkaroola-au, lanzarote-es, bockfjord-svalbard-sj, boulby-mine-gb.
- Previous E533 IDs are loaded unchanged and checked against their exact six-ID set.
- This is a source-to-claim review, not an expert site verification or a random sample.

## Source-by-source findings

| Candidate | Narrow scope | Primary evidence | Decision and limitation |
|---|---|---|---|
| Dallol, Ethiopia | Iron-rich, hyperacidic hydrothermal geochemistry | Kotopoulou et al. (2019), DOI [10.1021/acsearthspacechem.8b00141](https://doi.org/10.1021/acsearthspacechem.8b00141), explicitly identifies Dallol as a terrestrial Martian analogue site and documents Fe-rich brines and iron-mineral precipitation. | Candidate label supported for hydrothermal geochemistry and iron-mineral processes only. Not whole-site terrain equivalence. |
| McMurdo Dry Valleys, Antarctica | Dry-valley microclimate and geomorphic processes | Marchant & Head (2007), DOI [10.1016/j.icarus.2007.06.018](https://doi.org/10.1016/j.icarus.2007.06.018), explicitly links Antarctic dry-valley microclimate and geomorphic processes to Mars climate interpretation. | Candidate label supported for climate/geomorphology questions. Not a claim that Antarctic and Martian environments are identical. |
| Arkaroola / Mount Painter Inlier, Australia | Hyperspectral mapping of hydrothermal alteration | Thomas & Walter (2002), DOI [10.1089/153110702762027916](https://doi.org/10.1089/153110702762027916), validates airborne and field SWIR mineral mapping at Mount Painter and states that similar surveys could provide detail about putative hydrothermal deposits on Mars. | Candidate label supported for remote-sensing method transfer. Not proof of identical mineral abundance or alteration history. |
| Lanzarote lava tubes, Spain | Volcanic subsurface mineralogy, microbial communities and biosignature preservation | Palma et al. (2024), DOI [10.1016/j.scitotenv.2023.169583](https://doi.org/10.1016/j.scitotenv.2023.169583), explicitly frames Lanzarote lava tubes as Mars analogs and studies speleothems, microbial communities, mineralogy and organic biomarkers. | Candidate label supported for lava-tube volcanology and biosignature methods. A 2024 corrigendum exists (DOI [10.1016/j.scitotenv.2024.170811](https://doi.org/10.1016/j.scitotenv.2024.170811)); its specific correction is not interpreted here. The catalogue's unverified 2026 reference is not used. |
| Bockfjord volcanic complex, Svalbard | Carbonate-globule mineralogy and abiotic carbon processes | Steele et al. (2007), DOI [10.1111/j.1945-5100.2007.tb00590.x](https://doi.org/10.1111/j.1945-5100.2007.tb00590.x), compares Martian meteorite ALH 84001 carbonate globules with similar objects in Svalbard mantle xenoliths and reports similarities in carbonate/iron-oxide zoning and macromolecular carbon association. | Candidate label supported only for a narrow meteorite-mineralogy/process analogue. Not a general Mars surface or landscape analogue. |
| Boulby Mine, United Kingdom | Deep subsurface evaporite geology, instrument testing and habitability | Payler et al. (2017), DOI [10.1017/S1473550416000045](https://doi.org/10.1017/S1473550416000045), describes the MINAR programme as extraterrestrial analogue research and notes Mars subsurface habitability; Payler et al. (2019), DOI [10.3389/fmicb.2019.00426](https://doi.org/10.3389/fmicb.2019.00426), measures deep mine brines and microbial growth limits. | Candidate label supported for subsurface geology, instrument development and habitability research. Not a claim of matching Martian pressure, temperature, radiation or regolith. |

The review intentionally distinguishes a site used as a methodological analogue from a site with matched physical properties. A DOI attached to a catalogue record is not itself proof that every field in that record is correct.

## Cumulative result across E533 and E534

The pinned catalogue contains 16 features. Twelve have primary Mars/Moon labels: 10 Mars and 2 Moon. E533 reviewed six; E534 reviews the remaining six.

- Cumulative Mars/Moon candidates source-audited: 12/12.
- Cumulative target counts: Mars 10, Moon 2.
- Catalogue records marked Verified: 0.
- Catalogue records remain Draft: all 12 reviewed records.
- Explicit non-analogue controls: 0.
- Matched physical descriptors admitted for E001: 0.
- E001 readiness: NOT READY.
- Known-site recovery: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- Novel analogue discovery: NOT YET PROVEN.

**Decision:** primary sources support the narrow candidate-label claims for all twelve Mars/Moon records in this pinned catalogue. This does not make the catalogue a validated ground-truth set. The source review does not measure whether an algorithm can recover known sites or distinguish analogues from non-analogues.

## Reproducibility and validation

- experiments/e534_remaining_candidate_source_review.py fetches the same immutable E532 GeoJSON through E533's pinned-source fetcher, validates the previous and new six-ID sets, checks DOI membership, target-body consistency and Draft status, then emits a JSON receipt.
- research/E534_REMAINING_CANDIDATE_SOURCE_REVIEW_20261111.csv records the manual source-to-feature relation and explicit limitations.
- experiments/test_e534_remaining_candidate_source_review.py checks source pinning, exact selection, DOI membership, no overlap with E533, no status promotion, target counts and no negative-control inference.
- The workflow stores a machine-readable receipt. It does not copy external source photos, sensitive coordinates or the raw external catalogue.

## Next decisive work

1. Build a defensible, predeclared non-analogue control universe; absence from a positive catalogue must not be treated as a negative.
2. Obtain matched-support quantitative descriptors from Earth and planetary products, with units, uncertainty, spatial support and provenance.
3. Freeze a baseline and evaluate leave-one-site-out recovery only after the label and descriptor gates are satisfied.

The twelve source-supported candidate labels remain candidate positives, not verified ground truth.
