# E537 — ScienceBase item-ZIP raster-ingestion result contract (11 November 2026)

## Question

Does the public ScienceBase item-ZIP endpoint provide the named Grand Falls DEM as a size-matched TIFF, and does the workflow distinguish a measured negative acquisition result from an unexpected software/structure error?

## Pinned source

- ScienceBase item: `662bccfad34ea70bd5f11f88`
- DOI: `10.5066/P9FRH62D`
- DEM: `GFDF_Ripples_2023_04_18_DEM.tif`
- Catalogue DEM size: **619,492 bytes**
- Endpoint: the public item-ZIP endpoint documented by the ScienceBase client implementation.

## Observed result

The 11 November live run [#42957991093](https://github.com/stoicsatvik/NASA/actions/runs/42957991093) returned HTTP 200 and an `application/zip` response from `www.sciencebase.gov`.

- ZIP bytes: **1,002,830**
- ZIP SHA-256: `2b419b33290207efd35df355348258f7a041b34b621c235d223d217c0c46e2f2`
- Selected DEM member: **0 bytes**
- Empty-member SHA-256: `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- FGDC metadata member: **21,475 bytes**
- FGDC SHA-256: `53d931210df3c81c90eb3ebdb4136336661b2b5d6bc36c5a71cd1debec7a07df`

The workflow preserved the ZIP and metadata receipt as artifact [#13828156651](https://github.com/stoicsatvik/NASA/actions/runs/42957991093/artifacts/13828156651). The DEM was not acquired and no raster inspection was performed.

## Engineering correction

The original implementation classified any exception after ZIP-member enumeration as a zero-byte/missing-raster result whenever the selected byte count differed from the catalogue size. That could mislabel missing, duplicate, unsafe, or otherwise unselected members as a measured zero-byte DEM.

The revised implementation:

- Raises a typed `CatalogueSizeMismatchError` only after exactly one safe DEM member has been selected and its extracted byte count is known.
- Classifies a measured 0-byte member as `NEGATIVE_RESULT_ZERO_BYTE_DEM_MEMBER`.
- Classifies a nonzero catalogue-size discrepancy separately as `NEGATIVE_RESULT_DEM_SIZE_MISMATCH`.
- Leaves missing/duplicate members, unsafe paths, malformed archives, non-TIFF payloads, and unrelated validation errors as `ERROR`.
- Marks the experiment completed for a measured negative result while keeping `download.success=false` and `raw_dem_acquired=false`.
- Removes the unsupported inference that other ScienceBase paths necessarily require authentication. Only this ZIP endpoint's observed response is described.

## Claim boundary

The public item ZIP endpoint returned a named zero-byte DEM member while the catalogue lists 619,492 bytes. This is a negative result for this endpoint and item in the tested public context.

It does not establish that all ScienceBase/USGS access paths are unavailable, that authentication is required for other routes, or that the site lacks a usable DEM. No CRS, resolution, nodata, vertical datum, elevation units, pixel values, Earth/Mars comparability, known-site recovery, or analogue-discovery claim is made.

## Validation

The dedicated workflow runs deterministic fixtures before the live bounded request and always preserves the sanitized/raw-data receipt artifact. The expected zero-byte outcome is a completed research experiment, not a green claim of successful raster ingestion. Unexpected structural or software errors still fail the job.

The earlier failed run is preserved in Actions history; this branch adds explicit regression coverage for the classification boundary.
