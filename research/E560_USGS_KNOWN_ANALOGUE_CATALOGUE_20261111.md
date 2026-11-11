# E560 - USGS Known Terrestrial Analog Sites acquisition (11 November 2026)

## Question

Can the official USGS CC0 Known Terrestrial Analog Sites release (DOI 10.5066/P9J72921; ScienceBase item 5f88940b82cebb8c13d912ee) provide an actual vector file, and if so, is it suitable for quantitative candidate validation?

## Bounded acquisition

The initial exact-head live run [#43067276665](https://github.com/stoicsatvik/NASA/actions/runs/43067276665) returned HTTP 200 from the exact ScienceBase item JSON endpoint:

- Item ID and title matched the frozen release.
- JSON response: 19,203 bytes.
- One file record: AnalogSites_metadata.xml, declared size 9,406 bytes.
- Downloaded XML size: 9,406 bytes.
- The FGDC XML exposed only the DOI link; no vector URL was found.
- No shapefile, GeoJSON, GeoPackage or point-feature payload was acquired.
- Initial run outcome: METADATA_XML_NO_VECTOR_LINK.

The XML is available only in the seven-day Actions artifact. No source data was committed.

## FGDC metadata observations

The downloaded XML declares the following, but these statements are **not checksum-verified**:

- 192 entity-point features.
- Attribute fields: FID, Shape, Name, AnalogType, Lat, Lon and AnalogBody.
- AnalogType values listed: Impact Crater, Dunes and Volcanic Eruption.
- Projection: Mercator_1SP; horizontal datum: WGS_1984; coordinate units: meters.
- Purpose: "For identification of research areas, not for analysis."
- Positional statement: points approximate large areas and may be in error by up to 10 km from the feature centroid.
- Status: In work; update as needed.
- Completeness: limited to sites verified through NASA-funded research, not all possible sites.
- Processing lineage: None / Unknown.

The declared 0.6096 m coordinate resolution is not positional accuracy. The 10 km statement controls the use boundary. Even if the vector becomes available, this is a discovery/reference index, not a precise analytical label set or ground truth.

## Integrity discrepancy

The ScienceBase item JSON supplied an MD5 for AnalogSites_metadata.xml:

- Catalogue MD5: def5fcdca1a6e7dd4389def926c3c1f1
- Computed MD5 of the downloaded 9,406-byte XML: d514547ac0dd7e68a302e03cd4c59d9f
- XML SHA-256: 0b38af81da5fd638f830b066c4d6c6626b899ef0c1aad16a4cecef33821ef855
- Size comparison: match
- MD5 comparison: mismatch

This is preserved as a data-integrity discrepancy, not silently accepted. The FGDC fields above are provisional until the checksum/version mismatch is explained.

## Implementation and validation state

The E560 branch now:
- Pins the returned ScienceBase item ID and title.
- Refuses HTTP redirects rather than following a changed endpoint.
- Redacts URL query values from receipts.
- Parses the FGDC purpose, accuracy, geometry, feature count, schema and lineage fields.
- Compares the downloaded metadata bytes with the catalogue checksum.
- Records web-link metadata without storing query values.

The last successful Actions run (#43067276665) validated an earlier 7-test revision and completed the bounded metadata read. The later 13-test revision has **not yet received a confirmed exact-head Actions run**. Independent helper checks against the downloaded artifact passed for FGDC extraction, the 10 km limit, checksum mismatch detection, exact item identity, redirect refusal and query-value redaction.

Earlier failures are retained:
- #43066415267: one incorrect expected value in the normalized-name overlap test.
- #43066816401 and #43066919849: test-file indentation errors.
- #43067276665: earlier 7/7 deterministic tests passed and the live metadata audit completed.

## Claim boundary

- No vector file acquired.
- No feature names or coordinates recovered.
- No coordinate overlap, known-site recovery, negative-control construction or E001 result.
- The declared 192 points are metadata claims, not 192 acquired features.
- The metadata's own stated purpose and 10 km uncertainty rule out using this source as a precise analytical label set.
- The checksum mismatch prevents treating the downloaded FGDC metadata as integrity-verified.

## Next gate

The USGS TADP documentation states that its ScienceBase-backed holdings can be exposed through OGC WMS/WFS/CSW services. ScienceBase documentation explains that WFS layers are published only when a shapefile has been uploaded and a service created. That does not prove this item has a service.

Next, make one bounded WFS GetCapabilities inventory request and search for an item/title-matched feature type. If found, inspect DescribeFeatureType and a count-only result before any feature retrieval. If no layer exists, stop treating this 2020 item as an analytical data source and use an independently documented catalogue. Do not contact the previously emailed nonresponder with a follow-up.

References:
- USGS TADP service description: https://tadp.astrogeology.usgs.gov/how-to-contribute
- ScienceBase geospatial services: https://www.usgs.gov/sciencebase-instructions-and-documentation/sciencebase-geospatial-services
- ScienceBase API: https://www.usgs.gov/sciencebase-instructions-and-documentation/api-and-web-services
- USGS data release: https://www.usgs.gov/data/known-terrestrial-analog-sites-planetary-science
