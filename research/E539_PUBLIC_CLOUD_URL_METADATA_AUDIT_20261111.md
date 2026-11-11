# E539 — public ScienceBase/USGS metadata URL audit (2026-11-11)

## Question

Does the public ScienceBase item or its official USGS XML metadata explicitly expose an anonymous direct cloud/download URL for the Grand Falls 2023 DEM, beyond the already-tested manager-preview and item-wide ZIP routes?

## Frozen scope

- ScienceBase item: `662bccfad34ea70bd5f11f88`.
- Inspect the root item and its immediate public child items, plus the official USGS XML metadata URL.
- Recursively enumerate URL-like metadata fields only.
- Record host, path, query-key names and source field; never store query values, signed tokens or raw metadata.
- Classify manager-preview routes, official catalog file routes, signed/tokenized URLs and other HTTPS candidates separately.
- Do not follow any file URL, download any binary, or infer anonymous access from a metadata field.

## Validation history and correction

The first two exact-head live attempts, [#42967652009](https://github.com/stoicsatvik/NASA/actions/runs/42967652009) and [#42967666860](https://github.com/stoicsatvik/NASA/actions/runs/42967666860), each passed the six original deterministic helper tests but failed when invoking the CLI with:

```
NameError: name 'argparse' is not defined
```

The tests imported helper functions but never exercised `main()`, so the missing CLI import escaped the first test layer. The current branch adds the missing `argparse` import and a network-free CLI regression that patches `audit()`, invokes `main()`, and verifies the JSON receipt is written.

The earlier failures remain preserved. The exact-head live metadata audit completed on 11 November 2026; the result and its limits are recorded below.

## Claim boundary

A URL found in metadata is only a candidate until anonymous access is independently verified. No raw DEM, CRS, resolution, nodata, vertical datum, physical feature or analogue recovery is claimed.

## Stop rule

If the public metadata contains no explicit direct anonymous candidate, preserve that result and stop trying alternate ScienceBase endpoint patterns for this item. Continue the NASA stream with independent Earth/Mars sources and the all-14 challenge comparison.


## Exact-head live result — 11 November 2026

- Commit: `be8732fa3e576c380c645811c3d0a37fdd0bbd1f`.
- Exact-head workflow [#42969043206](https://github.com/stoicsatvik/NASA/actions/runs/42969043206) succeeded: **7/7 deterministic tests passed**.
- Pinned ScienceBase item JSON and official USGS XML metadata both returned HTTP 200.
- Six file records were present.
- The audit enumerated 45 URL-like metadata-field occurrences: 27 ScienceBase catalog/file endpoint occurrences, 16 other external HTTPS fields, and 2 signed S3 URLs.
- No file URL was followed, no binary bytes were downloaded, and no anonymous file access was established.
- The earlier `anonymous_direct_candidates=43` label was semantically too strong: those entries were unverified URL fields, including landing pages, manager routes, preview imagery and metadata views. The current implementation renames this output to `unverified_direct_url_candidates` and its decision state explicitly says `UNVERIFIED`; a metadata URL is not proof of anonymous access.
- The earlier CLI failures (missing `argparse` and incomplete test receipt) remain in Actions history. The final exact-head run passed without deleting or relabelling them.

## Next bounded gate

E540 selects only the exact `GFDF_Ripples_2023_04_18_DEM.tif` file record's metadata-provided `downloadUri`. It refuses signed/tokenized URLs, sends at most an anonymous `Range: bytes=0-31` request to an allowlisted official ScienceBase/S3 host, reads no more than 33 bytes, and stores only status/header metadata plus a SHA-256 digest of the prefix. A valid 32-byte TIFF prefix would prove only that the first range is accessible; it would **not** establish full DEM acquisition or geospatial metadata.
