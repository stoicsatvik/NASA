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

Exact-head workflow [#43242642721](https://github.com/stoicsatvik/NASA/actions/runs/43242642721) passed **12/12 tests**. Anonymous S3 ListObjectsV2 returned HTTP 200, 3,067 bytes, 8 objects, not truncated.

The prefix contains one 13,095-byte JSON metadata object, one 398-byte qa_metrics.txt, and the DTM/image/hillshade/intersection-error/orthoimage/MOLA-control assets. The JSON is a **STAC item mirror**, not a processing-provenance sidecar: it has the ordinary STAC Feature keys, the same seven assets and 18 ordinary properties. It contains one textual pc_align mention with zero operands, no structured tool record and no executable command. A regression test now ensures that a tool-name mention without arguments is not counted as a command.

The QA file parsed to the following **post-control CTX–MOLA diagnostics**:

| Metric | Value |
|---|---:|
| Maximum | 117.316 m |
| Minimum | -79.9007 m |
| Mean | 27.3687 m |
| Standard deviation | 10.934 m |
| Median | 26.7783 m |

The QA text mentions geodiff but contains no DEM operand order, CTX–MOLA versus MOLA–CTX label, or --reverse flag. These values are post-ground-control diagnostics, not independent accuracy or validation. The MOLA CSV is explicitly titled “MOLA Spot Observations Used for initial pc-align”; those points are control inputs, not held-out evidence.

**Result: STAC_JSON_MIRROR_AND_POST_CONTROL_QA_ONLY.** The item prefix contains no separate processing-command sidecar. Combined with E587 and E588, both STAC representations and the verified S3 item prefix have now been checked. The USGS documentation still lists processing commands as available provenance, so a separate data-browser/collection provenance route may exist; its location is not yet established. Do not infer command order or sign from the QA metrics.

- Workflow: [#43242642721](https://github.com/stoicsatvik/NASA/actions/runs/43242642721), 12/12 tests.
- Aggregate artifact: [#13956436025](https://github.com/stoicsatvik/NASA/actions/runs/43242642721/artifacts/13956436025), ZIP SHA-256 `a7b3a9331886816f34697e30db7733dfb597165ac006ba6ee3a5631e5e335040`.
- Metadata JSON SHA-256: `05146f1b8636737d653bc6e2cfecfe7a5d43ff602c2e08e5d97b35da0321622d`.
- QA text SHA-256: `c577c0a83ccc58375b4a7790b6edd9eeee0d84de41f602c56ba00c424a8bcd5e`.
- Current E589 branch head: `26bf8183033d0668a7baa18fa3328fff7ee8edad`.
- No raster, raw JSON, raw QA text, full S3 key, local path, credential or signed query value was stored.

E001 known-site recovery remains NOT YET MEASURED. Cross-body similarity, novel analogue discovery, local validation advantage and challenge-selection superiority remain NOT YET PROVEN.

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
