import unittest

from experiments.e534_remaining_candidate_source_review import (
    NEW_IDS,
    PREVIOUS_IDS,
    SOURCE_COMMIT,
    SOURCE_URL,
    audit,
    safe_source_url,
)


PREVIOUS = [
    ("atacama-yungay-cl", "Mars", "10.1126/science.1089143"),
    ("rio-tinto-es", "Mars", "10.3390/life4030511"),
    ("iceland-volcanic-fields-is", "Mars", "10.3847/PSJ/adb5f1"),
    ("lava-beds-us", "Moon", "10.1029/2021JE007140"),
    ("mauna-kea-us", "Moon", "10.1061/(ASCE)AS.1943-5525.0000200"),
    ("haughton-crater-ca", "Mars", "10.1111/j.1945-5100.2005.tb00144.x"),
]
NEW = [
    ("dallol-et", "Mars", "10.1021/acsearthspacechem.8b00141", "10.1038/s41559-019-1005-0"),
    ("mcmurdo-dry-valleys-aq", "Mars", "10.1016/j.icarus.2007.06.018", "10.1126/science.215.4536.1045"),
    ("arkaroola-au", "Mars", "10.1089/153110702762027916", ""),
    ("lanzarote-es", "Mars", "10.1016/j.scitotenv.2023.169583", ""),
    ("bockfjord-svalbard-sj", "Mars", "10.1111/j.1945-5100.2007.tb00590.x", ""),
    ("boulby-mine-gb", "Mars", "10.1017/S1473550416000045", "10.3389/fmicb.2019.00426"),
]


def row(site_id, target, doi, additional=""):
    return {
        "site_id": site_id,
        "target_body": target,
        "catalogue_status": "Draft",
        "catalogue_doi": doi,
        "additional_doi": additional,
        "source_title": "fixture",
        "source_year": "2024",
        "source_type": "primary research",
        "evidence_relation": "narrow source-to-feature relation",
        "limitations": "not whole-site equivalence",
        "review_decision": "SOURCE_SUPPORTS_CANDIDATE_LABEL",
    }


def feature(site_id, target, dois, status="Draft"):
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [10.0, 20.0]},
        "properties": {
            "id": site_id,
            "analogue_for_primary": target,
            "review_status": status,
            "references": [{"doi": doi} for doi in dois if doi],
        },
    }


def fixtures():
    previous_rows = [row(site, target, doi) for site, target, doi in PREVIOUS]
    new_rows = [row(site, target, doi, additional) for site, target, doi, additional in NEW]
    features = []
    for site, target, doi in PREVIOUS:
        features.append(feature(site, target, [doi]))
    for site, target, doi, additional in NEW:
        features.append(feature(site, target, [doi, additional]))
    return {"type": "FeatureCollection", "features": features}, previous_rows, new_rows


class E534RemainingSourceReviewTests(unittest.TestCase):
    def test_source_is_immutable_and_host_pinned(self):
        self.assertTrue(safe_source_url(SOURCE_URL))
        self.assertEqual(len(SOURCE_COMMIT), 40)
        self.assertFalse(safe_source_url(SOURCE_URL.replace(SOURCE_COMMIT, "main")))
        self.assertFalse(safe_source_url(SOURCE_URL.replace("raw.githubusercontent.com", "example.org")))
        self.assertFalse(safe_source_url(SOURCE_URL + "?raw=1"))

    def test_all_twelve_candidate_records_are_audited_without_promotion(self):
        document, previous_rows, new_rows = fixtures()
        result = audit(document, previous_rows, new_rows, "abc")
        self.assertEqual(result["catalogue_feature_count"], 12)
        self.assertEqual(result["mars_moon_primary_candidate_count"], 12)
        self.assertEqual(result["previous_e533_reviewed_count"], 6)
        self.assertEqual(result["new_e534_reviewed_count"], 6)
        self.assertEqual(result["cumulative_source_audited_count"], 12)
        self.assertEqual(result["unreviewed_mars_moon_candidate_count"], 0)
        self.assertEqual(result["cumulative_target_counts"], {"Mars": 10, "Moon": 2})
        self.assertEqual(result["catalogue_verified_count"], 0)
        self.assertTrue(result["catalogue_statuses_preserved"])
        self.assertTrue(result["candidate_positive_only"])
        self.assertEqual(result["negative_controls"], 0)
        self.assertFalse(result["e001_ready"])
        self.assertEqual(result["known_site_recovery"], "NOT YET MEASURED")

    def test_rejects_promoted_catalogue_record(self):
        document, previous_rows, new_rows = fixtures()
        document["features"][-1]["properties"]["review_status"] = "Verified"
        with self.assertRaises(ValueError):
            audit(document, previous_rows, new_rows, "abc")

    def test_rejects_doi_not_attached_to_pinned_record(self):
        document, previous_rows, new_rows = fixtures()
        new_rows[0]["catalogue_doi"] = "10.9999/not-in-catalogue"
        with self.assertRaises(ValueError):
            audit(document, previous_rows, new_rows, "abc")

    def test_rejects_additional_doi_not_attached_to_pinned_record(self):
        document, previous_rows, new_rows = fixtures()
        new_rows[0]["additional_doi"] = "10.9999/not-in-catalogue"
        with self.assertRaises(ValueError):
            audit(document, previous_rows, new_rows, "abc")

    def test_requires_exact_frozen_new_six_and_no_duplicates(self):
        document, previous_rows, new_rows = fixtures()
        with self.assertRaises(ValueError):
            audit(document, previous_rows, new_rows[:-1], "abc")
        duplicate = list(new_rows)
        duplicate[-1] = dict(duplicate[0])
        with self.assertRaises(ValueError):
            audit(document, previous_rows, duplicate, "abc")

    def test_rejects_overlap_with_preserved_e533_subset(self):
        document, previous_rows, new_rows = fixtures()
        new_rows[0]["site_id"] = previous_rows[0]["site_id"]
        with self.assertRaises(ValueError):
            audit(document, previous_rows, new_rows, "abc")

    def test_rejects_changed_candidate_universe(self):
        document, previous_rows, new_rows = fixtures()
        document["features"].append(feature("unexpected-moon", "Moon", ["10.1000/extra"]))
        with self.assertRaises(ValueError):
            audit(document, previous_rows, new_rows, "abc")


if __name__ == "__main__":
    unittest.main()
