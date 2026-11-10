# E529 exact-head CI syntax failure and correction — 2026-11-11

## Failure observed

GitHub Actions run [#42923772054](https://github.com/stoicsatvik/NASA/actions/runs/42923772054) failed before the live archive acquisition step. The deterministic test import reached `experiments/e529_mgd3_codebook_audit.py` and Python reported:

```text
File "experiments/e529_mgd3_codebook_audit.py", line 82
name=info.filename.replace("\\","/")
SyntaxError: unterminated string literal
```

The committed source contained a single unescaped backslash in a Python string literal. This was an implementation syntax defect, not a USGS source or archive failure. Because tests stopped at import, the workflow skipped live E527/E528/E529 acquisition and uploaded no artifact. Earlier failed runs are retained in Actions history.

## Correction

Commit [ed7db2b](https://github.com/stoicsatvik/NASA/commit/ed7db2b7163fc5474a3a598d6dc89b3127bacaad) corrects the path normalization to use a valid escaped backslash before checking archive paths for absolute paths and traversal.

## Validation on the corrected GitHub file contents

The exact current E529 module and test file were fetched from the corrected branch head and executed in an isolated Python 3 harness:

- E529 unit tests: **7/7 passed**.
- Module import/compilation succeeded.
- ZIP fixtures cover source URL allowlisting, archive CRC/path handling, HTML/text extraction, full numbered field definitions, code-list preservation, unit-vs-alias distinction, source hashes, and Windows-1252 en-dash decoding.

This is exact-file unit validation, not a full repository Actions run and not live archive extraction. The GitHub combined commit-status reader returned no statuses for the corrected commit; no exact-head Actions receipt is claimed.

## Preserved live-source evidence and next gate

The earlier exact-head run [#42922184681](https://github.com/stoicsatvik/NASA/actions/runs/42922184681) succeeded before the full-field E529 extractor was added. It acquired the official 2007 MGD3 archives, validated 547 polygons and 547 unique Dune IDs, joined the same-release Softcopy table 547/547, and linked 535 unique Equatorial IDs from the 2018 workbook.

Next: rerun the complete E527/E528/E529 workflow on the corrected head and verify the full field-definition output against the live official Documentation.zip and Metadata.zip. Until that run succeeds, the new full-field extractor is not considered live-source validated.

No PAAD/MGD3 taxonomy equivalence, shared physical descriptor, E001 recovery, or cross-body similarity claim is added by this fix.
