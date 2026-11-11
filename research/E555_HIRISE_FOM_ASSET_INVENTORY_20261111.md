# E555 — product-specific HiRISE FOM/provenance asset inventory (11 November 2026)

## Question

Does the pinned USGS 2020 Mars 2020 TRN HiRISE DTM release expose a Figure-of-Merit (FOM), confidence, quality, or provenance asset that can classify the three E550/E554 all-nodata neighborhoods?

## Why this is the next gate

E552 established that the three unsupported E550 windows are byte-identical to the product's declared all-nodata value. E554 then sampled a larger 128×128 neighborhood around each frozen coordinate: all three neighborhoods remained 16,384/16,384 nodata, with zero usable pixels. Repeating nearby raster windows is no longer useful.

USGS Astrogeology's general HiRISE DTM documentation says FOM images identify per-pixel provenance, including matcher correlation, manual edits, interpolation/extrapolation, shadow/saturation, no-data and suspicious terrain. It describes FOM as the definitive pixel-level provenance source for those standard HiRISE DTM products. This is a strong lead, not proof that the separate 2020 TRN flight mosaic has the same asset.

## Frozen sources

- USGS 2020 TRN HiRISE DTM release: DOI [10.5066/P9REJ9JN](https://doi.org/10.5066/P9REJ9JN).
- Public product directory: `https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/index.html`.
- Pinned PDS3 label and product XML for `JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40`.
- General USGS HiRISE DTM asset/provenance guidance: [HiRISE DTMs and Orthoimages](https://stac.astrogeology.usgs.gov/docs/data/mars/hirise_dtms/).

## Method

- Fetch only the public directory index, PDS3 label and product XML.
- Exact HTTPS host/path allowlist; redirects rejected.
- Byte caps: 128 KB index, 256 KB label, 512 KB XML.
- Inventory linked asset names and classify FOM/figure-of-merit/provenance/confidence/quality/hillshade/mask names.
- Scan the two metadata files for FOM/provenance/quality references, retaining only hashes, line numbers and keyword counts.
- No raster request, raw pixel read, credentials, signed URL, raw metadata persistence, imputation or registration fit.

## Exact-head result

Exact-head workflow [#43045846786](https://github.com/stoicsatvik/NASA/actions/runs/43045846786) succeeded.

- Deterministic tests: **8/8 passed**.
- Public directory index: **56 assets** (25 raster files, 31 metadata/other files).
- FOM/figure-of-merit assets: **0**.
- Filename-level provenance/quality/confidence/hillshade/mask assets: **0**.
- Pinned PDS3 label: 2,296 bytes, 47 lines; **0 FOM references** and no confidence/provenance/quality/mask/nodata keyword hits.
- Pinned product XML: 18,939 bytes, 305 lines; **0 FOM references**, no confidence/provenance/mask/nodata hits. The generic word `QUALITY` appears on lines 108, 157 and 260; these are keyword hits only, not evidence of a pixel-level quality layer.
- Directory index: 14,486 bytes. Total metadata transferred: **35,721 bytes**.
- Raster requests: **0**. Raw metadata bodies and raw pixels were not retained.

**Result:** the pinned 2020 TRN HiRISE public directory, its PDS3 label and its product XML do not list or reference a FOM/provenance asset. This is a product-specific negative inventory, not proof that no separate asset exists elsewhere.

## Claim boundary

Absence from this directory index and its two pinned metadata files does not prove that no separate FOM or quality product exists elsewhere. A generic STAC documentation page is not automatically a product-specific asset manifest for the 2020 TRN flight mosaic. The physical cause of the three nodata neighborhoods remains NOT DETERMINED. Cross-body similarity, E001 known-site recovery and route safety remain unproven/unmeasured/not claimed.

## Next action

If the pinned release exposes no FOM asset or metadata reference, use Trent Hare's referral to ask one designated PDS/USGS support contact whether this specific flight mosaic has a separate footprint, confidence, FOM or processing-provenance product. Do not contact both referrals with the same question. If no product-specific provenance exists, preserve partial support and stop local nodata probing.
