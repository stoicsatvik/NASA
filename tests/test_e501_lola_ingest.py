import unittest
import numpy as np
from research.e501_lola_ingest import summarize

class E501Tests(unittest.TestCase):
    def test_constant_real_raster_shape(self):
        a=np.full((720,1440),1.25,dtype=np.float32)
        r=summarize(a)
        self.assertEqual(r['finite_count'],1036800)
        self.assertEqual(r['min_km'],1.25)
        self.assertEqual(len(r['pixel_index_tiles']),5)
    def test_missing_values_are_not_filled(self):
        a=np.zeros((720,1440),dtype=np.float32)
        a[90,720]=np.nan
        r=summarize(a)
        self.assertEqual(r['nonfinite_count'],1)
        self.assertIsNone(r['pixel_index_tiles'][0]['values_km'][2][2])
    def test_wrong_shape_rejected(self):
        with self.assertRaises(ValueError): summarize(np.zeros((100,100),dtype=np.float32))
    def test_integer_visualization_rejected(self):
        with self.assertRaises(ValueError): summarize(np.zeros((720,1440),dtype=np.uint16))
    def test_all_nonfinite_rejected(self):
        with self.assertRaises(ValueError): summarize(np.full((720,1440),np.nan,dtype=np.float32))
    def test_no_geo_claim(self):
        r=summarize(np.zeros((720,1440),dtype=np.float32))
        self.assertIn('requires independent registration',r['resolution'])
        self.assertIn('not measured',r['claim'])
if __name__=='__main__':unittest.main()
