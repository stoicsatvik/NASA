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

Exact-head workflow [#43238810519](https://github.com/stoicsatvik/NASA/actions/runs/43238810519) passed all 7 deterministic tests and the bounded production API GET. The exact item endpoint returned HTTP 200 / 10,067 bytes.

The production item exposed the same seven assets as E587: dtm, image, intersection_error, mola_csv, orthoimage, qa_metrics and thumbnail. Link relations remained self, parent, collection and root. It exposed no provenance property, link, asset or command-bearing metadata. Result: **NO_ITEM_SPECIFIC_PROVENANCE_EXPOSED_IN_PRODUCTION_STAC_ITEM**.

A useful source detail was recovered: the asset title for mola_csv is **“MOLA Spot Observations Used for initial pc-align”**. The production collection description also says these DTMs are absolutely controlled to MOLA using ASP pc_align. This confirms that the MOLA points are control inputs. It further weakens any attempt to use the same points or the post-control QA residuals as independent validation. The exact pc_align reference/source order, inverse-transform application and geodiff --reverse flag remain NOT ESTABLISHED.

This negative result is bounded to both STAC item representations. The USGS documentation separately lists processing commands as a provenance asset, so a data-browser or S3 sidecar route may still expose them. E589 will test the verified public S3 object prefix; it will not assume that absence from STAC means absence from storage.

- Workflow: [#43238810519](https://github.com/stoicsatvik/NASA/actions/runs/43238810519), 7/7 tests passed, production API GET succeeded.
- Aggregate artifact: [#13953532728](https://github.com/stoicsatvik/NASA/actions/runs/43238810519/artifacts/13953532728), ZIP SHA-256 `59484393abe53740c896dd163cb413c147c358a2f2aa1b619dd6e676a0dedfdf`.
- Current E588 branch head: `6936605474e7ff52598a442d35612a4f57fde89e`.
- No credentials, raw item JSON, raw provenance text, local filesystem paths, coordinates or signed query values were retained. Safe URL summaries preserve public S3 object paths.

No E001 known-site recovery or cross-body similarity test was run. All planetary-analogue and challenge-ranking claim states remain unchanged.

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
