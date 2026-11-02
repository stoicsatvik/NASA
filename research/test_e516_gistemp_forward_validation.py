"""E516 frozen controls for rolling-origin GISTEMP analysis."""
import tempfile
import unittest
from pathlib import Path

from e516_gistemp_forward_validation import diagnostics, ols_forecast, read_source, run

HERE = Path(__file__).parent


class E516Tests(unittest.TestCase):
    def test_exact_linear_series_forecasts_without_error(self):
        years = tuple(range(2001, 2026))
        result = diagnostics(years, tuple(5 * i + 7 for i in range(25)))
        self.assertEqual(result["metrics"]["linear_trend"]["mae_c"], 0)
        self.assertGreater(result["metrics"]["last_year"]["mae_c"], 0)

    def test_constant_series_has_zero_error(self):
        result = diagnostics(tuple(range(2001, 2026)), (42,) * 25)
        self.assertTrue(all(m["mae_c"] == 0 for m in result["metrics"].values()))

    def test_prediction_uses_training_values_only(self):
        years = tuple(range(2001, 2011))
        values = tuple(range(10))
        self.assertEqual(ols_forecast(years, values, 2011), 10)
        with self.assertRaises(ValueError):
            ols_forecast(years + (2011,), values + (999999,), 2011)

    def test_pinned_real_source_and_four_series(self):
        result = run(HERE / "gistemp_zonal_2001_2025_snapshot.csv")
        self.assertEqual(len(result["series"]), 4)
        self.assertTrue(all(v["forecast_count"] == 15 for v in result["series"].values()))
        self.assertGreater(result["series"]["global_centi_c"]["trend_vs_persistence_mae_delta_c"], 0)

    def test_tampered_source_fails_closed(self):
        raw = (HERE / "gistemp_zonal_2001_2025_snapshot.csv").read_text()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "modified.csv"
            path.write_text(raw.replace("2001,53,42,108", "2001,54,42,108"))
            with self.assertRaisesRegex(ValueError, "pinned"):
                read_source(path)

    def test_invalid_windows_rejected(self):
        with self.assertRaises(ValueError):
            diagnostics(tuple(range(2001, 2025)), (0,) * 24)
        with self.assertRaises(ValueError):
            ols_forecast((2001,), (1,), 2002)


if __name__ == "__main__":
    unittest.main()
