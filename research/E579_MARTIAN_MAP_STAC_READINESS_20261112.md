# E579 — Martian Map source-readiness falsification
Date: 12 November 2026
Branch: research/e579-martian-map-stac-readiness-20261112
Base: E578 / PR #138. Draft research only; main untouched.

## Question

Does current evidence justify keeping the planetary-analog challenge as the readiness leader over the official Martian Map and MODIS/VIIRS alternatives? This is a challenge-selection experiment, not a scientific claim about cross-body similarity.

## Frozen comparison

The official 2026 challenge index states that the competition has 14 challenges: https://www.spaceappschallenge.org/2026/challenges/

The existing repository all-14 screen reports:
- Interplanetary Survival Guide: Martian Map: 4.10
- Harmonization of MODIS and VIIRS Hot Spots: 4.00
- Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars: 2.93

The top-two gap is 0.10, below the existing 0.25 meaningful-difference threshold. The E531 sensitivity screen favours Martian Map under the tested perturbations, but these are heuristic readiness scores, not objective probabilities or proof that the challenge will win. Challenge-selection superiority remains NOT YET PROVEN.

Official challenge descriptions:
- Martian Map: https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/
- MODIS/VIIRS: https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/
- Planetary analog: https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/

## Public data-source test

### Martian Map: controlled MRO CTX DTM collection

A live GET of the official USGS Astrogeology STAC collection metadata succeeded on 12 November 2026:

https://stac.astrogeology.usgs.gov/api/collections/mro_ctx_controlled_usgs_dtms

Observed metadata:
- Collection: mro_ctx_controlled_usgs_dtms
- Target: Mars
- Providers: NASA producer; USGS processor/host
- License: CC0-1.0
- Temporal interval: 2023-04-18 through 2025-07-04
- Ground sample distance metadata: minimum 20.0002065 m; maximum 35.9625866 m
- Projection metadata: Mars 2015 ocentric equirectangular WKT2, central longitude 0
- The collection description says CTX DTMs are generated with Ames Stereo Pipeline and controlled to MOLA.
- The same metadata explicitly warns that some DTMs are jittery or contain large missing-data regions and are not necessarily improvements over lower-resolution products.

The STAC items endpoint was not retrievable through this run's browser path. No item ID, raster, pixel sample, coverage polygon or terrain measurement was acquired. Therefore this is a successful collection-metadata access test, not a successful data-ingestion or map-validation test.

### Independent HiRISE context

The official NASA/USGS released HiRISE DTM registry describes CC0 data controlled to MOLA and warns that these controlled products are not guaranteed to co-register with uncontrolled HiRISE RDR imagery:
https://registry.opendata.aws/nasa-usgs-mars-hirise-dtms/

The official CTX DTM documentation reports 20 m post spacing and typical expected vertical precision around 3–5 m, but warns about jitter, nodata gaps, long-baseline tilt, MOLA control spacing and features below effective resolution:
https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/

Posting distance is not effective resolution. A map must preserve each product's CRS, control lineage, QA masks and acquisition provenance; it must not silently mosaic independently controlled DTMs as if their seams were exact.

### MODIS/VIIRS access constraint

The official challenge requires harmonizing active-fire records into a burning-activity calendar:
https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/

The official FIRMS access page states that Earthdata Login is required for daily text-file downloads and that API/WMS/WFS services use a MAP_KEY:
https://firms.modaps.eosdis.nasa.gov/content/active_fire/

No Earthdata account was created, no MAP_KEY was requested, and no credential was used. No credentialless historical MODIS/VIIRS dataset was verified in this run. This does not prove that no other public mirror or static sample exists.

### Planetary-analog data constraint

The official challenge asks teams to use open Earth, Moon and Mars data to identify and characterize new terrestrial analogs. The current NASA research branch has not yet assembled a defensible positive-site set plus matched non-analogue controls:
- E577 and E578 bounded ScienceBase source probes ended in transport timeouts with no records acquired.
- E572's independent catalogue remains a candidate site index, not quantitative physical labels or negative controls.
- Known-site recovery E001 remains NOT YET MEASURED.

## Result

Current evidence supports this **readiness ordering**, not a final challenge selection:

1. **Martian Map: strongest current data-readiness candidate.** An official CC0 STAC collection metadata endpoint is accessible and exposes CRS, target, GSD, temporal coverage, providers and control lineage. Actual item/raster access and feature validation are still missing.
2. **MODIS/VIIRS: viable but credential-gated in the official access path tested.** No key or account was created. A legitimate no-credential alternative remains worth searching.
3. **Planetary analog: scientifically interesting but currently weakest evidence readiness.** Positive/negative site labels are not established and E001 has not run.

No challenge is locked. The planetary-analog thesis remains a research hypothesis, not the proven best competition choice. Do not spend time on polished UI until at least one real data item is acquired and its spatial/measurement contract is validated.

## Next decisive experiment

Acquire exactly one public STAC item for a pinned Mars region and verify:
1. item identity, footprint and acquisition provenance;
2. CRS/WKT2 and coordinate convention;
3. COG asset availability and byte-range access;
4. nodata, QA/Figure-of-Merit and coverage masks;
5. co-registration only against products with documented shared control;
6. a small reproducible elevation/slope sample with units and uncertainty.

Use one pinned area, preserve the source item JSON and hashes, and fail closed on missing QA or CRS metadata. Compare the result with the same-area MOLA context. If the item endpoint remains inaccessible, preserve the failure and revisit the MODIS/VIIRS credentialless-source search; do not infer a scientific null.

## Claim states

- Repo operating system: SUPPORTED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Local validation advantage: NOT YET PROVEN.
- Challenge-selection superiority: NOT YET PROVEN.

No field data, raster measurements, site discoveries, route-safety claims, user tests or competition outcomes are asserted.
