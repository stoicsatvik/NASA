"""E436: exact retrospective label-permutation audit of E430's three-site diagnostic.

Only six previously measured E214 Earth windows are used. Not E001, not a
planetary-analogue classifier, and not a prospective statistical test.
"""
from __future__ import annotations

from itertools import permutations
from pathlib import Path
import json
import math

FEATURES = (
    'plane_detrended_relief_std_m', 'slope_p50_dimensionless',
    'slope_p90_dimensionless', 'elevation_range_m',
)
SITES = ('lonar_lead', 'western_ghats_lead', 'ladakh_lead')
SOURCE = Path(__file__).parent / 'results/e214_earth_skadi_real_data_20261024.json'


def load(path: Path = SOURCE):
    raw = json.loads(path.read_text(encoding='utf-8'))
    if not str(raw.get('experiment', '')).startswith('E214 real Earth'):
        raise ValueError('Only the E214 source receipt is admissible')
    if len(raw.get('sites', [])) != 6:
        raise ValueError('Exactly six E214 windows required')
    indexed = {}
    for row in raw['sites']:
        key = (row['site'], row['physical_window_km'])
        if key in indexed or key[0] not in SITES or key[1] not in (2, 4):
            raise ValueError('Unexpected or repeated site/support')
        vals = tuple(float(row['metrics'][f]) for f in FEATURES)
        if any(not math.isfinite(v) or v <= 0 for v in vals):
            raise ValueError('Nonpositive or nonfinite feature')
        indexed[key] = vals
    if set(indexed) != {(s, k) for s in SITES for k in (2, 4)}:
        raise ValueError('Incomplete site/support pairing')
    return indexed


def predicted_indices(indexed, mode='pooled_z', omit=None):
    if mode not in ('pooled_z', 'catalog_z', 'other_sites_z', 'log_ratio'):
        raise ValueError('Invalid distance mode')
    if omit is not None and omit not in FEATURES:
        raise ValueError('Invalid feature omission')
    dims = tuple(i for i, name in enumerate(FEATURES) if name != omit)
    output = []
    for site in SITES:
        if mode == 'pooled_z':
            pool = list(indexed.values())
        elif mode == 'catalog_z':
            pool = [indexed[(s, 4)] for s in SITES]
        elif mode == 'other_sites_z':
            pool = [indexed[(s, 4)] for s in SITES if s != site]
        else:
            pool = []
        scales = {}
        for j in dims:
            if mode == 'log_ratio':
                continue
            avg = sum(v[j] for v in pool) / len(pool)
            sd = math.sqrt(sum((v[j] - avg) ** 2 for v in pool) / len(pool))
            if sd <= 0:
                raise ValueError('Zero feature scale')
            scales[j] = sd
        query = indexed[(site, 2)]
        def distance(candidate):
            target = indexed[(candidate, 4)]
            return math.sqrt(sum(
                (math.log(query[j] / target[j]) if mode == 'log_ratio'
                 else (query[j] - target[j]) / scales[j]) ** 2
                for j in dims
            ))
        output.append(min(range(len(SITES)), key=lambda i: (distance(SITES[i]), SITES[i])))
    return tuple(output)


def exact_label_null(predictions):
    """Permute the THREE candidate labels jointly, preserving prediction dependence."""
    if len(predictions) != 3 or any(type(p) is not int or p not in range(3) for p in predictions):
        raise ValueError('Three candidate indices required')
    counts = [sum(perm[predictions[i]] == i for i in range(3))
              for perm in permutations(range(3))]
    observed = sum(predictions[i] == i for i in range(3))
    return {'observed': observed, 'null_counts': counts,
            'tail_ge_observed': sum(x >= observed for x in counts) / len(counts)}


def audit(indexed):
    configs = [(mode, omit) for mode in
               ('pooled_z', 'catalog_z', 'other_sites_z', 'log_ratio')
               for omit in (None, *FEATURES)]
    predictions = {f'{mode}:{omit or "all"}': predicted_indices(indexed, mode, omit)
                   for mode, omit in configs}
    observed_best = max(sum(p[i] == i for i in range(3)) for p in predictions.values())
    # The same global permutation must be applied to every configuration.
    max_null = [max(sum(perm[p[i]] == i for i in range(3))
                    for p in predictions.values())
                for perm in permutations(range(3))]
    return {
        'schema': 'nasa/e436/retrospective-three-site-label-null/v1',
        'source': 'E214 real Mapzen Skadi SRTM-derived Earth summaries, six overlapping windows',
        'configurations': {k: {'predicted': [SITES[j] for j in p], **exact_label_null(p)}
                           for k, p in predictions.items()},
        'best_of_20': {'observed': observed_best, 'null_counts': max_null,
                       'tail_ge_observed': sum(x >= observed_best for x in max_null) / 6},
        'claim': 'EARTH-ONLY RETROSPECTIVE LABEL-EXCHANGEABILITY AUDIT; E001 NOT YET MEASURED',
        'limitations': [
            'Three preselected unvalidated Earth research leads; no Moon/Mars matched labels.',
            'The 2-km and 4-km patches overlap, so this is not independent held-out recovery.',
            'Candidate-label permutations are an artificial exchangeability null, not a geological sampling model.',
            'Twenty configurations were inspected retrospectively; best-of-20 null is descriptive, not prospective inference.',
            'Pooled z-scaling uses query and target rows; catalog-only and other-site variants audit that leakage.',
            'No new raw raster acquisition or physical instrument harmonization.'
        ]
    }


def main():
    print(json.dumps(audit(load()), indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
