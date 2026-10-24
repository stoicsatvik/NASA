"""E227 coordinate QC deterministic controls; no synthetic data used as evidence."""
import unittest

from research.e227_usgs_coordinate_qc import audit, distance_m


class USGSCoordinateQCTests(unittest.TestCase):
    def test_distance_symmetry_and_zero(self):
        self.assertEqual(distance_m(0, 0, 0, 0), 0)
        self.assertAlmostEqual(distance_m(34, -116, 35, -116),
                               distance_m(35, -116, 34, -116), places=8)

    def test_coordinate_validation(self):
        with self.assertRaises(ValueError):
            distance_m(91, 0, 0, 0)

    def test_missing_body_and_discrepancy_are_separate(self):
        sample = {"usgs": {"arcgis_public_sample": {
            "status": "PUBLIC_SAMPLE_INGESTED", "point_features_ingested": 2,
            "raw_sha256": "synthetic-fixture",
            "first_five_points": [
                {"latitude": 0, "longitude": 0,
                 "attributes": {"Name": "A", "FID": 1, "Lat": 0, "Lon": 0,
                                "AnalogBody": "Mars", "AnalogType": "Impact"}},
                {"latitude": 0, "longitude": 0,
                 "attributes": {"Name": "B", "FID": 2, "Lat": 1, "Lon": 0,
                                "AnalogBody": " ", "AnalogType": "Volcanic"}},
            ],
        }}}
        result = audit(sample)
        self.assertEqual(result["sample_count"], 2)
        self.assertEqual(result["body_missing_count"], 1)
        self.assertEqual(result["coordinate_discrepancies_over_100m"], 1)
        self.assertGreater(result["max_coordinate_discrepancy_m"], 100000)
        self.assertIn("NOT YET MEASURED", result["claim"])

    def test_truncated_sample_cannot_masquerade_as_complete(self):
        source = {"usgs": {"arcgis_public_sample": {
            "status": "PUBLIC_SAMPLE_INGESTED", "point_features_ingested": 10,
            "first_five_points": [],
        }}}
        with self.assertRaises(ValueError):
            audit(source)


if __name__ == "__main__":
    unittest.main()
