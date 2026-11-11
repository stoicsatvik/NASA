import unittest
import numpy as np
import pyproj
from experiments.e549_ctx_hirise_matched_support import _overlap_weights, _stats

class E549GeometryTests(unittest.TestCase):
    def test_usgs_mars_equirectangular_parameters_match_ctx_crs(self):
        ctx=pyproj.CRS.from_user_input("ESRI:103885")
        hi=pyproj.CRS.from_proj4("+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +a=3396190 +b=3396190 +units=m +no_defs +type=crs")
        self.assertTrue(ctx.equals(hi,ignore_axis_order=True))
    def test_area_weighted_mean_on_aligned_grid(self):
        data=np.full((40,40),12.5,dtype=np.float32)
        window={"col_off":0,"row_off":0,"width":40,"height":40}
        mean,coverage=_overlap_weights(data,window,100.0,200.0,1.0,1.0,(110.0,130.0,170.0,190.0))
        self.assertAlmostEqual(mean,12.5,places=6)
        self.assertAlmostEqual(coverage,1.0,places=9)
    def test_fractional_grid_offset_preserves_physical_area(self):
        data=np.full((42,42),-3.0,dtype=np.float32)
        window={"col_off":0,"row_off":0,"width":42,"height":42}
        mean,coverage=_overlap_weights(data,window,100.25,200.14,1.0,1.0,(110.0,130.0,170.0,190.0))
        self.assertAlmostEqual(mean,-3.0,places=6)
        self.assertAlmostEqual(coverage,1.0,places=9)
    def test_nodata_reduces_support_without_entering_mean(self):
        data=np.full((40,40),8.0,dtype=np.float32); data[10,10]=-9999.0
        window={"col_off":0,"row_off":0,"width":40,"height":40}
        mean,coverage=_overlap_weights(data,window,100.0,200.0,1.0,1.0,(100.0,120.0,180.0,200.0),nodata=-9999.0)
        self.assertAlmostEqual(mean,8.0,places=6)
        self.assertLess(coverage,1.0)
        self.assertGreater(coverage,.99)
    def test_stats_preserve_empty_and_nonempty_samples(self):
        self.assertEqual(_stats([],[] )["n"],0)
        s=_stats([.2,.4,.6],[1.0,.999,1.0])
        self.assertEqual(s["n"],3)
        self.assertAlmostEqual(s["median"],.4)
        self.assertAlmostEqual(s["coverage_min"],.999)

if __name__=="__main__": unittest.main()
