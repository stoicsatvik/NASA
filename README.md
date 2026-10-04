# NASA

A research-to-build operating repository for the **2026 NASA International Space Apps Challenge**.

## Objective

Do not win by shipping the prettiest AI wrapper.

Win by finding a challenge where:

```
open space-agency data
+ hard scientific reasoning
+ proprietary/locally collected evidence
+ reproducible analysis
+ a sharp 48-hour product
= an entry that is difficult to imitate
```

The code is not the moat. The **evidence loop** is.

## Event constraints

- Event: NASA Space Apps Challenge 2026 — *The Next Frontier*
- Dates: **14–15 November 2026**
- Team: **maximum 6 participants**
- Submission closes: **15 November, 11:59 PM local time**
- Core input: open data from NASA and its Space Agency Partners
- For participants under 18, see the official participant terms before attending an in-person event.

Official sources:
- https://www.spaceappschallenge.org/2026/
- https://www.spaceappschallenge.org/legal/

## Selection function

Every candidate challenge is scored on:

```
S = 0.22 scientific_depth
  + 0.20 validation_strength
  + 0.18 proprietary_evidence_potential
  + 0.15 demo_quality
  + 0.10 local_access_advantage
  + 0.10 technical_fit
  + 0.05 execution_speed
```

Penalty:

```
S_final = S - cloneability_penalty - dependency_risk
```

A generic LLM/API layer gets almost no credit.

## Current high-leverage hypothesis

The strongest direction found so far is the 2026 challenge:

**Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars**

Why it is unusually interesting:

1. The challenge explicitly asks teams to combine open Earth, Moon and Mars data.
2. Planetary-analog research has real scientific precedent.
3. India contains scientifically discussed lunar/Martian analog environments.
4. Maharashtra has basaltic terrain and published work on lunar/Mars analogues, creating a possible local field-validation advantage.
5. A competitor can copy a web interface. They cannot instantly copy a carefully documented field-observation corpus, validation protocol and site-specific evidence.

This is a **working hypothesis**, not a locked challenge choice.

## Research tracks

### A. Planetary Analog Engine

Build a reproducible system that compares candidate Earth sites to Moon/Mars reference environments across:

- geology / lithology
- topography and slope
- surface roughness
- thermal behavior
- aridity / moisture
- spectral features
- elevation
- crater / volcanic morphology
- accessibility and operational constraints

The output should not merely be "AI says this looks like Mars." It should expose each comparison variable, source, uncertainty and score.

### B. India field-validation layer

Research candidate analog sites in India, then determine whether any can be safely and legally observed before the hackathon.

Initial literature leads:
- **Lonar crater, Maharashtra** — basalt-hosted impact crater with a long history in lunar/planetary analog research.
- **Deccan basalt / Western Ghats** — published work identifies Indian Deccan terrain in lunar/Martian analogue studies.
- **Ladakh** — recent astrobiology literature describes Mars-analogue characteristics.

No destructive sampling. Any field work must use permitted/public access and respect local/environmental rules.

### C. Proprietary evidence

If a viable local site is found, collect non-destructive observations such as:

- timestamped geotagged imagery
- repeat observations
- calibrated scale references
- surface-temperature measurements where practical
- weather/environment context
- terrain annotations
- field notes
- uncertainty / sensor metadata

This corpus becomes a validation asset rather than decorative media.

## Repository map

- `docs/CHALLENGE_SCORECARD.md` — decision framework and current candidates
- `docs/MOAT.md` — what counts as defensibility
- `docs/TEAM.md` — recruiting specification
- `research/INDIA_ANALOGS.md` — sourced India planetary-analogue leads
- `data/ground_truth_schema.csv` — proposed field-observation schema

## Immediate milestones

### Phase 0 — research
- map all 2026 challenges
- identify top 3 by the selection function
- validate required datasets and APIs
- find scientific literature for each
- identify failure modes and judging-story risk

### Phase 1 — evidence
- build a small reference dataset
- reproduce one published comparison
- validate one Earth candidate against one lunar/Martian reference site
- document uncertainty

### Phase 2 — product
- geospatial exploration interface
- transparent similarity scoring
- scientific evidence panel
- side-by-side Earth ↔ Moon/Mars comparisons
- reproducible notebook/pipeline

### Phase 3 — hackathon
- compress the strongest research into a polished submission
- prioritize validity, impact, clarity and a memorable demo

## Rule

**Never add AI because the pitch sounds emptier without it.**

AI is allowed to accelerate retrieval, coding, feature extraction or analysis. Every model-derived claim that matters must be traceable to data or independently validated.
