"""Deterministic, offline controls for E227. No invented field labels."""
from __future__ import annotations

import copy
import json
from io import BytesIO
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from research.e227_independent_analogue_labels import (
    DATA, audit, parse_usgs_metadata, probe_usgs, safe_public_service_url, probe_public_arcgis,
)


class E227AuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(Path(DATA).read_text(encoding="utf-8"))

    def test_nasa_gallery_counts_and_claim_boundary(self):
        result = audit(self.source)
        self.assertEqual(result["examples"], 11)
        self.assertEqual(result["moon_mars_examples"], 9)
        self.assertEqual(result["analyst_marked_surface_morphology_component"], 5)
        self.assertEqual(result["e001_known_site_recovery"], "NOT YET MEASURED")

    def test_duplicate_source_example_fails_closed(self):
        source = copy.deepcopy(self.source)
        source["pairs"][1]["id"] = source["pairs"][0]["id"]
        with self.assertRaises(ValueError):
            audit(source)

    def test_invented_coordinates_fail_closed(self):
        source = copy.deepcopy(self.source)
        source["pairs"][0]["latitude"] = 42.0
        with self.assertRaises(ValueError):
            audit(source)

    def test_missing_source_heading_fails_closed(self):
        source = copy.deepcopy(self.source)
        source["pairs"][0]["source_heading"] = ""
        with self.assertRaises(ValueError):
            audit(source)

    def test_usgs_metadata_parser_never_claims_coordinates(self):
        item = {
            "id": "5f88940b82cebb8c13d912ee",
            "title": "Known Terrestrial Analog Sites for Planetary Science",
            "files": [{"name": "analog.zip", "size": 123, "downloadUri": "https://example.invalid/data.zip"}],
        }
        result = parse_usgs_metadata(item)
        self.assertEqual(result["file_count"], 1)
        self.assertEqual(result["coordinates_ingested"], 0)
        with self.assertRaises(ValueError):
            parse_usgs_metadata({"title": "Unrelated dataset"})

    def test_usgs_network_failure_is_explicit(self):
        with patch("research.e227_independent_analogue_labels.urlopen", side_effect=URLError("offline")):
            result = probe_usgs()
        self.assertEqual(result["status"], "ACCESS_FAILED")
        self.assertEqual(result["coordinates_ingested"], 0)
        self.assertIn("NOT INGESTED", result["claim"])



    def test_public_service_token_is_never_persisted(self):
        uri = ("https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/"
               "Terrestrial_Analog_Sites_for_Planetary_Science/FeatureServer?token=SECRET")
        safe = safe_public_service_url(uri)
        self.assertIsNotNone(safe)
        self.assertNotIn("SECRET", safe)
        self.assertNotIn("token=", safe)
        self.assertIsNone(safe_public_service_url("https://example.invalid/FeatureServer?token=SECRET"))
        item = {"id": "5f88940b82cebb8c13d912ee",
                "title": "Known Terrestrial Analog Sites for Planetary Science",
                "webLinks": [{"title": "Arc REST Web Service", "uri": uri}]}
        self.assertNotIn("SECRET", json.dumps(parse_usgs_metadata(item)))

    def test_public_geojson_probe_requires_valid_point_geometry(self):
        body = json.dumps({"type": "FeatureCollection", "features": [
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [-111.5, 35.1]},
             "properties": {"name": "synthetic"}},
            {"type": "Feature", "geometry": {"type": "Point", "coordinates": [300, 95]},
             "properties": {"name": "invalid"}},
        ]}).encode()
        with patch("research.e227_independent_analogue_labels.urlopen", return_value=BytesIO(body)) as mocked:
            result = probe_public_arcgis(
                "https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/"
                "Terrestrial_Analog_Sites_for_Planetary_Science/FeatureServer"
            )
        self.assertEqual(result["status"], "PUBLIC_SAMPLE_INGESTED")
        self.assertEqual(result["point_features_ingested"], 1)
        self.assertFalse(result["authenticated"])
        self.assertNotIn("token=", mocked.call_args.args[0].full_url)


if __name__ == "__main__":
    unittest.main()
