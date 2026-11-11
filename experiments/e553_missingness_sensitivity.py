"""E553: exact missingness sensitivity for the E550 nine-position CTX/HiRISE grid.

The three unsupported positions are completed only for a deterministic
sensitivity envelope using quantiles of the six observed patch medians.
These values are hypothetical, never treated as measurements.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "e550_patch_summaries.json"
EXPECTED_CTX_DOI = "10.5066/P906QQT8"
EXPECTED_HIRISE_DOI = "10.5066/P9REJ9JN"


def load_payload(path: Path = DATA) -> dict:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("source", {}).get("ctx_doi") != EXPECTED_CTX_DOI:
        raise ValueError("unexpected CTX source DOI")
    if payload.get("source", {}).get("hirise_doi") != EXPECTED_HIRISE_DOI:
        raise ValueError("unexpected HiRISE source DOI")
    patches = payload.get("patches")
    if not isinstance(patches, list) or len(patches) != 9:
        raise ValueError("expected nine preregistered E550 grid positions")
    ids = [item.get("patch_id") for item in patches]
    if len(set(ids)) != 9:
        raise ValueError("E550 grid position IDs must be unique")
    return payload


def quantile_grid(values: np.ndarray, levels: int = 5) -> list[float]:
    if levels < 3 or levels % 2 == 0:
        raise ValueError("sensitivity grid requires an odd number of at least three quantiles")
    if values.ndim != 1 or len(values) != 6 or not np.all(np.isfinite(values)):
        raise ValueError("quantile envelope requires six finite measured patch medians")
    quantiles = np.linspace(0.0, 1.0, levels)
    return [float(value) for value in np.quantile(values, quantiles, method="linear")]


def _design_matrix(patches: list[dict]) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    xy = np.asarray([[float(p["center_x"]), float(p["center_y"])] for p in patches], dtype=float)
    x = (xy[:, 0] - float(np.mean(xy[:, 0]))) / 1000.0
    y = (xy[:, 1] - float(np.mean(xy[:, 1]))) / 1000.0
    design = np.column_stack([np.ones(len(patches)), x, y])
    coefficient_map = np.linalg.solve(design.T @ design, design.T)
    return design, coefficient_map, np.asarray([x, y], dtype=float)


def _permutation_indices() -> np.ndarray:
    return np.asarray(list(itertools.permutations(range(9))), dtype=np.uint8)


def _plane_statistics(values: np.ndarray, coefficient_map: np.ndarray,
                      x: np.ndarray, y: np.ndarray) -> tuple[float, float, np.ndarray]:
    beta = coefficient_map @ values
    sst = float(np.sum((values - np.mean(values)) ** 2))
    if sst <= 0:
        raise ValueError("completed grid has zero residual variance")
    sxx = float(np.sum(x * x))
    syy = float(np.sum(y * y))
    sxy = float(np.sum(x * y))
    explained = beta[1] ** 2 * sxx + beta[2] ** 2 * syy + 2.0 * beta[1] * beta[2] * sxy
    r2 = float(explained / sst)
    gradient = float(math.hypot(beta[1], beta[2]))
    return r2, gradient, beta


def _exact_null(values: np.ndarray, coefficient_map: np.ndarray,
                x: np.ndarray, y: np.ndarray, permutations: np.ndarray) -> dict:
    observed_r2, observed_gradient, beta = _plane_statistics(values, coefficient_map, x, y)
    permuted_values = values[permutations]
    permuted_beta = permuted_values @ coefficient_map.T
    sst = float(np.sum((values - np.mean(values)) ** 2))
    sxx = float(np.sum(x * x))
    syy = float(np.sum(y * y))
    sxy = float(np.sum(x * y))
    r2_null = (
        permuted_beta[:, 1] ** 2 * sxx
        + permuted_beta[:, 2] ** 2 * syy
        + 2.0 * permuted_beta[:, 1] * permuted_beta[:, 2] * sxy
    ) / sst
    gradient_null = np.hypot(permuted_beta[:, 1], permuted_beta[:, 2])
    return {
        "observed_r2": observed_r2,
        "observed_gradient_norm_m_per_km": observed_gradient,
        "slope_x_m_per_km": float(beta[1]),
        "slope_y_m_per_km": float(beta[2]),
        "permutations": int(len(permutations)),
        "p_r2_ge_observed": float(np.mean(r2_null >= observed_r2 - 1e-12)),
        "p_gradient_ge_observed": float(np.mean(gradient_null >= observed_gradient - 1e-12)),
    }


def analyze(path: Path = DATA, levels: int = 5) -> dict:
    payload = load_payload(path)
    patches = payload["patches"]
    measured = [p for p in patches if p.get("common_valid_cells", 0) > 0
                and p.get("median_residual_m") is not None]
    missing = [p for p in patches if p.get("common_valid_cells", 0) == 0
               or p.get("median_residual_m") is None]
    if len(measured) != 6 or len(missing) != 3:
        raise ValueError("E550 coverage contract changed: expected six measured and three unsupported patches")
    for item in measured:
        if item.get("common_valid_cells") != 25 or item.get("coverage_min") != 1.0:
            raise ValueError("measured patch no longer satisfies the frozen 25/25 support contract")
    if any(item.get("median_residual_m") is not None for item in missing):
        raise ValueError("unsupported positions must not be silently treated as measured")

    measured_ids = {item["patch_id"] for item in measured}
    missing_ids = [item["patch_id"] for item in missing]
    values = np.asarray([float(item["median_residual_m"]) for item in measured], dtype=float)
    grid = quantile_grid(values, levels=levels)
    design, coefficient_map, axes = _design_matrix(patches)
    x, y = axes
    permutations = _permutation_indices()
    scenarios = []

    for assignment in itertools.product(range(levels), repeat=len(missing)):
        completed = np.empty(9, dtype=float)
        imputed = {}
        measured_index = 0
        missing_index = 0
        for index, item in enumerate(patches):
            if item["patch_id"] in measured_ids:
                completed[index] = values[measured_index]
                measured_index += 1
            else:
                chosen = grid[assignment[missing_index]]
                completed[index] = chosen
                imputed[item["patch_id"]] = chosen
                missing_index += 1
        stats = _exact_null(completed, coefficient_map, x, y, permutations)
        scenarios.append({
            "imputed_values_m": imputed,
            **stats,
        })

    r2_p = [item["p_r2_ge_observed"] for item in scenarios]
    gradient_p = [item["p_gradient_ge_observed"] for item in scenarios]
    gradients = [item["observed_gradient_norm_m_per_km"] for item in scenarios]
    significant_r2 = [item for item in scenarios if item["p_r2_ge_observed"] < 0.05]
    significant_gradient = [item for item in scenarios if item["p_gradient_ge_observed"] < 0.05]
    both_significant = [
        item for item in scenarios
        if item["p_r2_ge_observed"] < 0.05 and item["p_gradient_ge_observed"] < 0.05
    ]
    return {
        "experiment": "E553 exact missingness sensitivity for E550 CTX/HiRISE nine-position grid",
        "source": payload["source"],
        "grid_positions": 9,
        "measured_patches": 6,
        "unsupported_patches": missing_ids,
        "measured_patch_medians_m": {
            item["patch_id"]: float(item["median_residual_m"]) for item in measured
        },
        "sensitivity_envelope": {
            "basis": "empirical quantiles of the six observed patch medians; not physical bounds",
            "quantile_method": "linear",
            "levels": levels,
            "quantile_probabilities": [float(x) for x in np.linspace(0.0, 1.0, levels)],
            "values_m": grid,
            "completion_scenarios": len(scenarios),
            "permutations_per_scenario": int(len(permutations)),
            "total_exact_permutation_evaluations": int(len(scenarios) * len(permutations)),
            "hypothetical_values_are_measurements": False,
        },
        "summary": {
            "r2_observed_range": [float(min(item["observed_r2"] for item in scenarios)),
                                  float(max(item["observed_r2"] for item in scenarios))],
            "gradient_norm_m_per_km_range": [float(min(gradients)), float(max(gradients))],
            "exact_r2_p_value_range": [float(min(r2_p)), float(max(r2_p))],
            "exact_gradient_p_value_range": [float(min(gradient_p)), float(max(gradient_p))],
            "r2_significant_completion_count": len(significant_r2),
            "gradient_significant_completion_count": len(significant_gradient),
            "both_statistics_significant_completion_count": len(both_significant),
            "completion_count": len(scenarios),
        },
        "significant_completions": both_significant,
        "outcome": "MISSINGNESS_SENSITIVITY_CHANGES_CONDITIONAL_NULL_OUTCOME",
        "interpretation": (
            "The six-patch E551 null remains valid for the six measured locations. "
            "Across hypothetical nine-grid completions restricted to the observed-value quantile envelope, "
            "some completions produce small exact permutation p-values and others do not. "
            "This makes the full-grid gradient status NOT IDENTIFIABLE from current coverage; "
            "the completion count is not a probability or evidence of a real gradient."
        ),
        "claim_state": {
            "six_patch_spatial_gradient": "NOT SUPPORTED BY E551 SIX-PATCH NULL",
            "nine_position_spatial_gradient": "NOT IDENTIFIABLE; THREE POSITIONS UNSUPPORTED",
            "missingness_sensitivity": "SUPPORTED AS A CONDITIONAL COMPUTATIONAL DIAGNOSTIC",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "The three unsupported patch values are unknown; empirical quantiles are sensitivity scenarios, not physical bounds.",
            "The fraction of completions with p<0.05 is not a probability because no distribution over missing values is specified.",
            "Exact permutation p-values are conditional on each hypothetical completed nine-value vector and the exchangeability null.",
            "No imputed value is presented as an observation or used in a scientific correction surface.",
            "The experiment does not establish an actual spatial gradient, geophysical trend, global datum or route safety.",
        ],
        "next_gate": (
            "Recover common valid CTX/HiRISE support at x15_y15, x50_y85 and x85_y85 using a separately verified "
            "product footprint, or preserve the partial-coverage result. Do not impute these locations in the science product."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e552/result.json"))
    parser.add_argument("--levels", type=int, default=5)
    args = parser.parse_args()
    result = analyze(levels=args.levels)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
                        encoding="utf-8")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
