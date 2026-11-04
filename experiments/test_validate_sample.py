"""Synthetic fixture controls only; no real planetary data ingested."""
import json
import tempfile
import unittest
from pathlib import Path
from validate_sample import audit

META = dict(source_url="https://example.org/fixture", product_id="SYNTHETIC",
            body="Mars", coordinate_frame="planetocentric-east-positive",
            latitude_unit="degree", longitude_unit="degree", value_unit="m",
            native_resolution="100", native_resolution_unit="m/pixel",
            missing_tokens=["-9999", ""])


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.csv = Path(self.tmp.name) / "sample.csv"
        self.meta = Path(self.tmp.name) / "meta.json"
        self.meta.write_text(json.dumps(META))

    def check(self, rows):
        self.csv.write_text("latitude,longitude,value\n" + rows)
        return audit(self.csv, self.meta)

    def test_valid_and_missing(self):
        result = self.check("0,10,12\n-90,180,-9999\n")
        self.assertEqual((result["valid"], result["missing"], result["minimum"]),
                         (1, 1, 12))

    def test_bad_coordinates(self):
        with self.assertRaisesRegex(ValueError, "coordinates"):
            self.check("91,0,12\n")

    def test_undeclared_fill(self):
        with self.assertRaisesRegex(ValueError, "undeclared"):
            self.check("0,0,N/A\n")

    def test_all_missing(self):
        with self.assertRaisesRegex(ValueError, "No valid"):
            self.check("0,0,-9999\n")

    def test_missing_provenance(self):
        self.meta.write_text("{}")
        with self.assertRaisesRegex(ValueError, "provenance"):
            self.check("0,0,1\n")

    def test_nonfinite(self):
        with self.assertRaisesRegex(ValueError, "nonfinite"):
            self.check("0,0,nan\n")

    def test_units(self):
        self.meta.write_text(json.dumps({**META, "latitude_unit": "radian"}))
        with self.assertRaisesRegex(ValueError, "degree"):
            self.check("0,0,1\n")


if __name__ == "__main__":
    unittest.main()
