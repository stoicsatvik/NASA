# E588 — USGS CTX product-level control provenance boundary

Date: 12 November 2026  
Branch: `research/e588-usgs-ctx-product-control-boundary-20261112`  
Parent: E587 / `research/e587-ctx-provenance-command-audit-20261112`  
Status: source audit complete; no raster or control-point data acquired

## Question

What does independently published USGS/NASA release documentation establish about the processing and MOLA control of the public CTX controlled-DTM products, and does it resolve the exact item-specific `geodiff` operand order or `pc_align` transform lineage for the nine E583 Jezero items?

## Sources inspected

1. USGS Astrogeology Analysis Ready Data, *Photogrammetrically Controlled MRO Context Camera (CTX)*: https://stac.astrogeology.usgs.gov/docs/data/mars/ctx/
2. AWS Open Data Registry, *NASA / USGS Mars Reconnaissance Orbiter (MRO) Context Camera (CTX) Targeted DTMs*: https://registry.opendata.aws/nasa-usgs-controlled-mro-ctx-dtms/
3. USGS Astrogeology CTX data documentation: https://astrogeology.usgs.gov/docs/concepts/missions/mro/ctx-data/

Accessed 12 November 2026. This was a documentation-only review. No raster, CSV, QA asset, STAC item JSON, control point, or signed URL was downloaded or retained.

## Source findings

- USGS describes CTX DTMs as local-scale topographic models derived from stereo pairs, with a nominal 20 m post spacing, and states that they are aligned to Mars Orbiter Laser Altimeter (MOLA) elevation data.
- USGS states that associated orthoimages are generated with the Ames Stereo Pipeline `point2dem` tool and are aligned to their associated DTM.
- USGS cautions that different CTX DTMs can retain offsets relative to one another because each is individually controlled to lower-resolution MOLA data and the MOLA alignment is uncertain at CTX-image scale.
- The public AWS release description says the products were made using the NASA Ames Stereo Pipeline, with globally bundle-adjusted CTX imagery using USGS ISIS `jigsaw`; it describes iterative `pc_align` alignment to the ultimate MOLA product in 26 groupings.
- USGS documents CTX image values as top-of-atmosphere I/F reflectance. They are affected by atmospheric dust, illumination geometry and topography; no topographic photometric correction is included. These values are not interchangeable with surface albedo or thermal measurements.

## Reconciliation with E587

E587's exact nine-item Jezero cohort matched 9/9 E583 IDs. Each item exposes the same seven asset keys; all nine expose a text/plain MOLA CSV titled “MOLA Spot Observations Used for initial pc-align”. E587 found zero provenance-named assets, zero item-specific `geodiff`/`pc_align` commands and no item-linked transform record in the STAC metadata.

The external documentation independently supports a **dataset/product-level MOLA-control statement**. It does not disclose the exact operands, command flags, per-item grouping assignment, transform file, or which transformed intermediate generated each released DTM. Generic ASP command semantics cannot fill those missing item-specific facts.

The MOLA CSV remains a control input, not held-out independent validation. The product-level alignment statement must not be upgraded into an independent accuracy result.

## Decision

- Product-level CTX-to-MOLA control: **SUPPORTED** by USGS release documentation.
- Exact E583 item-specific `geodiff` sign / operand order: **NOT YET ESTABLISHED**.
- Exact per-item `pc_align` reference/source order and applied transform lineage: **NOT YET ESTABLISHED**.
- Independent vertical accuracy or route-safety validation: **NOT YET MEASURED / NOT YET PROVEN**.
- E001 known-analogue recovery, cross-body similarity, novel analogue discovery, local validation advantage and challenge-selection superiority: unchanged.

The 20 m CTX DTM post spacing is not the support of MOLA elevation measurements. Do not infer robust 20 m slope, roughness or traversability from nominal grid spacing alone. The documented cross-DTM offsets and lower-resolution MOLA control remain relevant uncertainty terms.

## Next gate

1. Complete the already bounded E587 metadata-only S3 product-prefix inventory. Do not guess object paths or download raster/control assets.
2. If an item-linked provenance sidecar exists, record only its source hash and the minimum parsed command semantics needed to identify the exact transform lineage.
3. If no sidecar exists, stop searching the same STAC/catalogue surface for command text. Pivot to an independent validation source or use the dataset-level MOLA-control statement with explicit item-level lineage uncertainty.
4. Keep Martian Map and MODIS/VIIRS as live challenge rivals. The planetary-analog challenge remains a research candidate, not a locked choice.

## Validation and claim boundary

Documentation-only source audit. No code changed, no tests or benchmark were run, and no new measurement was made. The E587 exact-head workflow remains the relevant code validation: 10/10 deterministic tests passed and the bounded STAC inventory completed; the separate metadata-only S3 prefix inventory was pending at this state snapshot.

This result narrows the provenance question. It does not establish absolute accuracy, independent validation, route safety, or any novel scientific discovery.
