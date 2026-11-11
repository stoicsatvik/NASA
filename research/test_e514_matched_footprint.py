"""Synthetic E514 geometry controls; real numerical evidence requires CI receipt."""
import unittest
import numpy as np
from research.e514_matched_footprint import aggregate_earth_to_mola_cells,features,score,compare


class E514Tests(unittest.TestCase):
    def test_flat_plane_area_means_and_datum_invariance(self):
        dem=np.full((600,600),250.0)
        a=aggregate_earth_to_mola_cells(dem,29.0,76.0,0.0,tie_lat=30,tie_lon=75,pixel_deg=1/240)
        self.assertEqual(len(a),5)
        self.assertTrue(all(abs(v-250)<1e-9 for row in a for v in row))
        f=features(a,0)
        self.assertAlmostEqual(f['relief_p90_p10_m'],0)
        self.assertAlmostEqual(f['median_abs_gradient_m_per_km'],0)
        self.assertEqual(score(f,features([[v+500 for v in row] for row in a],0)),0)

    def test_georeference_center_and_mars_latitude_effect(self):
        dem=np.tile(np.arange(600,dtype=float),(600,1))
        a=aggregate_earth_to_mola_cells(dem,29,76,0,tie_lat=30,tie_lon=75)
        b=aggregate_earth_to_mola_cells(dem,29,76,60,tie_lat=30,tie_lon=75)
        self.assertGreater(a[2][3]-a[2][2],b[2][3]-b[2][2])
        self.assertAlmostEqual(a[2][2],b[2][2],delta=1)

    def test_outside_source_rejected(self):
        dem=np.ones((50,50))
        with self.assertRaisesRegex(ValueError,'outside'):
            aggregate_earth_to_mola_cells(dem,29,76,0)

    def test_nonfinite_source_rejected(self):
        dem=np.ones((600,600))
        dem[230:250,230:250]=np.nan
        with self.assertRaisesRegex(ValueError,'missing'):
            aggregate_earth_to_mola_cells(dem,29,76,0)

    def test_mola_missing_count_fail_closed(self):
        dem=np.ones((600,600))
        mola={'shape':[720,1440],'pixel_index_tiles':[{'center_row_col':[360,720],
              'topography_m':[[1]*5 for _ in range(5)],
              'ground_return_counts':[[0]*5 for _ in range(5)]} for _ in range(5)]}
        earth={'shape':[3600,3600],'tiepoint':[0,0,0,75,30,0],
               'pixel_scale_deg':[1/240,1/240],
               'sites':{k:{'center_lat_lon_deg':[29,76]} for k in ('a','b','c')}}
        with self.assertRaisesRegex(ValueError,'zero-shot'):
            compare(mola,earth,dem,permutations=1)

    def test_bad_descriptor_rejected(self):
        with self.assertRaises(ValueError):features([[1,2]],0)
        with self.assertRaises(ValueError):features([[1]*5 for _ in range(5)],90)


if __name__=='__main__':unittest.main()
