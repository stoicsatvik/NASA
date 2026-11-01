"""E478: exact fixed-count 5x5 observed-stencil null on archived E472 PDS-derived masks.

No interpolation, new data, planetary analogue labels, or independence assumptions.
The null is uniform placement of k observed cells on 5x5, not an instrument model.
"""
from __future__ import annotations
import argparse
import hashlib
import itertools
import json
from math import comb
from pathlib import Path

SHA = {
    'mars':'2e70d84ca45cc4730c87e8931194c5ba1cd7a31bdd15e9a7883c5611578c9dfb',
    'moon':'a4ed427e5996b8ef115e0bf8130f615089248bae8d89ec43cdd6fa2bf80f96c4',
}

def load(path, body):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=SHA[body]:
        raise ValueError('unpinned source bytes')
    obj=json.loads(raw)
    if len(obj.get('windows',[]))!=3:
        raise ValueError('unexpected site population')
    return obj

def bitmask(rows):
    n=len(rows)
    if n<3 or any(not isinstance(row,str) or len(row)!=n or set(row)-set('01') for row in rows):
        raise ValueError('invalid mask')
    return sum((ch=='1') << (i*n+j) for i,row in enumerate(rows) for j,ch in enumerate(row))

def stencils(n, full=False):
    offsets=tuple((dy,dx) for dy in (-1,0,1) for dx in (-1,0,1)) if full else ((0,0),(-1,0),(1,0),(0,-1),(0,1))
    return tuple(sum(1<<((y+dy)*n+x+dx) for dy,dx in offsets) for y in range(1,n-1) for x in range(1,n-1))

def count_stencils(mask, masks):
    return sum(mask & s == s for s in masks)

def exact_any_stencil_probability(n, k, full=False):
    """Exact inclusion-exclusion over all interior stencil unions; no simulation."""
    if n != 5 or not 0 <= k <= 25:
        raise ValueError('only 5x5 exact cohort')
    masks = stencils(n, full)
    favorable = 0
    for subset in range(1, 1 << len(masks)):
        union = 0
        for i, stencil in enumerate(masks):
            if subset & (1 << i):
                union |= stencil
        required = union.bit_count()
        if k >= required:
            favorable += (1 if subset.bit_count() % 2 else -1) * comb(25 - required, k - required)
    return favorable / comb(25, k)

def exact_fixed_count(n,k,threshold_cross,threshold_full):
    if n!=5 or k not in range(26):
        raise ValueError('only 5x5 exact cohort')
    cross,full=stencils(n),stencils(n,True)
    total=comb(n*n,k)
    cross_le=full_le=zero_cross=zero_full=0
    for cells in itertools.combinations(range(n*n),k):
        mask=sum(1<<i for i in cells)
        c=count_stencils(mask,cross)
        f=count_stencils(mask,full)
        cross_le+=c<=threshold_cross
        full_le+=f<=threshold_full
        zero_cross+=c==0
        zero_full+=f==0
    return {'total_masks':total,'observed_cross':threshold_cross,'observed_full':threshold_full,
            'cross_le_count':cross_le,'cross_le_fraction':cross_le/total,
            'full_le_count':full_le,'full_le_fraction':full_le/total,
            'zero_cross_fraction':zero_cross/total,'zero_full_fraction':zero_full/total}

def evaluate(mars,moon):
    result=[]
    for w in mars['windows']:
        lat=w['latitude_deg_requested']
        if w['longitude_deg_requested']!=45 or lat not in (-0.5,-20,-40):
            raise ValueError('unexpected location')
        rows=w['observed_mask_rows']
        if len(rows)!=9:
            raise ValueError('source width')
        central=[row[2:7] for row in rows[2:7]]
        mask=bitmask(central)
        k=mask.bit_count()
        if k!=w['center_5x5_observed_cells']:
            raise ValueError('count mismatch')
        c=count_stencils(mask,stencils(5))
        f=count_stencils(mask,stencils(5,True))
        result.append({'body':'mars','latitude_deg':lat,'observed':k,'cells':25,**exact_fixed_count(5,k,c,f)})
    for w in moon['windows']:
        mask=bitmask(w['observed_mask_rows'])
        if mask.bit_count()!=w['observed_cells']:
            raise ValueError('moon count mismatch')
        result.append({'body':'moon','latitude_deg':w['latitude_deg_requested'],'observed':mask.bit_count(),'cells':81,
                       'cross':count_stencils(mask,stencils(9)),'full':count_stencils(mask,stencils(9,True)),
                       'exact_fixed_count_null':'NOT COMPUTED: choose(81,k) too large'})
    return {'schema':'nasa/e478/exact-mars-fixed-count-stencil-null/v1',
            'uniform_null_first_five_point_95pct_min_observed':next(k for k in range(26) if exact_any_stencil_probability(5,k)>=0.95),
            'source':'E472 artifact 13075465278; official PDS-derived MOLA/LOLA count masks',
            'source_sha256':SHA,'windows':result,
            'null':'exact uniform fixed-count binary placement, not physical altimetry track model',
            'known_site_recovery':'NOT YET MEASURED','cross_body_similarity':'NOT YET PROVEN'}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mars');p.add_argument('moon');args=p.parse_args()
    print(json.dumps(evaluate(load(args.mars,'mars'),load(args.moon,'moon')),indent=2))
