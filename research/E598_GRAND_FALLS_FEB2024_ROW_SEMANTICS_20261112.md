# E598 — Grand Falls February 2024 row-semantics comparison

Date: 12 November 2026  
Branch: research/e598-grand-falls-feb2024-row-semantics-20261112  
Parent: E597 / PR #163. Main untouched.

## Question

Does the distinct 14–16 February 2024 CSV entity from the same official USGS Grand Falls release reproduce the six-row timestamp groups and within-group channel-vector duplication observed in the 5 MB prefix of the July–November 2023 file?

## Frozen source and safety boundary

- Parent DOI: 10.5066/P13HPPYM.
- Catalog item: 67bf94acd34e8876fcbfc91b.
- Exact file name: SensorData_02-14-24_to_02-16-24.csv.
- Exact catalog size: 1,091,813 bytes.
- Catalog metadata SHA-256 must match E590/E595 before file selection.
- Exactly one metadata-listed record must match both file name and byte size.
- Require HTTPS through the inherited strict ScienceBase/S3 host and redirect policy.
- Require HTTP 200, text/csv, exact Content-Length and exact payload byte count.
- Hard read ceiling: 5,000,000 bytes. The pinned 1,091,813-byte file is read completely because it is below that ceiling.
- Store only the file SHA-256, schema/row counts and aggregate statistics. Do not retain raw rows, timestamps, record IDs, channel values, download URLs or source file bytes.
- No credentials, contact, access-control bypass, field access or physical measurement.

## Discriminating outputs

- Row count and incomplete-row count.
- Record_Number uniqueness, progression, gaps and resets.
- Timestamp-group size distribution and adjacent intervals.
- Within-group 12-channel vector uniqueness and duplicate counts.
- Comparison with the E597 2023 bounded-prefix result.

A recurrence would show that the observed pattern is not unique to the 2023 prefix. It would not identify the export/acquisition mechanism or establish synchronization, independent replicates, calibration or sediment-mass conversion.

## Validation

- Deterministic tests run before the live source request.
- Exact source identity and response checks fail closed.
- The live run produces an aggregate-only, seven-day Actions artifact.
- Any parser/source failure remains a failed or negative acquisition result; it is not silently converted into a scientific conclusion.

## Claim boundary

This is a same-site, cross-release data-integrity experiment. It is not independent-site replication, planetary-analogue validation, cross-body feature comparability or E001 known-site recovery. Cross-body similarity and known-site recovery remain NOT YET PROVEN / NOT YET MEASURED respectively.

## Next gate

If the row-group pattern recurs, retain the mechanism as unresolved and stop treating repeated rows as independent sensors. If it does not recur, identify which row semantics differ before pooling releases. In either case, do not deduplicate or calculate wind/particle correlations until source semantics and calibration are resolved.
