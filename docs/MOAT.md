# Moat: what AI cannot cheaply regenerate

## Core thesis

Code is leverage. Code is not necessarily defensibility.

A useful test:

> If a competent competitor sees the demo tonight and has frontier AI coding tools, what do they still lack next month?

If the answer is "nothing", there is no moat.

## Defensibility ladder

### Weak
- prompt engineering
- standard RAG
- generic chatbot
- common public API integration
- polished frontend
- generic classifier
- unvalidated model output

### Medium
- unusual domain workflow
- hard data engineering
- reproducible scientific pipeline
- expert-created labels
- trusted evaluation set
- integrations that create switching costs

### Strong
- longitudinal proprietary observations
- repeated physical measurements
- hard-to-access domain relationships
- instrument/sensor deployment
- experimentally validated datasets
- cumulative feedback loops
- network effects
- regulated/certified operational position

## The evidence flywheel

```
public data
   ↓
hypothesis/model
   ↓
prediction
   ↓
physical or expert validation
   ↓
error analysis
   ↓
new proprietary evidence
   ↓
better model
   └──────────────↺
```

The important asset is the growing **prediction → observation → error** history.

## Rules for this repo

1. Every important metric needs units.
2. Every important claim needs a source or measurement.
3. Every similarity score exposes its component variables.
4. Model output is not ground truth.
5. Never hide missing data behind a confidence-looking number.
6. Preserve failed hypotheses and negative results.
7. Record provenance for every dataset.
8. Prefer a smaller validated system to a giant unverifiable one.
9. Do not collect protected geological/biological samples without explicit authorization.
10. Field work should default to non-destructive observation.

## Moat score

For any proposed feature:

```
M = R × T × A × V
```

where:

- **R** = reproduction cost
- **T** = time accumulation
- **A** = access asymmetry
- **V** = validation value

If any factor is approximately zero, ask whether the "moat" is merely a feature wearing a suit.
