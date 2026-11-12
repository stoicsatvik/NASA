# E597 — Grand Falls row-group and sensor-channel semantics

Date: 12 November 2026  
Branch: research/e597-grand-falls-row-group-semantics-20261112, stacked on E595 / PR #160.  
Workflow: [run 43267508332](https://github.com/stoicsatvik/NASA/actions/runs/43267508332), 4/4 deterministic tests passed and the exact bounded source audit passed. Artifact [13966637360](https://github.com/stoicsatvik/NASA/actions/runs/43267508332/artifacts/13966637360), ZIP SHA-256 371e176b75d285da91f4a4a50b637adeabe26ce79d12f983504d898d2fe2b97d.

## Question

E592 found roughly six rows per minute. E595 established that Record_Number is a sequential row identifier, not a sensor identifier, and documented 12 channel columns. Are the six rows distinct sensor records, repeated complete rows, or a mixture?

## Exact bounded sample

- Source item: 67bf94acd34e8876fcbfc91b.
- File: SensorData_07-07-23_to_11-03-23.csv, 67,050,032 bytes.
- Catalog metadata SHA-256: ce33f7a8a18d0076d0b883f634447c0466fa8354e9c3577ff43b48171225e389, matching E595.
- Read only the first 5,000,000 bytes; the full file was not downloaded.
- Prefix SHA-256: f9f150f9eee2f3a8e477614b1ad4cd2d4fd4de5de20d3d74e3350dc4f41e86a6.
- Complete-line bytes: 4,999,997; complete-line SHA-256: 29f68a77ac948949d869a64790b7e7e7b795681fb81f2c6a4962657e980737f7.
- Both prefix hashes match E590/E592 exactly.
- 85,145 complete rows; 14 columns; zero incomplete rows.
- No row-level records, individual timestamps, individual record IDs, coordinates or channel values are retained. The receipt contains only aggregate counts, distributions, identifier extrema and channel summary statistics.

## Results

### Record number and timestamp grouping

| Measure | Result |
|---|---:|
| Complete rows | 85,145 |
| Unique sequential Record_Number values | 85,145 |
| Aggregate Record_Number range | 662,976–748,120 |
| Unit increments | 85,144 |
| Gaps, resets or duplicates | 0 |
| Distinct timestamp groups | 14,192 |
| Group size 6 | 14,190 groups |
| Group size 3 | 1 group |
| Group size 2 | 1 group |
| Mean group size | 5.999507 |

All timestamp groups repeat. Adjacent timestamp intervals in file order are 0 seconds for 70,953 row transitions and 60 seconds for 14,191 transitions. No invalid timestamps or decreases were observed. The format is %m/%d/%Y %H:%M; no timezone is encoded, so values are treated as naive wall-clock times.

### Repeated channel vectors within each timestamp

| Unique 12-channel vectors in group | Number of groups |
|---:|---:|
| 1 | 10,480 |
| 2 | 2,902 |
| 3 | 614 |
| 4 | 176 |
| 5 | 18 |
| 6 | 2 |

- 14,190 of 14,192 groups contain repeated complete channel vectors.
- There are 18,932 unique vectors across 85,145 row slots. The remaining 66,213 row slots (77.76%) repeat a vector already present within that timestamp group.
- 73.84% of groups have one unique vector across all rows; 26.14% have partial vector duplication; only two groups have six distinct vectors.
- Every row has all 12 channel fields present and numeric. No channel-family field is missing in this prefix.

**Interpretation:** Record_Number advances once per row, but a six-row timestamp group is not six distinct sensor channels. Every row carries the same 12-column schema, and most groups repeat one or more complete channel vectors. This rejects the naive “six sensors per minute” interpretation. It does not establish whether the repeats are export duplication, repeated full records, repeated minute aggregates or another acquisition/export convention.

### Channel bounds and source semantics

| Channel family | Observed range in this prefix |
|---|---:|
| Wind speed, low / mid / high | 0–10.12 / 0–10.12 / 0–9.56 mph |
| Particle count, sensors 1 / 2 / 3 | 0–48 / 0–28 / 0–15 |
| Kinetic energy, sensors 1 / 2 / 3 | 0–6 / 0–7 / 0–7, uncalibrated units |
| wBSNE voltage, sensors 1 / 2 / 3 | 0.068–0.079 / 0.098–0.107 / 0.012–0.014 mV/V |

No particle-count value reached the documented 7,999 saturation limit. The source dictionary describes wind-speed channels at approximately 20, 60 and 100 cm AGL; particle-count totals at approximately 12 cm AGL; kinetic-energy totals in uncalibrated instrument units; and wBSNE voltage averaged over one minute. The wBSNE #3 height remains recorded as XX cm. None of these observations supplies a voltage-to-mass calibration.

The very small channel means are dominated by zeros. No wind/particle correlation or flux calculation is included in E597.

## Validation and preserved failures

- Run [#43267066778](https://github.com/stoicsatvik/NASA/actions/runs/43267066778): deterministic tests failed because the test module imported a missing summarize_rows helper. The live probe was skipped.
- Run [#43267342440](https://github.com/stoicsatvik/NASA/actions/runs/43267342440): one test still referenced a top-level key after the helper returned the nested aggregate schema. The live probe was skipped.
- Run [#43267508332](https://github.com/stoicsatvik/NASA/actions/runs/43267508332): corrected exact-head run passed 4/4 deterministic tests, fetched the exact pinned prefix, validated the aggregate receipt and uploaded artifact 13966637360.

The failures remain in Actions history; they were not overwritten or relabelled as successful.

## Claim states

- Source dictionary row-ID semantics: **SUPPORTED AS REPORTED**.
- Observed row-ID progression and timestamp-group structure: **MEASURED**.
- Six rows = six sensors: **NOT SUPPORTED** by the observed full-vector pattern.
- Physical cause of repeated rows: **NOT YET PROVEN**.
- Sensor synchronization / replicate independence: **NOT YET PROVEN**.
- Kinetic-energy calibration: **NOT YET PROVEN**.
- wBSNE voltage-to-sediment-mass conversion: **NOT YET PROVEN**.
- Cross-body similarity: **NOT YET PROVEN**.
- E001 known-site recovery: **NOT YET MEASURED**.

## Next discriminating experiment: E598

Compare the distinct SensorData_02-14-24_to_02-16-24.csv entity (catalogued size 1,091,813 bytes) under the same exact item/file/size and bounded-acquisition rules. Measure timestamp-group sizes, Record_Number progression and channel-vector duplication using aggregate-only output. This determines whether the six-row/repeated-vector pattern is specific to the 2023 file or recurs in another release.

Do not deduplicate to one row per timestamp or calculate wind/particle correlations until the repeated-row mechanism is better understood. Deduplication could discard legitimate repeated measurements. E598 remains a single-site data-integrity comparison, not independent-site validation or E001 recovery.
