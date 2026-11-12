# E592 — Grand Falls sensor timestamp-integrity audit

Date: 12 November 2026  
Branch: research/e592-grand-falls-timestamp-integrity-20261112  
Draft PR stacked on E590 / PR #154. Main untouched.

## Question

Does the first bounded 5 MB prefix of the USGS Grand Falls 2023–2024 sensor CSV contain a chronologically valid, duplicate-free timestamp sequence consistent with the published one-minute logging description?

E590 exposed a concrete defect in its own summary: the reported minimum and maximum Date and Time values were lexicographic string extrema. The receipt itself explicitly warned that they were not validated chronological bounds. E592 replaces that weak summary with parsed timestamp diagnostics.

## Pinned source and scope

- USGS DOI: 10.5066/P13HPPYM.
- ScienceBase catalog item: 67bf94acd34e8876fcbfc91b.
- Exact file: SensorData_07-07-23_to_11-03-23.csv.
- Catalogued file size: 67,050,032 bytes.
- Read at most the first 5,000,000 bytes; retain only complete CSV lines for parsing.
- Verify the exact item ID, exact filename and exact catalogue size before the sample request.
- Require the existing bounded-response contract: HTTP 206 with exact Content-Range, or HTTP 200 with non-HTML content and matching full-file Content-Length.
- HTTPS only; allowlisted ScienceBase/S3 hosts; standard port only; reject userinfo, fragments, path traversal and unsafe redirects.
- No credentials, cookies, raw rows, raw sensor values, raw URLs, signed query values, raw coordinates or full-file download.

The previously acquired E590 prefix hashes are retained as comparison values. A mismatch is reported as source/prefix drift, not silently overwritten.

## Frozen timestamp metrics

Parse the exact Date and Time column using the source-observed format MM/DD/YYYY HH:MM. Treat values as naive wall-clock timestamps because the column does not encode a timezone. Do not convert to UTC or infer a timezone.

Record only aggregate diagnostics:

- Complete row count, valid/invalid timestamp counts and parse fraction.
- First/last parsed timestamp in file order and chronological minimum/maximum.
- Negative, zero and positive adjacent-row intervals.
- Duplicate timestamp values and duplicate rows.
- One-minute interval count and fraction.
- Positive interval minimum, median, p95 and maximum.
- Gaps over 60 seconds and 300 seconds.
- Most common interval values.

Do not infer raw 1 Hz acquisition from row timestamps. The E590 report records the Data.gov description as 1 Hz sampling averaged/logged at one-minute intervals; E592 tests only the timestamps present in this bounded CSV prefix.

## Validation

The deterministic test suite covers:

1. Chronological bounds versus the lexicographic-extrema defect.
2. Duplicate and out-of-order timestamps.
3. One-minute interval recognition.
4. Missing/duplicate timestamp headers.
5. Raw timestamp redaction.
6. HTTPS host, port, userinfo, fragment and traversal rejection.
7. Exact catalogued-file selection and bounded aggregate output.
8. Catalog identity mismatch stopping before data access.
9. Catalogue-size mismatch stopping before data access.
10. Invalid Content-Range stopping before timestamp parsing.

The exact-head live result will be appended after the pull-request workflow completes. A failed request, malformed prefix or timestamp anomaly remains a measured negative result; it will not be converted into a successful cadence claim.

## Claim boundary

Even if all adjacent row timestamps are exactly 60 seconds apart, that supports only a one-minute timestamp cadence in this 5 MB prefix. It does not independently establish the sensor's raw 1 Hz sampling, averaging algorithm, timezone, calibration, instrument drift, wBSNE mass conversion, sediment flux, site representativeness, Mars/Earth feature comparability or E001 recovery.

A timestamp discontinuity may reflect missing rows, acquisition gaps, clock resets, daylight-saving behavior or source formatting. E592 reports the observed pattern without assigning a cause.

## E590 correction

E590's existing receipt remains unchanged and its original negative/uncertain state is preserved. E592 adds a separate exact-source re-read and parsed timestamp receipt so the earlier lexicographic bounds are not mistaken for chronological bounds.

## Next gate

Only if the parsed prefix has a stable timestamp sequence should a later experiment examine temporal covariation among wind and wBSNE voltage channels. That would still require calibration and instrument documentation before any sediment-mass or flux interpretation. No full CSV download and no E001 feature admission are authorized by this experiment.


## E592 exact-head result — 12 November 2026

- Exact PR head at live acquisition: d95e6d79519938203813158ae066faefb69e3841; workflow [#43256647630](https://github.com/stoicsatvik/NASA/actions/runs/43256647630) completed successfully. Deterministic tests: **11/11 passed**. Aggregate artifact [#13962385226](https://github.com/stoicsatvik/NASA/actions/runs/43256647630/artifacts/13962385226), ZIP SHA-256 c2caa4adce531aa0371d158bc9fc3ba28ae521d6d9cae6a775a278cab5dedbe0.
- Exact catalog item/filename/size matched. Metadata GET: HTTP 200. Bounded CSV GET: HTTP 200, text/csv, Content-Length 67,050,032; exactly 5,000,000 bytes read. No full file was downloaded.
- Both the 5 MB prefix SHA-256 and the complete-line SHA-256 exactly match E590's original receipt. No source/prefix drift was observed.
- All **85,145/85,145** timestamps parsed using MM/DD/YYYY HH:MM. The corrected chronological range is **2023-07-07 09:25 through 2023-07-17 05:56**, interpreted as naive wall-clock values because the column does not encode a timezone.
- There are **85,144 adjacent row intervals**: **70,953 are zero seconds** and **14,191 are exactly 60 seconds**. No negative intervals, no invalid timestamps, and no positive gaps over 60 seconds were observed.
- The file therefore has nondecreasing timestamps with extensive duplicates, not one unique row per minute. There are 14,192 distinct timestamp values, all repeated, with approximately six rows per timestamp on average. The 60-second fraction across adjacent rows is 16.667%; among positive intervals, every interval is exactly 60 seconds.
- This is compatible with minute-spaced timestamp groups, but not evidence that each row is a one-minute record or that the raw sensor stream was sampled at 1 Hz. The reason for the repeated rows is NOT YET ESTABLISHED; multiple sensor/instrument records, aggregation structure or another source convention must be checked rather than guessed.
- The E590 lexicographic extrema are superseded for chronological interpretation by the parsed bounds above. E590's original receipt remains unchanged as historical evidence.
- Durable aggregate receipt: research/results/E592_GRAND_FALLS_TIMESTAMP_AUDIT_20261112.json. It contains no raw rows, sensor values, raw timestamp strings, URLs, signed query values or coordinates.

### Interpretation and next experiment

- Timestamp parseability and row-order monotonicity in this bounded prefix: **SUPPORTED**.
- One-minute transitions between distinct timestamp groups: **MEASURED**.
- One-row-per-minute cadence: **NOT SUPPORTED**.
- Raw 1 Hz acquisition, averaging algorithm, timezone, calibration and wBSNE mass conversion: **NOT YET ESTABLISHED**.
- Next highest-information action: audit Record Number progression and per-timestamp group sizes/channel values using the same bounded prefix, then reconcile the row semantics against the source data dictionary. Do not calculate wind/wBSNE temporal covariation or sediment flux until the repeated-row structure and instrument calibration are understood.
