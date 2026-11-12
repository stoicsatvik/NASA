# E575 — HiRISE control-source independence audit

Date: 12 November 2026  
Branch: research/e575-hirise-control-source-independence-audit-20261112  
Parent: E574 / PR #134

## Question

Do the published alignment numbers for the 2025 Mars Sample Return (MSR) HiRISE DTM provide an independent horizontal-control residual, or are they internal/CTX-relative consistency measures?

## Source facts

1. The USGS MSR product page reports individual-DEM horizontal alignment better than 0.9 m at the 99th percentile, individual-DEM vertical offsets below 2.3 m at the 99th percentile, and mosaic-to-CTX alignment below 6 m at the 93rd percentile and below 10.2 m at the 99th percentile. It also records 8 of 10 planned stereo pairs completed. Source: [USGS product page, DOI 10.5066/P13CPYYU](https://astrogeology.usgs.gov/search/map/mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic).

2. The LPSC 2025 paper describes the processing lineage: the stereo-pair images were horizontally aligned to each other, DEMs vertically aligned to MOLA shot data, a preliminary DEM rigidly aligned to the existing Mars 2020 CTX DEM, and the final mosaic affine-aligned to that CTX reference. The 10.2 m statistic is therefore **CTX-relative**, not an absolute geodetic accuracy estimate. Source: [Bland et al., LPSC 2025, abstract 1627](https://www.hou.usra.edu/meetings/lpsc2025/pdf/1627.pdf).

3. The same LPSC paper's 1 m-at-30th-percentile / 3 m-at-80th-percentile comparison between the MSR and Mars-2020 HiRISE mosaics is produced by ASP normalized cross-correlation between **orthoimages**. It is a relative image-mosaic alignment check, not an independent ground-control network or a DTM-to-ground-truth residual. The paper explicitly states that no formal inter-mosaic horizontal-alignment requirement existed.

4. USGS general HiRISE DTM guidance states that horizontal accuracy relative to MOLA PEDR is at best approximately 100 m because a MOLA shot spot is about 100 m across, with approximately ±1.3 m vertical accuracy. This is general product-family guidance, not a 2025 MSR product-specific residual. Source: [USGS HiRISE DTM Analysis Ready Data guidance](https://stac.astrogeology.usgs.gov/docs/data/mars/hirise_dtms/).

## Result

No independent horizontal-control residual for the pinned 2025 MSR DTM was found in the public sources reviewed.

- 0.9 m: internal alignment between individual DEMs.
- 10.2 m: 99th-percentile alignment relative to CTX.
- 1 m / 3 m: relative alignment between HiRISE orthoimage mosaics, measured by image correlation.
- ~100 m: general best-case horizontal-accuracy guidance relative to MOLA PEDR, not a specific 2025 measurement.

The 10.2 m translation grid used by E573/E574 remains a legitimate sensitivity diagnostic for the CTX-relative statistic. It must not be described as an absolute horizontal-error bound or independent MOLA registration.

The paper also notes localized offsets correlated with dune fields, smooth texture and dark regions, with unresolved jitter or camera-model intrinsics as possible causes. This makes the local quality caveat especially relevant in aeolian terrain; it does not identify a cause or justify a correction.

## Claim states

- Repo operating system: **SUPPORTED**.
- 2025 HiRISE internal alignment: **SUPPORTED AS REPORTED**.
- 2025 HiRISE CTX-relative alignment: **SUPPORTED AS REPORTED**.
- Independent horizontal registration: **NOT YET MEASURED**.
- Absolute horizontal accuracy: **NOT ESTABLISHED**.
- Route safety: **NOT CLAIMED**.
- Cross-body similarity: **NOT YET PROVEN**.
- Known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery: **NOT YET PROVEN**.
- Planetary-analog challenge superiority: **NOT YET PROVEN**.

## Challenge-selection consequence

The latest all-14 screen and E541 factor ablations still place Martian Map #11 (4.10) and MODIS/VIIRS #9 (4.00) in the provisional top tier; planetary analog #10 remains at 2.93 and outside the top five. E575 does not change a frozen score factor, so it does not alter those scores. No challenge is locked. The planetary-analog thesis is not currently the leading readiness-ranked option.

## Next decisive gate

Acquire an independently controlled reference with documented control lineage, such as a held-out MOLA PEDR track set whose points were not used in the product control, or an independently controlled HRSC product. Measure multi-patch residuals and preserve the evaluation points as held out; do not fit a correction to the same points used for validation. If the required control lineage cannot be established, retain the NOT YET MEASURED claim and keep challenge selection conditional.
