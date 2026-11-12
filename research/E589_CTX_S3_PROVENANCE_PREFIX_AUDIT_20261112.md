# E589 — verified public S3 item-prefix provenance audit

Date: 12 November 2026  
Branch: research/e589-ctx-s3-provenance-prefix-audit-20261112  
Base: E588 / PR #151. Draft research only; main untouched.

## Question

E588 found that the official production STAC item exposes seven assets but no provenance asset. Its safe URL summaries revealed the exact public S3 object prefix. Does that prefix contain a provenance/processing sidecar omitted from the STAC item?

## Frozen target and method

- Bucket: astrogeo-ard.s3-us-west-2.amazonaws.com
- Prefix derived from the verified STAC DTM/MOLA/QA asset paths for the pinned item only.
- One anonymous ListObjectsV2 request, max-keys=100, 1 MB response cap, 20 s timeout.
- If a provenance-like text object is found, fetch at most one object, capped at 2 MB / 20 s.
- No raster download. No credentials. Redirects restricted to the explicit USGS/Astrogeology S3 host allowlist.
- Store relative filenames, sizes, ETags and timestamps only; no full S3 keys, raw XML, raw provenance text, local paths or signed query values.

## Result

Pending exact-head workflow. Distinguish listing denied, truncated listing, no sidecar, sidecar present without commands, and command sequence recovered. A denied listing is not evidence that no object exists.

## Claim states

- Repo operating system: SUPPORTED.
- CTX/MOLA source and QA access: SUPPORTED.
- Item-specific pc_align lineage and geodiff sign: NOT YET ESTABLISHED pending E589.
- Independent accuracy, E001 known-site recovery, cross-body similarity, novel analogue discovery, local validation advantage and challenge-selection superiority: NOT YET PROVEN.

## Sources

- USGS CTX DTM documentation: https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/
- Official production collection metadata: https://g6goyz4w56.execute-api.us-west-2.amazonaws.com/prod/collections/mro_ctx_controlled_usgs_dtms
- ASP pc_align: https://stereopipeline.readthedocs.io/en/latest/tools/pc_align.html
- ASP geodiff: https://stereopipeline.readthedocs.io/en/latest/tools/geodiff.html
