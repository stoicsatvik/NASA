# E594 — Grand Falls sensor data dictionary audit

Date: 12 November 2026  
Branch: \`research/e594-grand-falls-sensor-dictionary-20261112\`  
Draft PR stacked on E592 / PR #156. Main untouched.

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
