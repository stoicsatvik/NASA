# E587 — item-specific CTX processing provenance audit

Date: 12 November 2026  
Branch: research/e587-ctx-provenance-command-audit-20261112  
Base: E586 / PR #148. Draft research only; main untouched.

## Question

Can item-linked USGS provenance assets identify the actual command operand order used to generate CTX–MOLA QA metrics and the initial MOLA control alignment?

## Exact source inventory result

One bounded anonymous STAC search returned the exact nine E583 item IDs. All nine items expose the same seven asset keys:

- dtm
- image
- intersection_error
- mola_csv
- orthoimage
- qa_metrics
- thumbnail

All nine expose a text/plain MOLA CSV asset titled **MOLA Spot Observations Used for initial pc-align**. This confirms the identity and stated purpose of the MOLA control-point asset for each selected product.

No asset key/title identifies provenance, processing commands or pipeline history:

- Provenance candidate assets: 0/9.
- Provenance downloads: 0.
- Provenance bytes read: 0.
- Relevant item-specific geodiff/pc_align commands: 0.

The bounded metadata receipt is artifact #13951878650 from Actions #43236020927. The raw STAC response and any raw item JSON were not retained. The aggregate artifact contains safe asset metadata summaries only; signed query values are not stored.

The E582 audit of the pinned P18 item separately acquired its MOLA CSV and counted 8,750 rows with latitude/longitude/radius columns. That is an item-specific control input inventory, not independent validation. This E587 run did not download any of the nine MOLA CSVs.

## Tool semantics pinned from primary documentation

- ASP geodiff computes first DEM minus second DEM by default; --reverse flips the sign, and --absolute removes sign information.
- ASP pc_align treats the first input as the fixed reference cloud and the second as the movable source cloud. Its forward transform moves the second input to the first.
- USGS describes the QA values as final CTX–MOLA differences after ground control and identifies the MOLA spot observations as initial pc-align control points.

Sources:
- https://stereopipeline.readthedocs.io/en/latest/tools/geodiff.html
- https://stereopipeline.readthedocs.io/en/latest/tools/pc_align.html
- https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/

## Validation

- Exact-head workflow #43236020927 passed **10/10 deterministic tests** and completed the bounded STAC asset inventory.
- Aggregate artifact #13951878650 (2,582 bytes; seven-day retention).
- Exact E583 item-set match: 9/9.
- No provenance asset was downloaded because no provenance-named asset was exposed.
- Parser tests cover geodiff first-minus-second, --reverse, --absolute, pc_align reference/source order, unknown input roles, path redaction, signed-query redaction, exact-item-set fail-closed behavior and narrow provenance selection.

## Interpretation and next gate

The MOLA CSV asset is explicitly described as the initial pc-align control input. It is not a held-out validation set. The exact pc_align operand order and exact geodiff operand order remain unresolved because the item-linked STAC asset inventory exposes no provenance file.

Generic tool documentation defines command semantics but cannot substitute for the item-specific command. The QA values remain post-control product summaries; do not convert them into independent accuracy estimates or held-out residuals.

Next: search the official dataset release documentation/source package for a separately published processing-command record. Do not guess S3 object paths or treat the MOLA control CSV as independent validation.
