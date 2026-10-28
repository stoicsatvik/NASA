"""Offline, source-role-specific falsification controls for E375."""
import unittest

from research.e375_geology_subset_stress import audit_roles


def fixture(geo_score: float):
    sites = [
        {"name": f"environment-{i}", "kind": "environment",
         "bodies": ["mars"] if i < 5 else ["moon"]}
        for i in range(8)
    ] + [
        {"name": f"geology-{i}", "kind": "geology",
         "bodies": ["mars"] if i == 0 else ["moon"]}
        for i in range(4)
    ]
    negatives = [{"name": f"editorial-{i}"} for i in range(8)]
    samples = {
        **{s["name"]: {"score": 1.0 if s["kind"] == "environment" else geo_score}
           for s in sites},
        **{s["name"]: {"score": -1.0} for s in negatives},
    }
    e369 = {
        "source_repo": "synthetic",
        "source_commit": "fixture",
        "sha256": {},
        "results": {
            feature: {mask: {"control_scores": samples}
                      for mask in ("finite_only", "land_fraction_ge_0_5")}
            for feature in ("vegetation", "precipitation")
        },
    }
    return {"sites": sites, "negatives": negatives}, e369


class RoleStressTests(unittest.TestCase):
    def test_alternative_positives_do_not_become_negatives(self):
        catalog, base = fixture(0.0)
        r = audit_roles(catalog, base)["results"]["vegetation"]["finite_only"]
        self.assertEqual(r["all"]["environment_n"], 8)
        self.assertEqual(r["all"]["geology_n"], 4)
        self.assertEqual(r["mars"]["geology_n"], 1)
        self.assertEqual(r["moon"]["geology_n"], 3)
        self.assertEqual(r["all"]["geology_vs_editorial_auc"], 1.0)
        self.assertEqual(r["all"]["geology_vs_environment_auc"], 0.0)

    def test_source_subset_shift_reduces_apparent_auc(self):
        catalog, base = fixture(-2.0)
        r = audit_roles(catalog, base)["results"]["vegetation"]["finite_only"]
        self.assertEqual(r["all"]["environment_vs_editorial_auc"], 1.0)
        self.assertEqual(r["all"]["geology_vs_editorial_auc"], 0.0)
        self.assertAlmostEqual(r["all"]["pooled_analogue_vs_editorial_auc"], 8 / 12)
        self.assertAlmostEqual(r["mars"]["pooled_analogue_vs_editorial_auc"], 5 / 6)
        self.assertAlmostEqual(r["moon"]["pooled_analogue_vs_editorial_auc"], 3 / 6)

    def test_missing_scores_fail_closed(self):
        catalog, base = fixture(0.0)
        base["results"]["vegetation"]["finite_only"]["control_scores"]["geology-0"]["score"] = None
        with self.assertRaises(ValueError):
            audit_roles(catalog, base)

    def test_unexpected_source_roles_fail_closed(self):
        catalog, base = fixture(0.0)
        catalog["sites"][0]["kind"] = "unknown"
        with self.assertRaises(ValueError):
            audit_roles(catalog, base)


if __name__ == "__main__":
    unittest.main()
