"""E514: real MOLA vs Earth ETOPO equal-physical-footprint comparison.

Geometry and descriptor sensitivity only; NOT independent E001 recovery.
Earth DEM cells are averaged to nominal MOLA cell footprints. This does NOT
equalize instrument transfer functions, surface composition or error.
"""
from __future__ import annotations
import hashlib
import io
import json
import math
import random
import tempfile
from pathlib import Path

import numpy as np
import tifffile

from research import e502_mola_real_ingest as mola
from research import e505_etopo_earth_ingest as earth
from research.e513_mola_latitude_audit import mola_center

MARS_RADIUS_KM = 3389.5
EARTH_RADIUS_KM = 6371.0
DEG = math.pi / 180.0


def aggregate_earth_to_mola_cells(
    dem: np.ndarray, site_lat: float, site_lon: float, mars_lat: float,
    tie_lat: float = 30.0, tie_lon: float = 75.0, pixel_deg: float = 1/240,
) -> list[list[float]]:
    """Average DEM pixels in projected nominal MOLA cell rectangles.

    Local equirectangular approximation. Fail closed on missing or clipped
    physical support. Nominal MOLA cell width is latitude dependent.
    """
    if dem.ndim != 2 or not np.issubdtype(dem.dtype, np.number):
        raise ValueError('expected numeric 2-D DEM')
    if not all(map(math.isfinite, (site_lat,site_lon,mars_lat,tie_lat,tie_lon,pixel_deg))):
        raise ValueError('nonfinite georeference')
    if abs(site_lat) >= 89 or abs(mars_lat) >= 89 or pixel_deg <= 0:
        raise ValueError('unsupported latitude or resolution')
    step_ns_km = MARS_RADIUS_KM * DEG * 0.25
    step_ew_km = step_ns_km * math.cos(mars_lat * DEG)
    lat_step = step_ns_km / (EARTH_RADIUS_KM * DEG)
    lon_step = step_ew_km / (EARTH_RADIUS_KM * DEG * math.cos(site_lat * DEG))
    output=[]
    for di in range(-2,3):
        row=[]
        for dj in range(-2,3):
            north = site_lat - di * lat_step
            west = site_lon + dj * lon_step
            north_edge = north + lat_step/2
            south_edge = north - lat_step/2
            west_edge = west - lon_step/2
            east_edge = west + lon_step/2
            r0=math.ceil((tie_lat-north_edge)/pixel_deg-0.5)
            r1=math.floor((tie_lat-south_edge)/pixel_deg-0.5)+1
            c0=math.ceil((west_edge-tie_lon)/pixel_deg-0.5)
            c1=math.floor((east_edge-tie_lon)/pixel_deg-0.5)+1
            if r0<0 or c0<0 or r1>dem.shape[0] or c1>dem.shape[1] or r1<=r0 or c1<=c0:
                raise ValueError('physical support outside Earth DEM or empty')
            block=dem[r0:r1,c0:c1]
            if not np.isfinite(block).all():
                raise ValueError('missing Earth elevation in physical support')
            row.append(float(np.mean(block,dtype=np.float64)))
        output.append(row)
    return output


def features(patch: list[list[float]], mars_lat: float) -> dict:
    """Datum-offset-invariant descriptors in common physical units."""
    a=np.asarray(patch,dtype=float)
    if a.shape != (5,5) or not np.isfinite(a).all() or abs(mars_lat)>=89:
        raise ValueError('invalid 5x5 physical patch')
    ns=MARS_RADIUS_KM * DEG * 0.25
    ew=ns*math.cos(mars_lat*DEG)
    diffs=np.concatenate((np.abs(np.diff(a,axis=0)).ravel()/ns,
                          np.abs(np.diff(a,axis=1)).ravel()/ew))
    return {'relief_p90_p10_m':float(np.percentile(a,90)-np.percentile(a,10)),
            'median_abs_gradient_m_per_km':float(np.median(diffs)),
            'std_elevation_m':float(np.std(a))}


def score(x:dict,y:dict) -> float:
    # Dimensionless descriptive discrepancy, not calibrated similarity.
    return sum(abs(math.log1p(x[k])-math.log1p(y[k])) for k in
               ('relief_p90_p10_m','median_abs_gradient_m_per_km'))


def compare(mola_receipt:dict, earth_receipt:dict, dem:np.ndarray, permutations:int=500, seed:int=20261103) -> dict:
    if mola_receipt.get('shape') != [720,1440] or len(mola_receipt.get('pixel_index_tiles',[])) != 5:
        raise ValueError('unexpected MOLA sample schema')
    if earth_receipt.get('shape') not in ([3600,3600],[3601,3601]):
        raise ValueError('unexpected Earth DEM schema')
    if len(earth_receipt.get('sites',{})) != 3 or permutations<1:
        raise ValueError('unexpected Earth sites or permutation count')
    tie=earth_receipt['tiepoint']; sx,sy=earth_receipt['pixel_scale_deg']
    if abs(sx-sy)>1e-10:
        raise ValueError('anisotropic Earth grid')
    rng=random.Random(seed)
    rows=[]
    for i,tile in enumerate(mola_receipt['pixel_index_tiles']):
        if any(c<=0 for row in tile['ground_return_counts'] for c in row):
            raise ValueError('zero-shot/interpolated MOLA sample')
        lat,lon=mola_center(*tile['center_row_col'])
        target=tile['topography_m']
        mf=features(target,lat)
        candidates={}
        for name,site in earth_receipt['sites'].items():
            elat,elon=site['center_lat_lon_deg']
            matched=aggregate_earth_to_mola_cells(dem,elat,elon,lat,tie[4],tie[3],sx)
            candidates[name]={'features':features(matched,lat),'patch_elevation_m':matched}
        rank=sorted(candidates,key=lambda name:(score(mf,candidates[name]['features']),name))
        retained=0
        flattened=[v for row in target for v in row]
        for _ in range(permutations):
            shuffle=flattened[:]
            rng.shuffle(shuffle)
            null=[shuffle[j*5:j*5+5] for j in range(5)]
            nf=features(null,lat)
            n_rank=min(candidates,key=lambda name:(score(nf,candidates[name]['features']),name))
            retained+=int(n_rank==rank[0])
        rows.append({'mola_index':i,'mola_center_lat_lon_deg':[lat,lon],
                     'mola_features':mf,'ranked_earth_candidates':rank,
                     'scores':{name:score(mf,candidates[name]['features']) for name in rank},
                     'earth_equal_footprint':candidates,
                     'spatial_null_rank_retention':retained/permutations})
    return {'experiment':'E514','claim':'equal physical-support descriptive comparison; NOT E001 known-site recovery',
            'seed':seed,'permutations_per_target':permutations,'rows':rows,
            'limitations':['MOLA gridded values are not equivalent to Earth pixel-area means',
                           'MOLA 0-shot bins excluded; positive shot counts are not error bars',
                           'No independent analogue labels or hard negatives',
                           'Local equirectangular approximation and spherical radii',
                           'Three Earth candidates are research leads, not validated analogue labels']}


def run(output:str) -> dict:
    with tempfile.TemporaryDirectory() as td:
        receipt=mola.run(str(Path(td)/'mola.json'))
        raw=earth.bounded_download()
        metadata=earth.extract(raw)
        with tifffile.TiffFile(io.BytesIO(raw)) as tf:
            dem=tf.pages[0].asarray()
        result=compare(receipt,metadata,dem)
        result['source_sha256']={'mola_topography':receipt['topography_sha256'],
                                 'mola_counts':receipt['counts_sha256'],
                                 'earth_etopo':hashlib.sha256(raw).hexdigest()}
        Path(output).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
        return result


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',required=True)
    args=parser.parse_args()
    out=run(args.output)
    print(json.dumps({'source_sha256':out['source_sha256'],
                      'ranks':[x['ranked_earth_candidates'] for x in out['rows']],
                      'null_retention':[x['spatial_null_rank_retention'] for x in out['rows']]}))
