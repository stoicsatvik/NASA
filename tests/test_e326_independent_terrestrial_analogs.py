"""E326 independent-source integrity and conservative claim fixtures."""
import io
import json
import unittest
from zipfile import ZipFile

from research.e326_independent_terrestrial_analogs import (
    ITEM_ID, audit, metadata_files, permitted_download,
    profile_csv, profile_geojson, profile_zip, public_arcgis_base, arcgis_inventory,
)


def item(files=None):
    return {"id": ITEM_ID, "title": "Known Terrestrial Analog Sites for Planetary Science",
            "files": files or []}


class TestE326(unittest.TestCase):
    def test_reject_wrong_catalog_identity(self):
        with self.assertRaises(ValueError):
            metadata_files({"id": "other", "title": item()["title"]})
        with self.assertRaises(ValueError):
            metadata_files({"id": ITEM_ID, "title": "Unrelated"})

    def test_only_sciencebase_catalog_download(self):
        self.assertTrue(permitted_download(
            "https://www.sciencebase.gov/catalog/file/get/" + ITEM_ID))
        for url in ("http://www.sciencebase.gov/catalog/file/get/" + ITEM_ID,
                    "https://evil.example/catalog/file/get/" + ITEM_ID,
                    "https://www.sciencebase.gov/catalog/item/" + ITEM_ID,
                    "https://user@www.sciencebase.gov/catalog/file/get/" + ITEM_ID):
            self.assertFalse(permitted_download(url))

    def test_csv_labels_not_inferred_as_negatives(self):
        result = profile_csv(b"site,type,process\nA,impact,crater\nB,volcanic,eruption\n",
                             "analog.csv")
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["candidate_class_fields"]["type"],
                         {"impact": 1, "volcanic": 1})
        self.assertFalse(result["coordinates_validated"])

    def test_geojson_properties_not_coordinates_certification(self):
        raw = json.dumps({"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {"type": "aeolian"},
             "geometry": {"type": "Point", "coordinates": [100, 20]}}
        ]}).encode()
        result = profile_geojson(raw, "analog.geojson")
        self.assertEqual(result["rows"], 1)
        self.assertEqual(result["geometry_types"]["Point"], 1)
        self.assertFalse(result["coordinates_validated"])

    def test_zip_no_extraction_or_traversal(self):
        stream = io.BytesIO()
        with ZipFile(stream, "w") as z:
            z.writestr("../traversal.csv", "type,site\nimpact,A\n")
        result = profile_zip(stream.getvalue(), "catalog.zip")
        self.assertEqual(result[0]["rows"], 1)
        self.assertEqual(result[0]["file"], "../traversal.csv")

    def test_download_receipt_and_claim_boundaries(self):
        uri = "https://www.sciencebase.gov/catalog/file/get/" + ITEM_ID
        sample = b"type,site\naeolian,A\n"
        f = {"name": "sites.csv", "downloadUri": uri, "size": len(sample)}
        result = audit(item([f]), lambda url, max_bytes: sample)
        self.assertEqual(result["status"], "TABULAR_SOURCE_INGESTED")
        self.assertEqual(result["tabular_rows_profiled"], 1)
        self.assertEqual(result["e001_known_site_recovery"], "NOT YET MEASURED")
        self.assertEqual(result["cross_body_similarity"], "NOT YET PROVEN")


    def test_public_arcgis_link_strips_embedded_query_credentials(self):
        from research.e326_independent_terrestrial_analogs import ARCGIS_PATH
        original = "https://services.arcgis.com" + ARCGIS_PATH + "?token=EXAMPLE"
        source = item()
        source["webLinks"] = [{"title": "Arc REST Web Service", "uri": original}]
        base = public_arcgis_base(source)
        self.assertEqual(base, "https://services.arcgis.com" + ARCGIS_PATH)
        self.assertNotIn("EXAMPLE", base)

    def test_tokenless_public_feature_ingestion_and_auth_failure(self):
        from research.e326_independent_terrestrial_analogs import ARCGIS_PATH
        base = "https://services.arcgis.com" + ARCGIS_PATH
        calls = []
        def fake(url, maximum=5_000_000):
            calls.append(url)
            if url.endswith("?f=json"):
                return b'{"layers":[{"id":0}]}'
            if "returnCountOnly=true" in url:
                return b'{"count":2}'
            return json.dumps({"features": [
                {"attributes": {"Type": "impact"}, "geometry": {"x": 1, "y": 2}},
                {"attributes": {"Type": "volcanic"}, "geometry": {"x": 3, "y": 4}},
            ]}).encode()
        result = arcgis_inventory(base, fake)
        self.assertEqual(result["status"], "PUBLIC_FEATURES_INGESTED")
        self.assertEqual(result["rows"], 2)
        self.assertEqual(result["features_with_geometry"], 2)
        self.assertTrue(all("token=" not in url for url in calls))
        denied = arcgis_inventory(base, lambda url, maximum=5_000_000:
                                  b'{"error":{"code":498}}')
        self.assertEqual(denied["status"], "PUBLIC_SERVICE_ERROR")
        self.assertEqual(denied["error_code"], 498)

    def test_oversized_skipped(self):
        uri = "https://www.sciencebase.gov/catalog/file/get/" + ITEM_ID
        f = {"name": "big.zip", "downloadUri": uri, "size": 40_000_000}
        result = audit(item([f]), lambda url, max_bytes: self.fail("should not fetch"))
        self.assertEqual(result["status"], "NO_TABULAR_RECORDS_INGESTED")
        self.assertEqual(result["download_profiles"][0]["status"], "DECLARED_OVERSIZED")


if __name__ == "__main__":
    unittest.main()
