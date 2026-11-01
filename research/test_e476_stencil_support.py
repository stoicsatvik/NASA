"""Deterministic E476 structural and provenance tests."""
import tempfile
import os
import unittest
from pathlib import Path
from research.e476_stencil_support import mask, support, fixed_count_shuffle_null, load_pinned, evaluate

ROOT = Path(os.environ.get("E476_ARTIFACT_DIR", Path(__file__).resolve().parent))
HAS_ARTIFACT = (ROOT / "e472_mars_source.json").is_file() and (ROOT / "e472_moon_source.json").is_file()


class TestE476(unittest.TestCase):
    def test_empty_and_full(self):
        z = support(mask(["000"] * 3, 3))
        f = support(mask(["111"] * 3, 3))
        self.assertEqual((z["full_3x3_centers"], z["five_point_cross_centers"]), (0, 0))
        self.assertEqual((f["full_3x3_centers"], f["five_point_cross_centers"]), (1, 1))

    def test_striped_has_no_cross(self):
        r = support(mask(["10101"] * 5, 5))
        self.assertEqual(r["five_point_cross_centers"], 0)
        self.assertEqual(r["full_3x3_centers"], 0)
        self.assertEqual(r["horizontal_observed_edges"], 0)
        self.assertEqual(r["vertical_observed_edges"], 12)

    def test_invalid_mask_rejected(self):
        for rows in (["000", "010"], ["000", "01x", "000"], ["000", "00", "000"]):
            with self.assertRaises(ValueError):
                mask(rows, 3)

    @unittest.skipUnless(HAS_ARTIFACT, "requires archived E472 source JSON artifact")
    def test_exact_source_digest(self):
        for body in ("mars", "moon"):
            self.assertEqual(len(load_pinned(ROOT / ("e472_" + body + "_source.json"), body)["windows"]), 3)

    @unittest.skipUnless(HAS_ARTIFACT, "requires archived E472 source JSON artifact")
    def test_tamper_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.json"
            p.write_text((ROOT / "e472_mars_source.json").read_text().replace("000110011", "000110010"))
            with self.assertRaisesRegex(ValueError, "unrecognized"):
                load_pinned(p, "mars")

    def test_null_repeatable(self):
        self.assertEqual(fixed_count_shuffle_null(5, 11, 6, 100, 476),
                         fixed_count_shuffle_null(5, 11, 6, 100, 476))

    def test_null_no_anisotropy(self):
        self.assertEqual(fixed_count_shuffle_null(5, 0, 0, 100)["two_sided_mc_tail_plus_one"], 1)

    @unittest.skipUnless(HAS_ARTIFACT, "requires archived E472 source JSON artifact")
    def test_actual_windows(self):
        d = evaluate(load_pinned(ROOT / "e472_mars_source.json", "mars"),
                     load_pinned(ROOT / "e472_moon_source.json", "moon"), 100)
        self.assertEqual(len(d["windows"]), 6)
        self.assertEqual([w["five_point_cross_centers"] for w in d["windows"]], [0, 0, 0, 0, 49, 0])
        self.assertEqual([w["full_3x3_centers"] for w in d["windows"]], [0, 0, 0, 0, 48, 0])


if __name__ == "__main__":
    unittest.main()
