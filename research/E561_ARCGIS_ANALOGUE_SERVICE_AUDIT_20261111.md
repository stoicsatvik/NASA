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
