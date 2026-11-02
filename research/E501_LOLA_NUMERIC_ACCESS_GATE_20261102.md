# E501 | Real LOLA 4-ppd numerical raster access gate (2 November 2026)

## Falsifiable question

Can the Foundry ingest **actual numeric lunar elevation values**, rather than screenshots, count masks or decorative height-map colors, from a small official NASA-hosted file using a bounded free runner? This is a data-access experiment, **not** E001 known-analogue recovery.

## Source and provenance

- Official NASA SVS: https://svs.gsfc.nasa.gov/4720 , CGI Moon Kit, LOLA displacement section.
- Binary source: https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/ldem_4.tif
- Source page describes 1440x720, 4 pixels/degree, floating-point kilometers relative to a 1737.4 km lunar radius; it is a reformat of archived PDS LOLA gridded data, **not a new independent measurement**.
- Official page explicitly distinguishes visualization from scientific source data. We use this small numerical product for an access/units gate; future scientific comparison should use PDS source, projection metadata, observation coverage and instrument-specific uncertainty.
- Bounded download 8 MiB maximum, timeout 40 seconds; SHA-256 and source bytes recorded. Finite/missing values are reported without treating interpolated gridded values as independent laser observations.

## Executable experiment

`python -m research.e501_lola_ingest /tmp/e501_lola.json` downloads, validates TIFF signature, requires a single float-band raster of shape 720x1440, records source digest, finite counts, min/max/quantiles and five fixed pixel-index 5x5 numeric tiles. Pixel-index tiles are **not** independently registered lat/lon samples; orientation/projection remains a separate gate. `.github/workflows/e501-lola.yml` runs the same code on an isolated free GitHub Actions runner with pinned NumPy/tifffile and uploads a JSON receipt if successful. No raw large TIFF is committed.

Six local synthetic controls pass: float-shape acceptance, nonfinite handling, wrong shape/dtype/all-missing rejection and georeference claim guard. These tests **do not validate real ingestion**. Only a successful runner receipt with SHA-256 and numeric tiles advances the access claim.

## Claim boundaries

- LOLA source identity and units: SUPPORTED by official NASA metadata.
- Real numeric raster ingestion: **NOT YET MEASURED** until exact-head CI succeeds with a verified receipt.
- Physically comparable Moon/Mars/Earth descriptors: NOT YET PROVEN.
- E001 known-site recovery: NOT YET MEASURED.
- Cross-body similarity, novel analogue discovery, field-validation advantage, challenge-selection superiority: NOT YET PROVEN.

## Next decisive gate

If the TIFF is acquired, verify its spatial orientation and PDS grid equivalence; ingest MOLA numerical elevation and Earth DEM with explicit radius/areoid/projection differences, compute matched physical-scale descriptors and execute E001 known-site recovery with independent labels, random/Euclidean/physically weighted baselines, leave-one-site-out tests and nulls. If access fails, preserve exact HTTP/network failure and try a legitimate PDS-hosted bounded sample instead. No UI polish, competition submission, outreach or field work.
