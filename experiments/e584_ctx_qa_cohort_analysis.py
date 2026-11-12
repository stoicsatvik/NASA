"""E584: summarize the bounded E583 Jezero CTX QA cohort.

Descriptive product-level diagnostics only. QA residuals are post-control
differences, not independent validation errors or route-safety evidence.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path


def summarize(document: dict) -> dict:
    items = document.get("items")
    if not isinstance(items, list) or len(items) != 9:
        raise ValueError("E583 receipt must contain exactly nine selected items")
    if document.get("credentials_used") is not False:
        raise ValueError("credential use is outside the frozen E583 design")
    if document.get("qa_success_count") != 9:
        raise ValueError("all nine QA assets must have succeeded")

    means, medians, stddevs = [], [], []
    for item in items:
        if item.get("http_status") != 200:
            raise ValueError("every QA asset must be HTTP 200")
        metrics = item.get("metrics")
        if not isinstance(metrics, dict) or metrics.get("metric_count") != 6:
            raise ValueError("each item must contain six parsed QA metrics")
        for key, target in (
            ("mean_difference_m", means),
            ("median_difference_m", medians),
            ("stddev_difference_m", stddevs),
        ):
            value = metrics.get(key)
            if not isinstance(value, (int, float)):
                raise ValueError(f"missing numeric {key}")
            target.append(float(value))

    target_id = "P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W"
    target = next((x for x in items if x.get("id") == target_id), None)
    if target is None:
        raise ValueError("pinned E580 item absent from cohort")
    target_metrics = target["metrics"]

    return {
        "cohort_size": len(items),
        "qa_success_count": document["qa_success_count"],
        "mean_difference_m": {
            "median": statistics.median(means),
            "minimum": min(means),
            "maximum": max(means),
            "positive_count": sum(value > 0 for value in means),
        },
        "median_difference_m": {
            "median": statistics.median(medians),
            "minimum": min(medians),
            "maximum": max(medians),
            "positive_count": sum(value > 0 for value in medians),
        },
        "stddev_difference_m": {
            "median": statistics.median(stddevs),
            "minimum": min(stddevs),
            "maximum": max(stddevs),
        },
        "pinned_e580_item": {
            "id": target_id,
            "mean_rank_ascending": 1 + sum(value < target_metrics["mean_difference_m"] for value in means),
            "stddev_rank_ascending": 1 + sum(value < target_metrics["stddev_difference_m"] for value in stddevs),
            "mean_difference_m": target_metrics["mean_difference_m"],
            "median_difference_m": target_metrics["median_difference_m"],
            "stddev_difference_m": target_metrics["stddev_difference_m"],
        },
        "inference_boundary": (
            "First nine returned products in one bounded Jezero STAC search; "
            "not a random/exhaustive sample and not nine independent spatial "
            "validation samples. QA residuals are post-control CTX-MOLA "
            "differences; sign convention and absolute accuracy remain unresolved."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "receipt",
        nargs="?",
        default="research/results/E583_CTX_QA_COHORT_SCREEN_20261112.json",
    )
    args = parser.parse_args()
    document = json.loads(Path(args.receipt).read_text(encoding="utf-8"))
    print(json.dumps(summarize(document), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
