# E587 — item-specific CTX processing-provenance audit

Date: 12 November 2026  
Branch: `research/e587-ctx-processing-provenance-audit-20261112`  
Base: E586 / PR #148. Draft research only; `main` untouched.

## Question

Does the pinned Jezero CTX STAC item expose item-specific processing provenance sufficient to recover the exact `pc_align` reference/source order and `geodiff` sign convention for its CTX–MOLA QA residuals?

## Predeclared source constraints

- USGS CTX product documentation states that the 20 m/post CTX DTMs are aligned to individual MOLA shot tracks; QA statistics are CTX–MOLA differences after ground control. It describes MOLA along-track spacing of about 300 m and often kilometre-scale gaps near the equator.
- Ames Stereo Pipeline `pc_align` documentation defines the first cloud as the fixed reference and the second as the movable source; the reference should be denser. The transform is applied to the source. If CTX is the denser reference and MOLA the sparse source, an inverse transform would be required to move CTX into the MOLA frame.
- ASP `geodiff` documentation defines DEM1−DEM2 by default. For a DEM and CSV, the DEM supplies the grid regardless of input order; `--reverse` flips the sign. Therefore a QA label reading “CTX–MOLA” is consistent with the default DEM-minus-CSV operation, but does not prove that the pinned item omitted `--reverse`.

These are tool/product documentation constraints, not item-specific command evidence.

## Acquisition and privacy boundary

The runner performs one pinned anonymous STAC search, inspects selected metadata keys and link/asset descriptors, and fetches at most two allowlisted text provenance assets, each capped at 2 MB and 20 seconds. It stores no raw item JSON, raw provenance text, full command lines, local paths, coordinates, signed query values or credentials. Command summaries contain only tool names, input roles/extensions, flags, line hashes and bounded counts.

## Result

Pending exact-head workflow. The result must distinguish:
- an item-specific command sequence recovered from public metadata;
- a provenance file exposed but without the relevant commands;
- no item-specific provenance exposed in the pinned STAC item;
- acquisition/parser failure.

No command order or sign convention is inferred from a missing asset.

## Interpretation boundary

Even if the command order is recovered, the QA residuals remain post-control diagnostics, not independent validation. MOLA control points used in alignment cannot also be presented as held-out ground truth. A second source or independent reference is still required for accuracy claims.

## Claim states

- Repo operating system: SUPPORTED.
- CTX/MOLA source and QA access for the pinned item: SUPPORTED.
- Item-specific `pc_align` lineage: NOT YET ESTABLISHED pending this audit.
- Item-specific `geodiff` sign: NOT YET ESTABLISHED pending this audit.
- Independent accuracy, route safety, E001 known-site recovery, cross-body similarity, novel analogue discovery, local validation advantage and challenge-selection superiority: NOT YET PROVEN.

## Sources

- USGS, Mars ASP Generated CTX DTMs and Orthoimages: https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/
- Ames Stereo Pipeline, `pc_align`: https://stereopipeline.readthedocs.io/en/latest/tools/pc_align.html
- Ames Stereo Pipeline, `geodiff`: https://stereopipeline.readthedocs.io/en/latest/tools/geodiff.html
- Pinned item: `P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W`.
