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

The earlier failures remain preserved. A new exact-head live metadata audit is pending; no URL-discovery result is claimed until it completes.

## Claim boundary

A URL found in metadata is only a candidate until anonymous access is independently verified. No raw DEM, CRS, resolution, nodata, vertical datum, physical feature or analogue recovery is claimed.

## Stop rule

If the public metadata contains no explicit direct anonymous candidate, preserve that result and stop trying alternate ScienceBase endpoint patterns for this item. Continue the NASA stream with independent Earth/Mars sources and the all-14 challenge comparison.
