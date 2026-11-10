# E532 — independent public analogue-catalogue audit (2026-11-11)

## Question

Can an independent, openly licensed Earth-site catalogue provide usable candidate-positive labels for the NASA planetary-analogue stream, and is it sufficiently reviewed to support E001 known-site recovery?

## Frozen source

- Repository: [rachellelecussan/planetary-analogue-catalogue](https://github.com/rachellelecussan/planetary-analogue-catalogue)
- Source revision: `62e6339bdf308de3bc987388d0faa7130cf57de9`
- File: `data/sites.geojson` (GeoJSON FeatureCollection; generated 2026-10-12)
- Source README declares the `data/` directory CC BY 4.0, code MIT, and per-photo licences individually. No source photos or raw GeoJSON were copied into this repository.
- The catalogue describes 16 sites, 96 references and 42 photos. It is an independent candidate catalogue, not an official USGS/NASA ground-truth dataset.

## Audit results

The pinned GeoJSON contains:

- **16 Point features**, 16 unique site IDs and 16 non-empty primary analogue labels in `analogue_for_primary`.
- Primary target labels: **Mars 10, Moon 2, Early Earth 2, Enceladus 1, Europa 1**. Thus 12 records are Mars/Moon primary candidates; the others are outside the current Moon/Mars E001 scope.
- **All 16 records are marked `Draft`**. None is marked `Verified`.
- **96 references**: 33 marked peer-reviewed, 63 not marked peer-reviewed; 33 DOI-bearing references (33 unique DOIs); one reference is marked unverified. There are 95 unique reference URLs.
- **42 photos**, with individual attribution/licensing fields. These are not redistributed.
- **7/16 sites are marked sensitive**. Coordinate precision is approximately 10 km for 10 sites, approximately 1 km for 2, and region-only for 4.
- Descriptor completeness is uneven: extent 8/16; altitude minimum 3/16 and maximum 7/16; pH minimum/maximum 4/16 each; temperature minimum 7/16 and maximum 9/16; salinity 7/16; age 13/16; rock types 13/16; key minerals 10/16; geological setting 15/16; target feature 16/16; analogue limitations 9/16.

The catalogue uses `analogue_for_primary` and `analogue_for_other`, not a canonical `target_body` field. These are curator-entered candidate labels. The schema contains no explicit non-analogue control population.

## Result

**NOT E001-READY**

The catalogue is useful as a **candidate-positive discovery index** and literature-navigation aid. It is **not** accepted as known-site ground truth:

1. every record remains Draft;
2. there is no independent review status for any site;
3. there are no explicit non-analogue controls;
4. numeric physical descriptors are sparse and not uniformly measured;
5. sensitive-site flags and coarse coordinates must be respected.

The 12 Mars/Moon candidate records may be queued for source-by-source review against their cited primary literature, but they must not be treated as a validated holdout set or used to claim recovery. No E001 ranking was run on these records.

## Reproducibility

- `experiments/e532_public_catalogue_audit.py` fetches the exact pinned raw file, enforces the URL and byte limit, computes SHA-256, and emits a machine-readable receipt.
- `experiments/test_e532_public_catalogue_audit.py` covers source pinning, label/review accounting, control-population rejection, duplicate IDs and geometry validation.
- The workflow stores the generated receipt as a 30-day Actions artifact. It does not commit the external dataset or photos.

## Claim-state update

- Independent catalogue as a candidate-positive index: **SUPPORTED**.
- Catalogue as validated E001 ground truth: **REJECTED for current use**.
- Cross-body similarity: **NOT YET PROVEN**.
- Known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Planetary-analog challenge superiority: **NOT YET PROVEN**.

## Next decisive experiment

Acquire and inspect the separate official USGS 2020 *Known Terrestrial Analog Sites for Planetary Science* point layer (DOI [10.5066/P9J72921](https://doi.org/10.5066/P9J72921)) as another candidate-positive source. Then independently verify a small, predeclared subset of candidate sites against primary literature and obtain a defensible non-analogue control set plus matched physical descriptors. Do not treat absence from a positive catalogue as a negative label.
