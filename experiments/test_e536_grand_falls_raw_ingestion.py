import tempfile
import unittest
import zipfile
from pathlib import Path

from experiments.e536_grand_falls_raw_ingestion import (
    MAX_DOWNLOAD_BYTES,
    _catalogue_total_bytes,
    _child_items,
    _extract_first_tiff,
    _file_entries,
    _has_tiff_magic,
    _has_zip_magic,
    _is_direct_file_url,
    _normalize_file,
    _payload_matches,
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

    def test_manager_preview_route_is_not_a_direct_file_download(self):
        self.assertFalse(_is_direct_file_url(
            "https://sciencebase.usgs.gov/manager/item/662bccfad34ea70bd5f11f88/file/abc"
        ))
        self.assertTrue(_is_direct_file_url(
            "https://www.sciencebase.gov/catalog/file/get/662bccfad34ea70bd5f11f88?f=abc"
        ))
        self.assertFalse(_is_direct_file_url("http://www.sciencebase.gov/catalog/file/get/item"))

    def test_html_preview_bytes_do_not_pass_raster_or_archive_magic(self):
        html = b"<!doctype html>"
        tiff = bytes([73, 73, 42, 0, 8, 0, 0, 0])
        zip_header = bytes([80, 75, 3, 4, 20, 0, 0, 0])
        self.assertFalse(_has_tiff_magic(html))
        self.assertFalse(_payload_matches("dem.tif", html))
        self.assertTrue(_has_tiff_magic(tiff))
        self.assertTrue(_has_zip_magic(zip_header))
        self.assertFalse(_payload_matches("archive.zip", html))

    def test_item_archive_budget_requires_complete_catalogue_sizes(self):
        files = [{"size_bytes": 1171078}, {"size_bytes": 441}, {"size_bytes": 1170},
                 {"size_bytes": 21475}, {"size_bytes": 619492}, {"size_bytes": 46617552}]
        self.assertEqual(_catalogue_total_bytes(files), 48429208)
        self.assertLess(_catalogue_total_bytes(files), MAX_DOWNLOAD_BYTES)
        self.assertGreater(_catalogue_total_bytes([{"size_bytes": MAX_DOWNLOAD_BYTES + 1}]), MAX_DOWNLOAD_BYTES)
        self.assertIsNone(_catalogue_total_bytes([{"size_bytes": 100}, {"size_bytes": None}]))

    def test_archive_extracts_only_smallest_valid_tiff(self):
        small = bytes([73, 73, 42, 0, 8, 0, 0, 0]) + b"small-payload"
        large = bytes([73, 73, 42, 0, 8, 0, 0, 0]) + b"large-payload" * 10
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "item.zip"
            destination = Path(directory) / "sample.tif"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("large.tif", large)
                archive.writestr("small.tif", small)
            result = _extract_first_tiff(archive_path, destination)
            self.assertTrue(result["extracted"])
            self.assertEqual(result["member"], "small.tif")
            self.assertEqual(destination.read_bytes(), small)

    def test_archive_refuses_html_disguised_as_tiff(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_path = Path(directory) / "item.zip"
            destination = Path(directory) / "sample.tif"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("fake.tif", b"<!doctype html>")
            result = _extract_first_tiff(archive_path, destination)
            self.assertFalse(result["extracted"])
            self.assertEqual(result["reason"], "contained_file_has_no_tiff_magic")
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
