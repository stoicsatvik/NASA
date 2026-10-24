"""Deterministic E221 geometry and ranking controls; synthetic, not field evidence."""
import math
import unittest
import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_origin
from research.e214_earth_dem_site_qc import R
from research.e221_geolocation_jitter import OFFSETS_KM, WIDTHS_KM, shift_coordinate, window_metrics


class E221Tests(unittest.TestCase):
    def test_preregistered_grid(self):
        self.assertEqual(OFFSETS_KM, (-0.5, -0.25, 0.0, 0.25, 0.5))
        self.assertEqual(WIDTHS_KM, (2.0, 4.0))
        self.assertEqual(len({(a, b) for a in OFFSETS_KM for b in OFFSETS_KM}), 25)

    def test_coordinate_shift_metre_geometry(self):
        lat, lon = shift_coordinate(19.975, 76.51, 0.5, -0.5)
        self.assertAlmostEqual((lat - 19.975) * math.pi / 180 * R, -500, places=6)
        self.assertAlmostEqual((lon - 76.51) * math.pi / 180 * R * math.cos(math.radians(19.975)), 500, places=6)
        for args in ((90, 0, 0, 0), (0, 0, float("nan"), 0)):
            with self.assertRaises(ValueError):
                shift_coordinate(*args)

    def test_lonars_northern_tile_boundary_respected(self):
        lat, lon = shift_coordinate(19.975, 76.51, 0.5, 0.5)
        half_width_lat_deg = math.degrees(2000 / R)
        self.assertLess(lat + half_width_lat_deg, 20.0)

    def test_synthetic_plane_and_spatial_bump(self):
        size = 600
        yy, xx = np.indices((size, size), dtype=float)
        plane = 0.5 * xx + 0.7 * yy
        bump = 250 * np.exp(-((xx - 380)**2 + (yy - 300)**2) / (2 * 35**2))
        transform = from_origin(-0.03, 0.03, 0.0001, 0.0001)
        with MemoryFile() as mem:
            with mem.open(driver="GTiff", height=size, width=size, count=1, dtype="float32", crs="EPSG:4326", transform=transform) as ds:
                ds.write(plane.astype("float32"), 1)
                a = window_metrics(ds, 0.0, 0.0, 2.0)
                b = window_metrics(ds, 0.0, 0.0, 4.0)
                self.assertLess(a["plane_detrended_relief_std_m"], 1e-4)
                self.assertLess(b["plane_detrended_relief_std_m"], 1e-4)
                ds.write((plane + bump).astype("float32"), 1)
                center = window_metrics(ds, 0.0, 0.0, 2.0)
                shifted = window_metrics(ds, *shift_coordinate(0.0, 0.0, 0.5, 0), 2.0)
                self.assertGreater(center["plane_detrended_relief_std_m"], 0)
                self.assertNotAlmostEqual(center["plane_detrended_relief_std_m"], shifted["plane_detrended_relief_std_m"], places=2)

    def test_wrong_crs_fails_closed(self):
        with MemoryFile() as mem:
            with mem.open(driver="GTiff", height=10, width=10, count=1, dtype="float32", crs="EPSG:3857", transform=from_origin(0, 10, 1, 1)) as ds:
                ds.write(np.zeros((10, 10), dtype="float32"), 1)
                with self.assertRaisesRegex(ValueError, "CRS"):
                    window_metrics(ds, 0, 0, 2)


if __name__ == "__main__":
    unittest.main()
