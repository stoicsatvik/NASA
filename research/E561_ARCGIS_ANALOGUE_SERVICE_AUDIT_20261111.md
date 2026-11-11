# E561: public ArcGIS terrestrial-analogue service schema and count audit

**Question:** Does the ArcGIS FeatureServer exposed by the official ScienceBase item web link provide a public, schema-matched layer and a count-only query without credentials or downloading feature rows?

## Discovery basis

E560's exact-head live ScienceBase item response exposed one ArcGIS REST web link:

- Host: `services.arcgis.com`
- Path: `/v01gqwM5QqNysAAi/ArcGIS/rest/services/Terrestrial_Analog_Sites_for_Planetary_Science/FeatureServer`
- Query parameter names included `token`; its value was intentionally not retained or reused.
- E560 did not follow the link.

The public service metadata and layer directory are independently indexed by ArcGIS REST. The frozen service item ID is `db564f72235f49b39c4147df36fd3308`; layer 0 is `TerrestrialAnalogs`, point geometry, with fields FID, Name, AnalogType, Lat, Lon and AnalogBody. See the PR references for the live schema/count-only result.

## Frozen method

1. GET only the exact service metadata endpoint.
2. GET only layer 0 metadata.
3. GET the layer query endpoint with exactly `where=1=1`, `returnCountOnly=true`, `f=json`.
4. Require HTTPS, exact host/path allowlist, exact response URL, HTTP 200, JSON content type, and a 1 MB response cap.
5. Refuse redirects. No token, API key, login, feature rows, geometry, coordinate, or full export is requested.
6. Validate service item identity, anonymous-query permission, layer name/type/geometry, required fields, object-ID field and spatial reference.

## Claim boundary

A successful count-only query establishes service availability, schema and a record count only. It does **not** establish that the 192 FGDC-declared points were downloaded, that the metadata checksum discrepancy is resolved, or that the catalogue is suitable for analysis. E560's FGDC statement says the point locations are discovery/reference approximations with possible errors up to 10 km and explicitly says they are not for analysis. The catalogue remains a discovery index, not ground truth or a training-label source.

Raw service JSON and feature rows are not retained. Only a compact receipt is uploaded as a short-lived workflow artifact.


## Exact-head live result (11 November 2026)

- Exact implementation/test head: `e99866cccbffb83b0118f81256f5bed13d1446a1`.
- PR workflow [#43070089505](https://github.com/stoicsatvik/NASA/actions/runs/43070089505) and push workflow [#43070045960](https://github.com/stoicsatvik/NASA/actions/runs/43070045960) both succeeded; **7/7 deterministic tests** passed in each run.
- The exact public service item ID and layer 0 identity matched. The service advertises Query capability and explicitly allows anonymous querying. Layer 0 is `TerrestrialAnalogs`, a point Feature Layer, with fields FID, Name, AnalogType, Lat, Lon and AnalogBody; object-ID field FID; spatial reference 3857; max record count 2,000.
- The count-only request (`where=1=1&returnCountOnly=true&f=json`) returned **4 records**. No feature rows, geometries or coordinates were requested or downloaded.
- The count does **not** match the FGDC metadata's provisional declaration of 192 points. This is a material version/provenance discrepancy, not a reason to silently replace 192 with 4. E560's XML MD5 mismatch also remains unresolved.
- Service metadata reports static data and a last edit date of 10 July 2024. Its editor-tracking metadata advertises anonymous update/delete permissions; this experiment performed only GET requests and did not test or invoke any write operation.
- Outcome: public service schema and count-only access are SUPPORTED; catalogue feature contents, point identities, coordinate accuracy, version equivalence to the FGDC XML, quantitative suitability, and E001 known-site recovery remain NOT ESTABLISHED.

## Next gate

Do not download feature rows yet. First resolve the 4-versus-192 discrepancy using source/version provenance: compare the ArcGIS service item ID, last-edit metadata, ScienceBase file record and DOI release history. The FGDC file checksum mismatch prevents treating the XML as a trusted version manifest. If the publisher's version lineage cannot be reconciled, retain the ArcGIS service only as an unverified discovery endpoint and stop short of using it as an analytical label source.


## Exact-query allowlist hardening (11 November 2026)

A review of the E561 request guard found that it pinned the ArcGIS host and path but would still accept arbitrary query parameters if a future caller passed them to `fetch_json`. That was broader than the documented frozen request contract.

The guard now requires exact query maps:
- Service and layer metadata: only `f=json`.
- Count endpoint: only `where=1=1`, `returnCountOnly=true`, and `f=json`.
- Duplicate parameters, fragments, tokens, `outFields`, geometry-return flags and any other query additions are rejected.

Exact-head PR workflow [#43070943518](https://github.com/stoicsatvik/NASA/actions/runs/43070943518) and push workflow [#43070938391](https://github.com/stoicsatvik/NASA/actions/runs/43070938391) both succeeded; **7/7 deterministic tests** passed and the live count-only query again returned **4**. No feature rows or coordinates were requested. The earlier push run [#43070930458](https://github.com/stoicsatvik/NASA/actions/runs/43070930458) was cancelled by the workflow concurrency group after the second commit; it is not a scientific failure.

Implementation head: `97c00f1408711fb8ba8a08b0a30ef0bc5171815b`; exact test head: `66f5c01ab01a73f68aef25ed5bc8ec3d165e25fc`. Receipt artifact: [#13876899123](https://github.com/stoicsatvik/NASA/actions/runs/43070943518/artifacts/13876899123).


## Portal item provenance result (11 November 2026)

The ArcGIS Portal item REST endpoint returned JSON when its `text/plain` content type was parsed as JSON. The public item metadata validates:

- Item ID `db564f72235f49b39c4147df36fd3308`, matching the service root's `serviceItemId`.
- Title: `Terrestrial Analog Sites for Planetary Science`.
- Type: Feature Service; access: public.
- Owner account: `mahunter@usgs.gov_USGS`.
- Created: 2020-11-17 18:08:27 UTC.
- Item modified: 2024-07-09 18:04:14 UTC.
- Layer last edit: 2024-07-10 18:37:49.500 UTC.
- Portal item's service URL host/path matches the service endpoint after case normalization (`/arcgis/rest` versus `/ArcGIS/rest`). It contains no query parameters and no token.
- The 178-character item description does not mention DOI `10.5066/P9J72921`, the ScienceBase item ID, or FGDC.

This strengthens the identity link between the ScienceBase web link and the public ArcGIS item, but it still does **not** establish that the ArcGIS layer is the same 192-point FGDC release. The item description has no DOI/ScienceBase cross-reference; the service count remains **4**. The layer edit timestamp is about 24 h 33 min 35.5 s after the item modified timestamp, so those timestamps are not interchangeable.

The initial portal-item attempts returned `text/plain` and were first rejected; the parser was then corrected to accept `text/plain` only when the body parses as JSON. A subsequent identity check exposed a path case-only difference; the final validator records that normalization explicitly rather than discarding the discrepancy. No raw item URL, query value, or metadata body is retained.

Latest exact-head PR workflow [#43073044735](https://github.com/stoicsatvik/NASA/actions/runs/43073044735): **14/14 deterministic tests passed**; live portal item metadata, service schema and count-only audit completed. Receipt artifact: [#13879985771](https://github.com/stoicsatvik/NASA/actions/runs/43073044735/artifacts/13879985771).
