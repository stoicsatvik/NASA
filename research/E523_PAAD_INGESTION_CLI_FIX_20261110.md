# E523 PAAD ingestion CLI correction

**Date:** 2026-11-10  
**Source branch:** `research/e523-paad-acquisition-20261110`  
**Fix branch:** `fix/e523-paad-cli-summary-key-20261110`

## Observed failure

GitHub Actions run [#42869223993](https://github.com/stoicsatvik/NASA/actions/runs/42869223993) executed the deterministic parser/provenance suite successfully (**9/9 tests**). The live acquisition command then exited with `KeyError: 'count_matches_release_description'`.

The receipt schema had already been changed to `primary_table.count_matches_release_metadata`, but the CLI summary still indexed the old key. The exception occurred after `build_receipt()` returned and after the success receipt had been written; the exception handler then replaced that receipt with a failure receipt. The workflow therefore reported failure and did not retain a successful ingestion receipt. Its artifact contains 12 uploaded files, but this run is not counted as a successful end-to-end ingestion.

## Change

- Align the CLI summary field with the receipt schema: `count_matches_release_metadata`.
- Add a deterministic CLI regression test using a mocked receipt, so the command's output schema is tested without a live USGS request.
- Keep the existing parser, source-identity, byte-limit, ZIP-path safety, and provenance behavior unchanged.

## Validation status

The original run's 9 parser/provenance tests passed; the live step failed at summary serialization, not at a reported source HTTP, archive, XML, or table-parsing error. The correction is committed on the fix branch. A new exact-head workflow run is required to verify both the CLI regression and live acquisition after this correction.

## Claim boundary

No successful end-to-end PAAD ingestion is claimed until the corrected workflow completes and preserves an `INGESTED` receipt with the normalized table, source hashes, and metadata. The previous red run is retained as a software-interface failure, not silently relabelled as a successful data acquisition.
