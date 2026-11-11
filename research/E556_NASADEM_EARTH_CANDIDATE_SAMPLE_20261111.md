# E556 — NASADEM HGT Earth candidate/control access gate (2026-11-11)

## Question

Can the official NASADEM HGT V001 collection provide a bounded, anonymous elevation sample at the Lonar literature lead and a nearby comparison point?

## Provenance and exact execution

- Repository: stoicsatvik/NASA
- Branch: `research/e556-nasadem-earth-candidate-sample-20261111`
- Draft PR: #116, stacked on E554; main unchanged
- Exact implementation head: `24e7238f329df6f9189cee939c20258043489009`
- Exact-head Actions run: [#43049875930](https://github.com/stoicsatvik/NASA/actions/runs/43049875930), SUCCESS
- Aggregate artifact: [#13868747953](https://github.com/stoicsatvik/NASA/actions/runs/43049875930/artifacts/13868747953), 888 bytes; ZIP SHA-256 `ffe193339d56983d88ad0f8cfac13fcc67c29a1333cfec2275aca7f24b5c3d5a`
- Deterministic tests: **8/8 passed**.
- Source: NASADEM HGT V001, DOI 10.5067/MEASURES/NASADEM/NASADEM_HGT.001, CMR collection concept `C2763264762-LPCLOUD`.

## Measured result

The official CMR granule API returned the same exact tile for both frozen points:

| Point | Role | Granule | Tile | CMR response |
|---|---|---|---|---:|
| Lonar (19.9750 N, 76.5090 E) | Literature lead, not validated positive | `NASADEM_HGT_n19e076` | `N19E076` | 3,206 bytes |
| Nearby comparison (19.8000 N, 76.3000 E) | Not a negative label | `NASADEM_HGT_n19e076` | `N19E076` | 3,206 bytes |

The CMR responses were independently hashed:
- Lonar query: `4865efb743817af1ee7ab261af35cfe0df778d38501a765bcb2871d766d7f7a2`
- Nearby query: `140acb498a070eb8a21ca838a61993997fc4457bea111cd39de6198522f3c9b5`

CMR exposed only the following protected product path:

`/lp-prod-protected/NASADEM_HGT.001/NASADEM_HGT_n19e076/NASADEM_HGT_n19e076.zip`

Outcome: **EARTHDATA_AUTH_REQUIRED**. No credentials were used, no redirect was followed, no range request was made, and zero raster bytes were acquired. The script preserved the protected path and CMR response hashes without retaining raw metadata or credentials.

This is a specific access boundary, not evidence that the product is absent or scientifically unsuitable. The metadata route is accessible; the selected direct-data route requires Earthdata authentication.

## Interpretation

- NASADEM tile metadata resolution: **SUPPORTED** for both points.
- Anonymous NASADEM HGT pixel access: **BLOCKED by Earthdata authentication** for this route.
- No elevation, slope, relief or terrain statistic was measured.
- The two coordinates are not independent positive/negative labels.
- Cross-body similarity, known-site recovery, novel analogue discovery and local-validation advantage remain **NOT YET PROVEN / NOT YET MEASURED**.

## Next discriminating action

E557 tests the separate anonymous Copernicus GLO-30 public COG at the same two points. This is auxiliary ESA/Copernicus data, not a substitute for a challenge-required NASA resource. Treat its DSM semantics, vegetation/building contamination and vertical-reference differences explicitly. Do not merge it naively with MOLA/CTX/HiRISE or promote these two points into labels.
