# E001 — Known Analog Recovery

## Question

Can a transparent, physically motivated Earth↔planet similarity pipeline recover known planetary analog environments **without manually rewarding their identities**?

## Why this is first

Before searching for novel analogs, the system must demonstrate that its representation has scientific signal.

A model that cannot recover known analogues should not be trusted to discover new ones.

## Null hypothesis

The proposed feature space and scoring method do not rank established analog environments above arbitrary comparison sites better than chance / simple baselines.

## Reference families

Start with NASA-documented analog categories such as:
- basalt landscapes;
- impact/crater environments;
- arid Mars-like terrain;
- lava caves;
- subsurface-ice analogues.

NASA Analog Explorer:
https://science.nasa.gov/solar-system/analog-explorer/

## Candidate feature families

Do not use all blindly. Each requires a physical justification.

### Terrain
- elevation
- slope
- roughness
- local relief
- curvature
- drainage density
- crater/landform descriptors

### Surface / spectral
- reflectance bands
- band ratios tied to mineral/surface behavior
- albedo proxies
- thermal inertia proxies if defensible

### Environment
- temperature statistics
- precipitation/aridity
- humidity where appropriate
- freeze/thaw behavior
- snow/ice persistence

### Geology
- lithology class
- volcanic / sedimentary / impact context
- substrate age where usable

## Baselines

At minimum compare:

1. random ranking;
2. standardized Euclidean distance;
3. cosine similarity;
4. physically weighted distance;
5. learned metric only if enough defensible labelled examples exist.

Do not start with a black-box neural network. If a simple method wins, civilization survives another dashboard.

## Validation

Use leave-one-site-out tests.

For each known analog:
1. remove its identity/label from calibration;
2. compute its feature representation;
3. rank candidate Earth sites;
4. record percentile/rank;
5. inspect failure modes.

Metrics:
- top-k recovery rate;
- median percentile rank;
- rank stability under feature ablation;
- sensitivity to measurement uncertainty;
- false-positive characteristics.

## Ablations

Remove one feature family at a time:
- terrain;
- surface/spectral;
- climate/environment;
- geology.

If score barely changes after removing a supposedly important family, that family is not contributing much.

## India holdout test

Known Indian analog candidates from literature must be treated as holdouts when possible.

Question:
> Does the method independently surface Lonar / relevant Deccan or Ladakh environments at meaningful ranks?

A failure is useful evidence. Do not tune the weights on the same site and then call the recovery independent.

## Output

- reproducible notebook or script;
- feature provenance table;
- ranked candidates;
- uncertainty estimates;
- ablation table;
- map;
- documented failures.

## Success condition

Proceed to novel-site search only when the baseline demonstrates repeatable signal and the ranking is not dominated by one arbitrary feature.
