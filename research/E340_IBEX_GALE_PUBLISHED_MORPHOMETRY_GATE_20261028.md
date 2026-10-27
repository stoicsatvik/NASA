# E340 | Published Ibex–Gale analogue: raw wavelength equality falsified

**28 October 2026 | Independent scientific literature audit, not a Space Apps submission.**

## Decision question

Does a newly published, directly measured Earth–Mars morphological analogue pair support comparing raw ripple wavelengths as though the two planetary environments should have equal metre-scale values?

**No for the published exemplar means.** The independent 2026 accepted manuscript reports an average large-ripple wavelength of **0.71 m on Earth** (Ibex Dune Field, Death Valley) and **2.20 m on Mars** (two Gale crater case-study locations). The reported Mars/Earth ratio is **3.09859155**, with an absolute difference of **1.49 m**. The authors explicitly discuss longer Martian wavelengths due to lower atmospheric density while describing similarities in ripple heights and coarse-grain armoring. This is not evidence that the sites are identical.

## Primary evidence and measurement provenance

- Bretzfelder, J. M., et al. (2026), *The Ibex Dune Field of Death Valley National Park, California: Characterization and Assessment for Use as a Martian Analog*, *Aeolian Research* 75, DOI [10.1016/j.aeolia.2026.101032](https://doi.org/10.1016/j.aeolia.2026.101032).
- NASA Technical Reports Server [record 20260000452](https://ntrs.nasa.gov/citations/20260000452); [public accepted manuscript PDF](https://ntrs.nasa.gov/api/citations/20260000452/downloads/Bretzfelder_IbexDunes_finalsubmit_Jan142026.pdf).
- PDF section 3.5: KNaCK LiDAR/SLAM Earth field measurements, reported **±2 cm measurement confidence** after checking against objects of known dimensions; **3–32 ripples per terrestrial field** were averaged.
- PDF section 3.6: Mars comparison uses **two individual bedforms** measured from Curiosity Navcam stereo case-study images at **Gale crater sols 706 and 1788**. These are not matched samples or a statistically representative Mars cohort.
- PDF section 4.1.3: reported **0.71 m Earth** and **2.20 m Mars** average wavelengths; comparable heights but non-equal wavelength; atmospheric-density differences are discussed.
- The study was published in March 2026 and describes pre-existing measurements. **No field observations or instrument measurements were made by the Foundry.** Ibex lies within a protected wilderness; no field access is proposed.

## Frozen arithmetic and adversarial uncertainty check

Run `python research/e340_ibex_gale_literature_gate.py` and `python -m unittest tests.test_e340_ibex_gale_literature_gate`.

| Quantity | Value | Interpretation |
|---|---:|---|
| Earth reported mean wavelength | 0.71 m | Authors' field-average summary |
| Mars reported mean wavelength | 2.20 m | Authors' two selected rover case studies |
| Mars minus Earth | 1.49 m | Difference of reported means, **not** estimated population effect |
| Mars / Earth | 3.09859155 | Arithmetic ratio, not a universal scaling law |
| Conditional ratio at Earth 0.71±0.02 m | 3.01369863 to 3.18840580 | Illustrative instrument-tolerance perturbation, **NOT** a confidence interval |

**Uncertainty caveat:** ±2 cm applies to the source's terrestrial LiDAR measurement confidence, not to a confidence interval for the Earth mean. The Mars mean's uncertainty is not reported here; no cross-body significance test or confidence interval is justified. Rounding and selection effects are not estimated. The conditional ratio interval holds the reported Mars value fixed and must never be marketed as a scientific uncertainty band.

## Discriminating predictions / implications

1. A representation that treats *equal raw wavelength in metres* as a necessary condition for a legitimate morphologic analogue would reject this source-supported analogue example. **Raw equality is rejected for these reported exemplar means.**
2. A representation that explicitly models atmospheric regime and bedform scale could retain the pair, but **that prediction has not been measured**. Merely normalizing by wavelength is not a validated physical transfer function.
3. Height, wavelength, grain-armoring, substrate exposure, environmental regime and acquisition resolution must remain distinct features with instrument-specific provenance. The paper's own Mars and Earth sampling protocols are not interchangeable.
4. The source is a **positive scientific case study**, not a blinded, independent positive/negative Earth-site benchmark. It cannot be treated as E001 recovery or as a new analogue discovery. Its known identity would leak if used as a held-out recovery target after inspecting it.

## Claims and next evidence gate

- Published paired-example raw-wavelength equality: **REJECTED** under the source-reported means.
- Source-supported morphological analogue *case study*: **SUPPORTED AS PUBLISHED LITERATURE**, not independently reproduced.
- Cross-body retrieval/similarity generalization: **NOT YET PROVEN**.
- E001 known-site recovery: **NOT YET MEASURED**.
- Novel analogue discovery / local validation advantage / challenge-selection superiority: **NOT YET PROVEN**.

**Next:** Seek independent *unseen* matched-site morphology records with source-reported per-site heights, wavelengths, sampling uncertainty and true controls; freeze feature mapping before labels are revealed. Do not substitute this already-read pair for a holdout. Continue full 2026 challenge-statement comparison when official resources are accessible. No competition-specific solution code, submission, outreach, fieldwork or deployment.
