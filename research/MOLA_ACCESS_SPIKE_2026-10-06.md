# MOLA dataset-access spike — verified 2026-10-06

## Result

The previous assumption that MOLA MEGDR access was generically blocked is rejected.

The PDS Geosciences Node currently exposes the maintained MGS MOLA Topography Derived bundle online. The global 4 pixels/degree MEGDR topography product is:

- image: `megt90n000cb.img`
- PDS4 label: `megt90n000cb.xml`
- coverage: 90°N to 90°S, 0°E to 360°E
- resolution: 4 pixels/degree
- coordinate system: IAU 2000 for the final MEGDR maps

Higher-resolution MEGDR products are also documented at 16 and 32 pixels/degree, with 64/128 pixels/degree products tiled because of size.

## Provenance

Official PDS Geosciences documentation:

- https://pds-geosciences.wustl.edu/missions/mgs/mola.html
- https://pds-geosciences.wustl.edu/missions/mgs/megdr.html

PDS states that MOLA altimetry profiles were used to create the global topographic maps and that the PDS4 Topography Derived bundle is the maintained archive.

## Claim boundary

SUPPORTED: a legitimate maintained public source and exact low-resolution MOLA topography product have been identified.

NOT YET MEASURED: payload byte retrieval, checksum, label parsing, raster decoding, missing-value behavior, physical descriptor extraction, or E001 known-analogue recovery.

Do not treat this document as evidence that any raster values were downloaded or decoded.

## Next falsifiable gate

1. retrieve the XML label and IMG bytes from the official PDS4 bundle;
2. record URL, retrieval time, byte count and SHA-256;
3. parse dimensions, sample type/width, scaling/offset, projection/coordinate metadata and missing/special constants from the label;
4. decode a bounded deterministic raster window and assert its byte layout against the label;
5. only then derive topographic descriptors for E001.
