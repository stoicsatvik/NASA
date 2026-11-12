# E587 — item-specific CTX processing provenance audit

Date: 12 November 2026  
Branch: research/e587-ctx-provenance-command-audit-20261112  
Base: E586 / PR #148. Draft research only; main untouched.

## Question

Can the item-linked USGS provenance assets identify the actual command operand order used to generate the CTX–MOLA QA metrics and the initial MOLA control alignment?

E586 established actual item footprints, but did not resolve QA metric spatial support or processing-command lineage. The official USGS collection documentation says that provenance information contains processing commands and that MOLA shot points were used for ground control.

## Frozen design

- Re-query the same Jezero CTX collection and bbox used by E583–E586.
- Require the exact nine E583 item IDs before any asset download.
- Inventory all asset keys and safe metadata summaries.
- Fetch only assets whose key/title explicitly identifies provenance, processing commands, or pipeline history.
- Permit only allowlisted public HTTPS hosts inherited from E582.
- Cap each provenance text asset at 1 MB, total provenance transfer at 5 MB, and candidate assets at nine.
- Never fetch MOLA control CSVs, QA text, rasters, or arbitrary binary/archive assets in this experiment.
- Parse only geodiff and pc_align command lines. Retain command hashes, safe input basenames, option names and operand roles; never retain raw command text, full local paths or signed URL values.

## Tool semantics pinned from primary documentation

- ASP geodiff computes first DEM minus second DEM by default; --reverse flips the sign, and --absolute removes sign information.
- ASP pc_align treats the first input as the fixed reference cloud and the second as the movable source cloud. Its forward transform moves the second input to the first.
- USGS describes the QA values as final CTX–MOLA differences after ground control and says item provenance and MOLA control-point assets are available.

Sources:
- https://stereopipeline.readthedocs.io/en/latest/tools/geodiff.html
- https://stereopipeline.readthedocs.io/en/latest/tools/pc_align.html
- https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/

## Interpretation limits

A geodiff sign is identified only when the exact item-linked command has two recognizable operands and does not use --absolute. A pc_align command identifies reference/source order, but does not alone prove which transformed output was used to create the released DTM. MOLA control inputs are not held-out validation. If the provenance asset is absent, inaccessible, binary, or lacks relevant commands, that negative result is preserved rather than inferred away.

## Validation

Pending exact-head deterministic tests and bounded live acquisition. The workflow writes only an aggregate receipt to a short-retention Actions artifact; raw provenance bytes are not uploaded or committed.
