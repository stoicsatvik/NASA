"""Deterministic arithmetic and epistemic-boundary controls for E340."""
import unittest
from decimal import Decimal

from research.e340_ibex_gale_literature_gate import evaluate


class E340Tests(unittest.TestCase):
    def test_source_inputs_and_arithmetic(self):
        result = evaluate()
        inputs, derived = result["inputs"], result["derived"]
        self.assertEqual(inputs["earth_ibex_reported_mean_wavelength_m"], "0.71")
        self.assertEqual(inputs["mars_gale_reported_mean_wavelength_m"], "2.20")
        self.assertEqual(Decimal(derived["mars_minus_earth_mean_m"]), Decimal("1.49"))
        self.assertEqual(
            Decimal(derived["mars_to_earth_mean_wavelength_ratio"]) * Decimal("0.71"),
            Decimal("2.20"),
        )

    def test_conditional_tolerance_bounds(self):
        bounds = evaluate()["derived"]["ratio_if_earth_mean_shifted_by_lidar_tolerance"]
        lower, upper = Decimal(bounds["lower"]), Decimal(bounds["upper"])
        self.assertEqual(lower * Decimal("0.73"), Decimal("2.20"))
        self.assertEqual(upper * Decimal("0.69"), Decimal("2.20"))
        self.assertGreater(lower, Decimal(3))

    def test_no_fabricated_uncertainty_or_recovery(self):
        result = evaluate()
        self.assertIsNone(result["inputs"]["mars_mean_uncertainty_m"])
        self.assertEqual(result["claim_state"]["physically_generalizable_analogue_recovery"], "NOT YET MEASURED")
        self.assertEqual(result["claim_state"]["novel_analogue_discovery"], "NOT YET PROVEN")


if __name__ == "__main__":
    unittest.main()
