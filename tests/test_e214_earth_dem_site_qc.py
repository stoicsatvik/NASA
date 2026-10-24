"""E214 synthetic controls. They are NOT evidence of actual Earth terrain."""
import unittest
import numpy as np
from research.e214_earth_dem_site_qc import SITES,tile_name,source_url,square_bounds,physical_metrics

class E214Tests(unittest.TestCase):
    def test_tile_ids_and_urls(self):
        self.assertEqual(tile_name(*SITES["lonar_lead"]),"N19E076")
        self.assertEqual(tile_name(*SITES["western_ghats_lead"]),"N18E073")
        self.assertEqual(tile_name(*SITES["ladakh_lead"]),"N34E077")
        self.assertIn("/N19/N19E076.hgt.gz",source_url("lonar_lead"))
        with self.assertRaises(ValueError):source_url("lonar_lead","NASADEM")
    def test_square_footprint_and_tile_boundary(self):
        w,s,e,n=square_bounds(19.975,76.51,4)
        self.assertAlmostEqual((n-s)*np.pi/180*6371008.8,4000,places=6)
        self.assertAlmostEqual((e-w)*np.pi/180*6371008.8*np.cos(np.deg2rad(19.975)),4000,places=6)
        self.assertLess(n,20)
    def test_datum_invariance(self):
        yy,xx=np.indices((30,30),dtype=float)
        plane=2*xx+3*yy+17
        v=np.ones_like(plane,dtype=bool)
        a=physical_metrics(plane,v,10,10)
        b=physical_metrics(plane+9000,v,10,10)
        self.assertAlmostEqual(a["slope_p50_dimensionless"],np.hypot(.2,.3),places=12)
        self.assertAlmostEqual(a["slope_p90_dimensionless"],b["slope_p90_dimensionless"],places=12)
        self.assertLess(a["plane_detrended_relief_std_m"],1e-10)
    def test_void_rejected(self):
        z=np.ones((10,10))
        with self.assertRaisesRegex(ValueError,"coverage"):
            physical_metrics(z,np.zeros_like(z,dtype=bool),30,30)
    def test_nonfinite_rejected(self):
        z=np.ones((10,10));z[5,5]=np.nan
        with self.assertRaisesRegex(ValueError,"nonfinite"):
            physical_metrics(z,np.ones_like(z,dtype=bool),30,30)
    def test_void_neighbor_excluded(self):
        z=np.zeros((10,10));z[5,5]=1e6
        v=np.ones_like(z,dtype=bool);v[5,5]=False
        self.assertEqual(physical_metrics(z,v,30,30)["slope_p90_dimensionless"],0)
    def test_invalid_geometry(self):
        for x in ((90,0,4),(0,180,4),(20,76,0),(20,76,float("nan"))):
            with self.assertRaises(ValueError):square_bounds(*x)

if __name__=="__main__":unittest.main()
