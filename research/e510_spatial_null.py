"""E510: spatial-shuffle negative control on E501/E502/E505 numeric patches.

Descriptive rank stability only. No known-site labels, no analogue recovery.
"""
import argparse
import hashlib
import json
import math
import random
from pathlib import Path
from statistics import median
from zipfile import ZipFile

EXPECTED = {
    'lola': '84b72b67c9ea81bbccf6d0c6a301579a33925cb009ef7801b9a2076ee14bf7ae',
    'mola': 'eaa499260b4d15899e4a28c609b71f300e8669d00201bdbe55c2591b4020072d',
    'earth': 'db8c94a161c392626459f4032a40a850007e3b42d9f971ad6fdf5cc9009c6476',
}
RADII_KM = {'lola': 1737.4, 'mola': 3389.5, 'earth': 6371.0}
DELTA_DEG = {'lola': .25, 'mola': .25, 'earth': 1 / 240}


def load(path, kind):
    path = Path(path)
    if path.suffix == '.zip':
        with ZipFile(path) as archive:
            names = [n for n in archive.namelist() if n.endswith('.json')]
            if len(names) != 1:
                raise ValueError('ZIP must contain exactly one JSON receipt')
            raw = archive.read(names[0])
    else:
        raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED[kind]:
        raise ValueError(f'{kind}: source receipt hash mismatch')
    return json.loads(raw)


def gradient(patch, body, latitude):
    if len(patch) != 5 or any(len(row) != 5 for row in patch):
        raise ValueError('5x5 patch required')
    if not 0 <= abs(latitude) < 90:
        raise ValueError('invalid latitude')
    north = RADII_KM[body] * 1000 * math.pi / 180 * DELTA_DEG[body]
    east = north * math.cos(math.radians(latitude))
    diffs = [abs(row[j + 1] - row[j]) / east for row in patch for j in range(4)]
    diffs += [abs(patch[i + 1][j] - patch[i][j]) / north for i in range(4) for j in range(5)]
    return median(diffs)


def shuffled(patch, rng):
    values = [v for row in patch for v in row]
    rng.shuffle(values)
    return [values[i * 5:(i + 1) * 5] for i in range(5)]


def nearest(value, candidates):
    return min(sorted(candidates), key=lambda n: abs(candidates[n] - value))


def audit(lola, mola, earth, repeats=2000, seed=20261102, latitudes=(0, 30, 60)):
    if repeats < 1:
        raise ValueError('repeats must be positive')
    sites = {name: (site['elevation_m'], site['center_lat_lon_deg'][0])
             for name, site in earth['sites'].items()}
    if len(sites) < 2:
        raise ValueError('need at least two Earth controls')
    targets = [('lola', i, [[1000 * v for v in row] for row in tile['values_km']])
               for i, tile in enumerate(lola['pixel_index_tiles'])]
    for i, tile in enumerate(mola['pixel_index_tiles']):
        if any(c <= 0 for row in tile['ground_return_counts'] for c in row):
            raise ValueError('zero-shot MOLA cell')
        targets.append(('mola', i, tile['topography_m']))
    result = {'claim': 'spatial permutation negative control, NOT known-analogue recovery',
              'source_receipt_sha256': EXPECTED, 'seed': seed, 'repeats': repeats,
              'latitudes_assumed_not_georegistered': list(latitudes), 'results': {}}
    for latitude in latitudes:
        rng = random.Random(seed)
        original_earth = {n: gradient(p, 'earth', lat) for n, (p, lat) in sites.items()}
        original_targets = [gradient(p, body, latitude) for body, _, p in targets]
        baseline = [nearest(x, original_earth) for x in original_targets]
        earth_only = [0] * len(targets)
        planet_only = [0] * len(targets)
        both = [0] * len(targets)
        for _ in range(repeats):
            shuffled_earth = {n: gradient(shuffled(p, rng), 'earth', lat)
                              for n, (p, lat) in sites.items()}
            for j, (body, _, patch) in enumerate(targets):
                shuffled_target = gradient(shuffled(patch, rng), body, latitude)
                earth_only[j] += nearest(original_targets[j], shuffled_earth) == baseline[j]
                planet_only[j] += nearest(shuffled_target, original_earth) == baseline[j]
                both[j] += nearest(shuffled_target, shuffled_earth) == baseline[j]
        total = repeats * len(targets)
        result['results'][str(latitude)] = {
            'baseline_nearest': [{'body': body, 'index': idx, 'earth_choice': baseline[j]}
                                 for j, (body, idx, _) in enumerate(targets)],
            'earth_only_retained': earth_only,
            'planet_only_retained': planet_only,
            'both_retained': both,
            'earth_only_retention_fraction': sum(earth_only) / total,
            'planet_only_retention_fraction': sum(planet_only) / total,
            'both_retention_fraction': sum(both) / total,
        }
    result['limitations'] = [
        'No independent analogue labels; these are rank-stability diagnostics only',
        'Shuffling destroys spatial adjacency but preserves 25 elevation values per patch',
        '5x5 Earth/Moon/Mars patches cover unequal physical footprints',
        'Planetary latitude and orientation not independently georegistered',
        'No formal p-value or inference of morphological signal from retention rates',
    ]
    return result


def main():
    p = argparse.ArgumentParser()
    for name in EXPECTED:
        p.add_argument('--' + name, required=True)
    p.add_argument('--repeats', type=int, default=2000)
    p.add_argument('--seed', type=int, default=20261102)
    a = p.parse_args()
    print(json.dumps(audit(*(load(getattr(a, n), n) for n in EXPECTED),
                           repeats=a.repeats, seed=a.seed), sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
