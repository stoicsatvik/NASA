from __future__ import annotations

import unittest
from pathlib import Path

from experiments.e574_support_gain_decomposition import run


ROOT = Path(__file__).resolve().parents[1]


class E574SupportGainDecompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.result = run(ROOT / "research" / "receipts" / "e573_support_summary.json")

    def test_baseline_gain_reconciles_exactly(self):
        d = self.result["decomposition"]
        self.assertEqual(d["total_net_support_delta"], 95)
        self.assertEqual(d["shared_footprint_validity_delta"], 22)
        self.assertEqual(d["footprint_only_validity_delta"], 73)
        self.assertEqual(22 + 73, 95)

    def test_most_net_gain_is_footprint_extent_not_shared_mask(self):
        d = self.result["decomposition"]
        self.assertAlmostEqual(d["footprint_component_share_pct"], 76.8421052632, places=8)
        self.assertAlmostEqual(d["shared_footprint_component_share_pct"], 23.1578947368, places=8)

    def test_common_mode_offsets_preserve_positive_advantage(self):
        s = self.result["sensitivity"]["common_mode_translation"]
        self.assertEqual(s["offsets"], 13)
        self.assertEqual((s["total_valid_delta_min"], s["total_valid_delta_max"]), (94, 95))
        self.assertEqual((s["shared_footprint_validity_delta_min"], s["shared_footprint_validity_delta_max"]), (21, 22))
        self.assertEqual((s["footprint_only_validity_delta_min"], s["footprint_only_validity_delta_max"]), (73, 73))

    def test_differential_offsets_preserve_positive_advantage(self):
        s = self.result["sensitivity"]["differential_2025_translation"]
        self.assertEqual(s["offsets"], 13)
        self.assertEqual((s["total_valid_delta_min"], s["total_valid_delta_max"]), (95, 95))
        self.assertEqual((s["shared_footprint_validity_delta_min"], s["shared_footprint_validity_delta_max"]), (22, 22))
        self.assertEqual((s["footprint_only_validity_delta_min"], s["footprint_only_validity_delta_max"]), (73, 73))

    def test_claim_boundary_does_not_promote_support_to_accuracy(self):
        claim = self.result["claim_state"]
        self.assertEqual(claim["terrain_accuracy"], "NOT MEASURED")
        self.assertEqual(claim["independent_horizontal_registration"], "NOT MEASURED")
        self.assertEqual(claim["route_safety"], "NOT CLAIMED")
        self.assertEqual(claim["known_site_recovery"], "NOT YET MEASURED")

    def test_offset_decomposition_is_reconciled_by_runner(self):
        self.assertTrue(self.result["sensitivity"]["advantage_persists_at_every_tested_offset"])


if __name__ == "__main__":
    unittest.main()
