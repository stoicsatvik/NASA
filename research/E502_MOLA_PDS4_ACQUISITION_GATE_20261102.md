# E502 | PDS4 MOLA topography + observation-count acquisition gate (2 Nov 2026)

## Why this changes the evidence frontier
E501 obtained numerical LOLA, but a lunar grid is insufficient for a Moon/Mars/Earth comparison. NASA PDS Geosciences now maintains the MOLA MEGDR archive in a PDS4 bundle (migration announced 25 Aug 2026). Official 4-pixels-per-degree files include **separate topography and per-cell laser-shot counts**, allowing an explicit test of the error "finite gridded elevation implies direct observation."

Primary archive: https://pds-geosciences.wustl.edu/missions/mgs/megdr.html
PDS4 bundle: `urn:nasa:pds:mgs_mola_topography_derived`.
Products: `meg004/megt90n000cb.{xml,img}` and `meg004/megc90n000cb.{xml,img}`.
These are actual numerical source products, **not** color relief imagery.

## Executed validation
- Nine local deterministic Python unittest cases **PASS** using NumPy. Covers signed big-endian decoding, scale/offset, missing sentinel, wrong source identity, wrong dimensions, unsupported data types, short bytes, axis-order rejection, zero-shot gating and negative counts.
- Python compilation **PASS**.
- GitHub source/test blob identities match the executed local files exactly:
  - `research/e502_mola_pds4.py`: `b4e048d6b151de3c59f177525562ebc3ccc42d53`
  - `tests/test_e502_mola_pds4.py`: `b7991465d04cb974c8a2bddbf55d20e6027e7c4f`
- Remote workflow creation was blocked by a safety check. No alternate write path attempted. This execution environment cannot fetch the PDS4 binary directly. **No real MOLA numeric bytes were acquired or decoded in E502.**

## Discriminating predictions
If gridded finite topography includes interpolated cells, the number of finite elevation cells with **zero laser-shot count** should be nonzero. If every finite cell has positive count, this particular inference is not falsified. The code computes both and preserves five paired numeric patches, without assuming an answer.

The Martian topography is relative to the **areoid**, whereas the E501 lunar TIFF reports height relative to a **1,737.4 km reference radius**. Raw elevation values cannot be concatenated or treated as directly comparable.

## Claim states
- Official PDS4 source identities and separation of topography/count products: SUPPORTED BY PDS DOCUMENTATION.
- Deterministic parser and synthetic count-mask behavior: SUPPORTED LOCALLY.
- Real MOLA numerical ingestion, observation-mask prevalence: **NOT YET MEASURED**.
- E001 known-site recovery: **NOT YET MEASURED**.
- Cross-body similarity, novel analogue discovery, local validation advantage, challenge superiority: **NOT YET PROVEN**.

## Next
Run the existing source-exact E502 script in a permitted free compute environment with PDS4 network access, inspect both label and image SHA-256 receipts, and only then advance to Earth DEM registration and E001 leave-one-site-out comparisons. No submission, main merge, deployment, field data, spending or contact.
