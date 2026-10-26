# E291 | Independent Diviner thermal-anomaly access and missingness gate

**Execution:** 26 October 2026. Pre-event read-only source research, not a Space Apps submission or analogue discovery.

## Falsifiable question

Can a genuine lunar thermophysical observable be ingested with its units, encoding, projection and missing-value semantics rather than naively treating a temperature-looking visualization as a comparable Earth/Moon/Mars feature?

**Result:** YES for three bounded rows of official PDS Diviner Level 3 **nighttime normalized regolith-temperature deviation**. NO for the two separate UCLA Level 4 direct links on this runner, which failed TLS certificate-chain verification. The latter failure is **not** evidence that Diviner measurements are absent from NASA archives.

## Source and method

- Official PDS Geosciences Node GDR_L3 directory: https://pds-geosciences.wustl.edu/lro/urn-nasa-pds-lro_diviner_derived1/data_derived_gdr_l3/cylindrical/img/
- Detached label: `dgdr_stn_avg_cyl_032_img.lbl`; SHA-256 `254aade12b81b51560bbcce0501948acfe91ea61d878e06f7c66256ff28c20ad`.
- Raw image: `dgdr_stn_avg_cyl_032_img.img`. No full 88,473,600-byte image was downloaded. Only three **HTTP 206** byte ranges of 23,040 bytes each were read and hashed. No raw raster committed.
- PDS label: 3,840 rows × 11,520 columns, 32 pixels/degree, simple cylindrical projection, planetocentric latitude 60°N–60°S, 16-bit little-endian signed integers, `K`, `ST = DN × 0.02 + 0`, missing DN `-32768`.
- **Physical meaning:** a nighttime *deviation* of rock-free regolith temperature from filtered longitudinal/local-time averages, derived using Diviner channels 6–8 and selection filters. It is **not absolute temperature**, **not directly thermal inertia**, and **not an Earth/Mars-comparable descriptor** without further modeling.

## Real-source measurements

| Approximate latitude | Row | Valid / 11,520 | Missing | Valid fraction | Min / max anomaly |
|---|---:|---:|---:|---:|---:|
| +39.984° | 640 | 10,920 | 600 | 94.792% | −11.44 / +23.96 K |
| −0.016° | 1,920 | 9,547 | 1,973 | 82.873% | −7.10 / +22.16 K |
| −40.016° | 3,200 | 10,812 | 708 | 93.854% | −8.88 / +25.28 K |

Row byte SHA-256, respectively:

- `cd36dd68a19c647e96393a0580eddbbd5fcf68109b16bc4c0b806ed5a2a227b8`
- `a44e547eb91871b97b4ce50e0bffa1189e1e4ce947e59953c622bb866bba87ad`
- `eec2cc72ae43517470a6b49a6cbb9112f04ab0952983f228ac2685dab5aaa91e`

The equatorial sampled row has more missing cells than either ±40° row. This is **three descriptive row observations**, not a global missingness estimate or a test of physical causes.

## Verification and limits

[Exact-head CI 40287923992](https://github.com/stoicsatvik/NASA/actions/runs/40287923992) **SUCCESS**, four deterministic parser/metadata controls and real-source range requests. Machine-readable JSON is preserved in the workflow artifact. Final documentation-head CI should be checked separately.

- The UCLA maximum/minimum bolometric anomaly `.xyz` links failed with `SSL: CERTIFICATE_VERIFY_FAILED` on the CI runner. TLS verification was **not disabled**.
- PDS STN and UCLA Level 4 products are different derived products. Do not substitute them silently.
- No observation-count raster was ingested for STN. Missing DN fraction is not the same as instrument shot-count coverage.
- No co-registration to LOLA, THEMIS, Earth LST or physical point-spread model was attempted.
- No independent analogue positives/negatives or held-out E001 recovery were evaluated.

**Claim states:** official PDS Diviner STN row ingestion and label-constrained decoding **SUPPORTED IN REAL-SOURCE TESTS**; lunar thermal *anomaly* missingness across three rows **SUPPORTED DESCRIPTIVELY**; cross-body thermal comparability **NOT YET PROVEN**; E001 **NOT YET MEASURED**; novel discovery, local validation advantage and challenge-selection superiority **NOT YET PROVEN**.

## Highest-value next experiment

Obtain a legitimate quantitative Mars THEMIS thermal-inertia product and an Earth thermal observable with source-specific calibration, local-time, atmosphere, spatial support, missingness and provenance. Test a physically justified descriptor against a conventional baseline. Do not compare STN anomalies directly with absolute temperatures or THEMIS display-mosaic pixels. Independently labelled known-analogue recovery remains the decisive E001 gate.
