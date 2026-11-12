# E595 — Grand Falls sensor data dictionary audit

Date: 12 November 2026  
Branch: \`research/e595-grand-falls-sensor-dictionary-20261112\`  
Draft PR stacked on E592 / PR #156. Main untouched.

The first implementation was opened as PR #158 under E594. A separate FIRMS access experiment independently used E594 / PR #159, so this dictionary audit is reissued as E595 to keep experiment identifiers unique. The E594 prototype failure and correction history are preserved below and in PR #158.

## Question

Does the official 41,313-byte \`Sediment_Transport_Data.xml.xml\` metadata file define the \`Record Number\`, timestamp and sensor-channel fields well enough to interpret E592's repeated timestamp groups without guessing?

## Why this follows E592

E592 parsed 85,145 timestamps from the exact 5 MB CSV prefix. Of 85,144 adjacent row intervals, 70,953 were zero seconds and 14,191 were 60 seconds. Every distinct timestamp was repeated, approximately six rows per timestamp on average. The row sequence is not one row per minute. The source dictionary is the next independent evidence source for row semantics.

## Frozen scope

- One anonymous catalog metadata GET, capped by the inherited 5 MB metadata limit.
- Exact catalog metadata SHA-256 must match E590/E592: \`ce33f7a8a18d0076d0b883f634447c0466fa8354e9c3577ff43b48171225e389\`.
- Exact file name \`Sediment_Transport_Data.xml.xml\` and catalogue size 41,313 bytes must match uniquely before download.
- One HTTPS XML GET, maximum 65,536 bytes; exact 41,313-byte Content-Length and body required.
- Inherit the ScienceBase/S3 host allowlist and redirect validation. Reject userinfo, non-default ports, fragments and path traversal.
- Reject DTD/entity declarations. Parse only FGDC entity/attribute definitions.
- Store only field labels, sanitized definitions, units, broad domain kind and aggregate category counts.
- Do not retain raw XML, URLs, signed query values, contacts, coordinates, file paths, sensor rows or raw sensor values.
- Do not download any CSV, image, DEM, ZIP or raster bytes.

## Falsifiable outputs

- Whether a \`Record Number\` definition exists and what it says.
- Whether \`Date and Time\` has a source-defined meaning or timezone note.
- Whether wind, particle-count, kinetic-energy and wBSNE fields have definitions and units.
- Whether the XML contains no attribute dictionary, in which case the next experiment remains blocked rather than inventing row semantics.

## Validation

Fifteen deterministic tests cover namespace normalization, field classification, units/domain summaries, redaction, DTD/entity rejection, exact catalog hash, exact item/file identity, strict URL policy, bounded response validation and fail-closed negative cases.

The live probe runs only after deterministic tests pass. The sanitized receipt is uploaded as a short-retention workflow artifact; no raw XML or data rows are committed.

## Claim boundary

A field definition can explain the source's intended row semantics, but it cannot prove the actual CSV's record ordering, instrument synchronization, sensor averaging, calibration, timezone, wBSNE mass conversion or sediment flux. E592's measured duplicate pattern remains a separate observation. No temporal covariation or physical interpretation is admitted from metadata alone.

## Next gate

If the dictionary defines \`Record Number\` as a per-instrument record, design a separate bounded aggregate audit of record-number progression and per-timestamp channel patterns using the same 5 MB prefix. If the dictionary does not define the field or does not resolve row grouping, stop at the current descriptive timestamp result. Do not infer six synchronized sensors merely from the mean group size.


## Preserved initial validation failure and correction

The E594 prototype's first workflow [#43261847579](https://github.com/stoicsatvik/NASA/actions/runs/43261847579) executed all 15 deterministic tests: **8 passed, 3 failed and 4 errored**. The live request was correctly skipped because the test job failed.

The failures exposed two issues in the new audit implementation:

1. The E594 prototype initially reused E577's older URL validator. It checked the pinned host/scheme but did not enforce the stricter no-userinfo, absent/443-port, no-fragment and decoded-path-traversal contract required here; its exception type also differed from E594's test contract. The correction adds an E595-owned strict validator and redirect handler, and uses them for both metadata and XML requests.
2. The receipt's XML tag-count diagnostic retained range-bound tag names such as \`rdommin\`/\`rdommax\`, despite not retaining their numeric values. That diagnostic was unnecessary for the question and conflicted with the intended minimal domain summary, so it was removed; only the broad domain kind remains.

This was a real validation gap in the first E594 implementation. No live XML request or sensor-data access occurred on the failed run. The original failure remains in Actions history; the corrected exact head must pass all 15 tests before the single bounded XML request can run.


## First live dictionary acquisition — corrected interpretation

The initial E595 run [#43262464604](https://github.com/stoicsatvik/NASA/actions/runs/43262464604) passed all 15 tests and fetched exactly 41,313 bytes from the unique catalogue file record (HTTP 200, \`application/fgdc+xml\`). XML SHA-256: \`ece31278b299c144dddc48ed7554737a1b51bbcbd33dd6092bf50fba66e1259a\`. The catalog metadata was 4,880 bytes and matched the pinned SHA-256.

The first receipt exposed parser defects that are now corrected before the result is admitted:
- Four FGDC \`detailed\` sections describe four CSV entities. The first parser counted the same 14 field definitions four times (56 occurrences). The corrected parser deduplicates field definitions while preserving entity coverage and occurrence counts.
- \`Date_Time\` was not recognized as a timestamp label.
- A path-redaction expression treated slashes inside \`mm/dd/yyyy\` and \`mV/V\` as absolute paths. The corrected expression only redacts paths beginning at a token boundary; a regression test preserves both format and unit strings while still redacting actual paths, URLs, emails and coordinate pairs.

The source definitions already visible in the sanitized first receipt establish:
- \`Record_Number\`: “Sequential number assigned to row by computer” — a row identifier, not a sensor identifier.
- \`Date_Time\`: format \`mm/dd/yyyy hh:mm\`; the metadata describes time as ISO 8601.
- Three wind-speed channels at approximately 20 cm, 60 cm and 1 m AGL; sampled each second, one value reported per minute, in mph.
- Three Sensit particle-count channels at approximately 12 cm AGL; one-minute totals; each saturates at 7,999, so high-wind movement can be underestimated.
- Three kinetic-energy channels; one-minute totals in uncalibrated instrument units.
- Three wBSNE voltage channels; one-second measurements averaged over one minute and reported in mV/V. The third sensor's height is recorded as “XX cm” and remains unknown.

These definitions explain intended columns but do not prove the CSV's repeated timestamp groups, record-number progression, clock timezone or sensor synchronization. No CSV rows or raw XML were downloaded or retained.

## Next experiment after corrected receipt

E596 should re-fetch only the same bounded 5 MB CSV prefix and retain aggregate checks only: Record_Number monotonicity/gaps/resets; timestamp-group size distribution; per-row non-null counts by wind, particle-count, kinetic-energy and wBSNE channel families; and whether each repeated timestamp group contains distinct sequential row IDs. No row values, coordinates or raw CSV are to be retained. The result may distinguish repeated rows from minute-level channel columns, but still cannot prove physical synchronization or calibration.
