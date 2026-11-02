"""E506: descriptive cross-grid pixel-scale confound audit, NOT analogue recovery.

Run with three pinned, prior-CI numerical receipts (JSON or ZIP). No network,
no inferred lunar/Martian georegistration, and no analogue ground truth.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
from statistics import median
from zipfile import ZipFile

EXPECTED = {
    'lola': '84b72b67c9ea81bbccf6d0c6a301579a33925cb009ef7801b9a2076ee14bf7ae',
    'mola': 'eaa499260b4d15899e4a28c609b71f300e8669d00201bdbe55c2591b4020072d',
    'earth': 'db8c94a161c392626459f4032a40a850007e3b42d9f971ad6fdf5cc9009c6476',
}
RADII_KM = {'lola': 1737.4, 'mola': 3389.5, 'earth': 6371.0}
DELTA_DEG = {'lola': 0.25, 'mola': 0.25, 'earth': 1 / 240}


def load_receipt(path, name):
    path = Path(path)
    if path.suffix == '.zip':
        with ZipFile(path) as archive:
            members = [m for m in archive.namelist() if m.endswith('.json')]
            if len(members) != 1:
                raise ValueError('expected exactly one JSON in ZIP')
            raw = archive.read(members[0])
    else:
        raw = path.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED[name]:
        raise ValueError(f'{name}: receipt SHA mismatch {sha}')
    return json.loads(raw)


def features(values_m, body, latitude_deg):
    if len(values_m) != 5 or any(len(row) != 5 for row in values_m):
        raise ValueError('expected 5x5 numeric patch')
    if not 0 <= abs(latitude_deg) < 90:
        raise ValueError('latitude out of scope')
    dx = [abs(row[j + 1] - row[j]) for row in values_m for j in range(4)]
    dy = [abs(values_m[i + 1][j] - values_m[i][j]) for i in range(4) for j in range(5)]
    north_m = RADII_KM[body] * 1000 * math.pi / 180 * DELTA_DEG[body]
    east_m = north_m * math.cos(math.radians(latitude_deg))
    if east_m <= 0:
        raise ValueError('degenerate east-west spacing')
    return {
        'median_abs_adjacent_m': median(dx + dy),
        'median_dimensionless_gradient': median([d / east_m for d in dx] + [d / north_m for d in dy]),
        'north_spacing_km': north_m / 1000,
        'east_spacing_km': east_m / 1000,
    }


def nearest(target, candidates, key):
    return min(sorted(candidates), key=lambda name: abs(candidates[name][key] - target[key]))


def audit(lola, mola, earth):
    samples = {}
    for body, receipt, field, multiplier in (
        ('lola', lola, 'values_km', 1000),
        ('mola', mola, 'topography_m', 1),
    ):
        samples[body] = []
        for idx, tile in enumerate(receipt['pixel_index_tiles']):
            if body == 'mola' and any(c <= 0 for row in tile['ground_return_counts'] for c in row):
                raise ValueError('zero-shot MOLA sample must not enter this audit')
            vals = [[float(x) * multiplier for x in row] for row in tile[field]]
            samples[body].append({'index': idx, 'features_by_assumed_latitude': {
                str(lat): features(vals, body, lat) for lat in (0, 30, 60)
            }})
    candidates = {}
    for name, site in earth['sites'].items():
        candidates[name] = features(site['elevation_m'], 'earth', site['center_lat_lon_deg'][0])
    reversals = {}
    for lat in (0, 30, 60):
        flips = []
        for body in ('lola', 'mola'):
            for tile in samples[body]:
                target = tile['features_by_assumed_latitude'][str(lat)]
                raw = nearest(target, candidates, 'median_abs_adjacent_m')
                corrected = nearest(target, candidates, 'median_dimensionless_gradient')
                if raw != corrected:
                    flips.append({'body': body, 'tile_index': tile['index'], 'raw_choice': raw,
                                  'gradient_choice': corrected})
        reversals[str(lat)] = {'changed_nearest': len(flips), 'total_targets': 10, 'examples': flips}
    return {
        'claim': 'Descriptive sample-grid resolution confound; NOT E001 or validated analogue matching',
        'source_receipt_sha256': EXPECTED,
        'planetary_latitudes_are_assumptions_not_georegistration': [0, 30, 60],
        'earth_candidate_labels_are_unverified_research_leads': sorted(candidates),
        'source_grid_north_spacing_km': {b: RADII_KM[b] * math.pi / 180 * DELTA_DEG[b]
                                         for b in ('lola', 'mola', 'earth')},
        'earth_candidates': candidates, 'planetary_tiles': samples, 'nearest_choice_reversals': reversals,
        'limitations': ['5x5 patches at unequal physical footprints',
                        'planetary pixel orientation/latitude not independently georegistered',
                        'no independent positive/negative analogue labels',
                        'median gradient is not a band-limited equal-footprint roughness descriptor',
                        'MOLA counts screen only sample cells; do not prove measurement accuracy'],
    }


def main():
    p = argparse.ArgumentParser()
    for name in EXPECTED:
        p.add_argument('--' + name, required=True)
    args = p.parse_args()
    result = audit(*(load_receipt(getattr(args, n), n) for n in EXPECTED))
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == '__main__':
    main()
