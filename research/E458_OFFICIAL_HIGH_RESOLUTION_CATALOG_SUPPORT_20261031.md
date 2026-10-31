# E458 | Official high-resolution LOLA/MOLA catalog support (31 October 2026)

## Decision question

Does E452's **0/6** four-pixel result reflect a fundamental lack of planetary terrain products, or merely the low-resolution 4ppd Moon and 16ppd Mars products actually ingested so far?

**Answer: the latter, for nominal grid spacing only.** Official catalogs list LOLA LDEM 64/128 pixels per degree and MOLA MEGDR 64/128 pixels per degree. Under the declared *diagnostic* four-pixel-per-axis threshold, the cataloged 64ppd products pass for 4-km windows on both bodies, while the 128ppd products pass for both 2-km and 4-km windows. **No high-resolution raster bytes were ingested here; no per-site shot counts, measured coverage, effective resolution, morphology or analogue recovery was measured.**

## Primary source provenance (catalog, not raster measurement)

- NASA/USGS Lunar Orbital Data Explorer LOLA GDRDEM product table: LDEM_4, LDEM_16, LDEM_64, LDEM_128, with 64ppd at ~0.4738 km per equatorial latitude pixel and 128ppd at ~0.2369 km. https://ode.rsl.wustl.edu/MArs/pagehelp/Content/Missions_Instruments/Lunar%20Reconnaissance%20Orbiter%20%28LRO%29/LOLA/GDR/GDRDEM.htm
- PDS Geosciences Node MGS MOLA MEGDR catalog, updated 25 August 2026: 4, 16, 32, 64, 128ppd global products; MEGDR counts are available to distinguish measured from interpolated bins; PDS4 maintained archive. https://pds-geosciences.wustl.edu/missions/mgs/megdr.html
- USGS Mars MGS MOLA DEM 463m product metadata: 128ppd, equatorial pixel size 463.0835744 m, equatorial projection radius 3,396,190 m; gaps are interpolated. https://astrogeology.usgs.gov/search/map/mars_mgs_mola_dem_463m
- E452 prior *measured-receipt* resolution gate: `research/E452_MOLA16_RESOLUTION_RESCUE_20261031.md`. E214 Earth windows are research leads, not independently labelled analogue truth.

## Frozen calculation

Nominal equatorial north-south grid spacing = `2*pi*body_radius_km/(360*ppd)`, with Moon 1737.4 km and Mars MOLA projection equatorial radius 3396.19 km. This differs from E452's Mars mean-radius convention (~3389.5 km) by ~0.2%; the binary pass/fail verdicts below are unchanged. Widths 2/4 km are the six E214 site-window widths, not six independent site measurements here.

| Product | Pixel spacing km | 2-km spans | 4-km spans |
|---|---:|---:|---:|
| Moon 4ppd | 7.580838 | 0.264 | 0.528 |
| Moon 16ppd | 1.895209 | 1.055 | 2.111 |
| Moon 64ppd | 0.473802 | **4.221** | **8.442** |
| Moon 128ppd | 0.236901 | **8.442** | **16.885** |
| Mars 4ppd | 14.818674 | 0.135 | 0.270 |
| Mars 16ppd | 3.704669 | 0.540 | 1.080 |
| Mars 64ppd | 0.926167 | 2.159 | **4.319** |
| Mars 128ppd | 0.463084 | **4.319** | **8.638** |

At a nominal four-pixel threshold, **same-ppd paired pass** is 128ppd for 2 km and 64/128ppd for 4 km. At a stricter eight-pixel threshold, only 128ppd passes for 4 km; no listed equal-ppd pair passes for 2 km. The four/eight-pixel thresholds are sensitivity diagnostics, **not independent-sample guarantees or scientific validation criteria**.

## Falsification and evidence boundaries

- **REJECTED:** the inference that no *cataloged* high-resolution planetary product can nominally support E214's 2/4-km windows.
- **SUPPORTED FROM OFFICIAL CATALOG METADATA AND DETERMINISTIC CALCULATION:** nominal spacing feasibility at 64/128ppd.
- **NOT YET MEASURED:** actual 64/128ppd bytes, site-specific MOLA count masks, LOLA effective independent sample density, uncertainty in interpolation, valid cross-body matched patches, E001 known-site recovery.
- **NOT YET PROVEN:** physically comparable relief descriptors, cross-body similarity, novel analogue discovery, Maharashtra field advantage, or planetary-analogue challenge superiority.

High pixel count is not high independent-information count. Mars MOLA bins may be interpolated where no shots exist; LOLA GDR products are gridded representations with uneven observation density. A catalog metadata pass is **not** an E001 evidence gate pass.

## Validation

`python -m unittest -v research/test_e458_high_resolution_catalog_gate.py` when `research/` is on `PYTHONPATH`, or `cd research && python -m unittest -v test_e458_high_resolution_catalog_gate`: **7/7 focused tests passed in isolated local Python**, and `py_compile` passed. Script emits a 16-row machine-readable JSON receipt on demand. The exact remote committed files were not run under GitHub Actions; full repository CI and raster ingestion were not performed.

## Highest-EV next action

Obtain small **real** high-resolution LOLA 64ppd and MOLA 128ppd site-specific tiles with original product labels and MOLA count masks, checksum every file, and measure *per-site observed coverage and effective independent support*. Compare at common physical footprint, preserve interpolation masks, use matched slopes/relief after unit and datum normalization. Only then run E001 against independently labelled analogue positives and hard negatives with random, Euclidean, physically weighted, leave-one-site-out, permutation and ablation controls. Reassess all fourteen 2026 challenges; do not lock a winner or polish UI based on metadata alone.
