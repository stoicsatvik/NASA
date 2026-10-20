# FOUNDRY_STATE — NASA

Updated: 2026-10-05
Class: Tier A
Time horizon: NASA Space Apps Challenge, 14–15 Nov 2026
Working branch: `foundry/planetary-analog-v1`
Main objective: maximize uncertainty eliminated per run and converge on a scientifically defensible Space Apps entry.

## Current thesis

The leading candidate is the 2026 planetary-analog challenge: identify Earth environments analogous to Moon/Mars locations using open Earth + planetary datasets.

This is **NOT YET PROVEN** to be the best challenge.

## Claim state

- Repo operating system: SUPPORTED
- India/Maharashtra analogue literature leads: SUPPORTED as research leads, not as new discoveries
- Cross-body similarity model: NOT YET PROVEN
- Recovery of known analogue sites: NOT YET MEASURED
- Novel analogue discovery: NOT YET PROVEN
- Local field-validation advantage: NOT YET PROVEN
- Space Apps challenge-selection superiority: NOT YET PROVEN

## Highest-value frontier

Run `E001_KNOWN_ANALOG_RECOVERY` and the dataset-access spike before polishing UI.

Priority order:

1. verify ingestion of real LOLA / Diviner / MOLA / THEMIS / Earth datasets;
2. derive a small set of physically comparable descriptors;
3. reproduce/recover known analogue environments using transparent baselines;
4. perform ablations and uncertainty analysis;
5. try to falsify the current challenge ranking;
6. only then build the polished geospatial product.

## Evidence gate

No claim that the system can identify useful Moon/Mars analogues until:

- at least one real lunar and one real Martian dataset are ingested;
- at least one known Earth analogue is held out and ranked independently;
- a random/simple baseline is beaten;
- ranking stability is measured;
- feature ablations are reported;
- instrument/resolution mismatch is documented.

## Proprietary-evidence strategy

Potential moat:

```
public NASA/partner data
→ physically justified comparison
→ prediction
→ permitted/non-destructive local observation
→ prediction error
→ proprietary validation corpus
→ improved model
```

A field trip does not count as progress unless a measurement maps directly to a model feature or validation question.

## Highest-value missing capability

Recruit one teammate with real planetary geology / Earth science / remote sensing / GIS evidence.

Do not optimize for prestige, follower count, or "AI" labels.

## Active issues

- #1 map every 2026 challenge and attempt to falsify current ranking
- #2 run E001 known-analogue recovery
- #3 dataset-access spike
- #4 Maharashtra field-validation feasibility
- #5 recruit planetary science / remote-sensing teammate

## Hourly Foundry contract

When this stream is selected by the Unified Parallel Foundry:

1. inspect exact current branch/PR/issue state;
2. choose the single action with highest expected uncertainty reduction;
3. prefer experiments/data access/validation over presentation;
4. preserve negative/null results;
5. do not manufacture commits if no evidence changes;
6. keep raw large datasets out of Git unless justified;
7. do not merge to `main` autonomously;
8. update this state only when durable evidence or frontier changes.

## Stop / pivot conditions

Pivot away from the planetary-analog track if any of these becomes clear:

- required datasets cannot be accessed or meaningfully compared;
- known analogue recovery fails after reasonable physically motivated revisions;
- another 2026 challenge clearly dominates the scorecard;
- required domain expertise cannot be recruited and scientific validity remains weak;
- the only differentiator becomes UI/LLM orchestration.

## Next trigger

**Dataset access + known-analogue recovery.**

The next substantive run should reduce one of these uncertainties, not add another planning document.
