# E594 — NASA FIRMS keyless MODIS/VIIRS data-readiness probe

Date: 12 November 2026  
Branch: \`research/e594-firms-keyless-modis-viirs-20261112\`  
Draft PR: #159, stacked on E593. Main untouched.  
Workflow: [run 43263519356](https://github.com/stoicsatvik/NASA/actions/runs/43263519356), passed 6/6 deterministic tests and the live probe. Aggregate artifact SHA-256: \`f4e7d58ee190c01593b1f69a28b1d5b572e5fcb85f8c6181b0c8a7bc052ef280\`.

## Question

Does the MODIS/VIIRS hot-spot alternative have a usable recent data path without an Earthdata account or MAP_KEY, and can the two sensor families be compared using a common schema?

## Results

| Product | Result | Exact evidence |
|---|---|---|
| MODIS C6.1 Global 7-day CSV | **Accessible** | HTTP 206, \`text/csv\`; 256 KiB prefix of a 6,715,583-byte file; Last-Modified 12 Nov 2026 16:46:21 GMT |
| VIIRS S-NPP Global 7-day candidate | **Not established** | Tested URL returned HTTP 404; official product coverage ended 2 Nov 2026 |
| VIIRS NOAA-20 / NOAA-21 | **Not established** | Guessed direct paths returned 404; no product-unavailability inference is made |
| FIRMS active-fire directory root | **Not listed** | Bounded request returned HTTP 404, so automatic directory discovery yielded no links |

### MODIS prefix

- 3,371 complete CSV rows; one truncated final row dropped.
- All 3,371 complete rows had valid latitude/longitude and acquisition date/time fields.
- Prefix-only acquisition date bounds: 2026-11-05 to 2026-11-05. This is not the full file's date range.
- Prefix coordinate bounds: latitude [-38.19415, 58.15745], longitude [-155.29503, 179.44702].
- Header fields include \`brightness\` and \`bright_t31\`; no \`instrument\` column exists. The \`satellite\` field contains A/T.
- The parser initially required \`instrument\`, causing a false-negative schema admission. E594 corrected this: instrument is optional; the common field set is limited to fields actually present in the file.
- Only aggregate counts, schema, bounds and a SHA-256 of the bounded prefix were retained. No raw observation or coordinate is stored.

## Interpretation

The MODIS 7-day endpoint is demonstrably reachable without credentials. This is a real but partial data-readiness result.

VIIRS is the limiting side. The tested S-NPP candidate path returned 404, and the official FIRMS archive page reports S-NPP coverage through 2 November 2026. NOAA-20 and NOAA-21 remain in coverage through the present, but their archive download path is email-authenticated; this run did not use the login flow. The guessed direct 7-day paths and the directory root returned 404, which is not sufficient evidence that no public current VIIRS endpoint exists.

The official FIRMS archive page distinguishes data older than the last seven days and presents an email-authentication step; it also lists MODIS C6.1 and the three VIIRS platforms' temporal coverage. The active-fire page advertises 24-hour, 48-hour and 7-day products. These facts do not prove that a current NOAA-20/21 point-data file is available without credentials.

## Claim states

- Exact MODIS C6.1 7-day keyless CSV access: **SUPPORTED**.
- Exact VIIRS S-NPP keyless 7-day path: **NOT YET ESTABLISHED**.
- Current NOAA-20/21 keyless point-data path: **NOT YET ESTABLISHED**.
- Cross-sensor schema harmonization: **NOT YET PROVEN**.
- Detection-bias correction / sensor equivalence: **NOT YET PROVEN**.
- Historical archive access without email authentication: **NOT YET PROVEN**.
- MODIS/VIIRS challenge superiority over the Martian Map candidate: **NOT YET PROVEN**.

This result slightly improves the MODIS/VIIRS alternative's evidence score on MODIS availability but leaves its critical VIIRS path unresolved. The all-14 challenge ranking remains provisional; no challenge is locked.

## Next decisive step

Inspect the official FIRMS page's exact 24-hour/48-hour/7-day download links for NOAA-20/21, without attempting account creation or authentication. If no public current point-data endpoint exists, record that as a concrete dependency and compare the challenge on the basis of available public layers rather than claiming full data readiness. Do not substitute rendered tiles for point-level detections without an explicit change in evaluation target.
