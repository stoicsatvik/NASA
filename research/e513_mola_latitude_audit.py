"""E513: source-registered MOLA latitude correction of E511 sample gradients.

Read-only, source-hash-pinned descriptive audit; NOT known-analogue recovery.
MOLA MEGT90N000CB: upper-left 90 N, 0 E, 4 pixels/degree,
720 x 1440 equirectangular grid. Source: NASA PDS MOLA MEGDR.
"""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from statistics import median
from zipfile import ZipFile

EXPECTED = {
    "mola": "eaa499260b4d15899e4a28c609b71f300e8669d00201bdbe55c2591b4020072d",
    "earth": "db8c94a161c392626459f4032a40a850007e3b42d9f971ad6fdf5cc9009c6476",
}


def load_receipt(path: str | Path, kind: str) -> dict:
    path = Path(path)
    if path.suffix.lower() == ".zip":
        with ZipFile(path) as archive:
            members = [x for x in archive.namelist() if x.endswith(".json")]
            if len(members) != 1:
                raise ValueError("expected exactly one JSON receipt")
            raw = archive.read(members[0])
    else:
        raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != EXPECTED[kind]:
        raise ValueError(f"{kind} receipt hash mismatch")
    return json.loads(raw)


def mola_center(row: int, col: int) -> tuple[float, float]:
    """North-up MOLA 4-pixel/degree grid, pixel-centre convention."""
    if not isinstance(row, int) or not isinstance(col, int) or not (0 <= row < 720 and 0 <= col < 1440):
        raise ValueError("MOLA grid index outside 720x1440")
    return 90.0 - (row + 0.5) / 4.0, (col + 0.5) / 4.0


def median_abs_gradient(patch: list[list[float]], body: str, latitude: float) -> float:
    """Approximate local spherical spacing; not a true equal-footprint descriptor."""
    if body not in ("mola", "earth") or not math.isfinite(latitude) or abs(latitude) >= 90:
        raise ValueError("invalid body or latitude")
    n = len(patch)
    if n != 5 or any(len(row) != n for row in patch):
        raise ValueError("expected a 5x5 patch")
    radius = 3389.5 if body == "mola" else 6371.0
    angular = 0.25 if body == "mola" else 1 / 240
    north = radius * 1000 * math.radians(angular)
    east = north * math.cos(math.radians(latitude))
    values = [abs(float(patch[i][j + 1]) - float(patch[i][j])) / east
              for i in range(n) for j in range(n - 1)]
    values += [abs(float(patch[i + 1][j]) - float(patch[i][j])) / north
               for i in range(n - 1) for j in range(n)]
    if not all(math.isfinite(x) for x in values):
        raise ValueError("nonfinite elevation")
    return median(values)


def audit(mola: dict, earth: dict, assumed_latitude: float = 30.0) -> dict:
    if mola.get("shape") != [720, 1440] or len(mola.get("pixel_index_tiles", [])) != 5:
        raise ValueError("unexpected MOLA raster shape/patch count")
    if len(earth.get("sites", {})) != 3:
        raise ValueError("expected three frozen Earth candidates")
    earth_gradients = {
        name: median_abs_gradient(site["elevation_m"], "earth", site["center_lat_lon_deg"][0])
        for name, site in earth["sites"].items()
    }
    rows = []
    for index, tile in enumerate(mola["pixel_index_tiles"]):
        if any(count <= 0 for row in tile["ground_return_counts"] for count in row):
            raise ValueError("MOLA patch contains zero-shot/interpolated cell")
        lat, lon = mola_center(*tile["center_row_col"])
        actual = median_abs_gradient(tile["topography_m"], "mola", lat)
        assumed = median_abs_gradient(tile["topography_m"], "mola", assumed_latitude)
        rank = lambda g: sorted(earth_gradients, key=lambda name: (abs(g - earth_gradients[name]), name))
        north_span_km = 4 * 3389.5 * math.radians(.25)
        east_span_km = north_span_km * math.cos(math.radians(lat))
        rows.append({"tile_index": index, "center_row_col": tile["center_row_col"],
                     "center_lat_lon_deg": [lat, lon], "assumed_latitude_deg": assumed_latitude,
                     "registered_gradient": actual, "assumed_gradient": assumed,
                     "relative_change_pct": 100 * (actual / assumed - 1),
                     "registered_rank": rank(actual), "assumed_rank": rank(assumed),
                     "nearest_changed": rank(actual)[0] != rank(assumed)[0],
                     "north_south_5x5_span_km": north_span_km,
                     "east_west_5x5_span_km": east_span_km})
    earth_ns_span_km = 4 * 6371.0 * math.radians(1 / 240)
    return {"claim": "source-registered MOLA latitude sensitivity; NOT E001 known-site recovery",
            "source_receipt_sha256": EXPECTED,
            "source_metadata": "NASA PDS MOLA MEGT90N000CB 4 pix/deg 90N-90S, 0E-360E",
            "earth_candidate_gradients": earth_gradients,
            "earth_5x5_north_south_span_km": earth_ns_span_km,
            "mola_to_earth_north_south_span_ratio": rows[0]["north_south_5x5_span_km"] / earth_ns_span_km,
            "nearest_changed_count": sum(x["nearest_changed"] for x in rows),
            "maximum_absolute_relative_gradient_change_pct": max(abs(x["relative_change_pct"]) for x in rows),
            "rows": rows,
            "limitations": ["MOLA PDS grid mapping is supported by source naming/metadata; LOLA orientation not re-registered here",
                            "Five 5x5 MOLA patches have ~32x the Earth patch north-south physical span",
                            "Three Earth candidates have no independent analogue labels",
                            "Gradient median discards morphology; rank agreement is not analogue recovery",
                            "Positive MOLA ground-return counts do not establish per-pixel elevation accuracy",
                            "Local spherical approximation, not a geodetic reprojection or uncertainty interval"]}


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--mola", required=True)
    p.add_argument("--earth", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    result = audit(load_receipt(args.mola, "mola"), load_receipt(args.earth, "earth"))
    Path(args.output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("nearest_changed_count", "maximum_absolute_relative_gradient_change_pct", "mola_to_earth_north_south_span_ratio")}))
