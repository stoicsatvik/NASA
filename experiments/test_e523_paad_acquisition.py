from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from experiments.e523_paad_acquisition import (
    collect_file_info,
    inspect_csv,
    inspect_geojson,
    safe_extract_zip,
    validate_item,
    write_normalized_csv,
)


class PAADIngestionTests(unittest.TestCase):
    def test_collects_top_level_and_facet_files_without_duplicates(self):
        item = {
            "files": [{"name": "sites.zip", "url": "https://example.test/sites.zip", "size": 12}],
            "facets": [{"files": [
                {"name": "sites.zip", "url": "https://example.test/sites.zip", "size": 12},
                {"name": "metadata.xml", "url": "https://example.test/metadata.xml", "size": 5},
            ]}],
        }
        files = collect_file_info(item)
        self.assertEqual([entry["name"] for entry in files], ["sites.zip", "metadata.xml"])

    def test_item_identity_fails_closed(self):
        validate_item({"id": "64d418c3d34ef477cf3ced10", "title": "PAAD: Planetary Aeolian Analog Database"})
        with self.assertRaisesRegex(ValueError, "ID"):
            validate_item({"id": "wrong", "title": "PAAD: Planetary Aeolian Analog Database"})
        with self.assertRaisesRegex(ValueError, "title"):
            validate_item({"id": "64d418c3d34ef477cf3ced10", "title": "unrelated data"})

    def test_csv_counts_rows_and_missing_values(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sites.csv"
            path.write_text("site_name,latitude,longitude\nA,1.0,2.0\nB,,3.0\n", encoding="utf-8")
            result = inspect_csv(path)
            self.assertIsNotNone(result)
            self.assertEqual(result["record_count"], 2)
            self.assertEqual(result["missing_counts"]["latitude"], 1)
            self.assertEqual(result["missing_counts"]["longitude"], 0)

    def test_geojson_preserves_geometry_and_properties(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sites.geojson"
            path.write_text(json.dumps({
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"site": "A", "climate": "arid"},
                    "geometry": {"type": "Point", "coordinates": [10.0, 20.0]},
                }],
            }), encoding="utf-8")
            result = inspect_geojson(path)
            self.assertIsNotNone(result)
            self.assertEqual(result["record_count"], 1)
            self.assertIn("__geometry_json", result["fields"])
            self.assertEqual(result["rows"][0]["site"], "A")

    def test_safe_zip_extracts_normal_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = io.BytesIO()
            with zipfile.ZipFile(payload, "w") as archive:
                archive.writestr("paad/sites.csv", "site\nA\n")
            extracted = safe_extract_zip(payload.getvalue(), Path(tmp))
            self.assertEqual(len(extracted), 1)
            self.assertEqual(extracted[0].read_text(encoding="utf-8"), "site\nA\n")

    def test_safe_zip_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = io.BytesIO()
            with zipfile.ZipFile(payload, "w") as archive:
                archive.writestr("../escape.txt", "no")
            with self.assertRaisesRegex(ValueError, "unsafe archive path"):
                safe_extract_zip(payload.getvalue(), Path(tmp))

    def test_normalized_csv_preserves_all_source_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "paad_sites.csv"
            candidate = {
                "fields": ["site", "latitude"],
                "source_file": "sites.csv",
                "rows": [{"site": "A", "latitude": "1.0"}, {"site": "B", "latitude": ""}],
            }
            write_normalized_csv(output, candidate)
            with output.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[1]["site"], "B")
            self.assertEqual(rows[1]["source_file"], "sites.csv")


if __name__ == "__main__":
    unittest.main()
