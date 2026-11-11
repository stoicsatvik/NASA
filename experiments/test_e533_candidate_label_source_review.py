import unittest

from experiments.e533_candidate_label_source_review import (
    SOURCE_COMMIT, SOURCE_URL, audit, safe_source_url
)


def feature(site_id, target="Mars", status="Draft", doi="10.1126/science.1089143"):
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [10.0, 20.0]},
        "properties": {
            "id": site_id,
            "analogue_for_primary": target,
            "review_status": status,
            "references": [{"doi": doi}],
        },
    }


def row(site_id="atacama-yungay-cl", target="Mars", doi="10.1126/science.1089143"):
    return {
        "site_id": site_id,
        "target_body": target,
        "catalogue_status": "Draft",
        "catalogue_doi": doi,
        "additional_doi": "",
        "source_title": "fixture source",
        "source_year": "2003",
        "source_type": "primary research",
        "evidence_relation": "direct",
        "limitations": "narrow feature scope",
        "review_decision": "SOURCE_SUPPORTS_CANDIDATE_LABEL",
    }


class E533SourceReviewTests(unittest.TestCase):
    def test_source_is_immutable_and_host_pinned(self):
        self.assertTrue(safe_source_url(SOURCE_URL))
        self.assertEqual(len(SOURCE_COMMIT), 40)
        self.assertFalse(safe_source_url(SOURCE_URL.replace(SOURCE_COMMIT, "main")))
        self.assertFalse(safe_source_url(SOURCE_URL.replace("raw.githubusercontent.com", "example.org")))
        self.assertFalse(safe_source_url(SOURCE_URL + "?raw=1"))

    def test_audit_preserves_draft_and_candidate_only_boundary(self):
        rows = [row(f"site-{i}", "Mars" if i < 4 else "Moon") for i in range(6)]
        # Use distinct IDs/DOIs in the fixture.
        rows[0]["site_id"] = "atacama-yungay-cl"
        rows[0]["catalogue_doi"] = "10.1126/science.1089143"
        features = [feature("atacama-yungay-cl")]
        for i in range(1, 6):
            target = "Mars" if i < 4 else "Moon"
            doi = f"10.1000/{i}"
            rows[i]["catalogue_doi"] = doi
            features.append(feature(f"site-{i}", target, doi=doi))
        document = {"type": "FeatureCollection", "features": features}
        result = audit(document, rows, "abc")
        self.assertEqual(result["catalogue_feature_count"], 6)
        self.assertEqual(result["mars_moon_primary_candidate_count"], 6)
        self.assertEqual(result["predeclared_reviewed_count"], 6)
        self.assertEqual(result["reviewed_target_counts"], {"Mars": 4, "Moon": 2})
        self.assertEqual(result["catalogue_verified_count"], 0)
        self.assertFalse(result["e001_ready"])
        self.assertEqual(result["negative_controls"], 0)
        self.assertEqual(result["known_site_recovery"], "NOT YET MEASURED")

    def test_rejects_promoted_or_mismatched_catalogue_status(self):
        rows = [row(f"site-{i}", "Mars" if i < 4 else "Moon",
                     "10.1126/science.1089143" if i == 0 else f"10.1000/{i}")
                for i in range(6)]
        rows[0]["site_id"] = "atacama-yungay-cl"
        features = [feature("atacama-yungay-cl")]
        for i in range(1, 6):
            target = "Mars" if i < 4 else "Moon"
            features.append(feature(f"site-{i}", target, doi=f"10.1000/{i}"))
        features[0]["properties"]["review_status"] = "Verified"
        with self.assertRaises(ValueError):
            audit({"type": "FeatureCollection", "features": features}, rows, "abc")

    def test_rejects_doi_not_attached_to_pinned_record(self):
        rows = [row(f"site-{i}", "Mars" if i < 4 else "Moon",
                     "10.1126/science.1089143" if i == 0 else f"10.1000/{i}")
                for i in range(6)]
        rows[0]["site_id"] = "atacama-yungay-cl"
        rows[0]["catalogue_doi"] = "10.9999/not-in-catalogue"
        features = [feature("atacama-yungay-cl")]
        for i in range(1, 6):
            features.append(feature(f"site-{i}", "Mars" if i < 4 else "Moon", doi=f"10.1000/{i}"))
        with self.assertRaises(ValueError):
            audit({"type": "FeatureCollection", "features": features}, rows, "abc")

    def test_requires_exact_predeclared_six_and_no_duplicate_ids(self):
        with self.assertRaises(ValueError):
            audit({"type": "FeatureCollection", "features": []}, [row()], "abc")
        rows = [row("same") for _ in range(6)]
        with self.assertRaises(ValueError):
            audit({"type": "FeatureCollection", "features": []}, rows, "abc")


if __name__ == "__main__":
    unittest.main()
