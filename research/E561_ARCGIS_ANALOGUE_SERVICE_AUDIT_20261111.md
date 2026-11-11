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
