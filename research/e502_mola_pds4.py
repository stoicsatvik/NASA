"""E502: fail-closed official PDS4 MOLA 4-ppd topography/count ingestion.

No hidden data, no planetary analogue claim. Raw topography is relative to the
Martian areoid (not comparable to LOLA's 1737.4 km reference-radius heights).
"""
from __future__ import annotations

import hashlib
import io
import json
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np

ROOT = 'https://pds-geosciences.wustl.edu/mgs/urn-nasa-pds-mgs_mola_topography_derived/meg004/'
NAMES = {'topography': 'megt90n000cb', 'counts': 'megc90n000cb'}
DTYPES = {'SignedMSB2': '>i2', 'UnsignedMSB2': '>u2',
          'SignedLSB2': '<i2', 'UnsignedLSB2': '<u2',
          'SignedMSB4': '>i4', 'UnsignedMSB4': '>u4',
          'SignedLSB4': '<i4', 'UnsignedLSB4': '<u4'}
MAX_BYTES = 8 * 1024 * 1024
PATCHES = ((90, 720), (180, 540), (360, 720), (540, 900), (630, 360))


def bounded_download(url: str, maximum: int = MAX_BYTES) -> bytes:
    if not url.startswith(ROOT) or not url.endswith(('.xml', '.img')):
        raise ValueError('only fixed official PDS4 products are permitted')
    with urlopen(Request(url, headers={'User-Agent': 'SpaceApps-E502-evidence/1.0'}), timeout=45) as response:
        raw = response.read(maximum + 1)
    if not raw or len(raw) > maximum:
        raise ValueError('empty or oversized PDS4 response')
    return raw


def local(tag: str) -> str:
    return tag.rsplit('}', 1)[-1]


def children(node: ET.Element, name: str) -> list[ET.Element]:
    return [x for x in node if local(x.tag) == name]


def child_text(node: ET.Element, name: str, required: bool = True) -> str | None:
    xs = children(node, name)
    if len(xs) > 1 or (required and len(xs) != 1):
        raise ValueError(f'ambiguous or missing PDS4 {name}')
    if not xs:
        return None
    value = (xs[0].text or '').strip()
    if required and not value:
        raise ValueError(f'empty PDS4 {name}')
    return value


def parse_label(xml_bytes: bytes, filename: str, expected_shape: tuple[int, int] = (720, 1440)) -> dict:
    root = ET.fromstring(xml_bytes)
    areas = [x for x in root.iter() if local(x.tag) == 'File_Area_Observational']
    matches = []
    for area in areas:
        files = children(area, 'File')
        if len(files) == 1 and child_text(files[0], 'file_name') == filename:
            matches.append(area)
    if len(matches) != 1:
        raise ValueError('PDS4 file identity missing/ambiguous')
    arrays = [x for x in matches[0] if local(x.tag) in ('Array_2D_Image', 'Array_2D')]
    if len(arrays) != 1:
        raise ValueError('expected exactly one PDS4 2D image array')
    array = arrays[0]
    order = child_text(array, 'axis_index_order')
    axes = children(array, 'Axis_Array')
    axis_map = {}
    for a in axes:
        index = int(child_text(a, 'sequence_number'))
        axis_map[index] = (child_text(a, 'axis_name'), int(child_text(a, 'elements')))
    if len(axes) != 2 or set(axis_map) != {1, 2}:
        raise ValueError('expected exactly two numbered axes')
    valid_order = ((order == 'Last Index Fastest' and axis_map[1][0] == 'Line' and axis_map[2][0] == 'Sample')
                   or (order == 'First Index Fastest' and axis_map[1][0] == 'Sample' and axis_map[2][0] == 'Line'))
    if not valid_order:
        raise ValueError('unrecognized PDS4 row-major axis layout')
    shape = (next(v for k, v in axis_map.values() if k == 'Line'),
             next(v for k, v in axis_map.values() if k == 'Sample'))
    if shape != expected_shape:
        raise ValueError(f'unexpected MOLA grid shape: {shape}')
    elements = children(array, 'Element_Array')
    if len(elements) != 1:
        raise ValueError('missing/ambiguous Element_Array')
    elem = elements[0]
    data_type = child_text(elem, 'data_type')
    if data_type not in DTYPES:
        raise ValueError(f'unsupported PDS4 data type {data_type}')
    scale = float(child_text(elem, 'scaling_factor', required=False) or '1')
    value_offset = float(child_text(elem, 'value_offset', required=False) or '0')
    if not np.isfinite(scale) or scale == 0 or not np.isfinite(value_offset):
        raise ValueError('invalid PDS4 scale/offset')
    offset = int(child_text(array, 'offset'))
    if offset < 0:
        raise ValueError('negative PDS4 byte offset')
    special = set()
    for sc in children(array, 'Special_Constants'):
        for x in sc:
            if local(x.tag).endswith('_constant'):
                special.add(int((x.text or '').strip()))
    return {'shape': shape, 'dtype': DTYPES[data_type], 'data_type': data_type,
            'offset': offset, 'scale': scale, 'value_offset': value_offset,
            'special_constants': sorted(special), 'axis_order': order,
            'filename': filename}


def decode(raw: bytes, label: dict) -> tuple[np.ndarray, np.ndarray]:
    dtype = np.dtype(label['dtype'])
    size = int(np.prod(label['shape']))
    start = label['offset']
    expected = start + size * dtype.itemsize
    if len(raw) != expected:
        raise ValueError(f'PDS4 byte count mismatch: got {len(raw)}, expected {expected}')
    values = np.frombuffer(raw, dtype=dtype, count=size, offset=start).reshape(label['shape'])
    missing = np.zeros(label['shape'], dtype=bool)
    for v in label['special_constants']:
        missing |= values == v
    physical = values.astype(np.float64) * label['scale'] + label['value_offset']
    physical[missing] = np.nan
    return physical, missing


def patch(a: np.ndarray, row: int, col: int) -> list[list[float | None]]:
    return [[None if not np.isfinite(v) else float(v) for v in line]
            for line in a[row-2:row+3, col-2:col+3]]


def summarize(topo: np.ndarray, counts: np.ndarray) -> dict:
    if topo.shape != (720, 1440) or counts.shape != topo.shape:
        raise ValueError('MOLA grid mismatch')
    good_counts = np.isfinite(counts) & (counts >= 0)
    if np.any(np.isfinite(counts) & (counts < 0)):
        raise ValueError('negative MOLA observation counts')
    observed = good_counts & (counts > 0)
    valid_topo = np.isfinite(topo)
    both = observed & valid_topo
    if not np.any(both):
        raise ValueError('no observed topography cells')
    v = topo[both]
    return {'shape': [720, 1440], 'topography_finite_cells': int(valid_topo.sum()),
            'counts_valid_cells': int(good_counts.sum()), 'counts_positive_cells': int(observed.sum()),
            'finite_topography_with_zero_count': int((valid_topo & good_counts & (counts == 0)).sum()),
            'joint_observed_topography_cells': int(both.sum()),
            'observed_topography_min_m': float(v.min()), 'observed_topography_max_m': float(v.max()),
            'observed_topography_median_m': float(np.median(v)),
            'patches_pixel_index_only': [{'row_col': [r, c], 'topography_m': patch(topo, r, c),
                                          'shot_counts': patch(counts, r, c)} for r, c in PATCHES]}


def run(output: str = 'e502_mola_receipt.json') -> dict:
    products = {}
    arrays = {}
    for kind, stem in NAMES.items():
        xml = bounded_download(ROOT + stem + '.xml')
        img = bounded_download(ROOT + stem + '.img')
        label = parse_label(xml, stem + '.img')
        data, missing = decode(img, label)
        arrays[kind] = data
        products[kind] = {'url': ROOT + stem + '.img', 'label_url': ROOT + stem + '.xml',
                          'img_sha256': hashlib.sha256(img).hexdigest(),
                          'xml_sha256': hashlib.sha256(xml).hexdigest(),
                          'img_bytes': len(img), 'label': label,
                          'masked_special_cells': int(missing.sum())}
    receipt = {'source_page': 'https://pds-geosciences.wustl.edu/missions/mgs/megdr.html',
               'source_bundle': 'urn:nasa:pds:mgs_mola_topography_derived',
               'instrument': 'Mars Global Surveyor MOLA MEGDR 4ppd PDS4',
               'topography_datum': 'Mars areoid; not comparable directly to lunar radius-referenced heights',
               'source_units': 'topography metres (PDS label scale/offset preserved)',
               'products': products, 'statistics': summarize(arrays['topography'], arrays['counts']),
               'claim': 'real numeric MOLA ingestion only; Earth/Moon/Mars analogue recovery NOT YET MEASURED'}
    Path(output).write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n', encoding='utf-8')
    return receipt


if __name__ == '__main__':
    import sys
    print(json.dumps({k: v for k, v in run(sys.argv[1] if len(sys.argv) > 1 else 'e502_mola_receipt.json').items() if k != 'statistics'}, sort_keys=True))
