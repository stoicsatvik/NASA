"""E369: independently test trivial single-feature baselines on a public analogue catalog.

Research-only, not a competition solution or validation of cross-body recovery.
Public source is pinned; binary rasters are checked against Git blob IDs.
"""
from __future__ import annotations

import hashlib
import io
import json
import math
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import numpy as np

OWNER = "Yakiyo/terra-nova"
COMMIT = "f6c53ba50a9379d1c06f610b0e598395a0a54b43"
SOURCES = {
    "data/known_analogs.json": ("d75240ce203ddb00b2d9186e7981ab90720ff9a3", 6500),
    "cache/derived/land_fraction.npy": ("fd29c109b315e6a07e2b4ec9c28e9d96088427d0", 1036928),
    "cache/derived/vegetation.npy": ("781d0ca7fb89b8c83a5a059aaf9fb7cc5662c9c0", 1036928),
    "cache/derived/precipitation.npy": ("94093f7cefe8dfe1e53134fe2817e7ed2ac68f7b", 1036928),
}
SHAPE = (360, 720)
SEARCH_RADIUS = 2


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\\0" + data).hexdigest()


def fetch_pinned(path: str) -> bytes:
    if path not in SOURCES:
        raise ValueError("unapproved path")
    expected_sha, expected_len = SOURCES[path]
    url = "https://raw.githubusercontent.com/" + OWNER + "/" + COMMIT + "/" + path
    with urlopen(Request(url, headers={"User-Agent": "NASA-E369-Independent-Feature-Audit/1.0"}), timeout=45) as response:
        final = urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname != "raw.githubusercontent.com":
            raise ValueError("unexpected redirect")
        data = response.read(expected_len + 1)
    if len(data) != expected_len or git_blob_id(data) != expected_sha:
        raise ValueError("source size/blob mismatch: " + path)
    return data


def decode_raster(raw: bytes) -> np.ndarray:
    a = np.load(io.BytesIO(raw), allow_pickle=False)
    if a.shape != SHAPE or a.dtype.kind != "f" or a.dtype.itemsize != 4:
        raise ValueError("unexpected raster geometry or dtype")
    return np.asarray(a, dtype=np.float64)


def nearest_cell(values: np.ndarray, lat: float, lon: float) -> tuple[float | None, int | None]:
    if values.ndim != 2:
        raise ValueError("not a 2D raster")
    nr, nc = values.shape
    if not all(math.isfinite(x) for x in (lat, lon)) or not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("invalid coordinates")
    row = min(max(int((90 - lat) / (180 / nr)), 0), nr - 1)
    col = min(max(int((lon + 180) / (360 / nc)), 0), nc - 1)
    if np.isfinite(values[row, col]):
        return float(values[row, col]), 0
    best = None
    for dr in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
        for dc in range(-SEARCH_RADIUS, SEARCH_RADIUS + 1):
            r, c = row + dr, (col + dc) % nc
            if 0 <= r < nr and np.isfinite(values[r, c]):
                distance = dr * dr + dc * dc
                if best is None or distance < best[0]:
                    best = (distance, r, c)
    return (None, None) if best is None else (float(values[best[1], best[2]]), best[0])


def auc(pos: list[float], neg: list[float]) -> float | None:
    if not pos or not neg:
        return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def measure(catalog: dict, layers: dict[str, np.ndarray]) -> dict:
    sites = catalog["sites"]
    negatives = catalog["negatives"]
    if len(sites) != 12 or len(negatives) != 8:
        raise ValueError("catalog control count changed")
    if len({s["name"] for s in sites + negatives}) != 20:
        raise ValueError("duplicate control name")
    if sum(s["kind"] == "environment" for s in sites) != 8:
        raise ValueError("positive role changed")
    land = layers["land_fraction"]
    out = {}
    for variable in ("vegetation", "precipitation"):
        raw = layers[variable]
        if raw.shape != SHAPE or land.shape != SHAPE:
            raise ValueError("raster shape mismatch")
        out[variable] = {}
        for mask_name, mask in (
            ("finite_only", np.isfinite(raw)),
            ("land_fraction_ge_0_5", np.isfinite(raw) & np.isfinite(land) & (land >= 0.5)),
        ):
            values = np.where(mask, -raw, np.nan)
            samples = {}
            for site in sites + negatives:
                score, offset = nearest_cell(values, site["lat"], site["lon"])
                samples[site["name"]] = {"score": score, "offset_squared_cells": offset}
            group_results = {}
            for group in ("mars", "moon", "cold_polar"):
                positive_sites = [
                    s for s in sites if s["kind"] == "environment"
                    and (("cold_polar" in s.get("tags", [])) if group == "cold_polar"
                         else (group in s["bodies"]))
                ]
                pos = [samples[s["name"]]["score"] for s in positive_sites]
                neg = [samples[s["name"]]["score"] for s in negatives]
                pos = [x for x in pos if x is not None]
                neg = [x for x in neg if x is not None]
                score = auc(pos, neg)
                group_results[group] = {
                    "positives_scored": len(pos),
                    "negatives_scored": len(neg),
                    "auc": score,
                    "leave_one_negative_out_auc_min": min(
                        (auc(pos, neg[:i] + neg[i + 1:]) for i in range(len(neg))), default=None
                    ) if len(neg) > 1 else None,
                    "leave_one_negative_out_auc_max": max(
                        (auc(pos, neg[:i] + neg[i + 1:]) for i in range(len(neg))), default=None
                    ) if len(neg) > 1 else None,
                }
            out[variable][mask_name] = {
                "valid_grid_cells": int(mask.sum()),
                "groups": group_results,
                "unscored_controls": [name for name, x in samples.items() if x["score"] is None],
                "control_scores": samples,
            }
    return {
        "experiment": "E369_EDITORIAL_NEGATIVE_SINGLE_FEATURE_BASELINES",
        "source_repo": OWNER,
        "source_commit": COMMIT,
        "method": "source-pinned single-feature -vegetation and -precipitation scores, two prespecified land masks, original nearest-scored-cell 2-cell search, exact pairwise AUC",
        "results": out,
        "limits": [
            "These are Earth-only climate/vegetation screening controls, not cross-body analog recovery.",
            "The catalog negatives were selected editorially for humidity/vegetation; AUC is not blinded or independent.",
            "Site coordinates and raster resolution may misrepresent region-scale or coastal environments.",
            "Small positive samples and shared negatives do not justify population generalization.",
            "A single-feature AUC is not an independent reproduction of TerraNova's multifeature AUC.",
        ],
        "claim_state": {
            "earth_editorial_control_separation": "MEASURED_ONLY_FOR_PINNED_SOURCE_AND_FEATURES",
            "third_party_full_model_auc": "NOT INDEPENDENTLY REPRODUCED",
            "e001_known_site_recovery": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "challenge_superiority": "NOT YET PROVEN",
        },
    }


def run() -> dict:
    data = {path: fetch_pinned(path) for path in SOURCES}
    catalog = json.loads(data["data/known_analogs.json"])
    layers = {path.rsplit("/", 1)[-1][:-4]: decode_raster(blob)
              for path, blob in data.items() if path.endswith(".npy")}
    receipt = measure(catalog, layers)
    receipt["sha256"] = {path: hashlib.sha256(blob).hexdigest() for path, blob in data.items()}
    return receipt


if __name__ == "__main__":
    print(json.dumps(run(), indent=2, sort_keys=True, allow_nan=False))
