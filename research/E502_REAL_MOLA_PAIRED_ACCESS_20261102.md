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
