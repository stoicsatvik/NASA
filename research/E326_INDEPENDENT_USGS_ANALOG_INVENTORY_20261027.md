# E326 | Independent 2020 USGS terrestrial analogue inventory

**27 October 2026. Claim: PUBLIC SOURCE INGESTION SUPPORTED. Dune analogue validation NOT SUPPORTED by this source.**

## Falsifiable question

Can the USGS *Known Terrestrial Analog Sites for Planetary Science* release (Hunter, 2020; DOI [10.5066/P9J72921](https://doi.org/10.5066/P9J72921)) provide independently catalogued terrestrial analogue positives for the existing PAAD dune recovery stream?

## Direct source result

- ScienceBase item: `5f88940b82cebb8c13d912ee`.
- The item metadata exposes **no downloadable tabular files**. Initial CI #40482005252 therefore produced zero ingested rows, a real access-path negative.
- The metadata instead exposes a USGS-associated ArcGIS REST FeatureServer. The public metadata's link contains a query credential. The code **strips the query string entirely** and requests only anonymous public feature access; no token is used, stored, or printed in final receipt.
- Exact-head [CI #40482249632](https://github.com/stoicsatvik/NASA/actions/runs/40482249632) SUCCESS: **16 source/integrity tests passed** and **4 actual feature rows** were retrieved anonymously from layer 0. [Receipt artifact](https://github.com/stoicsatvik/NASA/actions/runs/40482249632/artifacts/12723207792) (verified against Actions API).
- Source-reported schema: `AnalogBody`, `AnalogType`, `FID`, `Lat`, `Lon`, `Name`.
- `AnalogType`: **Volcanic 4/4**. `AnalogBody`: three empty and one null-like value. Geometry present 4/4, but coordinate accuracy was not independently verified.
- **No independently catalogued dune positive or negative** was observed in these four records. The 2020 source cannot validate the 45-site 2023 PAAD dune model under the tested criteria.

## Interpretation

This is a useful negative result: a published dataset title and a working public API are insufficient evidence of a scientifically relevant validation cohort. The four catalogued volcanic entries may inform a *different* volcanic-analogue track, but cannot be promoted to Mars/Moon matched positives or negatives. Both sources are USGS-related, so even an apparent overlap would not automatically be statistically independent.

**E001 known-site recovery: NOT YET MEASURED. Cross-body similarity: NOT YET PROVEN.**

## Reproduction

```bash
python -m pip install pytest pyshp
python -m pytest -q tests/test_e326_independent_terrestrial_analogs.py tests/test_e317_paad_independent_source.py
python -m research.e326_independent_terrestrial_analogs --output e326_inventory_receipt.json
```

The script enforces source identity, exact public ArcGIS service path, no embedded query credentials, bounded downloads/pagination, and explicit claim limitations. Source bytes are not committed.

## Highest-EV next step

Do **not** build a dune classifier using these four volcanic records. Obtain independently defined Earth/Mars dune morphology and true negative controls from published catalogues, or pivot to a volcanic/crater challenge if the official 28 October full challenge statements and stronger matched data justify it. NASA competition solution development remains subject to event rules.
