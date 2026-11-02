# E511: Exact within-patch crop sensitivity on source-pinned real terrain receipts

Date: 2026-11-03. **NOT E001; no analogue-recovery claim.**

## Hypothesis attacked

E510's nearest-Earth-candidate rankings might depend on arbitrary 5x5 sample window placement. E511 enumerates all nine overlapping 3x3 windows within each of the 5x5 real-numerical patches from E501 LOLA, E502 MOLA and E505 ETOPO2022. It keeps the same approximate dimensionless median-gradient metric, 3 unverified Earth candidate patches, 10 planetary patches and assumed planetary latitudes 0/30/60 degrees.

For each target, exact enumeration includes 9 target-only crop choices, 9^3 = 729 Earth-only combinations and 9^4 = 6,561 simultaneous target/Earth crop combinations. Each latitude therefore has 65,610 joint comparisons; across three assumed latitudes, **196,830 joint comparisons**. All are deterministic enumerations, not independent measurements.

## Observed (local, pinned receipt hashes, 2026-11-03)

| Assumed planetary latitude | Target-only retained | Earth-only retained | Both retained |
|---|---:|---:|---:|
| 0° | 81.1111% | 91.6049% | 85.2263% |
| 30° | 83.3333% | 94.0741% | 86.0082% |
| 60° | 88.8889% | 98.0247% | 90.2469% |

At assumed 30°, the most crop-sensitive planetary target is LOLA tile index 2: its original nearest Earth choice survives only 43.5% of simultaneous crop combinations. Some other targets survive 100% of combinations. The effect is heterogeneous, so neither universal crop robustness nor universal crop instability is supported.

Seven focused Python controls passed locally, including elevation-datum shift invariance, deterministic tie handling, nonfinite rejection, exact window enumeration and fail-closed zero-shot MOLA handling. Native GitHub Actions validation is separate.

## Provenance

Input receipts are prior successful GitHub Actions artifacts; the script fails closed on exact JSON SHA-256:
- LOLA E501: 84b72b67c9ea81bbccf6d0c6a301579a33925cb009ef7801b9a2076ee14bf7ae
- MOLA E502: eaa499260b4d15899e4a28c609b71f300e8669d00201bdbe55c2591b4020072d
- Earth E505: db8c94a161c392626459f4032a40a850007e3b42d9f971ad6fdf5cc9009c6476

Run: python research/e511_window_sensitivity.py --lola e501_lola.json --mola e502_mola.zip --earth e505_earth.zip --output e511_result.json

## Interpretation and next gate

**SUPPORTED:** exact descriptive crop-window sensitivity of the frozen small-sample ranking. **NOT YET MEASURED:** E001 known-site recovery. **NOT YET PROVEN:** cross-body similarity, novel analogue discovery, local validation advantage or challenge superiority.

The overlapping crops are dependent and change physical footprint. Their retention fractions are **not p-values, confidence intervals, held-out accuracy or evidence of morphological/geological analogue validity**. The three Earth labels are research leads, not verified analogue ground truth; the planetary latitude assumptions are not georegistration. MOLA positive return counts do not guarantee topographic accuracy.

Next: acquire georegistered equal-physical-footprint patches, independently source known positive/negative analog labels, and compare random, histogram-only, standardized Euclidean and physically weighted descriptors with leave-one-site-out and ablations. No UI polishing, field claims or competition submission.
