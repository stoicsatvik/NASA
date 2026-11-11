"""E551: exact patch-level spatial permutation null for the E550 residual pattern."""
from __future__ import annotations
import itertools
import json
import math
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "e550_patch_summaries.json"


def _solve3(matrix, vector):
    a = [list(row) + [float(value)] for row, value in zip(matrix, vector)]
    for col in range(3):
        pivot = max(range(col, 3), key=lambda row: abs(a[row][col]))
        if abs(a[pivot][col]) < 1e-12:
            raise ValueError("singular plane design")
        a[col], a[pivot] = a[pivot], a[col]
        scale = a[col][col]
        a[col] = [value / scale for value in a[col]]
        for row in range(3):
            if row == col:
                continue
            factor = a[row][col]
            a[row] = [a[row][j] - factor * a[col][j] for j in range(4)]
    return [a[i][3] for i in range(3)]


def _plane_stats(points, values):
    if len(points) != len(values) or len(points) < 4:
        raise ValueError("at least four paired patch points are required")
    x0 = sum(p["center_x"] for p in points) / len(points)
    y0 = sum(p["center_y"] for p in points) / len(points)
    design = [[1.0, (p["center_x"] - x0) / 1000.0, (p["center_y"] - y0) / 1000.0] for p in points]
    xtx = [[sum(row[i] * row[j] for row in design) for j in range(3)] for i in range(3)]
    xty = [sum(design[k][i] * values[k] for k in range(len(values))) for i in range(3)]
    beta = _solve3(xtx, xty)
    predicted = [sum(row[j] * beta[j] for j in range(3)) for row in design]
    mean_y = sum(values) / len(values)
    sse = sum((values[i] - predicted[i]) ** 2 for i in range(len(values)))
    sst = sum((value - mean_y) ** 2 for value in values)
    r2 = 1.0 - sse / sst if sst > 0 else 0.0
    slope_norm = math.hypot(beta[1], beta[2])
    return {"intercept_m_at_patch_centroid": beta[0], "slope_x_m_per_km": beta[1],
            "slope_y_m_per_km": beta[2], "slope_norm_m_per_km": slope_norm,
            "r2_descriptive": r2, "n_patches": len(points)}


def _sign_test_two_sided(values):
    nonzero = [v for v in values if v != 0]
    n = len(nonzero)
    negatives = sum(v < 0 for v in nonzero)
    tail = sum(math.comb(n, k) for k in range(negatives, n + 1)) / (2 ** n)
    lower_tail = sum(math.comb(n, k) for k in range(0, negatives + 1)) / (2 ** n)
    return {"n_nonzero": n, "negative": negatives, "positive": n - negatives,
            "one_sided_negative_p": tail, "two_sided_p": min(1.0, 2.0 * min(tail, lower_tail))}


def analyze(path=DATA):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    patches = payload["patches"]
    if len(patches) != 9 or len({p["patch_id"] for p in patches}) != 9:
        raise ValueError("E550 must contain nine unique preregistered grid positions")
    measured = [p for p in patches if p["common_valid_cells"] > 0 and p["median_residual_m"] is not None]
    unsupported = [p["patch_id"] for p in patches if p["common_valid_cells"] == 0]
    if len(measured) != 6 or len(unsupported) != 3:
        raise ValueError("expected six measured patches and three unsupported patches")
    for p in measured:
        if p["common_valid_cells"] != 25 or p.get("coverage_min") != 1.0:
            raise ValueError("measured patches must preserve the E550 25/25, 100% support contract")
    points = [{"center_x": p["center_x"], "center_y": p["center_y"]} for p in measured]
    values = [float(p["median_residual_m"]) for p in measured]
    observed = _plane_stats(points, values)
    perm_r2, perm_slope = [], []
    for permuted in itertools.permutations(values):
        stats = _plane_stats(points, list(permuted))
        perm_r2.append(stats["r2_descriptive"])
        perm_slope.append(stats["slope_norm_m_per_km"])
    n_perm = len(perm_r2)
    p_r2 = sum(v >= observed["r2_descriptive"] - 1e-12 for v in perm_r2) / n_perm
    p_slope = sum(v >= observed["slope_norm_m_per_km"] - 1e-12 for v in perm_slope) / n_perm
    loo = []
    for omitted in range(len(values)):
        keep_points = [p for i, p in enumerate(points) if i != omitted]
        keep_values = [v for i, v in enumerate(values) if i != omitted]
        stats = _plane_stats(keep_points, keep_values)
        loo.append({"omitted_patch": measured[omitted]["patch_id"], **stats})
    return {
        "experiment": "E551 exact patch-level spatial permutation null for E550 CTX/HiRISE residuals",
        "source": payload["source"],
        "grid_positions": 9,
        "measured_patches": len(measured),
        "unsupported_patches": unsupported,
        "patch_medians": [{"patch_id": p["patch_id"], "fraction_x": p["fraction_x"],
                            "fraction_y": p["fraction_y"], "median_residual_m": p["median_residual_m"]}
                           for p in measured],
        "observed_plane": observed,
        "exact_permutation": {
            "permutations": n_perm,
            "r2_null_median": median(perm_r2),
            "r2_null_p95": sorted(perm_r2)[math.ceil(0.95 * n_perm) - 1],
            "r2_null_max": max(perm_r2),
            "p_r2_ge_observed": p_r2,
            "slope_norm_null_median": median(perm_slope),
            "slope_norm_null_p95": sorted(perm_slope)[math.ceil(0.95 * n_perm) - 1],
            "slope_norm_null_max": max(perm_slope),
            "p_slope_norm_ge_observed": p_slope,
            "exchangeability_boundary": "patch medians are permuted across the six measured locations; the three unsupported locations are excluded, so spatially informative missingness remains unresolved"
        },
        "sign_test": _sign_test_two_sided(values),
        "leave_one_patch_out": loo,
        "summary": {
            "all_nine_positions_measured": False,
            "common_support_fraction_of_grid": len(measured) / len(patches),
            "spatial_plane_permutation_signal": "NOT SUPPORTED BY THIS SIX-PATCH NULL TEST" if p_r2 >= 0.05 and p_slope >= 0.05 else "CANDIDATE SIGNAL",
            "residual_sign_consistency": "DESCRIPTIVE ONLY"
        },
        "claim_state": {
            "CTX_HiRISE_projection_parameter_equivalence": "SUPPORTED BY E550",
            "six_patch_common_support": "SUPPORTED FOR SIX PATCHES ONLY",
            "nine_position_common_support": "PARTIAL; THREE PATCHES HAVE ZERO COMMON VALID CELLS",
            "spatially_coherent_residual_gradient": "NOT SUPPORTED BY THIS SIX-PATCH PERMUTATION TEST",
            "local vertical residual": "MEASURED FOR SIX PATCHES ONLY",
            "global vertical offset reproduction": "NOT ESTABLISHED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED"
        },
        "limitations": [
            "Only six of nine preregistered positions have common valid CTX/HiRISE support.",
            "The exact permutation test treats the six patch medians as exchangeable under the null; spatially informative missingness is unresolved.",
            "Pixels within a patch are not independent; patch medians are the permutation units.",
            "The test concerns a descriptive plane over one local Jezero overlap, not a global vertical datum or geophysical model.",
            "No cross-body similarity, known-site recovery, analogue discovery or route safety is tested."
        ]
    }


if __name__ == "__main__":
    print(json.dumps(analyze(), indent=2, sort_keys=True))
