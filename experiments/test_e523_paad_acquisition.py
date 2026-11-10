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
    build_console_summary,
    choose_primary_table,
    parse_fgdc_metadata,
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


    def test_primary_table_prefers_full_name_csv_over_truncated_shapefile(self):
        candidates = [
            {"format": "shapefile", "record_count": 45, "fields": ["Field_Site", "Center_Lat", "__geometry_json"]},
            {"format": "csv", "record_count": 45, "fields": ["Field_Site", "Center_Latitude", "Center_Longitude"]},
        ]
        self.assertEqual(choose_primary_table(candidates, 45)["format"], "csv")

    def test_fgdc_metadata_supplies_units_and_missing_conventions(self):
        xml = """<?xml version="1.0"?>
        <metadata>
          <idinfo><citation><citeinfo>
            <origin>USGS Author</origin><pubdate>20230620</pubdate>
            <title>PAAD: The Planetary Aeolian Analog Database</title>
            <onlink>https://doi.org/10.5066/P9IFVZEX</onlink>
          </citeinfo></citation></idinfo>
          <eainfo><detailed>
            <attr><attrlabl>Center_Latitude</attrlabl><attrdef>Decimal degrees.</attrdef></attr>
            <attr><attrlabl>Elevation</attrlabl><attrdef>Approximate elevation. Values are reported in meters (m).</attrdef>
              <attrdomv><edom><edomv>&lt;&lt; empty cell &gt;&gt;</edomv><edomvd>No data found.</edomvd></edom></attrdomv>
            </attr>
            <attr><attrlabl>Sand_Source</attrlabl><attrdef>Text source.</attrdef>
              <attrdomv><edom><edomv>NaN</edomv><edomvd>Not found in cited sources.</edomvd></edom></attrdomv>
            </attr>
            <attr><attrlabl>Dune_Type</attrlabl><attrdef>Bedform type.</attrdef>
              <attrdomv><edom><edomv>B</edomv><edomvd>Barchan.</edomvd></edom></attrdomv>
            </attr>
            <attr><attrlabl>Coordinate_Test</attrlabl><attrdef>Coordinates are recorded in decimal degrees.</attrdef></attr>
            <attr><attrlabl>Height_Test</attrlabl><attrdef>Estimated height values are reported in meters (m).</attrdef></attr>
            <attr><attrlabl>Coverage_Test</attrlabl><attrdef>Areal coverage is reported in kilometers squared (km2).</attrdef></attr>
            <attr><attrlabl>Areal_Coverage</attrlabl><attrdef>Areal coverage is reported in kilometers squared (km2).</attrdef></attr>
          </detailed></eainfo>
        </metadata>"""
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "metadata.xml"
            path.write_text(xml, encoding="utf-8")
            metadata = parse_fgdc_metadata(path)
        self.assertEqual(metadata["publication_date"], "2023-06-20")
        self.assertEqual(metadata["doi_url"], "https://doi.org/10.5066/P9IFVZEX")
        self.assertEqual(metadata["attributes"]["Center_Latitude"]["units"], "decimal degrees")
        self.assertEqual(metadata["attributes"]["Elevation"]["units"], "m")
        self.assertTrue(metadata["attributes"]["Elevation"]["approximate"])
        self.assertEqual(metadata["attributes"]["Sand_Source"]["missing_value_conventions"][0]["value"], "NaN")
        self.assertEqual(metadata["attributes"]["Dune_Type"]["domain_values"][0]["definition"], "Barchan.")
        self.assertEqual(metadata["attributes"]["Coordinate_Test"]["units"], "decimal degrees")
        self.assertEqual(metadata["attributes"]["Coordinate_Test"]["data_type"], "coordinate")
        self.assertEqual(metadata["attributes"]["Height_Test"]["units"], "m")
        self.assertTrue(metadata["attributes"]["Height_Test"]["approximate"])
        self.assertEqual(metadata["attributes"]["Height_Test"]["approximation_basis"], "FGDC attribute definition")
        self.assertEqual(metadata["attributes"]["Coverage_Test"]["units"], "km2")
        self.assertFalse(metadata["attributes"]["Coverage_Test"]["approximate"])
        self.assertEqual(metadata["attributes"]["Areal_Coverage"]["units"], "km2")
        self.assertTrue(metadata["attributes"]["Areal_Coverage"]["approximate"])
        self.assertIn("USGS data-release", metadata["attributes"]["Areal_Coverage"]["approximation_basis"])


    def test_console_summary_uses_v2_release_metadata_field(self):
        receipt = {
            "status": "INGESTED",
            "download_archive_sha256": "abc123",
            "primary_table": {
                "format": "csv",
                "record_count": 45,
                "count_matches_release_metadata": True,
                "fields": ["Field_Site"],
                "missing_counts": {},
                "crs_wkt": "GEOGCS[\"WGS 84\"]",
            },
        }
        summary = build_console_summary(receipt)
        self.assertTrue(summary["count_matches_release_metadata"])
        self.assertNotIn("count_matches_release_description", summary)


if __name__ == "__main__":
    unittest.main()
