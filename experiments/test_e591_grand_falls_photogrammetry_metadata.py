import json
import unittest

from experiments.e591_grand_falls_photogrammetry_metadata import (
    CHILD_ITEM_ID,
    audit,
    summarize_document,
)


class E591Tests(unittest.TestCase):
    def test_raster_and_archive_candidates_are_classified(self):
        document = {
            "title": "Grand Falls ripple photogrammetry",
            "spatial": {"type": "Polygon", "coordinates": [[[1, 2], [3, 4]]]},
            "files": [
                {"name": "ripple_dem.tif", "size": 1000},
                {"name": "orthomosaic.jp2", "size": 2000},
                {"name": "source_images.zip", "size": 3000},
                {"name": "metadata.xml", "size": 400},
            ],
        }
        result = summarize_document(document, json.dumps(document).encode())
        self.assertEqual(result["file_count"], 4)
        self.assertEqual(result["raster_candidate_count"], 2)
        self.assertEqual(result["archive_candidate_count"], 1)
        self.assertTrue(result["spatial_extent_present"])
        self.assertEqual(result["source_item_id"], CHILD_ITEM_ID)

    def test_signed_query_values_are_not_stored(self):
        document = {
            "files": [
                {
                    "name": "dem.tif",
                    "size": 1000,
                    "url": "https://www.sciencebase.gov/catalog/file/get/?f=secret-token",
                }
            ]
        }
        result = summarize_document(document, b"fixture")
        encoded = json.dumps(result)
        self.assertNotIn("secret-token", encoded)
        self.assertNotIn("\\\"coordinates\\\":", encoded)
        self.assertFalse(result["raw_urls_stored"])
        self.assertFalse(result["raw_coordinates_stored"])

    def test_http_failure_fails_closed(self):
        result = audit(lambda url, limit: {"status": 403, "payload": b"denied"})
        self.assertEqual(result["decision"], "METADATA_UNAVAILABLE")
        self.assertEqual(result["http_status"], 403)
        self.assertFalse(result["file_bytes_downloaded"])

    def test_empty_inventory_is_not_misreported_as_raster(self):
        result = summarize_document({"title": "Empty item"}, b"{}")
        self.assertEqual(result["decision"], "NO_FILE_RECORDS")
        self.assertEqual(result["raster_candidate_count"], 0)
        self.assertEqual(result["archive_candidate_count"], 0)

    def test_invalid_json_fails_closed(self):
        result = audit(lambda url, limit: {"status": 200, "payload": b"not-json"})
        self.assertEqual(result["decision"], "METADATA_UNAVAILABLE")
        self.assertEqual(result["error_type"], "JSONDecodeError")


if __name__ == "__main__":
    unittest.main()
