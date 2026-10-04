# India Planetary-Analog Research Map

This file contains **research leads**, not conclusions. Every candidate must survive dataset and field-validation checks.

## Why India may matter

The 2026 Space Apps analog-location challenge asks teams to identify and characterize Earth environments that resemble potential Moon/Mars locations using open Earth and planetary data.

India contains multiple environments already discussed in planetary-analogue literature. That creates a plausible route from public satellite data to **locally verifiable evidence**.

---

## 1. Lonar impact crater, Maharashtra

### Evidence lead

NASA Technical Reports Server contains a 1992 conference paper describing Lonar as an impact crater in Deccan Trap basalt and discussing it as a close lunar-crater analogue.

Source:
https://ntrs.nasa.gov/citations/19930000980

### Why investigate

- basalt target rock;
- impact morphology;
- historical planetary-science interest;
- within Maharashtra.

### Questions

- Which modern remote-sensing products characterize the crater best?
- Which lunar crater properties are scientifically comparable?
- What has changed in the scientific interpretation since the older paper?
- Can morphology be compared quantitatively using DEM-derived metrics?
- What observations can be made legally/non-destructively?

---

## 2. Deccan basalt / Western Ghats

### Evidence lead A — Indian-subcontinent Mars analogues

A 2022 *Icarus* paper discusses terrestrial Martian analogues from the Indian subcontinent, including **Deccan Trappean terrain in the Western Ghats**, and compares geomorphic/fluvial features with Martian terrain.

Source:
https://www.sciencedirect.com/science/article/abs/pii/S0019103522002251

### Evidence lead B — lunar basalt spectral analogues near Mumbai

A planetary-science paper on reflectance spectra of analogue basalts reports using Deccan basalt from India as a lunar mare-basalt analogue and describes field/lab work at sites including **Pathanpada, Yeoor, Gaibunder and Panvel** near Mumbai.

Source:
https://www.sciencedirect.com/science/article/abs/pii/S0032063309001792

### Why investigate

This is potentially the highest-access research lead because it connects:
- relevant geology;
- published planetary analogue work;
- remote sensing;
- locations in the Mumbai region.

### Hard rule

No rock collection or protected-area activity is assumed or planned. Any validation should default to public/permitted, non-destructive observation unless proper permission exists.

### Questions

- Can current multispectral data distinguish relevant basalt units?
- What surface/spectral variables were used in the literature?
- Are any suitable sites observable from public/permitted locations?
- Can ground photographs + simple environmental measurements validate satellite-derived features?
- Can we reconstruct the original spectral comparison with modern open datasets?

---

## 3. Ladakh

### Evidence lead

A 2024 *Planetary and Space Science* paper studies rock varnish from Ladakh as a Mars-analogue field setting, emphasizing the cold/dry environment, UV exposure and mineralogical/biogeochemical interest.

Source:
https://www.sciencedirect.com/science/article/abs/pii/S0032063324000965

### Why investigate

- strong scientific precedent;
- extreme environment;
- possible astrobiology relevance.

### Limitation

Low near-term access. Treat as a literature/reference candidate unless the team gains legitimate local collaborators.

---

## 4. NASA analog methodology reference

NASA's BASALT program used basalt-rich volcanic terrain on Earth as analog environments for Mars, combining geology/biology with operational field research.

Sources:
- https://www.nasa.gov/general/about-basalt/
- https://www.nasa.gov/missions/analog-field-testing/what-is-basalt/
- https://science.nasa.gov/solar-system/analog-explorer/

This is useful methodologically: an analog is not selected because it "looks Mars-like." The comparison must be tied to physical/geological properties and the intended mission question.

---

## 5. ISRO / PRL research alignment

ISRO's published research-area material includes planetary-analogue studies, noting the value of terrestrial sites for understanding processes on Mars and the Moon and validating orbital observations.

Source:
https://www.isro.gov.in/media_isro/pdf/programme/Research_Areas_Space_Doc2025.pdf

## Candidate experiment

### Hypothesis

A transparent multi-variable pipeline can recover known Indian planetary-analog sites from open data **without being manually told their identities**, then generate ranked new candidates.

### Test

1. Define Moon/Mars reference environment.
2. Define physically meaningful variables.
3. Train/calibrate on known global analog sites.
4. Search Earth globally or regionally.
5. Hide known Indian analog labels.
6. Check whether known sites rank highly.
7. Perform sensitivity/ablation analysis.
8. Field-validate a safely accessible candidate if feasible.

If known analogs do not emerge, investigate why. Do not massage weights until they do.

## Potential differentiator

The strongest version is not:

> "Here is a map of places that look like Mars."

It is:

> "Here is a reproducible search system, calibrated against known analog sites, with uncertainty and ablation tests, plus independent observations from a candidate environment."

That difference is basically the difference between a science project and a map wearing NASA stickers.
