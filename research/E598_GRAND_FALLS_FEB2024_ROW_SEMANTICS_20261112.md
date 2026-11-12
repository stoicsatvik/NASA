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


## Preserved first exact-head failure and response-contract correction

- Workflow #43270910285 ran all 6/6 deterministic tests successfully.
- The bounded source request reached the exact-size response, but the first implementation rejected its media type because it was not text/csv. The run did not produce a receipt and is preserved as a failed acquisition attempt, not a data null.
- The revised parser records the exact response media type, byte count and payload hash. A nonstandard media type is admitted only if the complete pinned-size payload decodes as CSV and its unique header contains the full 14-field E595 dictionary schema. HTML, malformed text, duplicate headers and missing fields remain rejected.
- This correction does not weaken the exact catalogue identity, size, HTTPS host/redirect, or 5 MB read-ceiling checks.


## Preserved second exact-head failure and fail-closed size receipt

- Workflow #43271278785 again passed all 6 deterministic tests.
- The metadata-supplied endpoint returned a payload whose Content-Length did not equal the pinned 1,091,813-byte catalogue size. The implementation rejected it before parsing.
- The corrected code now records the actual response media type, Content-Length, bytes read, payload hash, host and header-admissibility flag as a sanitized negative receipt. It does not reinterpret an HTML or truncated response as sensor data.
- This is an endpoint/payload-integrity result, not evidence about the physical row-group pattern.


## Final exact-head result — 12 November 2026

- Workflow [#43271607662](https://github.com/stoicsatvik/NASA/actions/runs/43271607662) passed all 6 deterministic tests, completed the bounded source request and validated the aggregate receipt. Artifact #13966839833 SHA-256: 3eb25046d061ac6974175a7127f2430b3f2eadfa22fbea238211f96ddd9faf50.
- The pinned catalogue metadata was HTTP 200 and matched SHA-256 ce33f7a8a18d0076d0b883f634447c0466fa8354e9c3577ff43b48171225e389.
- The exact metadata-listed record is pinned as SensorData_02-14-24_to_02-16-24.csv, 1,091,813 bytes. Its supplied URL returned HTTP 200 from sciencebase.usgs.gov but the response was text/html, only 4,255 bytes, with no Content-Length header. Payload SHA-256: 01d324b90d086dd7389e13cfabbc185a7b7afe7917620e05254248773d01e1a2. The CSV header was inadmissible.
- The 1,091,813-byte CSV was **not acquired or parsed**. No row count, timestamp grouping, channel-vector or record-number result is claimed. This is a source-route/payload-integrity negative, not a scientific null.
- Independent public-catalogue cross-checks: Data.gov lists only the DOI landing page as the Digital Data access URL and the original metadata XML as a separate resource; the USGS release page describes the dataset but does not expose a direct CSV URL in its page content. Sources: [USGS release page](https://www.usgs.gov/data/imagery-sediment-collection-photogrammetry-and-meteorological-data-july-2023-november-2024), [Data.gov record](https://catalog.data.gov/dataset/sediment-transport-data-from-july-2023-to-november-2024-grand-falls-dune-field-arizona), [DOI 10.5066/P13HPPYM](https://doi.org/10.5066/P13HPPYM).
- Stop retrying this same metadata-supplied HTML route. Resume only if a distinct direct file URL is exposed by official metadata or the publisher. The Navajo Nation fieldwork permit boundary remains in force; no field visit or contact was attempted.

## Final claim boundary

- Exact catalogue record identity: SUPPORTED AS PINNED.
- Metadata-supplied payload as the requested CSV: NOT ESTABLISHED.
- February 2024 row semantics: NOT YET MEASURED.
- Cross-release row-pattern recurrence: NOT YET MEASURED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery / E001: NOT YET MEASURED.
- Novel analogue discovery and local validation advantage: NOT YET PROVEN.


## Deterministic receipt-contract regression correction

- Added a pure `rejected_size_mismatch_receipt` helper so response-size failures are represented as sanitized negative receipts without attempting CSV parsing.
- Added regression checks for an HTML payload and for a schema-valid CSV header whose byte count still fails the pinned-size gate. Schema validity must never override the exact catalogue-size contract.
- Exact-head runs #43273561878 and #43273625070 initially failed 9/10 tests because the new CSV fixture encoded a literal backslash-n instead of a newline. The live source-acquisition step was skipped on both runs; these are test-fixture failures, not source or parser results.
- Corrected the fixture to contain a real CSV header line terminator. The next exact-head push run is deterministic-only: the prior source-route negative receipt is already committed, and no repeat live request is authorized by this commit.


## Exact-head deterministic validation after fixture correction

- Commit `284b2b7cd439e5adeb7c154cacc27e05b6f8e971` corrects the test fixture to use a real newline in the schema-valid CSV header.
- Workflow [#43274117119](https://github.com/stoicsatvik/NASA/actions/runs/43274117119) passed **10/10 deterministic tests**. The acquisition step was skipped because the exact source-route negative receipt is already committed; this documentation/test correction did not repeat the live request.
- The earlier 9/10 failures (#43273561878 and #43273625070) remain preserved as fixture failures. The source-route result remains the separate negative receipt from workflow #43271607662.
