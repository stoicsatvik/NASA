# E529 full field-definition extraction — 2026-11-11

## Why this change

The first E529 run inspected the official 2007 MGD3 metadata and documentation archives, preserving archive hashes and keyword excerpts. Its excerpts were deliberately bounded to 600 characters around each term. That was enough to discover the relevant documents, but not enough to audit the complete Dune_Type code list or every unit-bearing field definition.

The next E530 gate depends on the exact source wording for dune-form codes, polygon area, average elevation and mean dune height. The extractor therefore needs to preserve complete numbered field definitions rather than treating keyword hits as a codebook.

## Implementation

Updated `experiments/e529_mgd3_codebook_audit.py` to:

- Decode UTF-8 first and fall back to Windows-1252 when replacement characters appear. This preserves the source's en-dash separators instead of storing U+FFFD.
- Extract complete `Field N:` blocks from `ReadMe_GIS.txt` and `ReadMe_Softcopy.txt`.
- Preserve field number, display label, parenthetical field alias, normalized full definition, source document byte count and SHA-256.
- Keep unit parentheses such as `(km2)` and `(m)` in the label instead of misclassifying them as field aliases.
- Keep code extraction separate from semantic mapping. The parser does not decide that PAAD and MGD3 categories are equivalent.

Updated `experiments/test_e529_mgd3_codebook_audit.py` with fixtures for the Dune_Type B/Bd definition block, area and height units, field aliases, archive source hashes, and Windows-1252 en-dash decoding.

## Local validation

The three new parser-focused fixture cases were run in an isolated Python unittest harness:

- numbered field parsing, code-block preservation, unit-vs-alias distinction: PASS
- archive field-definition extraction and SHA-256 preservation: PASS
- Windows-1252 en-dash decoding: PASS

**3/3 isolated parser tests passed.** This is not a full repository CI run and does not yet validate extraction from the live USGS archive.

The previous exact-head E527/E528/E529 workflow run [#42922184681](https://github.com/stoicsatvik/NASA/actions/runs/42922184681) passed 22 parser/provenance tests and acquired the official 2007 and 2018 archives. That run predates the new full-field extractor. The current parser changes are committed on `research/e527-mgd3-spatial-ingestion-20261111`; exact-head live archive re-execution remains pending.

## Claim boundary

No PAAD/MGD3 taxonomy crosswalk or shared physical descriptor is admitted by this parser change. E530's current strict S/SS crosswalk, candidate L, rejected ambiguous B, and zero directly shared quantitative feature families remain unchanged until the full source definitions are inspected.

## Next falsifiable gate

Run the updated E529 extractor against the official `Documentation.zip` and `Metadata.zip`; verify that the full Dune_Type field definition and unit-bearing area/elevation/height definitions are present with source hashes. Then compare the exact PAAD definitions and retain only defensible matches. Any ambiguous category stays unmatched.
