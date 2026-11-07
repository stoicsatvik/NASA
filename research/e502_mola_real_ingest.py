"""E502: retrieve paired real MOLA MEG004 topography/counts from official PDS.

Fail closed on source, size, metadata, and binary alignment. No E001 claims.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from research.mola_megdr_quality_gate import ARCHIVE, analyze, read_grid

PRODUCTS = ("megt90n000cb.img", "megc90n000cb.img",
            "megt90n000cb.lbl", "megc90n000cb.lbl")
MAX_IMAGE = 4 * 1024 * 1024
MAX_LABEL = 128 * 1024
CENTERS = ((90, 720), (180, 540), (360, 720), (540, 900), (630, 360))


def bounded_read(response, limit: int) -> bytes:
    if limit < 1:
        raise ValueError("invalid byte limit")
    raw = response.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("source exceeds bounded size")
    if not raw:
        raise ValueError("empty source")
    return raw


def fetch_product(filename: str) -> bytes:
    if filename not in PRODUCTS:
        raise ValueError("unapproved product")
    url = ARCHIVE + filename
    if urlparse(url).hostname != "pds-geosciences.wustl.edu":
        raise ValueError("unapproved source")
    req = Request(url, headers={"User-Agent": "NASA-SpaceApps-E502/1.0"})
    with urlopen(req, timeout=45) as response:
        if urlparse(response.geturl()).hostname != "pds-geosciences.wustl.edu":
            raise ValueError("source redirected off official PDS host")
        return bounded_read(response, MAX_LABEL if filename.endswith(".lbl") else MAX_IMAGE)


def patch(values: tuple[int, ...], rows: int, cols: int, row: int, col: int) -> list[list[int]]:
    if not (2 <= row < rows - 2 and 2 <= col < cols - 2):
        raise ValueError("patch center out of bounds")
    return [[values[r * cols + c] for c in range(col - 2, col + 3)]
            for r in range(row - 2, row + 3)]


def run(output: str) -> dict:
    import tempfile
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        hashes = {}
        sizes = {}
        for filename in PRODUCTS:
            data = fetch_product(filename)
            (root / filename).write_bytes(data)
            hashes[filename] = hashlib.sha256(data).hexdigest()
            sizes[filename] = len(data)
        top, counts, top_lbl, counts_lbl = (root / x for x in PRODUCTS)
        receipt = analyze(top, counts, top_lbl, counts_lbl)
        h, _ = read_grid(top, (720, 1440))
        c, _ = read_grid(counts, (720, 1440))
        tiles = []
        for row, col in CENTERS:
            tiles.append({
                "center_row_col": [row, col],
                "topography_m": patch(h, 720, 1440, row, col),
                "ground_return_counts": patch(c, 720, 1440, row, col),
            })
        receipt.update({
            "source_urls": [ARCHIVE + x for x in PRODUCTS],
            "source_sha256": hashes,
            "source_bytes": sizes,
            "pixel_index_tiles": tiles,
            "claim": "Real paired MOLA gridded topography/counts access only; E001 NOT YET MEASURED",
            "datum_warning": "MOLA heights above Mars areoid; LOLA above lunar reference sphere; do not compare absolute heights",
            "grid_warning": "Zero-count MOLA bins are interpolated; no cell represents independent ground truth for analogue recovery",
        })
        Path(output).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return receipt


if __name__ == "__main__":
    import sys
    result = run(sys.argv[1] if len(sys.argv) > 1 else "e502_mola.json")
    print(json.dumps({k: v for k, v in result.items() if k != "pixel_index_tiles"}, sort_keys=True))
