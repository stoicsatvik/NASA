# E513 | Source-registered MOLA latitude and footprint falsification

Date: 2026-11-03. Research-only continuation of E511. **NOT E001 known-site recovery.**

## Question

E511 compared five 5x5 Martian elevation patches to three unverified Earth candidate patches at assumed planetary latitudes 0, 30, 60 degrees. Does replacing the arbitrary common 30-degree latitude with the source-derived latitude of each MOLA raster pixel change the nearest-Earth candidate, and how unequal are the physical footprints?

The maintained NASA PDS MOLA MEGDR documentation identifies `MEGT90N000CB` as 4 pixels/degree, north-west upper-left at 90 N and 0 E, spanning 90 N to 90 S and 0 E to 360 E. A pixel centre at (row, col) therefore maps to latitude 90-(row+0.5)/4, longitude (col+0.5)/4. Source: https://pds-geosciences.wustl.edu/missions/mgs/megdr.html (checked 2026-11-03).

## Executed source-pinned result

Read the **actual** E502 MOLA paired topography/count receipt and E505 ETOPO2022 Earth receipt, verifying exact raw JSON SHA-256 before numerical work. Recomputed E511's median absolute adjacent gradient, using local spherical east-west spacing at each MOLA patch's derived latitude, while retaining the Earth candidates' actual E505 coordinates. No new field data or site labels.

| MOLA row | Derived latitude | Gradient change vs assumed 30° | Nearest Earth candidate changed? |
|---:|---:|---:|---|
| 90 | +67.375° | +20.606% | No |
| 180 | +44.875° | +5.369% | No |
| 360 | -0.125° | -11.177% | No |
| 540 | -45.125° | +9.975% | No |
| 630 | -67.625° | +59.324% | No |

**Result:** 0/5 nearest-candidate rankings changed, despite up to **59.324%** gradient change. This is a **negative ranking-sensitivity result**, not evidence of analogue recovery or correct morphology matching. The frozen 5x5 MOLA patch spans about **59.16 km** north-south versus about **1.853 km** for the ETOPO2022 Earth patch, a **31.921x footprint mismatch**. The existing same-pixel-count comparisons are not equal-area/equal-scale experiments.

Seven deterministic Python tests passed locally, covering first/last pixel centres, source row, index bounds, elevation-datum offset invariance, nonfinite rejection, and fail-closed zero-shot MOLA handling. The committed source and tests are byte-identical to the locally executed versions. Native GitHub CI is a separate validation step.

## Reproduction

```bash
python -m unittest discover -s research -p 'test_e513_mola_latitude_audit.py' -v
python research/e513_mola_latitude_audit.py --mola e502_mola_paired_receipt.zip --earth e505-earth-dem-final-head.zip --output e513_result.json
```

Source receipts are available from the successful E502/E505 GitHub Actions artifacts; do not commit large raw rasters. This experiment checks receipt SHA-256, not independent raw source re-acquisition.

## Claims and blockers

- MOLA source-coordinate calculation and this five-patch sensitivity audit: **SUPPORTED LOCALLY**.
- Rank stability under this single correction: **SUPPORTED for these frozen samples**, not a scientific validation metric.
- E001 known-site recovery: **NOT YET MEASURED**.
- Cross-body similarity, novel analogue discovery, local validation advantage, challenge superiority: **NOT YET PROVEN**.
- LOLA's independent orientation/projection validation was **not** performed here.
- No independent analogue labels, equal-footprint terrain, hard negatives or leave-one-site-out evaluation.
- Positive MOLA ground-return counts do not prove per-cell elevation accuracy.

**Next decisive experiment:** independently georegistered Moon/Mars reference locations and labelled Earth analogue/non-analogue sites, resample equal physical footprints, then run E001 random/histogram-only/physical baselines with leave-one-site-out and failure inspection. Do not spend on UI polish before that gate.
