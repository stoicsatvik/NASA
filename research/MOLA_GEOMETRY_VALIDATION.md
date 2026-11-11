# MOLA MEG004 geospatial alignment contract

Status: synthetic validation only; draft PR, not a scientific result.

The paired topography and observation-count rasters must have the same spatial footprint, not just identical dimensions. The PDS3 labels are checked against the published MEG004 global grid geometry: center (0°, 180°), longitude 0°–360°, latitude -90°–90°, line/sample projection offsets 360.5/720.5, and zero rotation. All nine fields must be present and match the expected values.

Falsifiable regression: a synthetic counts label with CENTER_LONGITUDE=90° previously passed the reader despite a topography label at 180°. It must now fail with `unexpected MEG004 projection: CENTER_LONGITUDE`. A missing line offset must also fail. Existing reader regressions must remain green.

Local result on 2026-10-20: 11/11 synthetic MOLA reader unit tests passed with the paired patch; this is **not** validation against real NASA raster bytes. The existing checksum-verifier tests were previously run separately, not part of this claim.

Official source labels:
- https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg004/megt90n000cb.lbl
- https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg004/megc90n000cb.lbl

Remaining gates: download both real rasters, independently verify archive MD5 manifest, run the reader on real labels, and establish green CI. Do not interpret synthetic checks as evidence for planetary analogue recovery.
