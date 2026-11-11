# E541 — Challenge-selection leave-one-factor-out falsification (2026-11-11)

## Question

Is the provisional Martian Map lead robust, or is its 0.10-point lead over MODIS/VIIRS an artifact of assigning 20% weight to reuse of existing portfolio preparation?

## Frozen inputs

Source scorecard: `research/CHALLENGE_SELECTION_SCREEN_20261111.md`, based on all 14 listed 2026 challenge candidates.

Weights:

- Public-data readiness: 25%
- Measurable validation within the 48-hour event: 25%
- Reuse of current portfolio/preparation: 20%
- Technical differentiation: 15%
- Execution feasibility: 15%

The score difference below 0.25 is already defined as not meaningful. Scores are decision heuristics, not predictions of judging outcomes.

## Experiment

For each of the five factors, remove that factor entirely and renormalize the remaining weights to sum to 1. Rescore **all 14 challenges**, not just the two leaders.

### Top-five results

| Removed factor | Rank 1 | Rank 2 | Rank 3 | Rank 4 | Rank 5 |
|---|---|---|---|---|---|
| Public-data readiness | #11 Martian Map 4.133 | #9 MODIS/VIIRS 3.833 | #4 CLPS 3.800 | #2 Earth Trend 3.567 | #7 Field Shift 3.533 |
| Validation | #11 Martian Map 4.133 | #9 MODIS/VIIRS 3.833 | #4 CLPS 3.800 | #2 Earth Trend 3.733 | #7 Field Shift 3.533 |
| Portfolio reuse | #9 MODIS/VIIRS 4.125 | #11 Martian Map 4.000 | #2 Earth Trend 3.875 | #4 CLPS 3.813 | #1 Abandoned but Not Forgotten 3.469 |
| Technical differentiation | #11 Martian Map 4.206 | #9 MODIS/VIIRS 4.176 | #2 Earth Trend 4.029 | #4 CLPS 4.000 | #7 Field Shift 3.529 |
| Execution feasibility | #11 Martian Map 4.029 | #9 MODIS/VIIRS 4.000 | #4 CLPS 3.824 | #2 Earth Trend 3.765 | #7 Field Shift 3.618 |

### Direct leader comparison

| Removed factor | Martian Map #11 | MODIS/VIIRS #9 | Gap (#11 − #9) |
|---|---:|---:|---:|
| None (frozen scorecard) | 4.100 | 4.000 | +0.100 |
| Data | 4.133 | 3.833 | +0.300 |
| Validation | 4.133 | 3.833 | +0.300 |
| Reuse | 4.000 | 4.125 | −0.125 |
| Differentiation | 4.206 | 4.176 | +0.029 |
| Feasibility | 4.029 | 4.000 | +0.029 |

## Falsification result

- The Martian Map lead **does not survive removal of the portfolio-reuse factor**. MODIS/VIIRS moves ahead by 0.125.
- That 0.125 gap is still below the predeclared 0.25 meaningful-difference threshold. The two challenges remain a provisional top tier; neither is established as superior.
- Martian Map remains first under the other four single-factor removals, but its lead is only 0.029–0.300. The larger gaps occur only when data-readiness or validation is removed, which are core criteria and should not be discarded for this competition.
- No other challenge enters the top two under any single-factor ablation.
- The planetary-analog challenge (#10) does not enter the top five in any single-factor ablation. Its high reuse/differentiation cannot compensate for currently weak data readiness (2.0/5) and validation (1.5/5).

## What would change the planetary-analog ranking?

Under the frozen weights, challenge #10 currently scores 2.93:

`0.25·2.0 + 0.25·1.5 + 0.20·5.0 + 0.15·5.0 + 0.15·2.0 = 2.925`.

With reuse, differentiation and feasibility held fixed at their current scores, matching the MODIS/VIIRS 4.00 score requires:

`0.25·(Data + Validation) + 2.05 ≥ 4.00`

so `Data + Validation ≥ 7.8` (currently 3.5 combined). For example, data readiness 4.0 and measurable validation 3.8 would only just reach 4.0. Matching Martian Map's 4.10 requires `Data + Validation ≥ 8.2`.

This makes the missing evidence concrete: an independently sourced, physically comparable positive/negative site set and a successful held-out known-site recovery. Until then, challenge #10 remains a conditional research challenger, not the best-supported event choice.

## Official challenge-scope cross-check

- [Martian Map](https://www.spaceappschallenge.org/2026/challenges/interplanetary-survival-guide-martian-map/): an integrated layered view of a Mars location or route combining multiple NASA mission datasets. The brief does not require claiming that a route is safe; no route-safety claim should be made.
- [MODIS/VIIRS Hot Spots](https://www.spaceappschallenge.org/2026/challenges/modis-and-viirs-hot-spots/): harmonize active-fire hotspot records into a burning-activity calendar for a selected area.
- [Planetary analogs](https://www.spaceappschallenge.org/2026/challenges/permanent-moon-base-locations-and-mars/): identify and characterize new terrestrial analogs using open Earth, Moon and Mars data.

A partner-page cross-check lists 14 challenge titles and summaries: [2026 challenge list](https://spaceapps.conocimiento.gob.ar/). This is used as a title/brief cross-check; primary NASA challenge pages are linked above. Search-indexed team pages are incomplete and are not used as a crowding or judging-probability metric.

## Claim states and next experiment

- Challenge #11 is the best first-pass **portfolio-readiness** candidate under the frozen heuristic: SUPPORTED AS A PROVISIONAL TIE-BREAK, NOT PROVEN SUPERIOR.
- Challenge #9 is a genuine co-leader; it wins when reuse is excluded.
- Challenge #10 is NOT YET PROVEN as the best challenge; E001 known-site recovery remains NOT YET MEASURED.
- No challenge choice is locked and no competition submission is made.

**Next highest-information experiment:** test MOLA/CTX/HiRISE geometry, CRS registration and actual map coverage on one pinned Mars area. If the layered coverage/registration is insufficient, lower #11 and reassess #9. Do not spend time polishing a map before this evidence gate. Keep #9 as the alternative, but do not create NASA FIRMS credentials or rely on gated data without approval.

No new external dataset was ingested in E541. No E001 experiment, fieldwork, contact, paid API, deployment, merge or competition submission occurred.
