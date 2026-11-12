# E588 — production CTX STAC item provenance audit

Date: 12 November 2026  
Branch: research/e588-ctx-production-api-provenance-audit-20261112  
Base: E587 / PR #149. Draft research only; main untouched.

## Question

The USGS CTX documentation lists processing-command provenance as an available data asset, while E587 found no provenance property, link or asset in the pinned item returned by the documentation-site STAC endpoint. Does the official production STAC API expose a different item record or a provenance asset?

## Frozen target

- Collection: mro_ctx_controlled_usgs_dtms
- Item: P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W
- Endpoint: GET the exact collection/items/{item_id} path from the official collection metadata.
- One request to the pinned item endpoint; at most two allowlisted provenance text assets, each capped at 2 MB / 20 seconds.
- Redirects remain on an explicit USGS STAC / Astrogeology S3 host allowlist. No credentials or query-string tokens.

## Interpretation constraints

- USGS CTX documentation says the CTX DTMs are aligned to MOLA shot tracks; their QA metrics are CTX–MOLA differences after ground control. It separately lists processing commands as provenance information.
- ASP pc_align documentation defines the first input as fixed reference and second as movable source; the reference should be denser. The transform can be inverted to move the reference cloud to the source frame.
- ASP geodiff documentation defines DEM1−DEM2 by default; for DEM+CSV the DEM supplies the grid regardless of input order, and --reverse flips sign.
- E587's negative result was limited to the item representation exposed by the documentation-site STAC search endpoint. It does not rule out a distinct production API representation or data-browser provenance record.

## Acquisition and privacy boundary

The runner stores only selected STAC property keys, asset/link descriptors, command roles/flags and hashes. It never stores raw item JSON, raw provenance text, full paths, coordinates, signed query values or credentials.

## Result

Pending exact-head workflow. Distinguish production API inaccessible, exact item accessible without provenance, provenance metadata/asset exposed without commands, and item-specific pc_align/geodiff commands recovered. Do not infer order or sign from missing metadata.

## Claim states

- Repo operating system: SUPPORTED.
- CTX/MOLA source and QA access for the pinned item: SUPPORTED.
- Item-specific pc_align lineage: NOT YET ESTABLISHED pending E588.
- Item-specific geodiff sign: NOT YET ESTABLISHED pending E588.
- Independent accuracy, E001 known-site recovery, cross-body similarity, novel analogue discovery, local validation advantage and challenge-selection superiority: NOT YET PROVEN.

## Sources

- USGS CTX DTM documentation: https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/
- Official production collection metadata: https://g6goyz4w56.execute-api.us-west-2.amazonaws.com/prod/collections/mro_ctx_controlled_usgs_dtms
- ASP pc_align: https://stereopipeline.readthedocs.io/en/latest/tools/pc_align.html
- ASP geodiff: https://stereopipeline.readthedocs.io/en/latest/tools/geodiff.html
