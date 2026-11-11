import unittest

from experiments.e536_grand_falls_sciencebase_probe import (
    ITEMS,
    _child_records,
    _file_records,
    children_url,
    item_url,
    safe_sciencebase_url,
)


class E536ScienceBaseProbeTests(unittest.TestCase):
    def test_known_item_ids_are_valid_and_unique(self):
        ids = [item["item_id"] for item in ITEMS]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertTrue(all(len(item_id) == 24 for item_id in ids))

    def test_item_url_is_pinned_to_sciencebase_catalog(self):
        item_id = ITEMS[0]["item_id"]
        url = item_url(item_id)
        self.assertTrue(url.startswith("https://www.sciencebase.gov/catalog/item/"))
        self.assertTrue(safe_sciencebase_url(url))

    def test_child_query_is_pinned_to_catalog_items_endpoint(self):
        url = children_url(ITEMS[0]["item_id"])
        self.assertTrue(url.startswith("https://www.sciencebase.gov/catalog/items?"))
        self.assertTrue(safe_sciencebase_url(url))

    def test_invalid_item_ids_fail_closed(self):
        with self.assertRaises(ValueError):
            item_url("../not-an-item")
        with self.assertRaises(ValueError):
            children_url("g" * 24)

    def test_lookalike_hosts_and_non_https_urls_are_rejected(self):
        self.assertFalse(safe_sciencebase_url("http://www.sciencebase.gov/catalog/item/abc"))
        self.assertFalse(safe_sciencebase_url("https://sciencebase.gov.example.org/catalog/item/abc"))
        self.assertFalse(safe_sciencebase_url("https://example.org/catalog/item/abc"))

    def test_file_summary_strips_query_tokens_and_deduplicates(self):
        item = {
            "files": [
                {
                    "name": "ripple-dem.zip",
                    "size": 1234,
                    "contentType": "application/zip",
                    "url": "https://www.sciencebase.gov/api/file/123?token=secret",
                },
                {
                    "name": "ripple-dem.zip",
                    "size": 1234,
                    "contentType": "application/zip",
                    "url": "https://www.sciencebase.gov/api/file/123?token=other",
                },
            ],
        }
        files = _file_records(item)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["url_path"], "/api/file/123")
        self.assertFalse(files[0]["url_query_stored"])
        self.assertNotIn("secret", str(files))

    def test_facet_files_are_included(self):
        item = {
            "facets": [{
                "files": [{
                    "name": "metadata.xml",
                    "size": 99,
                    "contentType": "text/xml",
                    "url": "https://sciencebase.gov/api/file/metadata",
                }]
            }]
        }
        files = _file_records(item)
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0]["name"], "metadata.xml")

    def test_child_summary_is_bounded_and_metadata_only(self):
        document = {
            "items": [
                {"id": "a", "title": "DEM", "hasChildren": False, "files": []},
                {"id": "b", "title": "Weather", "hasChildren": True, "files": [{"name": "x"}]},
            ]
        }
        children = _child_records(document)
        self.assertEqual(len(children), 2)
        self.assertEqual(children[1]["file_count_in_listing"], 1)
        self.assertNotIn("download_url", children[0])


if __name__ == "__main__":
    unittest.main()
