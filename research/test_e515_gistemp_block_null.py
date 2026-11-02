"""E515 frozen deterministic exact-null controls, no network or hidden labels."""
import json
import tempfile
import unittest
from pathlib import Path

from e515_gistemp_block_null import diagnostic, read_snapshot, run, slope_c_per_decade


class E515Tests(unittest.TestCase):
    def test_constant_has_no_trend_and_all_nulls_extreme(self):
        r = diagnostic((7,) * 25)
        self.assertEqual(r["observed_c_per_decade"], 0)
        self.assertEqual(r["block_extreme_two_sided"], 120)
        self.assertEqual(r["circular_extreme_two_sided"], 25)

    def test_exact_linear_trend(self):
        self.assertAlmostEqual(slope_c_per_decade(tuple(range(25))), 0.1)
        r = diagnostic(tuple(range(25)))
        self.assertEqual(r["block_extreme_two_sided"], 1)
        self.assertEqual(r["five_year_block_permutations"], 120)

    def test_reject_wrong_length(self):
        with self.assertRaises(ValueError):
            diagnostic(tuple(range(24)))

    def test_reject_invalid_year_sequence(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "bad.csv"
            p.write_text("year,global_centi_c,tropics_24S_24N_centi_c,arctic_64N_90N_centi_c\n2001,1,2,3\n")
            with self.assertRaises(ValueError):
                read_snapshot(p)

    def test_frozen_real_snapshot_and_contrast(self):
        r = run(Path(__file__).with_name("gistemp_zonal_2001_2025_snapshot.csv"))
        self.assertEqual(r["n_annual_observations"], 25)
        global_r = r["results"]["global_centi_c"]
        contrast = r["results"]["arctic_minus_tropics_centi_c"]
        self.assertAlmostEqual(global_r["observed_c_per_decade"], 0.258769231)
        self.assertEqual(global_r["block_extreme_two_sided"], 1)
        self.assertAlmostEqual(contrast["observed_c_per_decade"], 0.484769231)
        self.assertEqual(contrast["block_extreme_two_sided"], 6)
        self.assertEqual(contrast["circular_extreme_two_sided"], 1)

    def test_committed_receipt_matches_recomputation(self):
        expected = json.loads((Path(__file__).with_name("results") / "e515_gistemp_block_null_20261103.json").read_text())
        actual = run(Path(__file__).with_name("gistemp_zonal_2001_2025_snapshot.csv"))
        self.assertEqual(actual, expected)

    def test_source_hash_is_stable(self):
        a = read_snapshot(Path(__file__).with_name("gistemp_zonal_2001_2025_snapshot.csv"))
        b = read_snapshot(Path(__file__).with_name("gistemp_zonal_2001_2025_snapshot.csv"))
        self.assertEqual(a["sha256"], b["sha256"])
        self.assertEqual(len(a["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
