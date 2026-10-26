"""E291: no source-content or unit claims without actual validated bytes."""
import unittest
from unittest.mock import patch
from urllib.error import HTTPError

from research.e291_diviner_access import parse_numeric_triplets, probe, validate_pds_stn_label


class DivinerAccessTests(unittest.TestCase):
    def test_numeric_triplets_are_uninterpreted(self):
        r = parse_numeric_triplets(b"# source\n1 2 -3\n4,5,6\n")
        self.assertEqual(r["rows"], 2)
        self.assertEqual(r["column_min_uninterpreted"], [1.0, 2.0, -3.0])
        self.assertFalse(r["units_verified"])
        self.assertFalse(r["coordinate_order_verified"])

    def test_reject_html_and_nonfinite_and_wrong_shape(self):
        for raw in (b"<html>error</html>", b"1 2 nan\n", b"1 2\n",
                    b"1 2 3 4\n", b"header not numeric\n", b""):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    parse_numeric_triplets(raw)

    def test_pds_stn_metadata_gate(self):
        label = """DESCRIPTION = "deviation of rock-free regolith surface"
LINES = 3840
LINE_SAMPLES = 11520
SAMPLE_TYPE = LSB_INTEGER
SAMPLE_BITS = 16
UNIT = K
SCALING_FACTOR = 0.02
OFFSET = 0.00
MISSING_CONSTANT = -32768
MAP_RESOLUTION = 32 <pix/degree>
MAP_PROJECTION_TYPE = "SIMPLE CYLINDRICAL"
"""
        metadata = validate_pds_stn_label(label)
        self.assertEqual(metadata["unit"], "K")
        self.assertIn("NOT ABSOLUTE", metadata["semantic"])
        with self.assertRaisesRegex(ValueError, "MISSING_CONSTANT"):
            validate_pds_stn_label(label.replace("-32768", "0"))

    def test_http_failure_is_not_mislabeled_ingestion(self):
        with patch("research.e291_diviner_access.urlopen",
                   side_effect=HTTPError("https://example.org/file", 502,
                                         "Bad Gateway", None, None)):
            r = probe("test", "https://example.org/file")
        self.assertFalse(r["ingested"])
        self.assertEqual(r["http_status"], 502)
        self.assertEqual(r["status"], "SOURCE_UNAVAILABLE_OR_UNVERIFIED")


if __name__ == "__main__":
    unittest.main()
