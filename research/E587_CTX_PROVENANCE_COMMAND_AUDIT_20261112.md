# E587 — item-specific CTX processing provenance audit

Date: 12 November 2026  
Branch: research/e587-ctx-provenance-command-audit-20261112  
Base: E586 / PR #148. Draft research only; main untouched.

## Question

Can item-linked USGS provenance assets or separately stored files identify the actual command operand order used to generate CTX–MOLA QA metrics and the initial MOLA control alignment?

## STAC result

One bounded anonymous STAC search returned the exact nine E583 item IDs. All nine expose the same seven asset keys: dtm, image, intersection_error, mola_csv, orthoimage, qa_metrics, thumbnail.

All nine expose a text/plain MOLA CSV asset titled **MOLA Spot Observations Used for initial pc-align**. No asset key/title identifies provenance, processing commands or pipeline history:

- Provenance candidate assets: 0/9.
- Provenance downloads: 0.
- Provenance bytes read: 0.
- Item-specific geodiff/pc_align commands: 0.

The E587 first exact-head run #43236020927 passed 10/10 tests and uploaded aggregate artifact #13951878650.

## S3-prefix follow-on

The second phase derives each exact product-folder prefix from that item's advertised DTM asset URL; it does not guess object paths. It issues a metadata-only S3 ListObjectsV2 request with max-keys=100, 500 KB per prefix, 5 MB total, and stops after access denial. It stores only object basenames, sizes, ETags and last-modified timestamps; full object keys and query values are not stored. It downloads no sidecar contents, MOLA CSV, QA text or raster.

The result of the exact-head S3 prefix listing is pending.

## Tool semantics pinned from primary documentation

- ASP geodiff computes first DEM minus second DEM by default; --reverse flips the sign, and --absolute removes sign information.
- ASP pc_align treats the first input as the fixed reference cloud and the second as the movable source cloud. Its forward transform moves the second input to the first.
- USGS describes the QA values as final CTX–MOLA differences after ground control and identifies the MOLA spot observations as initial pc-align control points.

Sources:
- https://stereopipeline.readthedocs.io/en/latest/tools/geodiff.html
- https://stereopipeline.readthedocs.io/en/latest/tools/pc_align.html
- https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/

## Interpretation limits

The MOLA CSV is a control input, not held-out validation. Generic ASP documentation defines command semantics but cannot establish item-specific command order. Even a discovered sidecar filename is not proof of its contents; no sidecar will be downloaded unless its identity and text type are explicitly established and the bounded follow-on is reviewed.

## Validation

- First exact-head run #43236020927: 10/10 deterministic tests passed; exact E583 item set 9/9; zero provenance assets exposed.
- Second exact-head run: includes URL-derived S3-prefix inventory and fail-closed access-denial/truncation tests; result pending.
