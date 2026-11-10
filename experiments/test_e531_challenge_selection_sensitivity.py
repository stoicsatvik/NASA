import unittest

from experiments.e531_challenge_selection_sensitivity import (
    BASE_WEIGHTS,
    CHALLENGES,
    SCORES,
    run_sensitivity,
)


class E531ChallengeSensitivityTests(unittest.TestCase):
    def test_scorecard_covers_all_fourteen_challenges(self):
        self.assertEqual(len(CHALLENGES), 14)
        self.assertEqual(len(SCORES), 14)
        self.assertTrue(all(len(row) == 5 for row in SCORES))
        self.assertAlmostEqual(sum(BASE_WEIGHTS), 1.0)

    def test_fixed_seed_is_reproducible(self):
        first = run_sensitivity(0.5, draws=2000, seed=526)
        second = run_sensitivity(0.5, draws=2000, seed=526)
        self.assertEqual(first, second)
        self.assertEqual(first["draws"], 2000)
        self.assertEqual(first["seed"], 526)

    def test_winner_share_is_a_sensitivity_frequency_not_a_probability_claim(self):
        result = run_sensitivity(0.25, draws=5000, seed=526)
        self.assertAlmostEqual(sum(result["winner_pct"].values()), 100.0, delta=0.1)
        self.assertIn("Interplanetary Survival Guide: Martian Map", result["winner_pct"])
        self.assertIn("Harmonization of MODIS and VIIRS Hot Spots", result["winner_pct"])


    def test_martian_map_is_modal_under_small_perturbation_fixture(self):
        result = run_sensitivity(0.25, draws=5000, seed=526)
        martian = result["winner_pct"]["Interplanetary Survival Guide: Martian Map"]
        modis = result["winner_pct"]["Harmonization of MODIS and VIIRS Hot Spots"]
        self.assertGreater(martian, modis)

    def test_invalid_scenarios_fail_closed(self):
        with self.assertRaises(ValueError):
            run_sensitivity(-0.1, draws=100)
        with self.assertRaises(ValueError):
            run_sensitivity(0.5, draws=0)


if __name__ == "__main__":
    unittest.main()
