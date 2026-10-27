# E319 — Falsifying a premature PAAD ↔ Mars dune-label join

**27 October 2026. Research only.** This is an evidence audit, not a competition solution or E001 analogue recovery.

## Question and preregistered decision rule

The real 45-site Earth [USGS PAAD catalog](https://doi.org/10.5066/P9IFVZEX) from E317 and the real Mars MGD3 thermal/mineral workbooks from E318 are not automatically comparable. Can their raw dune-type labels even be placed in a common, source-verified taxonomy?

Use the E317 frozen Earth CSV SHA-256 `5be67b4da584987d9ce5207f2ee3c90b5b3b5849469461847111eaab5aafcecd`. Read `Dune_Type` as a raw multi-valued text field; do not invent an expansion for abbreviations. Compare its **exact, case-sensitive tokens** against the independently published [Hayward et al. (2007) MGD3 Table 1](https://doi.org/10.1029/2007JE002943): SS, D, B, Bd, T, L, S, U. Preserve unknown codes, multiple labels, empty cells and source hash.

**Predeclared gate:** Even 100% string overlap does **not** pass semantic harmonization. That requires an independently verified PAAD codebook, a linked Martian morphology dataset (not merely the 2018 composition/thermal workbooks), comparable observation supports, independent known-positive/negative site identities and blinded held-out recovery. No class counts from Mars Table 1 are to be treated as independent sites. Unknown labels are never negatives.

## Reproducible test

```bash
python -m pytest -q tests/test_e319_paad_mars_codebook_overlap.py tests/test_e317_paad_independent_source.py
python -m research.e319_paad_mars_codebook_overlap --output e319_label_gate_receipt.json
```

The first command uses synthetic controls only. The second downloads the source-fingerprinted **real** PAAD CSV through the allowlisted USGS ScienceBase endpoint and produces a machine-readable evidence receipt. The CI artifact retains actual counts, unsupported raw tokens, and the negative interpretation.

## Claim boundary

- Earth PAAD site data ingestion: **SUPPORTED** by E317.
- Mars MGD3 2018 workbook ingestion: **SUPPORTED** by E318.
- Hayward 2007 Table 1 code definitions: **SOURCE-DOCUMENTED**.
- PAAD ↔ Mars lexical code overlap: **TO BE MEASURED BY E319 CI**.
- Semantic equivalence of source labels: **NOT ESTABLISHED**.
- E001 known-site recovery: **NOT YET MEASURED**.
- Cross-body similarity, novel discovery, local field advantage, challenge-selection superiority: **NOT YET PROVEN**.

**Next discriminating experiment:** obtain the official PAAD abbreviation definitions and an actual MGD3 dune-field morphology table with provenance and independent site identifiers. Audit the cross-source taxonomy before running any similarity or retrieval benchmark. The 2026 challenge ranking must be reassessed against all 14 complete official statements after October 28.

No fabricated field data, paid access, outreach, deployment, submission or main merge.
