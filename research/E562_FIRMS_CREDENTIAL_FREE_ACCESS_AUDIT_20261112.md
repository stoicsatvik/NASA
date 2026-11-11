# E562 — NASA FIRMS credential-free data-access audit (12 November 2026)

## Question

Does the 2026 MODIS/VIIRS hot-spots challenge have a usable no-credential path for current or historical data, or is the publicly accessible material limited to a static VIIRS example?

## Frozen protocol

The exact-head experiment used only three pinned NASA FIRMS endpoints:

1. Official tutorial sample: `https://firms.modaps.eosdis.nasa.gov/content/notebooks/sample_viirs_snpp_071223.csv`, maximum 8,000,000 bytes.
2. One exact South Asia daily VIIRS file exposed in the official NRT directory listing: `J1_VIIRS_C2_South_Asia_VJ114IMGTDL_NRT_2026312.txt`, maximum 2,048 bytes.
3. One 1° × 1° / one-day API request with the literal placeholder `NO_KEY`, never a real key.

No redirects were followed. No Earthdata token or MAP_KEY was requested, created, read, stored or transmitted. Raw rows were not retained; only a compact receipt was uploaded.

## Measured result

Exact-head workflow [#43085578996](https://github.com/stoicsatvik/NASA/actions/runs/43085578996) completed successfully. All **6/6 deterministic tests passed**. Artifact [#13886920824](https://github.com/stoicsatvik/NASA/actions/runs/43085578996/artifacts/13886920824) contains the receipt.

### Static VIIRS sample

- HTTP 200; 6,077,404 bytes; SHA-256 `edf79f62b35ba4485d7c85e01be5f6f61d30ab7b4addcf2eea00e2581982c30f`.
- **74,605 rows × 14 fields**, independently matching the official NASA tutorial's published count.
- Acquisition date: **2023-07-12** only.
- Instrument: VIIRS; source filename identifies Suomi-NPP; version values `2.0NRT` and `2.0URT`.
- All 14 fields were present and every field had zero missing values in this sample.
- This is a real public sample, but it is static, one-day, VIIRS-only data. It is not a paired MODIS/VIIRS cohort.

### Daily file and API

- Exact South Asia daily file, anonymous GET: **HTTP 303 redirect**. The redirect was not followed. Outcome: authentication required.
- FIRMS area API with `NO_KEY`: **HTTP 400**, classified as `MAP_KEY_REQUIRED`.
- The official active-fire page explicitly directs users to register for Earthdata Login before downloading daily text files; the API documentation requires a free MAP_KEY for area/data-availability requests.

## Interpretation

The no-credential path is **sufficient for parser and visualization fixtures**, not for a current or historical MODIS+VIIRS harmonization campaign. The live/historical path is credential-gated. A free credential may be available to a participant, but this run did not create or use one.

The challenge #9 data-readiness claim must therefore remain conditional. E562 does not prove that the challenge is infeasible; it proves that the static VIIRS example alone is insufficient for the full paired-sensor objective.

The all-14 challenge ranking is not changed by this result. E541 still places Martian Map (#11, 4.10) and MODIS/VIIRS (#9, 4.00) in a provisional top tier, with a 0.10 gap below the predeclared 0.25 meaningful-difference threshold; removing portfolio reuse reverses their order. No challenge is locked.

## Claim states

- Public static VIIRS sample ingestion: **SUPPORTED**.
- Current/historical MODIS+VIIRS access without credentials: **NOT YET PROVEN**.
- Cross-sensor harmonization: **NOT YET MEASURED**.
- Regional/global fire calendar: **NOT YET MEASURED**.
- Martian Map challenge superiority: **NOT YET PROVEN**.
- Planetary-analog challenge superiority: **NOT YET PROVEN**.
- Cross-body analogue similarity and E001 known-site recovery: **NOT YET PROVEN / NOT YET MEASURED**, unchanged.

## Next experiment

Test actual CRS registration and spatial coverage for the already-acquired MOLA, CTX and HiRISE layers over one pinned Mars footprint. Report common support, resolution, nodata and registration error before scoring route-risk features. If the map layers do not share defensible support, lower Martian Map data readiness and re-run the all-14 screen. No UI polish before this gate.

## Sources

- NASA FIRMS Active Fire Data: https://firms.modaps.eosdis.nasa.gov/content/active_fire/
- NASA FIRMS NRT South Asia directory: https://nrt3.modaps.eosdis.nasa.gov/archive/FIRMS/noaa-20-viirs-c2/South_Asia/
- NASA FIRMS data-ingest tutorial: https://firms.modaps.eosdis.nasa.gov/content/academy/data_ingest/firms_data_ingest.html
- NASA FIRMS API: https://firms.modaps.eosdis.nasa.gov/api/
