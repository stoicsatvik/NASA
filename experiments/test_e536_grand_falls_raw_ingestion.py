import unittest
from experiments.e536_grand_falls_raw_ingestion import (
    _child_items,
    _file_entries,
    _normalize_file,
)


class E536ScienceBaseProbeTests(unittest.TestCase):
    def test_child_items_accepts_sciencebase_list_shape(self):
        self.assertEqual(_child_items({"items": [{"id": "abc"}, None]}), [{"id": "abc"}])

    def test_child_items_accepts_nested_shape(self):
        self.assertEqual(_child_items({"items": {"items": [{"id": "def"}]}}), [{"id": "def"}])

    def test_file_entries_fail_closed_on_non_list(self):
        self.assertEqual(_file_entries({"files": {"name": "not-a-list"}}), [])

    def test_file_normalization_preserves_id_size_and_url(self):
        normalized = _normalize_file(
            "item123",
            {"name": "dem.tif", "size": "1234", "url": "/catalog/file/get/dem.tif/item123"},
        )
        self.assertEqual(normalized["item_id"], "item123")
        self.assertEqual(normalized["size_bytes"], 1234)
        self.assertTrue(normalized["url"].startswith("https://www.sciencebase.gov/"))

    def test_file_without_url_is_not_downloadable(self):
        self.assertIsNone(_normalize_file("item123", {"name": "dem.tif", "size": 1234}))


if __name__ == "__main__":
    unittest.main()
