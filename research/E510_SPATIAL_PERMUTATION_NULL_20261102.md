# E510: Spatial-permutation null on real planetary elevation patches (2 Nov 2026)

**Question:** Does the E506 physically scaled median-gradient Earth-site ranking actually require the 5×5 *spatial arrangement* of the elevation samples, or does it largely survive destruction of that arrangement?

**Result:** It often survives spatial shuffling. This is a **negative control**, not a measurement of analogue recovery or a formal significance test. It cautions against interpreting the present nearest-site output as geological/morphological discrimination.

## Frozen inputs and provenance

The script checks SHA-256 of the exact unzipped numerical receipts from the earlier GitHub Actions experiments:

- E501 LOLA: `84b72b67c9ea81bbccf6d0c6a301579a33925cb009ef7801b9a2076ee14bf7ae`
- E502 MOLA topography and ground-return counts: `eaa499260b4d15899e4a28c609b71f300e8669d00201bdbe55c2591b4020072d`
- E505 ETOPO2022 Earth: `db8c94a161c392626459f4032a40a850007e3b42d9f971ad6fdf5cc9009c6476`

The original source raster hashes are recorded in E501/E502/E505. No field measurements, geologically verified analogue labels, or new full-raster acquisition are claimed.

## Experiment

For each of 5 LOLA and 5 MOLA 5×5 elevation patches, compute median absolute east/west and north/south elevation gradients normalized by the approximate body-specific pixel spacing. The three Earth candidates are Lonar_candidate, Deccan_control and Northern_control, **unverified site labels**.

Freeze the original nearest Earth choice, then independently shuffle the 25 elevation values *within each patch*, preserving the elevation histogram but destroying spatial adjacency. Compare (a) shuffled Earth only, (b) shuffled Moon/Mars target only, (c) both shuffled. Repeat 2,000 times at each assumed planetary latitude of 0°, 30°, and 60° with seed 20261102. All selected MOLA cells must have positive ground-return counts.

| Assumed latitude | Earth-only retained | Planetary-only retained | Both shuffled retained |
|---|---:|---:|---:|
| 0° | 57.325% | 86.620% | 82.845% |
| 30° | 64.130% | 84.655% | 84.865% |
| 60° | 70.890% | 90.325% | 98.785% |

At assumed 30°, seven of ten planetary targets retain their original Earth choice in all 2,000 planetary-only spatial permutations; one retains it in 1,999/2,000. One target flips in every permutation, and one retains it in 932/2,000. This is heterogeneous, not universal invariance.

These are **descriptive retention fractions conditional on the selected ten patches and three Earth sites**. They are not accuracy scores, p-values, or independent replicate site counts. The high retention of many rankings under destroyed spatial morphology is evidence that the current scalar median-gradient comparison cannot by itself establish morphology-sensitive analogue identification. The one consistently flipped target demonstrates that spatial arrangement can matter for individual cases.

## Reproduction

```bash
python -m unittest discover -s research -p 'test_e510_spatial_null.py' -v
python research/e510_spatial_null.py \
  --lola e501_lola_numeric_receipt.json \
  --mola e502_mola_paired_receipt.zip \
  --earth e505-earth-dem-final-head.zip \
  --repeats 2000 --seed 20261102
```

Six deterministic local tests passed against exact committed-source blob hashes. Native GitHub Actions validation is not yet established.

## Claim boundary and next experiment

- **SUPPORTED LOCALLY:** the spatial-shuffle retention counts for the pinned 13 real numerical patches; histogram preservation; MOLA shot-count gate.
- **NOT YET MEASURED:** E001 known-analogue recovery.
- **NOT YET PROVEN:** cross-body similarity, novel analogues, local field-validation advantage, challenge-selection superiority.
- **NOT A PROOF:** absence of morphology information, because the three candidates, instrument sampling kernels, and unequal physical footprints confound interpretation.

**Next:** Obtain independently georegistered known reference sites and independently sourced analogue labels; match physical footprints and instrument effective resolution; compare morphology-aware features with histogram-only, randomized, Euclidean and physically weighted baselines; run leave-one-site-out, ablations and hard-negative inspection. If no held-out signal survives, pivot the thesis rather than polishing the map.
