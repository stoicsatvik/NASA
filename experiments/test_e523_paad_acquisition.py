from __future__ import annotations

import csv
import io
import json
import sys
from contextlib import redirect_stdout
from unittest.mock import patch
from pathlib import Path
import tempfile
import unittest
import zipfile

from experiments.e523_paad_acquisition import (
    collect_file_info,
    choose_primary_table,
    parse_fgdc_metadata,
    inspect_csv,
    inspect_geojson,
    inspect_spatial,
    safe_extract_zip,
    validate_item,
    write_normalized_csv,
    main,
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


    def test_cli_summary_uses_receipt_metadata_key(self):
        receipt = {
            "status": "INGESTED",
            "download_archive_sha256": "abc123",
            "primary_table": {
                "format": "csv",
                "record_count": 45,
                "count_matches_release_metadata": True,
                "fields": ["Field_Site"],
                "missing_counts": {},
                "crs_wkt": "LOCAL_CS[\"fixture\"]",
            },
        }
        with tempfile.TemporaryDirectory() as tmp:
            output = io.StringIO()
            with patch.object(sys, "argv", ["e523_paad_acquisition.py", "--out", tmp]):
                with patch("experiments.e523_paad_acquisition.build_receipt", return_value=receipt):
                    with redirect_stdout(output):
                        exit_code = main()
            self.assertEqual(exit_code, 0)
            summary = json.loads(output.getvalue())
            self.assertTrue(summary["count_matches_release_metadata"])
            self.assertNotIn("count_matches_release_description", summary)


    
    def test_spatial_cross_file_check_uses_geometry_precision_not_dbf_rounding(self):
        import shapefile

        def inspect_point(longitude):
            with tempfile.TemporaryDirectory() as tmp:
                base = Path(tmp) / "sites"
                writer = shapefile.Writer(str(base), shapeType=shapefile.POINT)
                writer.field("Field_Site", "C")
                writer.point(longitude, 10.0)
                writer.record("A")
                writer.close()
                candidate = {
                    "rows": [{
                        "Field_Site": "A",
                        "Center_Latitude": "10.0000",
                        "Center_Longitude": "20.0000",
                    }]
                }
                return inspect_spatial(Path(tmp), candidate)["coordinate_validation"]

        exact = inspect_point(20.0)
        self.assertEqual(exact["matched_csv_sites"], 1)
        self.assertEqual(exact["mismatched_csv_sites"], 0)
        self.assertEqual(exact["tolerance_degrees"], 1e-8)

        shifted = inspect_point(20.0001)
        self.assertEqual(shifted["matched_csv_sites"], 0)
        self.assertEqual(shifted["mismatched_csv_sites"], 1)


if __name__ == "__main__":
    unittest.main()
