# E001 data-access audit: MOLA archive migration (2026-11-03)

**Status:** verified source/catalog metadata only; **no binary raster ingested, no numerical analogue recovery measured**. This is an access/provenance finding, not evidence of cross-body similarity.

## Falsifiable acquisition finding

The PDS Geosciences Node's MOLA MEGDR landing page states that on **2026-08-25** the MOLA MEGDR collection migrated to the maintained **PDS4 MGS MOLA Topography Derived bundle**. The PDS3 archive remains temporarily accessible. Thus a pipeline pinned only to old PDS3 locations is not a reliable long-term source. Verify PDS4 labels and actual byte payloads before asserting successful ingestion.

- Primary maintained catalog: https://pds-geosciences.wustl.edu/missions/mgs/megdr.html
- MOLA instrument/data coordinate caveat (IAU 2000 for final version, older IAU 1991): https://pds-geosciences.wustl.edu/missions/mgs/mola.html
- LOLA PDS release catalog (Release 67, 2026-09-15): https://pds-geosciences.wustl.edu/missions/lro/lola.htm
- SLDEM format/quality background: https://ode.rsl.wustl.edu/moon/pagehelp/content/Missions_Instruments/LRO/LOLA/SLDEM.htm

## Product semantics that affect the experiment

MOLA MEGDR is binned orbital laser-altimeter topography. Product types include **planetary radius**, **areoid**, **topography = radius − areoid**, and **observation counts per cell**. Available global grids: 4, 16, 32, 64 and 128 pixels/degree; the areoid map is omitted from some higher-resolution products. Treat counts as coverage/quality context, not elevation. Each PDS4 directory provides `.img`, `.xml`, `.lbl` and `.hdr` counterparts. Pixel resolution in degrees is not a fixed metre-scale resolution across latitude. Mars topography above an areoid is **not directly comparable** to lunar radial elevation without a documented reference-frame/datum transformation.

LOLA/SLDEM elevation products also have their own reference radius, coverage, spatial resolution, instrument/processing lineage and missing-value conventions. Do not concatenate raw elevations, temperatures, slopes or radiances across planets.

## Next decisive machine-checkable gate

1. Fetch one small **real MOLA PDS4 topography IMG + XML + counts** and one real LOLA/SLDEM raster with its label; record exact URL, SHA-256, byte length, dimensions, pixel type, scale/offset, missing-value sentinel, coordinate frame, projection and observation density.
2. Parse without silent resampling; cross-check header-derived dimensions against file bytes and independently calculated min/max/nonmissing counts.
3. Compute *dimensionless/local* relief descriptors on matched physical windows, with latitude-dependent pixel spacing and missing-data masks. Keep thermal/spectral features separate until comparable physical definitions exist.
4. Freeze a pre-registered known-site holdout and compare random, Euclidean and physically weighted rankings, followed by leave-one-site-out, ablations and false-positive inspection.

**Stop condition:** if raster labels/bytes cannot be reconciled, report DATA ACCESS UNVERIFIED; if baselines do not beat random under held-out evaluation, report NEGATIVE RESULT, not a discovered analogue.

**Claim states:** repo operating system SUPPORTED; cross-body similarity NOT YET PROVEN; E001 known-site recovery NOT YET MEASURED; novel analogue discovery NOT YET PROVEN; local validation advantage NOT YET PROVEN.
