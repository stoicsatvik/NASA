# E530 — PAAD / MGD3 cross-body feature admissibility (2026-11-11)

## Question

Do the actual USGS PAAD and MGD3 records now support a leakage-resistant E001 known-analogue recovery experiment, or are there still missing labels and non-comparable descriptors?

## Source-pinned inputs

- PAAD v1, USGS data release DOI 10.5066/P9IFVZEX, 45 terrestrial dune-analogue sites. The source metadata describes bedform type, climate class, sand source/composition, coordinates, approximate elevation and approximate area.
- MGD3 2007, USGS Open-File Report 2007-1158, DOI 10.3133/ofr20071158. The exact-head E527 run acquired the official Shapefiles.zip and Tables.zip. The spatial layer contains 547 dune-field polygons and 547 unique Dune_IDs. Its Mars sinusoidal CRS uses a 3,396,190 m sphere; THEMIS IR source support is 100 m/pixel and the inventory is restricted to 65°N–65°S.
- MGD3 2018, USGS Open-File Report 2018-1164, DOI 10.3133/ofr20181164. The E528 workbook join contains 1,853 normalized rows. In the Equatorial workbook, 535 unique 2007 Dune_IDs match (535/547 = 97.81%); 12 2007 spatial IDs are not present in this workbook. The South Polar workbook is outside the 2007 layer's latitude range and is not treated as a failed join.

Source artifact receipts:
- PAAD workflow run 42902970540, head 7f767e36b875c72fb5d36aff556c4317eb4e1726, artifact 13804420438; archive SHA-256 404d938ec4d55e1bac4a6bb06d463434a4c7e2fdb291fca026fb8ef90bc2427e.
- MGD3 workflow run 42904750899, head 03300510d932128df58f64dc91bf04bd0825617f, artifact 13804087352; shapefile archive SHA-256 a43e8f842aa0e9b1edb920a2624a430ebf7fb6a059fc9c6f1ae37cc179635f34; tables archive SHA-256 9f2e7fe86f813cafcabf34587648e2d6d31a6207046a6d32fb2a98953c8cadb1; 2018 workbook SHA-256 92771c23cfa4a64dfcc38f5ad29de00adfa41b9f321d3665beb2112eefe3485e.
- Both downloaded workflow artifacts passed ZIP CRC checks and their downloaded SHA-256 values matched the GitHub artifact digests.

## Measured data audit

### PAAD

- 45 unique sites; no per-site target-body/family field and no non-analogue control labels.
- Missing: composition 16/45, approximate areal coverage 12/45, sand source 3/45, elevation 1/45.
- The metadata describes the first release as a subset of known analog dune fields, not a balanced Earth control population.

### MGD3

- 2007 layer: 547 polygons, 547 unique IDs; same-release table join was 547/547 with no duplicate IDs.
- 2018 Equatorial workbook: 956 worksheet rows, 691 matched rows, 535 unique matched Dune_IDs.
- Stability Index: 787 rows, 786 unique IDs, one duplicate row, 535 matched rows.
- THEMIS ATI / TES dune-model sheet: 53 rows, 40 matched.
- Each Equatorial Global Summary sheet contains 58 unique IDs, all matched to the 2007 spatial layer. Thermal inertia and albedo are present for 58/58. Mineral composition is present for 42/58 in the “ocks <7000” sheet and 52/58 in the “all ocks” sheet.

## Taxonomy crosswalk and sensitivity

PAAD metadata defines 13 tokens. MGD3's codebook defines B=barchan, Bd=barchanoid, D=dome, L=linear, S=star, T=transverse, SS=sand sheet; U remains unmapped in this audit.

- Strict name/definition matches: S (star) and SS (sand sheet).
- Candidate, not yet admitted: L (PAAD longitudinal vs MGD3 linear).
- Rejected as ambiguous: B. PAAD combines barchan and barchanoid ridges, while MGD3 separates B and Bd.
- TR (transverse ridge) is not equated with T (transverse dune).

Coverage sensitivity across the 45 PAAD sites and 547 MGD3 fields:

| Crosswalk rule | PAAD sites covered | MGD3 fields covered |
|---|---:|---:|
| Strict S + SS only | 16/45 | 132/547 |
| Add candidate L | 20/45 | 152/547 |
| Naively include ambiguous B as well | 29/45 | 255/547 |

Naively accepting B inflates apparent coverage by 1.81× on PAAD and 1.93× on MGD3 relative to strict S/SS. This is a material ranking/coverage sensitivity, not evidence that the matched sites are physically analogous.

## Descriptor admissibility
The 2018 report limits its detailed thermal/compositional analysis to dune fields of 300 km² or larger. Therefore the 58 Global Summary IDs are a selected large-field subset, not a representative sample of all 547 MGD3 fields.



No directly shared quantitative physical feature is admitted from the current PAAD + MGD3 pair.

- Elevation exists in both tables in metres, but Earth sea-level / GMTED2010 or literature-derived values and Mars MOLA-based elevation do not share an absolute datum. At most, within-body normalized ranks can be tested.
- Area exists in both in km², but PAAD coverage is approximate literature/site coverage while MGD3 area is a THEMIS-derived polygon measurement with different spatial support and mapping rules.
- PAAD composition is heterogeneous prose; MGD3 composition is instrument-derived mineral abundance with errors. Do not parse the prose into false numeric values.
- PAAD climate class and sand-source narrative have no corresponding fields in MGD3.
- MGD3 thermal inertia, albedo, mineral abundance and stability are absent from PAAD.

## E001 decision

<badge>NOT READY</badge>

Do not run the E001 ranking on these tables. The current harness requires site_id, family, is_analog and numeric features. PAAD supplies neither target-body/family labels nor non-analogue controls. MGD3 is a Mars target/reference inventory, not an Earth negative-control population. Filling those fields by guessing or treating “not listed” as “not an analogue” would fabricate ground truth.

This is a decisive negative result: E527/E528 solved data access and ID linkage, but they did not solve label validity or physical descriptor comparability. E001 known-site recovery remains NOT YET MEASURED; cross-body similarity remains NOT YET PROVEN; novel analogue discovery remains NOT YET PROVEN.

## Validation

- E527 exact-head Actions run #42904750899 passed on commit 03300510d932128df58f64dc91bf04bd0825617f.
- Six E530 tests passed on an equivalent local harness. The committed branch test module was not executed in this runtime, and no E530 exact-head Actions run was triggered.
- Both downloaded source-artifact ZIPs passed CRC checks and matched their GitHub artifact SHA-256 digests.

## Next experiment

1. Ingest the separate public USGS 2020 “Known Terrestrial Analog Sites for Planetary Science” point layer as a candidate independent positive-site source. It is CC0, but it is not a negative-control set.
2. Find a defensible Earth non-analogue control population for the specific dune/aeolian task. Keep unlisted sites explicitly UNLABELLED until their status is sourced.
3. Derive Earth-side albedo / surface-temperature / terrain descriptors at PAAD and control sites from suitable NASA Earthdata products at documented physical support; preserve acquisition date, resolution, projection, missingness and provenance.
4. Reassess whether any physically comparable features survive; only then run random, Euclidean and physically weighted baselines with leave-one-site-out, ablations and false-positive inspection.

No field measurements, local validation advantage or novel discovery are claimed. No restricted-area access or destructive sampling is proposed.
