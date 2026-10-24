"""Deterministic, offline controls for E227. No invented field labels."""
from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import URLError

from research.e227_independent_analogue_labels import (
    DATA, audit, parse_usgs_metadata, probe_usgs,
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


if __name__ == "__main__":
    unittest.main()
