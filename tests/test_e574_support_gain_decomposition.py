from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from experiments.e574_support_gain_decomposition import run

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "receipts" / "e573_support_summary.json"


class E574SupportGainDecompositionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(SOURCE.read_text(encoding="utf-8"))
        cls.result = run(SOURCE)

    def run_mutated(self, mutate):
        payload = copy.deepcopy(self.source)
        mutate(payload)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "receipt.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return run(path)

    def test_source_is_pinned_to_latest_exact_head_e573_receipt(self):
        source = self.result["source"]
        self.assertEqual(source["workflow_run_id"], 43155697664)
        self.assertEqual(source["artifact_id"], 13916101713)
        self.assertEqual(source["source_commit"], "7f6541e10a823402c2c50bcf6647e425d037ca3a")

    def test_baseline_gain_reconciles_exactly(self):
        d = self.result["decomposition"]
        self.assertEqual(d["total_net_support_delta"], 95)
        self.assertEqual(d["shared_footprint_validity_delta"], 22)
        self.assertEqual(d["footprint_only_validity_delta"], 73)
        self.assertEqual(22 + 73, 95)

    def test_shared_footprint_partition_reconciles(self):
        b = self.result["baseline"]
        self.assertEqual(
            b["both_valid_within_shared_footprint"]
            + b["both_nodata_within_shared_footprint"]
            + b["hirise_2025_only_valid_within_shared_footprint"]
            + b["hirise_2020_only_valid_within_shared_footprint"],
            b["shared_footprint_points"],
        )

    def test_valid_point_partitions_reconcile_to_each_product_total(self):
        b = self.result["baseline"]
        self.assertEqual(
            b["both_valid_within_shared_footprint"]
            + b["hirise_2020_only_valid_within_shared_footprint"]
            + b["hirise_2020_valid_where_2025_outside"],
            b["hirise_2020_valid"],
        )
        self.assertEqual(
            b["both_valid_within_shared_footprint"]
            + b["hirise_2025_only_valid_within_shared_footprint"]
            + b["hirise_2025_valid_where_2020_outside"],
            b["hirise_2025_valid"],
        )

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

    def test_rejects_unpinned_source_receipt(self):
        with self.assertRaisesRegex(ValueError, "source provenance mismatch"):
            self.run_mutated(lambda p: p["source"].update({"artifact_receipt_sha256": "0" * 64}))

    def test_rejects_broken_shared_footprint_partition(self):
        with self.assertRaisesRegex(ValueError, "shared footprint partition"):
            self.run_mutated(lambda p: p["baseline"].update({"both_nodata_within_shared_footprint": 8}))

    def test_rejects_broken_offset_decomposition(self):
        with self.assertRaisesRegex(ValueError, "common_mode min support decomposition"):
            self.run_mutated(lambda p: p["common_mode_translation"].update({"shared_footprint_validity_delta_min": 20}))

    def test_rejects_wrong_offset_count(self):
        with self.assertRaisesRegex(ValueError, "must contain 13 frozen offsets"):
            self.run_mutated(lambda p: p["differential_2025_translation"].update({"offsets": 12}))

    def test_offset_advantage_flag_is_true_for_frozen_receipt(self):
        self.assertTrue(self.result["sensitivity"]["advantage_persists_at_every_tested_offset"])


if __name__ == "__main__":
    unittest.main()
