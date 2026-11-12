# E576 — HRSC independent-control admissibility audit

Date: 2026-11-12  
Branch: `research/e576-hrsc-independent-control-admissibility-20261112`  
Parent: E575 / PR #135  
Question: Can Mars Express HRSC provide independent horizontal control with documented accuracy materially below the 10.2 m CTX-relative alignment statistic reported for the pinned 2025 HiRISE mosaic?

## Sources and observations

### Li & Jiang et al. (2023), Mars Express HRSC geometric calibration

[Open-access Earth and Space Science article](https://doi.org/10.1029/2023EA002971).

The calibration uses MOLA PEDR ground-control points. The article reports 476 MOLA GCPs in the calibration image, with 125,749 overlapping MOLA points across 126 tracks. It gives approximate MOLA planimetric accuracy of 100 m, footprint diameter 168 m and footprint spacing 300 m.

After calibration, the reported horizontal positional accuracy against MOLA GCP coordinates is:

| Image | Camera | Horizontal positional accuracy |
|---|---|---:|
| Calibration I864 | S1 | 145.31 m |
| Calibration I864 | S2 | 144.61 m |
| Validation I818 | S1 | 217.017 m |
| Validation I818 | S2 | 235.313 m |
| Validation I863 | S1 | 273.349 m |
| Validation I863 | S2 | 301.776 m |
| Validation I977 | S1 | 178.716 m |
| Validation I977 | S2 | 286.364 m |

The paper itself attributes the remaining planimetric limit to MOLA laser-point accuracy on the order of hundreds of metres. HRSC is an independent sensor family, but these absolute-positioning results are MOLA-controlled.

### Kirk et al. (2020), Jezero DTM quality comparison

[Open-access ISPRS paper](https://doi.org/10.5194/isprs-archives-XLIII-B3-2020-1129-2020).

This study uses a mosaicked HiRISE DTM as the reference for evaluating HRSC and CTX DTMs. It reports horizontal resolution estimates of 10–20 image pixels and typical DTM ground-sample spacing of 3–5 pixels. Those are resolution and relative-comparison results, not an independent absolute horizontal-control residual.

## Discriminating test

The current E575 next gate requires a separate control network or independently controlled product with documented horizontal uncertainty materially below 10.2 m. The 10.2 m number is itself a CTX-relative 99th-percentile alignment statistic, not an absolute-accuracy bound.

The best HRSC calibration value is 144.61 m, approximately 14.18 times 10.2 m as a scale comparison; the best validation value is 178.716 m. These ratios are **not formal uncertainty comparisons** because the underlying metrics differ. They are sufficient to reject HRSC as the requested 10 m-scale control source.

## Result

**NEGATIVE: HRSC does not clear the independent 10 m-scale horizontal-control gate.**

- HRSC is a separate instrument family.
- Its retrieved absolute-positioning evidence is tied to MOLA GCPs and remains on the order of hundreds of metres.
- The 2020 HRSC/CTX comparison uses HiRISE as its reference, so it cannot independently validate the HiRISE mosaic's absolute horizontal registration.
- HRSC remains useful for coarse cross-sensor comparison and gross-error screening, not 10 m-scale validation.

No new raster, coordinate sample, field measurement or control network was acquired. No route-safety or analogue-similarity claim follows.

## Claim state

- Repo operating system: **SUPPORTED**.
- Independent horizontal registration of the pinned 2025 HiRISE DTM: **NOT YET MEASURED**.
- Absolute horizontal accuracy: **NOT ESTABLISHED**.
- Cross-body similarity: **NOT YET PROVEN**.
- Known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Route safety: **NOT CLAIMED**.
- Planetary-analog challenge superiority: **NOT YET PROVEN**.

The challenge ranking remains provisional: Martian Map #11 = 4.10, MODIS/VIIRS #9 = 4.00, planetary analog #10 = 2.93. E576 changes no frozen score factor. No challenge is locked.

## Next move

Find a separate ground-control network or independently controlled product with documented horizontal uncertainty materially below 10.2 m and no shared CTX/HiRISE/MOLA control dependency. Retain HRSC only as a coarse independent-sensor cross-check.
