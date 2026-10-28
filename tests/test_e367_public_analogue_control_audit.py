"""E367 source-control provenance and negative tests (no network)."""
import pytest

from research.e367_public_analogue_control_audit import audit, download

POLICY = 'role = "positive" if site["kind"] == "environment" else "geology"\nfor site in catalog["negatives"]:\n    pass\ndef roc_auc(positives, negatives): pass'
README = "ROC-AUC 1.00 on all five built-in targets"


def site(name, kind="environment", body="mars"):
    return {
        "name": name, "kind": kind, "bodies": [body],
        "lat": 20.0, "lon": 30.0,
        "source_url": "https://en.wikipedia.org/wiki/Example",
    }


def catalog():
    return {
        "sites": [site("mars"), site("moon", body="moon"),
                  site("geology", kind="geology")],
        "negatives": [{"name": "humid", "lat": 1.0, "lon": 2.0}],
        "provenance": "Negatives are editorial reference points",
    }


def test_counts_are_control_design_not_cross_body_validation():
    result = audit(catalog(), POLICY, README)
    assert result["catalog_sites"] == 3
    assert result["environment_positive_sites"] == 2
    assert result["geology_only_sites_excluded_from_auc"] == 1
    assert result["body_specific_positive_negative_pairs"] == {"mars": 1, "moon": 1}
    assert result["independent_auc_reproduction"] == "NOT PERFORMED"
    assert result["source_self_reports_auc_one"]


def test_fail_closed_on_duplicate_missing_and_invalid_coordinates():
    c = catalog()
    c["negatives"][0]["name"] = "mars"
    with pytest.raises(ValueError):
        audit(c, POLICY, README)
    c = catalog()
    c["sites"][0]["lat"] = 1000.0
    with pytest.raises(ValueError):
        audit(c, POLICY, README)
    c = catalog()
    del c["sites"][0]["lon"]
    with pytest.raises(ValueError):
        audit(c, POLICY, README)


def test_policy_source_mismatch_and_unapproved_fetch_rejected():
    with pytest.raises(ValueError):
        audit(catalog(), "def roc_auc(): pass", README)
    with pytest.raises(ValueError):
        download("../secrets")
