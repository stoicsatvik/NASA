"""E501: ingest official NASA SVS LOLA 4-ppd numeric elevation, no geologic claims.

Source https://svs.gsfc.nasa.gov/4720 ; source units: float32 km above
lunar radius 1737.4 km. Visualization reformat of PDS LOLA grid, not a
new measurement, and not a proof of observed-only coverage.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import tifffile

URL = 'https://svs.gsfc.nasa.gov/vis/a000000/a004700/a004720/ldem_4.tif'
MAX_BYTES = 8 * 1024 * 1024
SAMPLE_PIXELS = ((90, 720), (180, 540), (360, 720), (540, 900), (630, 360))


def bounded_download(url=URL, max_bytes=MAX_BYTES):
    req = Request(url, headers={'User-Agent':'NASA-SpaceApps-research-E501/1.0'})
    with urlopen(req, timeout=40) as response:
        raw = response.read(max_bytes + 1)
    if len(raw) > max_bytes:
        raise ValueError('source exceeds bounded download size')
    if len(raw) < 1024 or raw[:4] not in (bytes.fromhex('49492a00'), bytes.fromhex('4d4d002a')):
        raise ValueError('not a valid uncompressed TIFF header')
    return raw


def summarize(data):
    a = np.asarray(data)
    if a.shape != (720, 1440) or a.dtype.kind != 'f':
        raise ValueError(f'unexpected LOLA raster shape/dtype: {a.shape}/{a.dtype}')
    finite = np.isfinite(a)
    if not np.any(finite):
        raise ValueError('no finite elevation cells')
    vals = a[finite].astype(np.float64)
    tiles = []
    for row, col in SAMPLE_PIXELS:
        patch = a[row-2:row+3, col-2:col+3]
        tiles.append({'center_row_col':[row,col],
                      'shape':list(patch.shape),
                      'finite':int(np.isfinite(patch).sum()),
                      'values_km':[[float(v) if np.isfinite(v) else None for v in line] for line in patch]})
    return {'source':URL, 'source_page':'https://svs.gsfc.nasa.gov/4720',
            'instrument':'LRO LOLA gridded elevation, NASA SVS reformatted TIFF',
            'units':'km relative to 1737.4 km lunar radius',
            'resolution':'4 pixels/degree; 1440 x 720; spatial orientation requires independent registration',
            'shape':[720,1440], 'dtype':str(a.dtype),
            'finite_count':int(finite.sum()), 'nonfinite_count':int(a.size-finite.sum()),
            'min_km':float(vals.min()), 'max_km':float(vals.max()),
            'quantiles_km':{str(p):float(np.quantile(vals,p)) for p in (0.01,0.5,0.99)},
            'pixel_index_tiles':tiles,
            'claim':'numeric LOLA raster ingestion only; E001 known-site recovery not measured'}


def run(output='e501_lola.json'):
    import io
    raw=bounded_download()
    with tifffile.TiffFile(io.BytesIO(raw)) as tf:
        if len(tf.pages)!=1:
            raise ValueError('expected single-band TIFF')
        data=tf.asarray()
    result=summarize(data)
    result['source_sha256']=hashlib.sha256(raw).hexdigest()
    result['source_bytes']=len(raw)
    Path(output).write_text(json.dumps(result,indent=2,sort_keys=True)+chr(10),encoding='utf-8')
    return result

if __name__=='__main__':
    import sys
    result=run(sys.argv[1] if len(sys.argv)>1 else 'e501_lola.json')
    print(json.dumps({k:v for k,v in result.items() if k!='pixel_index_tiles'},sort_keys=True))
