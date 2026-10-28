"""Deterministic offline controls for E369 public-data feature audit."""
import io
import hashlib
import unittest

import numpy as np

from research.e369_single_feature_control_baselines import (
    SHAPE, auc, decode_raster, git_blob_id, measure, nearest_cell,
)


class E369Controls(unittest.TestCase):
    def test_git_blob_identity(self):
        payload = b"independent public data"
        expected = hashlib.sha1(
            b"blob " + str(len(payload)).encode() + bytes([0]) + payload
        ).hexdigest()
        self.assertEqual(git_blob_id(payload), expected)
        self.assertNotEqual(git_blob_id(payload), hashlib.sha1(payload).hexdigest())

    def test_auc_ties_and_direction(self):
        self.assertAlmostEqual(auc([1, 2], [0, 2]), 0.625)
        self.assertEqual(auc([1, 1], [2, 2]), 0)
        self.assertEqual(auc([2, 2], [1, 1]), 1)
        self.assertIsNone(auc([], [1]))

    def test_raster_dtype_geometry(self):
        buf = io.BytesIO()
        np.save(buf, np.zeros(SHAPE, dtype=np.float32))
        self.assertEqual(decode_raster(buf.getvalue()).shape, SHAPE)
        bad = io.BytesIO()
        np.save(bad, np.zeros((10, 10), dtype=np.float32))
        with self.assertRaises(ValueError):
            decode_raster(bad.getvalue())

    def test_nearest_finite_and_coordinate_guard(self):
        a = np.full(SHAPE, np.nan)
        a[140, 200] = 0.25
        lat = 90 - (140.5) * (180 / SHAPE[0])
        lon = -180 + (200.5) * (360 / SHAPE[1])
        self.assertEqual(nearest_cell(a, lat, lon), (0.25, 0))
        a[140, 200] = np.nan
        a[141, 200] = 0.8
        self.assertEqual(nearest_cell(a, lat, lon), (0.8, 1))
        with self.assertRaises(ValueError):
            nearest_cell(a, 91, 0)

    def test_predeclared_role_and_mask_controls(self):
        sites = []
        for i in range(12):
            sites.append({
                "name": "site" + str(i), "lat": 60 - i, "lon": 0,
                "kind": "environment" if i < 8 else "geology",
                "bodies": ["mars" if i < 5 else "moon"],
                "tags": ["cold_polar"] if i < 3 else [],
            })
        negatives = [{"name": "negative" + str(i), "lat": -30 - i, "lon": 0}
                     for i in range(8)]
        land = np.ones(SHAPE)
        veg = np.full(SHAPE, 0.5)
        rain = np.full(SHAPE, 0.5)
        for site in sites[:8]:
            row = int((90 - site["lat"]) / (180 / SHAPE[0]))
            veg[row, 360] = 0.1
        for site in negatives:
            row = int((90 - site["lat"]) / (180 / SHAPE[0]))
            veg[row, 360] = 0.9
        result = measure(
            {"sites": sites, "negatives": negatives},
            {"land_fraction": land, "vegetation": veg, "precipitation": rain},
        )
        for mask in ("finite_only", "land_fraction_ge_0_5"):
            for group, n in (("mars", 5), ("moon", 3), ("cold_polar", 3)):
                v = result["results"]["vegetation"][mask]["groups"][group]
                self.assertEqual(v["positives_scored"], n)
                self.assertEqual(v["negatives_scored"], 8)
                self.assertEqual(v["auc"], 1)
                self.assertEqual(
                    result["results"]["precipitation"][mask]["groups"][group]["auc"], 0.5
                )
        with self.assertRaises(ValueError):
            measure({"sites": sites[:-1], "negatives": negatives},
                    {"land_fraction": land, "vegetation": veg, "precipitation": rain})


if __name__ == "__main__":
    unittest.main()
