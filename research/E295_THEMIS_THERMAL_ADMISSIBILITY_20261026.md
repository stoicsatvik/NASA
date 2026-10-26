# E295 | Reject visual THEMIS mosaics as quantitative Mars temperatures

**Date:** 2026-10-26. Pre-event research/data-admissibility falsification, not a Space Apps competition solution.

## Falsifiable question

Can the convenient Mars THEMIS global nighttime IR mosaic be treated as a calibrated numerical temperature layer and compared directly to the E291/E293 lunar Diviner STN temperature-deviation raster?

**No.** The USGS primary mosaic description explicitly says its values are a **visual representation**, with the original nighttime temperatures **stretched and blended** for seamless display. A brightness-looking pixel is not an instrument-calibrated Kelvin observation.

- USGS THEMIS nighttime mosaic: https://astrogeology.usgs.gov/search/map/mars_odyssey_themis_ir_night_60n60s_mosaic_100m_v14
- NASA PDS THEMIS IR-PBT catalog: https://data.nasa.gov/dataset/odyssey-themis-ir-pbt-v2-0
- PDS/ODE IR-PBT product specification: https://ode.rsl.wustl.edu/venus/pagehelp/Content/Missions_Instruments/Mars_Odyssey/THEMIS/ODTGEO/IR/IRPBT4.htm
- ASU THEMIS projection guidance: https://themis-data.mars.asu.edu/faq/what-map-projection-themis-images
- Lunar Diviner E291 source/units: https://github.com/stoicsatvik/NASA/pull/22

The physically meaningful alternative for a future experiment is an **individual calibrated, projected THEMIS IR-PBT scene**, with its original label, acquisition time, band, projection, footprint, scaling, quality mask and scene-specific context verified. This source was identified, **not downloaded or ingested** in E295. The NASA Open Data Portal catalog itself provides metadata, not image bytes.

## Decisive mathematical falsification (synthetic, not instrument data)

Consider a target of **245 K** and candidate sites A = **240 K** and B = **260 K**. Calibrated Kelvin distance ranks A nearer: **5 K versus 15 K**.

Apply the same strictly increasing, invertible piecewise-linear display stretch to all three values, using the anchors (240 K → 0), (245 K → 90), (260 K → 100). In display coordinates, A is 90 units from the target and B only 10 units. **The nearest-neighbor ranking reverses.**

This is a constructive proof that even a common monotone visual stretch need not preserve *distance-based* retrieval. It is **not** a reconstruction of the actual THEMIS mosaic stretch and does not claim that this reversal occurred in a real site comparison. Unknown spatially varying stretches and blends only make quantitative interpretation less defensible.

A separate semantic gate rejects directly comparing Diviner STN **nighttime rock-free regolith temperature deviations (K)** to THEMIS IR-PBT **brightness temperatures (K)**. Equal unit labels do not imply equal physical quantities. A complete hypothetical scene-metadata flag permits only a **within-product quantitative candidate**, never cross-body harmonization.

## Executed validation and boundaries

Run `python -m unittest discover -s tests -p 'test_e295_*.py' -v` and `python -m research.e295_thermal_product_admissibility`. Six deterministic tests check rank reversal, strict monotonicity, visual-source rejection, missing scene metadata, equal-unit/different-quantity rejection and conservative claim states.

**Supported:** USGS global mosaic is visualization-only by primary metadata. **Proven for the synthetic construction:** monotone display transforms can reverse distance-based ranking. **Not established:** calibrated THEMIS ingestion, Mars/Earth/Lunar thermal harmonization, analogue recovery or any new field measurement.

**Decision:** exclude visual THEMIS mosaics from quantitative thermal descriptors. Seek actual PDS IR-PBT observations, not prettier mosaics. E001 known-site recovery **NOT YET MEASURED**; cross-body similarity, novel discovery, local validation advantage and challenge-selection superiority **NOT YET PROVEN**. No raw planetary data, credentials, competition submission or fieldwork was produced in E295.
