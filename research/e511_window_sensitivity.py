"""E511: exact 3x3 crop sensitivity of E510 real-numeric 5x5 patch rankings.

No independently labelled analogues or equal-footprint terrain. NOT E001.
"""
import argparse
import hashlib
import itertools
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
DELTA_DEG = {'lola': .25, 'mola': .25, 'earth': 1 / 240}


def load_receipt(path, kind):
    path = Path(path)
    if path.suffix == '.zip':
        with ZipFile(path) as archive:
            members = [x for x in archive.namelist() if x.endswith('.json')]
            if len(members) != 1:
                raise ValueError('expected one JSON receipt in ZIP')
            raw = archive.read(members[0])
    else:
        raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED[kind]:
        raise ValueError(f'{kind}: source receipt SHA-256 mismatch')
    return json.loads(raw)


def windows(patch):
    if len(patch) != 5 or any(len(row) != 5 for row in patch):
        raise ValueError('expected a 5x5 numeric patch')
    return [[[float(v) for v in row[j:j + 3]] for row in patch[i:i + 3]]
            for i in range(3) for j in range(3)]


def gradient(patch, body, latitude):
    n = len(patch)
    if n not in (3, 5) or any(len(row) != n for row in patch):
        raise ValueError('expected square 3x3 or 5x5 patch')
    if body not in RADII_KM or not 0 <= abs(latitude) < 90:
        raise ValueError('unsupported body/latitude')
    north = RADII_KM[body] * 1000 * math.pi / 180 * DELTA_DEG[body]
    east = north * math.cos(math.radians(latitude))
    diffs = [abs(patch[i][j + 1] - patch[i][j]) / east
             for i in range(n) for j in range(n - 1)]
    diffs += [abs(patch[i + 1][j] - patch[i][j]) / north
              for i in range(n - 1) for j in range(n)]
    if not all(math.isfinite(x) for x in diffs):
        raise ValueError('nonfinite elevation or gradient')
    return median(diffs)


def nearest(value, candidates):
    return min(sorted(candidates), key=lambda n: abs(value - candidates[n]))


def audit(lola, mola, earth, latitudes=(0, 30, 60)):
    sites = {n: (v['elevation_m'], v['center_lat_lon_deg'][0])
             for n, v in earth['sites'].items()}
    if len(sites) != 3:
        raise ValueError('frozen experiment requires exactly 3 Earth candidates')
    targets = [('lola', i, [[float(v) * 1000 for v in row] for row in t['values_km']])
               for i, t in enumerate(lola['pixel_index_tiles'])]
    for i, t in enumerate(mola['pixel_index_tiles']):
        if any(c <= 0 for row in t['ground_return_counts'] for c in row):
            raise ValueError('zero-shot MOLA patch must be excluded')
        targets.append(('mola', i, t['topography_m']))
    if len(targets) != 10:
        raise ValueError('frozen experiment requires exactly 10 planetary patches')
    out = {'claim': 'exact within-5x5 crop sensitivity; NOT known-site recovery',
           'source_receipt_sha256': EXPECTED, 'latitudes_assumed_not_georegistered': list(latitudes),
           'earth_candidates_are_unverified': sorted(sites), 'results': {}}
    for latitude in latitudes:
        earth_full = {n: gradient(p, 'earth', lat) for n, (p, lat) in sites.items()}
        earth_crops = {n: [gradient(w, 'earth', lat) for w in windows(p)]
                       for n, (p, lat) in sites.items()}
        combos = [{n: v for n, v in zip(sorted(sites), values)} for values in
                  itertools.product(*(earth_crops[n] for n in sorted(sites)))]
        rows = []
        for body, idx, patch in targets:
            full = gradient(patch, body, latitude)
            cropped = [gradient(w, body, latitude) for w in windows(patch)]
            choice = nearest(full, earth_full)
            target_retained = sum(nearest(v, earth_full) == choice for v in cropped)
            earth_retained = sum(nearest(full, v) == choice for v in combos)
            both_retained = sum(nearest(v, c) == choice for v in cropped for c in combos)
            rows.append({'body': body, 'index': idx, 'full_5x5_choice': choice,
                         'target_only_retained': target_retained, 'target_only_total': 9,
                         'earth_only_retained': earth_retained, 'earth_only_total': len(combos),
                         'both_retained': both_retained, 'both_total': len(cropped) * len(combos)})
        out['results'][str(latitude)] = {
            'rows': rows,
            'target_only_fraction': sum(r['target_only_retained'] for r in rows) / (9 * len(rows)),
            'earth_only_fraction': sum(r['earth_only_retained'] for r in rows) / (len(combos) * len(rows)),
            'both_fraction': sum(r['both_retained'] for r in rows) / (9 * len(combos) * len(rows)),
            'both_comparisons': 9 * len(combos) * len(rows),
        }
    out['limitations'] = [
        'Nine overlapping 3x3 windows are not independent samples',
        '3x3 and 5x5 crops have different physical footprints and cannot validate cross-body similarity',
        'Only three unverified Earth research candidates; no independent known-site labels',
        'Planetary latitude/orientation not independently georegistered',
        'MOLA positive ground-return counts do not guarantee elevation accuracy',
        'Exact combinatorial proportions are descriptive, not confidence intervals or p-values',
    ]
    return out


def main():
    p = argparse.ArgumentParser()
    for kind in EXPECTED:
        p.add_argument('--' + kind, required=True)
    p.add_argument('--output', required=True)
    args = p.parse_args()
    result = audit(*(load_receipt(getattr(args, n), n) for n in EXPECTED))
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({lat: {k: v for k, v in r.items() if k != 'rows'}
                      for lat, r in result['results'].items()}, sort_keys=True))


if __name__ == '__main__':
    main()
