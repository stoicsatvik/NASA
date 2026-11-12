# E599 — CTX–MOLA QA sign and control-lineage documentation audit

Date: 13 November 2026  
Branch: `research/e599-ctx-mola-sign-control-audit-20261113`  
Base: `research/e598-grand-falls-feb2024-row-semantics-20261112`  
Scope: documentation/provenance audit only. No raw raster, new measurement, deployment, or main-branch write.

## Question

Can official public processing documentation resolve the sign of the E582 CTX–MOLA QA residuals and identify the MOLA control lineage for the pinned Jezero CTX product?

## Source evidence

1. **USGS Astrogeology CTX controlled-DTM product documentation**  
   https://stac.astrogeology.usgs.gov/docs/data/mars/ctxdtms/

   - The product page states that CTX DTMs are aligned to individual MOLA shot tracks (page lines 65–76).
   - The available assets include QA metrics, provenance information containing processing commands, and the MOLA points used for ground control in CSV form (lines 78–86).
   - The page defines `qa_metrics.txt` as maximum, minimum, mean, median, and standard deviation of the final **CTX–MOLA differences after ground control** (lines 98–100).
   - The product documentation therefore supports the *named comparison* and the product-family control method. It does not expose the exact command line or control-shot IDs for the pinned item.

2. **Ames Stereo Pipeline `geodiff` documentation**  
   https://stereopipeline.readthedocs.io/en/latest/tools/geodiff.html

   - Default behavior is second input subtracted from first input: `dem1 - dem2` (lines 2–3 and 18–25).
   - `--reverse` flips the sign (lines 27–34 and 68–71).
   - For DEM-versus-CSV comparisons, the documented default is DEM height minus CSV height (lines 35–45).
   - Therefore, if the USGS QA asset was produced with default `geodiff` and the inputs followed the documented CTX–MOLA label order, positive values would mean CTX minus MOLA is positive. The public product page does not prove that exact invocation or exclude `--reverse`.

3. **Ames Stereo Pipeline `pc_align` documentation**  
   https://stereopipeline.readthedocs.io/en/latest/tools/pc_align.html

   - The first input is the fixed/reference cloud and the second is the movable/source cloud (lines 11–22).
   - The transform is applied to the source cloud to bring it into alignment with the reference (lines 209–214).
   - This explains the tool's control semantics, but does not reveal the per-item command or exact MOLA point set used by the USGS processing run.

4. **Existing E582 receipt in this repository**

   The pinned MOLA-control CSV was reported to contain 8,750 rows with latitude, longitude, and radius columns. The radius reference was deliberately not inferred. The CSV is a control input, not held-out validation. The CTX DTM product page describes elevations relative to the areoid, so planet-centre radius must not be silently treated as areoid elevation.

## Findings and claim updates

- **SUPPORTED — product-level QA semantics:** USGS names the reported metric as final CTX–MOLA differences after ground control.
- **SUPPORTED — product-family control method:** the released CTX DTM family is aligned to individual MOLA shot tracks using ASP `pc_align`.
- **CANDIDATE INTERPRETATION, NOT ITEM-VERIFIED:** under default `geodiff` ordering, a CTX-first/MOLA-second comparison would produce CTX minus MOLA. The product documentation's label is consistent with this, but the exact item-specific input order and `--reverse` setting remain unverified.
- **NOT YET VERIFIED — item-specific control lineage:** the exact MOLA shot IDs/grouping, command arguments, tool version, and provenance for the pinned item are not present in the reviewed documentation. The product page says a provenance asset exists; it was not acquired in this run.
- The existing approximately +27 m cohort residual must **not** yet be described as CTX being physically higher or lower than MOLA. Preserve the sign as reported, without a physical-direction interpretation.
- Post-control QA residuals remain neither independent accuracy estimates nor held-out validation.

## NASA claim states

- Repo operating system: **SUPPORTED**
- Cross-body similarity: **NOT YET PROVEN**
- Known-site recovery: **NOT YET MEASURED**
- Novel analogue discovery: **NOT YET PROVEN**
- Local validation advantage: **NOT YET PROVEN**
- Challenge-selection superiority: **NOT YET PROVEN**

E599 does not change the challenge ranking or promote the planetary-analog thesis. All 14 official challenge candidates remain open.

## Next decisive action

Use one bounded, anonymous USGS STAC item request to obtain the pinned item's provenance asset, if the public endpoint is available. Retain only the processing-command text needed to identify the exact `geodiff` input order, `--reverse` flag, `pc_align` reference/source arguments, MOLA shot identifiers, and software version. Do not retain signed URL values, credentials, raw rasters, or unrelated item metadata.

If the provenance asset is unavailable, keep the residual sign ambiguous and seek a genuinely independent control set. Do not substitute the 8,750 control rows for held-out validation.

## Validation

Documentation-only source audit. No code changed; no CI or benchmark claimed. Sources were reviewed directly from the official USGS Astrogeology and Ames Stereo Pipeline documentation on 13 November 2026.
