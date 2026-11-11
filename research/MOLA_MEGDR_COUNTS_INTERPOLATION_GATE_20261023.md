# MOLA MEGDR counts/interpolation evidence gate | 2026-10-23

**Research preparation, not competition-solution development.** The 2026 Space Apps project itself must not be developed before 14 November 2026. The full challenge statements/resources are scheduled for 28 October; do not lock a challenge from the summaries.

## Independent primary-source verification

The maintained NASA PDS4 MGS MOLA derived-topography bundle lists the `meg004` products, including the paired `MEGT90N000CB.IMG` (median topography) and `MEGC90N000CB.IMG` (observation counts). The accompanying legacy PDS3 labels are linked in the maintained bundle and provide the following source-level contracts.

| Contract | MEGT topography | MEGC counts |
|---|---|---|
| Official label | https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg004/megt90n000cb.lbl | https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg004/megc90n000cb.lbl |
| Dimensions | 720 rows × 1440 columns | 720 × 1440 |
| Numeric encoding | 16-bit MSB integer | 16-bit MSB integer |
| Units | metres above/below Mars areoid | number of observations in bin |
| Grid | simple cylindrical, 0.25° × 0.25° | same |
| Longitudes | 0–360° east-positive | same |
| Latitude reference | planetocentric, IAU2000 | same |
| Approx. map scale | 14.818 km/pixel at equator | same |
| Binary size listed | 2,073,600 bytes | 2,073,600 bytes |

The MEGT label states that **where a bin contains no observations, an interpolated topography value is supplied**. It also reports that **only about 55% of equatorial bins contain at least one MOLA shot**. The accompanying MEGC counts grid identifies those bins. This is a documented *measurement-vs-interpolation* distinction, not a guess about fill values.

The nominal map scale does not imply equal-area cells: east–west physical width scales approximately with `cos(latitude)`; do not compare unweighted high-latitude and equatorial pixel histograms as if footprints were identical.

Maintained archive: https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/

## Falsification and decisive next data-access test

**Question:** Are terrain-roughness features from the topography raster stable when interpolated cells are excluded and the remaining measurements are weighted by area and observation support?

Competing explanations for a smooth candidate patch:
1. The actual terrain is smooth.
2. Low shot density caused interpolation to smooth or invent structure.
3. Unequal pixel areas/resampling changed the descriptor.
4. Reference-surface and product geometry were conflated.

**Discriminating predictions:** If (2) dominates, low-count bins will be associated with systematic roughness shifts, and rankings will change when counts=0 cells are excluded. If (3) dominates, rankings change under equal-area/physical-scale normalization. If none matter within uncertainty, the morphology descriptor survives a stronger baseline.

Next permitted research preparation: fetch and checksum the paired official MEGT/MEGC rasters, parse them as 720×1440 big-endian signed 16-bit samples according to labels, verify coordinate orientation and counts distribution, then report how summary descriptors change with the observation-count mask. Avoid inferring missing-value codes beyond what labels actually specify. The full 2-raster pair should be ~4,147,200 bytes. **No raw raster bytes were downloaded or parsed in this run**; the execution environment rejected both binary and label download attempts. The metadata were inspected from official web-served labels.

Do **not** claim real Mars topography ingested from inspecting metadata. E001 known-site recovery remains **NOT YET MEASURED**. Cross-body similarity, novel analogue discovery, and local validation advantage remain **NOT YET PROVEN**.

## Challenge-selection impact

The prior 14-challenge provisional scorecard already placed fire harmonization and Earth-trend alternatives above planetary analogues under its analyst assumptions. That is not empirical win probability, but it falsifies the claim that planetary analogues are unambiguously best. This counts-mask dependence adds another validation cost. Reassess against the full 28 October challenge statements and legitimate data access, without developing a submission solution before the event.

Competition-preparation boundary (official 2026 local-event guidance):
https://www.spaceappschallenge.org/2026/local-events/santiago-dominican-republic/

**Claim states:** repo operating system SUPPORTED; challenge superiority NOT YET PROVEN; real MEGT/MEGC ingestion NOT YET MEASURED; E001 NOT YET MEASURED; cross-body similarity NOT YET PROVEN.
