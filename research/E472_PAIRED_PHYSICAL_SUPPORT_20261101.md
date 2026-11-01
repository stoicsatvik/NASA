# E472 | Paired real LOLA/MOLA measured-bin support at approximately 2 km

Date: 2026-11-01. Pre-event **data-quality research only**. No Space Apps competition solution or analogue identification.

## Falsifiable question

E463/E469 reported 9x9 observed-bin fractions at 128 pixels/degree, but equal angular windows differ by nearly 2x in physical width. Do approximately equal *physical* windows contain measured (rather than only interpolated) bins? Do the aggregate 9x9 fractions conceal material local support changes?

## Sources and frozen method

- E212 official-derived 4ppd Moon/Mars equatorial north-south pixel spacing: 7.580837606 km and 14.789483749 km. Divide each by 32 for 128ppd; these are nominal gridded spacings, **not** independent instrument resolution.
- E463 official PDS MOLA MEGC128 count and MEGT128 elevation, 9x9 bounded reads at 45°E and latitudes 0.5°S, 20°S, 40°S.
- E469 official PDS LOLA LDEC128 count and LDEM128 elevation at the same requested angular centers. Both use the source-declared byte order.
- Preserve the **full 9x9 binary count>0 mask** for each body, not just aggregate fractions. Compare lunar 9x9 (8 grid intervals, 1.895209 km N–S) with the **central Martian 5x5** (4 intervals, 1.848685 km N–S). Relative north-south footprint difference is 2.4853%. East-west widths shrink with latitude; registration and instrument support remain imperfect.
- The original sample centers were fixed before reading raster values. They are **not** labelled analogues or representative global samples.

## Measured real-data result

| Requested latitude | LOLA Moon 9x9 | MOLA Mars central 5x5 | Mars original 9x9 |
| --- | ---: | ---: | ---: |
| 0.5°S | **18/81 = 22.22%** | **11/25 = 44.00%** | 33/81 = 40.74% |
| 20°S | **34/81 = 41.98%** | **3/25 = 12.00%** | 15/81 = 18.52% |
| 40°S | **80/81 = 98.77%** | **15/25 = 60.00%** | 38/81 = 46.91% |

**Negative finding:** the earlier 9x9 Mars fraction at 20°S (18.52%) is not the physically matched central-window fraction (12.00%). An aggregate count cannot substitute for a spatial observation mask. Conversely, the 40°S Mars central window has 60% observed bins versus 46.91% in the original larger window. Direction varies by site.

**Positive, narrow finding:** nominal 128ppd grid spacings permit a roughly matched 2 km north-south comparison, unlike E446's 4ppd and E452's 16ppd gate. Actual observed-bin support is now measured at all three sampled centers for both bodies.

## Reproducibility

- Exact-head read-only [E472 Actions #41285355814](https://github.com/stoicsatvik/NASA/actions/runs/41285355814) **SUCCESS**. Companion E463 #41285355565 and E469 #41285355625 **SUCCESS**.
- E472 artifact **13075560235** contains the complete bounded-source JSON receipts and the derived paired receipt. It contains count masks, bounded source hashes and PDS label fingerprints; raw full rasters were not downloaded.
- All eight new E472 offline tests and six E463 plus eight E469 offline controls passed in the E472 workflow.
- Independently downloaded artifact ZIP was opened, verified for archive corruption, and independently checked with Python: 9x9 counts, central 5x5 counts, latitudes and spherical footprint arithmetic all matched the paired receipt.
- Source-derived concise committed result: `research/results/e472_paired_support_20261101.json`.

## Interpretation and next gate

**SUPPORTED BY REAL-SOURCE EXACT-HEAD CI:** site-specific observed-bin fractions in the three approximately matched windows, plus the failure of an aggregate-only spatial-support inference.

**NOT YET MEASURED:** independent effective resolution, shot/track-spacing, 2km Earth/Moon/Mars matched descriptors and E001 known-analogue recovery.

**NOT YET PROVEN:** cross-body similarity, novel analogue discovery, local field-validation advantage, or superiority of the planetary-analogue challenge.

Next high-value experiment: independently verify LOLA/MOLA latitude registration and elevation scaling; select **independently published mechanism-specific analogue-positive and spatially separated negative sites**, sample corresponding count-masked terrain at equal physical support, and run frozen random/Euclidean/physical baselines with leave-one-site-out and ablations. The three locations in E472 must **not** be reused as analogue ground truth. If a reliable independent cohort cannot be assembled before the event, re-evaluate the challenge choice rather than inventing scores.

No main merge, deployment, fieldwork, outreach, paid API, competition submission or destructive action.
