# E247 | Common 15-km-lag elevation contrast: an Earth-only falsification check

**Executed:** 2026-10-25. **Claim:** SUPPORTED only for two public Earth DEM research leads and a finite, deterministic sampling stress test. **Not** an Earth/Moon/Mars analogue recovery result.

## Question and preregistered alternative

E243 found 27/256 rank reversals at 2×2 for separately plane-detrended relief SD. A 2×2 plane residual has only one checkerboard mode. Does a descriptor with a physically interpretable *common separation distance* preserve the ordering of these two sites under the same sampling stress?

Use **RMS height differences between cells separated by half the 30-km footprint** in east-west and north-south directions (nominal 15-km lags). Compare combined RMS and two directional components. At 2×2 this uses only two horizontal and two vertical pairs. This is a **long-wavelength contrast/slope-sensitive descriptor, not a roughness measure**.

## Frozen inputs and design

- Western Ghats public Mapzen Skadi SRTM-derived N18E073 tile SHA-256: `73523b876c229607f421c529b8c91a5ed7dd9b504ba413064b5ab0fcb193361b`.
- Ladakh public Mapzen Skadi SRTM-derived N34E077 tile SHA-256: `9179642ad2f9ccd90266229b9e9d7c49044bda661ec731d0068879dd607f2c7c`.
- Both extracted using the same E243 30-km Earth windows and source-fingerprint gate.
- For 2×2, 4×4, 8×8 and 16×16, use 16 deterministic registration phases per site and **all 256 independent cross-site phase combinations**. Also report idealized block-mean rank.
- Compare each coarse site ordering against its own dense-grid reference. No tuning against observed reversals.

## Measured result

[Exact-head GitHub Actions 40162430995](https://github.com/stoicsatvik/NASA/actions/runs/40162430995) **SUCCESS** at commit `444ee04c173f0ba2150c0a14214a1534fd3f651d`. **74/74 deterministic tests passed**; real public tiles were downloaded, source SHA-256 gates passed, and a complete JSON numerical receipt was uploaded as [artifact 12587210698](https://github.com/stoicsatvik/NASA/actions/runs/40162430995/artifacts/12587210698).

| Descriptor | 2×2 reversed / 256 | 4×4 | 8×8 | 16×16 |
|---|---:|---:|---:|---:|
| Combined 15-km-lag RMS contrast | **0** | 0 | 0 | 0 |
| East-west 15-km-lag RMS contrast | **5** | 0 | 0 | 0 |
| North-south 15-km-lag RMS contrast | **0** | 0 | 0 | 0 |
| E243 separately detrended relief SD (comparison) | **27** | 0 | 0 | 0 |

The combined contrast preserved the two-site ranking in all enumerated registrations, **whereas the east-west component still reversed five times**. These are finite artificial scenario counts, **not empirical probabilities**, confidence intervals, or evidence of actual lunar/Martian instrument stability.

## Interpretation and negative controls

This experiment **rejects the proposition that every terrain descriptor must exhibit the same 2×2 ranking instability as plane-detrended relief SD**, for this pair of Earth sites and these phase registrations. It **does not establish** a universally stable or geologically discriminative descriptor.

A synthetic planar-gradient control produces a nonzero RMS contrast despite **zero local detrended roughness**. Thus the stable combined ranking may reflect broad topographic gradient, not transferable geology. Four height-difference pairs at 2×2 remain a fragile statistic. Nominal 15-km lag is only approximate because finite raster and coarse-grid cell positions differ. Neither point sampling nor idealized block averaging models LOLA/MOLA PSFs or acquisition.

The two sites are *research leads*, not validated positive/negative analogue labels. No independent lunar/Martian label, blinded recovery, field observation, or discovery is claimed.

**E001 known-site recovery: NOT YET MEASURED. Cross-body similarity: NOT YET PROVEN. Novel analogue discovery: NOT YET PROVEN. Local validation advantage: NOT YET PROVEN. Challenge-selection superiority: NOT YET PROVEN.**

## Next decision

Stop using 2×2 plane-detrended relief SD as a standalone similarity feature. Do **not** promote the 15-km contrast as a planetary analogue score on the basis of two Earth sites. The decisive next test is independently established geological positive/negative labels with physically matched multi-instrument features, blinded leave-one-site-out recovery, simple/random baselines and explicit instrument/registration uncertainty. Re-evaluate all official 2026 challenges after the full October 28 statements.
