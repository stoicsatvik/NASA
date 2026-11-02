# E514 | Real MOLA-to-Earth equal nominal physical footprint

Date: 2026-11-03. **E001 known-site recovery NOT YET MEASURED.**

## Decisive question

E513 found that same-sized 5×5 Martian and terrestrial arrays cover north-south
spans differing by **31.921×**. Does resampling real Earth ETOPO2022
elevation into the nominal physical cell support of MOLA change the descriptive
Earth-candidate ranking? Does the resulting ranking require spatial morphology?

## Real source-backed experiment

At each of five MOLA registered sample latitudes (+67.375°, +44.875°,
−0.125°, −45.125°, −67.625°), calculate the nominal north-south
MOLA cell size (~14.789 km) and longitude-dependent east-west size.
Area-average all valid NOAA ETOPO2022 15-arcsecond pixel centres inside
the corresponding rectangles around each of three frozen Earth candidate
locations. Reject clipped Earth windows and any MOLA zero-shot cell.
Compare datum-offset-invariant 5×5 relief and median absolute gradient.
Do not concatenate absolute Mars-areoid and Earth-datum elevations.

**Official source hashes from exact-head numerical receipt:**

- NOAA ETOPO N30E075 SHA-256:
  `cbb763175d331ed0222da35f357d3837aa8218aeda72e586974ef2a53f9027d4`
- NASA PDS MOLA topography:
  `25f16fb7aaf857898dcf98bc4f841341a24f8b9f7e98453ca083bc45d897ca2c`
- NASA PDS MOLA shot counts:
  `7e920ec43497b4beddf974650471600c7afd4916e2a8dd3500d6b14714365661`

E514 receipt raw JSON SHA-256:
`e7d161f812336aef71bd4eac759e6a09437ea9db73a20340ba342bc5d60aff2b`

## Observed result (real numerical data)

| MOLA sample | E513 raw-pixel nearest | E514 matched-support nearest | 500 spatial-null rank retention |
|---|---|---|---:|
| 0 (+67.375°) | Northern control | Lonar candidate | 17.4% |
| 1 (+44.875°) | Northern control | Lonar candidate | 100.0% |
| 2 (−0.125°) | Deccan control | Deccan control | 100.0% |
| 3 (−45.125°) | Lonar candidate | Deccan control | 100.0% |
| 4 (−67.625°) | Deccan control | Deccan control | 100.0% |

**3/5 nearest-candidate rankings changed** after nominal physical-support
matching. **4/5 rankings survived all 500 within-target spatial permutations**,
which preserve the elevation histogram but destroy adjacency. This is strong
evidence that the present two-descriptor ranking is often driven by
distribution/scale rather than informative spatial morphology.

The five targets are not independent known-analogue validation examples;
three Earth locations are **unverified research candidates**, not known
positives/negatives. The 2,500 permutations are repeated tests of five frozen
patches, not 2,500 independent field observations.

## Validation and limits

- Six synthetic tests passed in exact-head GitHub Actions.
- Real official NOAA + NASA PDS downloads, metadata gates, numerical
  comparison and artifact upload succeeded on head
  `9bed04569c4bc9bfd514265d4d302210259e2fcb`:
  https://github.com/stoicsatvik/NASA/actions/runs/41529678394
- Numerical artifact:
  https://github.com/stoicsatvik/NASA/actions/runs/41529678394/artifacts/13181097179
- Local independent readback verified source hashes, all five ranks,
  500-per-target null fractions and the receipt SHA-256.

**SUPPORTED:** real nominal physical-support Earth DEM aggregation and
ranking sensitivity for five MOLA patches.

**REJECTED for these samples:** raw 5×5 pixel ranking is invariant to
physical-support correction; current rankings necessarily depend on spatial
morphology.

**NOT YET PROVEN:** instrument-response comparability, cross-body
similarity, known-analogue recovery, novel analogue discovery, local field
advantage or challenge-selection superiority.

MOLA point/interpolated gridded elevations are not equivalent to Earth
area-averaged elevations. Local spherical/equirectangular geometry, shot
count limitations, unequal resolution/uncertainty and lack of independent
labels remain. No new field data, UI or competition submission.

## Next experiment

Stop tuning these three unlabelled Earth candidates. Acquire
**independently sourced known analogue/non-analogue site labels** and
georegistered planetary reference regions, predefine hard negatives, then
run E001 with random, histogram-only and physically weighted baselines,
leave-one-site-out evaluation, ablations and false-positive inspection.
If morphology-sensitive performance does not beat histogram-only nulls,
pivot or narrow the thesis.
