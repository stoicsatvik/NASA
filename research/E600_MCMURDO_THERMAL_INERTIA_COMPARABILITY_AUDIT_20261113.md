# E600 — McMurdo Dry Valleys thermal-inertia comparability audit

Date: 13 November 2026  
Branch: `research/e600-mcmurdo-thermal-inertia-comparability-audit-20261113`  
Base: E599 / PR #165. Draft research only; `main` untouched.

## Question

Does the published McMurdo Dry Valleys (MDV) thermal-inertia work provide an admissible, physically comparable positive-site benchmark for Mars analogue recovery, or does it expose a feature/scale mismatch that should falsify a naive thermal-inertia matcher?

## Primary source

J. S. Levy (2026), “Apparent thermal inertia of soils in the McMurdo Dry Valleys, Antarctica: Orbital thermal remote sensing reveals modern and ancient hydrological processes in a cold desert landscape,” *Arctic, Antarctic, and Alpine Research* 58(1), article 2617687. DOI: https://doi.org/10.1080/15230430.2026.2617687. Open article/PDF: https://www.tandfonline.com/doi/pdf/10.1080/15230430.2026.2617687.

The article identifies MDV as a long-used terrestrial analogue for cold, dry Martian permafrost/soil processes. The paper covers 77–78° S, 160–164° E and Taylor, Wright, Beacon and Garwood valleys.

## Source-backed measurements and acquisition semantics

### Field thermal inertia

- Seventeen soil samples were collected in 2009 and 2015 from the upper 10 cm at sites across four MDV valleys. The samples were approximately 500 mL.
- Samples were oven-dried at 105 °C for 24 hours, homogenized and compressed to previously measured field dry bulk density.
- Thermal conductivity, diffusivity and derived heat capacity were measured with a KD2 Pro dual-needle SH-1 probe. The paper reports ±10% instrument accuracy for each of those properties.
- Triplicate measurements were made at each of six water-saturation levels: 0–1%, 2%, 5%, 10%, 15% and 20% by mass.
- Reported physical thermal inertia spans 285–694 TIU for dry soils and reaches 2,041 TIU for water-saturated soils. TIU is J m⁻² K⁻¹ s⁻½.
- Across the 17 samples, thermal inertia is strongly associated with bulk density (R = 0.87, p < 0.001), negatively associated with fine fraction (R = −0.49, p = 0.046), and has a weaker positive association with coarse fraction (R = 0.45, p = 0.0696). Sand fraction is not associated in the reported analysis (R = 0.02, p = 0.9268).

These are repeated moisture-state measurements of samples within one established analogue region, not 17 independent analogue sites or 17 independent Earth/Mars replications.

### Satellite apparent thermal inertia

- Landsat 8 OLI visible observations are 30 m/pixel; Landsat 8 TIRS thermal observations are 100 m/pixel.
- The paper uses 6 August, 20 October and 30 December 2024 acquisitions. Albedo is terrain-corrected using a 1 m/pixel airborne lidar DEM; shadows and selected snow/ice artefacts are masked.
- The article reports spring ATI from 0 to 1.400 (mean 0.060, SD 0.043) and summer ATI from 0 to 0.045 (mean 0.019, SD 0.003). The thermal support is constrained by the 100 m TIRS observations, even where other layers are finer.
- ATI is an apparent proxy derived from albedo and seasonal temperature change. It is not the same measured variable or unit as physical thermal inertia in TIU.
- The paper reports poor point-scale correspondence between calculated field thermal inertia and satellite ATI. It attributes mismatches to mixed thermal pixels, lake ice/snow contamination, unresolved moisture and clast heterogeneity. The author states that a one-to-one calibration cannot be derived without contemporaneous field water content and sampling representative of the satellite thermal pixel.

## Falsification result

A naive feature pipeline that equates MDV satellite ATI with Mars physical thermal inertia, or treats dry laboratory TIU as a direct label for a 100 m mixed pixel, is **REJECTED** by this source's own measurement-scale analysis.

Physical TIU remains a potentially comparable feature family because the article reports TIU and cites Mars thermal-inertia ranges in the same physical units. However, the source does not yet provide an E001-ready sample table with verified coordinates and a matching Mars footprint. Its Supporting Table S2 is identified by the paper but has not been retrieved in this run. No non-analogue control sites are supplied.

The paper cites typical Mars thermal-inertia ranges of less than 120 TIU for dusty/low-density surfaces, 150–350 TIU for sandy/rocky surfaces and 800 TIU or greater for bedrock. These values are retained as literature context only; they are not independent validation data and were not used to score a site.

## E001 admissibility decision

| Gate | Result |
|---|---|
| Recognized Earth positive-site identity | SUPPORTED: MDV is a published Mars analogue |
| Physical Earth feature with stated units | SUPPORTED AS REPORTED: field TIU |
| Georeferenced sample-to-raster join | NOT YET ESTABLISHED: supporting coordinates/table not retrieved |
| Satellite ATI directly interchangeable with physical TIU | REJECTED |
| Matched Mars-side physical TIU footprint | NOT YET INGESTED in this audit |
| Defensible non-analogue controls | NOT YET ESTABLISHED |
| E001 leave-one-site-out recovery | NOT RUN; known-site recovery remains NOT YET MEASURED |

No analogue ranking, cross-body similarity score, novel discovery, local field measurement or E001 result is claimed.

## Next discriminating test

1. Retrieve and source-hash Supporting Table S2; establish whether sample identifiers and coordinates are present and whether the 17 samples can be georegistered without inference.
2. If georeferencing is defensible, preserve sample-level moisture states and uncertainty; do not treat moisture repeats as independent sites.
3. Acquire a Mars THEMIS physical thermal-inertia product and document units, map support, retrieval method and missing values. Do not substitute apparent ATI for TIU.
4. Define independent non-analogue Earth control windows before scoring. Match physical footprint and support, then compare a frozen random baseline, Euclidean TIU baseline and physically weighted baseline.
5. Run leave-one-site-out and moisture-state sensitivity. If the known MDV site is not recovered robustly, reject or narrow thermal-inertia-only matching rather than tune on the held-out site.

This is a candidate data source, not a blocker or a discovery. No fieldwork, destructive sampling, restricted access, credentialed download, paid API or UI work was performed.

## Claim states

- Repo operating system: SUPPORTED.
- MDV as a published Mars analogue: SUPPORTED as literature context.
- Physical TIU feature feasibility at MDV: SUPPORTED AS REPORTED.
- Satellite ATI as a direct substitute for physical TIU: REJECTED.
- Cross-body similarity: NOT YET PROVEN.
- Known-site recovery: NOT YET MEASURED.
- Novel analogue discovery: NOT YET PROVEN.
- Local validation advantage: NOT YET PROVEN.
- Planetary-analog challenge superiority: NOT YET PROVEN.

## Validation

- Source identity, acquisition dates, instrument resolutions, field protocol, units, uncertainty semantics, reported correlations and ATI/TIU scale mismatch were checked against the open 2026 article/PDF.
- No raw sample table, raster or new field measurement was downloaded.
- No code, CI, benchmark or E001 ranking was run.
- No specimen/site rows were added to the production dataset.
