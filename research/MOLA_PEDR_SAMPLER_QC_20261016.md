# MOLA PEDR sampler quality-control spike (2026-10-16)

**Evidence status:** real NASA PDS source excerpt inspected; **not** a full product download, **not** the maintained MOLA MEGDR, and **not** an E001 known-analogue recovery result.

Official source: [AP00035V.TAB](https://pds.nasa.gov/data/mgs-m-moc-4-sampler-v1.0/mgs_0001/mola/pedr_asc/ap00035v.tab) and [detached PDS3 label](https://pds.nasa.gov/data/mgs-m-moc-4-sampler-v1.0/mgs_0001/mola/pedr_asc/ap00035v.lbl).

## What was inspected

The official label identifies orbit 35 (1997 orbit-insertion sampler), 12,673 fixed-length ASCII records, 29 columns, 236 bytes per record. Longitude is east-positive areocentric degrees, latitude is areocentric degrees, and areopotential topography is in metres relative to a reference equipotential surface.

The **first 59 source rows (indices 0–58)** were manually transcribed for their row number, longitude, latitude and topography, and checked for sequential row indices and finite numeric values. This is a small, non-random orbit-track excerpt, **not** a full-file ingestion or independent spatial sample.

- Unfiltered topography in this excerpt: minimum **−4,868.83 m**, maximum **425,477.81 m**, median **35,915.28 m**, mean **124,139.46 m**.
- Exploratory plausibility range **[−25,000, +25,000] m** flags **31/59** rows and retains **28/59**. The retained mean is **−3,329.05 m**, median **−4,865.625 m**.
- Rows 33–58 show a comparatively smooth local segment near −4.86 km, while early rows include extreme positive values exceeding 400 km.

**Interpretation:** unfiltered early-orbit PEDR topography is not automatically trustworthy as terrain elevation. The ±25 km filter is **an analyst heuristic, not an official PDS quality flag**, and retained rows are not automatically validated measurements. Instrument state, geometry, saturation, uncertainty and per-shot quality must be checked before physically interpreting the values. This excerpt must not be generalized to maintained MEGDR quality.

## Consequence for E001

Do **not** calculate cross-body terrain descriptors from unqualified PEDR rows or mix this orbit sampler with MEGDR without distinguishing product type, projection, epoch, coordinate reference and acquisition conditions.

Next decisive gate: obtain and checksum a maintained PDS4 **MEGDR topography + counts** pair, parse its official labels and missing-value rules, and quantify the change in terrain descriptors under observation-count and physical-area weighting. Then seek LOLA and Earth comparison products. Cross-body similarity **NOT YET PROVEN**; E001 known-site recovery **NOT YET MEASURED**.

No field observations or analogue discoveries are claimed.
