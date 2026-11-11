# E560 - USGS Known Terrestrial Analog Sites acquisition (11 November 2026)

## Question
Can the official USGS CC0 point-layer release (DOI 10.5066/P9J72921; ScienceBase item 5f88940b82cebb8c13d912ee) be acquired through its public item metadata, and can its actual schema/CRS/features be compared by name with PAAD, the 16-site Le Cussan catalogue and NASA Analog Explorer pairs?

## Method
- Exact official ScienceBase item JSON endpoint, anonymous HTTPS, 2 MB metadata cap and 25 MB file cap.
- No guessed file URLs. Download only one vector file if official metadata exposes exactly one unambiguous candidate URL within the cap.
- HTTPS ScienceBase/S3 allowlist; no credentials, cookies, access-control bypass or API keys.
- Parse GeoJSON directly or one shapefile/GeoJSON inside a bounded ZIP. Record SHA-256, feature count, geometry, property fields and CRS declaration.
- Exact and normalized full-name overlap only; not coordinate overlap or physical-feature equivalence.
- Raw bytes remain in a seven-day Actions artifact; no source data committed.

## Result
PENDING exact-head Actions. HTTP 403/404 or absent vector URL is a negative acquisition result, not proof that the dataset is private or inaccessible to ordinary users.

## Claim boundary
The official USGS release is a candidate-positive point layer and CC0 1.0. It is not ground truth, supplies no negative controls, and cannot validate cross-body similarity by itself. No E001 recovery is claimed.
