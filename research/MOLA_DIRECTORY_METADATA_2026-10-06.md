# MOLA PDS4 directory metadata — 2026-10-06

Official PDS Geosciences maintained bundle index:
https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg004/

The official `meg004` directory reports:
- `megt90n000cb.img`: 2,073,600 bytes
- `megt90n000cb.xml`: 15,509 bytes
- `megt90n000cb.hdr`: 1,057 bytes
- `megt90n000cb.lbl`: 4,796 bytes

The directory listing is readable in the current environment. Direct XML/IMG payload materialization still fails in available fetch/download paths.

Claim boundary:
- SUPPORTED: maintained public PDS4 product identity and server-reported byte counts.
- NOT YET MEASURED: locally retrieved byte count, checksum, label parsing, raster decoding, descriptor extraction, E001 recovery.

The server-reported byte count is integrity metadata, not a locally measured payload size.

Next gate: retrieve XML+IMG through a byte-capable path, assert local sizes against these directory values, hash the payloads, parse the label, then decode a deterministic raster window.
