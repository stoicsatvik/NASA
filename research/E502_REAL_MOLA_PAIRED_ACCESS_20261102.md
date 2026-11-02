# E502 | MOLA MEG004 paired real-data access gate (2 Nov 2026)

## Decisive question
Can the existing quality-gated MOLA reader ingest **actual** PDS-hosted, paired 4-pixels/degree Mars topography and observation-count rasters, instead of only synthetic labels or inferred access?

## Sources and representation
- Official NASA PDS Geosciences MEG004: https://pds-geosciences.wustl.edu/missions/mgs/megdr.html
- Topography: `megt90n000cb.img` and matching detached PDS3 label.
- Ground-return counts: `megc90n000cb.img` and matching label.
- Grid 720x1440, 4 ppd, signed big-endian 16-bit samples. Topography **metres above the MOLA areoid**; counts **shots/bin**. The reader rejects wrong dimensions, labels, projection, negative counts, wrong filenames, and mismatched binary lengths.
- The code downloads four allowlisted official-host files under strict byte limits and records SHA-256, counts, observed/interpolated fractions, and five 5x5 paired numeric tiles. No large raster is committed.

## Falsification criteria
- Any HTTP failure, unexpected redirect, size mismatch, label disagreement, or nonconforming binary fails closed. Preserve failure logs; do not replace data with synthetic examples.
- A successful exact-head CI artifact with source hashes and paired numeric tiles supports **real MOLA ingestion only**.
- A successful MOLA download plus E501 LOLA still does **not** establish physical cross-body comparability, independent site labels, or E001 recovery.

## Validation and claim boundary
The nine focused tests use deterministic mocked responses and row-major fixtures. They test bounds, redirect controls, allowlist, indexing and edge cases, **not real scientific data**. Real-data status depends on the Actions receipt.

**E001 known-site recovery: NOT YET MEASURED.** Cross-body similarity, novel analogue discovery, India field advantage, and challenge-selection superiority: NOT YET PROVEN.

## Next
If MOLA is acquired, reconcile PDS pixel-center coordinates, areoid versus lunar-radius datums and observed-only support; obtain an independently labelled Earth DEM analogue set and run E001 with random/Euclidean/physically weighted baselines, leave-one-site-out, ablations, nulls and uncertainty. If MOLA fails, diagnose exact PDS host/label failure and test a legitimate alternate PDS mirror without weakening provenance.

## E502 verified real-source result (2 Nov 2026)

Exact-code-head [GitHub Actions #41437637037](https://github.com/stoicsatvik/NASA/actions/runs/41437637037), commit `13bc12b799e7e7ca41ab6d5b47780b89c0ae7b52`, **SUCCESS**. The job passed **20/20** deterministic tests (9 new E502, 11 inherited MOLA) and downloaded four real official PDS files. Artifact `e502-mola-paired-numeric-receipt` ID `13138090009` was independently downloaded and parsed; not inferred from workflow status alone.

- Both 720×1440 signed 16-bit rasters: **2,073,600 bytes each**; source PDS labels 4,796 bytes topography and 3,066 bytes counts.
- Topography SHA-256: `25f16fb7aaf857898dcf98bc4f841341a24f8b9f7e98453ca083bc45d897ca2c`.
- Counts SHA-256: `7e920ec43497b4beddf974650471600c7afd4916e2a8dd3500d6b14714365661`.
- **1,027,663** cells with at least one ground-return count; **9,137** zero-count/interpolated cells (**0.88126929%**); observed fraction **99.11873071%**. This is a count-mask coverage statement, not measurement accuracy.
- Observed-cell topography extrema: **−8,068 m / +21,134 m** relative to the **Mars areoid**, not the lunar 1,737.4-km sphere.
- Five fixed paired 5×5 topography/count tiles are present in the verified artifact. They are pixel-index examples, not independent analogue labels.

**Updated claim:** real paired MOLA MEG004 topography/counts ingestion **SUPPORTED BY EXACT-HEAD CI AND RETRIEVED NUMERICAL RECEIPT**. Together with E501, real Moon and Mars gridded elevation access is now established. Earth DEM access, source-PDS LOLA equivalence, physically matched descriptors, held-out labels, E001 recovery, and any novel analogue or challenge superiority claim remain **NOT YET PROVEN / NOT YET MEASURED**.

**Next experiment:** acquire and register a legitimate Earth DEM, then compare physical-scale relief/roughness (not absolute elevation across unlike datums) at matched footprints, mask Mars zero-count cells, and run E001 leave-one-site-out against random/Euclidean/weighted controls. Do not spend this evidence window on UI polish.
