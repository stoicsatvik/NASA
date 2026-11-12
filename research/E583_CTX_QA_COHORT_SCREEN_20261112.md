# E583 — bounded Jezero CTX QA cohort screen

Date: 12 November 2026  
Branch: \`research/e583-ctx-qa-cohort-screen-20261112\`  
Base: E582 QA/MOLA audit / PR #143. Draft research only; \`main\` untouched.

## Question

Is the E580 Jezero CTX item's approximately +27 m mean / +27 m median CTX–MOLA QA difference an isolated item-level result or part of a broader pattern among nearby CTX DTM products?

## Frozen search and acquisition limits

- Collection: \`mro_ctx_controlled_usgs_dtms\`
- Jezero search bbox: [76.69, 17.41, 78.69, 19.41] in longitude/latitude order.
- One anonymous STAC POST, limit 9; sort returned features by item ID before processing.
- Fetch only each selected item's \`qa_metrics\` asset; do not download DTM, orthoimage, MOLA CSV or intersection-error rasters.
- Per QA asset cap: 1 MB; 30-second timeout; same HTTPS host allowlist as E582.
- Record item IDs/datetimes, QA metric values, asset hashes and safe URL summaries only.
- No raw item JSON, raw QA text, signed query values, credentials or individual MOLA coordinates are persisted.

## Deterministic validation

Tests cover fixed search scope/limit, collection filtering, item de-duplication, deterministic sorting, cohort cap, missing QA assets, named-metric extraction and aggregate-only receipts.

Exact-head Actions result is pending.

## Live result

Pending exact-head workflow. No cohort-level conclusion is asserted before the bounded search and QA acquisition complete.

## Interpretation boundary

USGS describes each QA file as final CTX–MOLA differences after ground control. These are control residuals, not independent validation errors. The exact sign convention is not inferred unless item-specific processing provenance establishes the \`geodiff\` input order. A cohort comparison can identify outliers or common residual patterns, but it cannot certify absolute accuracy, horizontal registration, route safety or E001 recovery.

## Next gate

If the cohort shows one or more items with substantially smaller mean/median/standard-deviation residuals, select candidates for later spatial artifact inspection using the intersection-error raster and co-registered orthoimage. Do not compute route slopes until the chosen item's residual structure and unit provenance are defensible. If the cohort is uniformly poor or unavailable, pivot to a different controlled product rather than relaxing thresholds.
