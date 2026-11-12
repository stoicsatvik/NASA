# E582 — pinned CTX QA metrics and MOLA-control asset audit

Date: 12 November 2026  
Branch: \`research/e582-ctx-qa-mola-control-audit-20261112\`  
Base: E581 / PR #141. Draft research only; \`main\` untouched.

## Question

Do the pinned E580/E581 CTX item’s QA metrics and MOLA-control CSV expose usable residual statistics and a bounded control-point schema?

## Frozen source and limits

- Collection: \`mro_ctx_controlled_usgs_dtms\`
- Item: \`P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W\`
- One anonymous STAC POST for the exact collection and item.
- QA metrics asset cap: 1 MB.
- MOLA-control CSV cap: 5 MB.
- 30-second timeout; HTTPS host allowlist inherited from the E581 USGS/S3 source boundary.
- No credentials, raw item JSON, raw QA text, CSV rows, individual coordinates or signed query values are persisted.
- Receipts contain asset hashes, safe URL summaries, content metadata, metric key/value summaries, CSV schema, row counts and numeric aggregates only.

## Deterministic validation

The test module covers exact item binding, URL allowlisting and signed-query redaction, bounded QA key/value extraction, CSV schema and aggregate parsing, row-cap handling, and fail-closed empty/non-UTF-8 inputs.

Exact-head Actions result is pending.

## Live result

Pending exact-head workflow. No asset contents or scientific conclusions are asserted before the bounded probe completes.

## Interpretation boundary

A QA metrics file can summarize CTX–MOLA differences after ground control; it is not an independent horizontal-control network. The MOLA-control CSV identifies the points used for control and may support a schema/coverage audit, but the control points are not held-out validation points. No independent accuracy, registration, route safety, E001 recovery, cross-body similarity, or challenge superiority follows from this audit.

## Next gate

After the exact-head receipt is available, inspect only the bounded aggregate output. If the QA asset is absent, inaccessible, malformed or exceeds its cap, preserve that as an acquisition result and do not substitute guessed URLs. If the CSV is acquired, keep control-point summaries separate from any future held-out validation design.
