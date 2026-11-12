from experiments.e584_ctx_qa_cohort_analysis import summarize


def fixture():
    return {
        "credentials_used": False,
        "qa_success_count": 9,
        "items": [
            {
                "id": f"item-{i}",
                "http_status": 200,
                "metrics": {
                    "metric_count": 6,
                    "mean_difference_m": value,
                    "median_difference_m": value - 0.1,
                    "stddev_difference_m": spread,
                },
            }
            for i, (value, spread) in enumerate([
                (21.4381, 13.9730),
                (21.2787, 13.4709),
                (37.0019, 12.9054),
                (24.9900, 12.1603),
                (27.3646, 15.6490),
                (40.5091, 12.8508),
                (38.1975, 15.0610),
                (28.4886, 15.0384),
                (27.3687, 10.9340),
            ])
        ],
    }


def test_cohort_summary_and_all_positive_offsets():
    data = fixture()
    data["items"][-1]["id"] = (
        "P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W"
    )
    result = summarize(data)
    assert result["cohort_size"] == 9
    assert result["mean_difference_m"]["positive_count"] == 9
    assert result["median_difference_m"]["positive_count"] == 9
    assert result["mean_difference_m"]["median"] == 27.3687
    assert result["stddev_difference_m"]["minimum"] == 10.934
    assert result["pinned_e580_item"]["mean_rank_ascending"] == 5
    assert result["pinned_e580_item"]["stddev_rank_ascending"] == 1


def test_rejects_partial_cohort():
    data = fixture()
    data["items"].pop()
    try:
        summarize(data)
    except ValueError as error:
        assert "exactly nine" in str(error)
    else:
        raise AssertionError("partial cohort must fail closed")


def test_rejects_credentialed_or_failed_acquisition():
    data = fixture()
    data["credentials_used"] = True
    try:
        summarize(data)
    except ValueError:
        pass
    else:
        raise AssertionError("credentialed acquisition must fail closed")

    data = fixture()
    data["items"][0]["http_status"] = 403
    try:
        summarize(data)
    except ValueError:
        pass
    else:
        raise AssertionError("failed QA asset must fail closed")
