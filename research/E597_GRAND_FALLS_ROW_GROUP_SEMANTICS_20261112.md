# E597 — Grand Falls row-group and sensor-channel semantics

Date: 12 November 2026  
Branch: \`research/e597-grand-falls-row-group-semantics-20261112\`, stacked on E595.  
Workflow: [run 43267508332](https://github.com/stoicsatvik/NASA/actions/runs/43267508332), 4/4 deterministic tests passed; exact source audit passed. Artifact: \`e597-grand-falls-row-group-semantics\`.

## Question

The E592 timestamp audit found roughly six rows per minute. E595 established that \`Record_Number\` is a sequential row identifier, not a sensor identifier, and documented 12 channel columns. Are the six rows distinct sensor records, repeated complete rows, or a mixture?

## Exact bounded sample

- Source item: \`67bf94acd34e8876fcbfc91b\`
- File: \`SensorData_07-07-23_to_11-03-23.csv\`, 67,050,032 bytes.
- Read only the first 5,000,000 bytes; full file was not downloaded.
- Prefix SHA-256: \`f9f150f9eee2f3a8e477614b1ad4cd2d4fd4de5de20d3d74e3350dc4f41e86a6\`.
- Complete-line bytes: 4,999,997; complete-line SHA-256: \`29f68a77ac948949d869a64790b7e7e7b795681fb81f2c6a4962657e980737f7\`.
- Both hashes match the earlier E590/E592 sample. The source metadata hash also matches E595.
- 85,145 complete rows; 14 columns (Date and Time, Record Number, 12 channel fields).
- No raw row, timestamp, record ID, coordinate or channel value is retained in the result.

## Results

### Record number and timestamp grouping

| Measure | Result |
|---|---:|
| Complete rows | 85,145 |
| Unique sequential Record_Number values | 85,145 |
| Record_Number range | 662,976–748,120 |
| Unit increments | 85,144 |
| Gaps, resets or duplicates | 0 |
| Distinct timestamp groups | 14,192 |
| Group size 6 | 14,190 groups |
| Group size 3 | 1 group |
| Group size 2 | 1 group |
| Mean group size | 5.9995 |

All timestamp groups repeat. Adjacent timestamp intervals in file order are 0 seconds for 70,953 row transitions and 60 seconds for 14,191 transitions. The timestamp format is \`%m/%d/%Y %H:%M\`; no timezone is encoded, so these are naive wall-clock values.

### Repeated channel vectors within each timestamp

| Unique 12-channel vectors in group | Number of groups |
|---:|---:|
| 1 | 10,480 |
| 2 | 2,902 |
| 3 | 614 |
| 4 | 176 |
| 5 | 18 |
| 6 | 2 |

- 14,190 of 14,192 timestamp groups contain repeated complete channel vectors.
- Summed over groups, there are 18,932 unique vectors among 85,145 row slots. The remaining 66,213 row slots (77.76%) repeat a vector already present within that timestamp group.
- Only two groups contain six distinct channel vectors.
- Every one of the 85,145 rows has all 12 channel fields present and numeric; there are no missing channel values in this prefix.

**Interpretation:** Record_Number advances per row, but a six-row timestamp group is not six distinct sensors. In most groups, multiple rows repeat the same full 12-channel vector. This falsifies the naive “six sensors per minute” interpretation. The data alone does not identify whether the repeats are export duplication, repeated full records or another acquisition/export behavior.

### Channel ranges in the bounded prefix

| Channel family | Field | Min | Max | Mean |
|---|---|---:|---:|---:|
| Wind speed (mph) | Low, ~20 cm | 0 | 10.12 | 0.000461 |
| Wind speed (mph) | Mid, ~60 cm | 0 | 10.12 | 0.000854 |
| Wind speed (mph) | High, ~1 m | 0 | 9.56 | 0.004081 |
| Particle count | Sensor 1, ~12 cm | 0 | 48 | 0.001352 |
| Particle count | Sensor 2, ~12 cm | 0 | 28 | 0.000529 |
| Particle count | Sensor 3, ~12 cm | 0 | 15 | 0.000364 |
| Kinetic energy (uncalibrated) | Sensors 1–3 | 0 | 6–7 | 0.000188–0.000352 |
| wBSNE voltage (mV/V) | Sensor 1 | 0 | 0.075 | 0.069 |
| wBSNE voltage (mV/V) | Sensor 2 | 0.0993 | 0.0994 | 0.0993 |
| wBSNE voltage (mV/V) | Sensor 3 | 0.0127 | 0.0130 | 0.01288 |

No particle-count value reached the documented 7,999 saturation limit. The very small means are dominated by zeros; a later correlation analysis must report zero fractions and sensitivity to nonzero-only filtering rather than relying on means alone.

## Claim states

- Record_Number sequential row-ID semantics: **SUPPORTED AS REPORTED** by the source dictionary; observed progression **MEASURED**.
- Timestamp-group structure and repeated full vectors: **MEASURED**.
- Six rows = six sensors: **REJECTED** by the observed channel-vector pattern.
- Physical cause of repeated rows: **NOT YET PROVEN**.
- Sensor synchronization / replicate independence: **NOT YET PROVEN**.
- Kinetic-energy calibration: **NOT YET PROVEN**.
- wBSNE voltage-to-sediment-mass conversion: **NOT YET PROVEN**.
- Cross-body similarity / known-site recovery: **NOT YET PROVEN / NOT YET MEASURED**.

## Next decisive experiment

E598 should aggregate to one record per timestamp using unique channel vectors, compare raw-row and deduplicated summaries, then test pre-specified wind-speed/particle-count associations with a circular-shift or block-permutation null. Report effect sizes, zero fractions, saturation and sensitivity to duplicate handling. This remains a single-site Earth sensor experiment; it cannot validate E001 without independent sites, matched planetary descriptors and explicit controls.
