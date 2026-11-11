import unittest
import numpy as np
from experiments.e550_ctx_hirise_spatial_grid import _grid_centers,_window_for_bounds

class E550SpatialGridTests(unittest.TestCase):
    def test_nine_patch_grid_is_fixed_and_spans_overlap(self):
        overlap=(1000.0,31000.0,2000.0,32000.0)
        points=_grid_centers(overlap)
        self.assertEqual(len(points),9)
        self.assertEqual(len({p["patch_id"] for p in points}),9)
        self.assertEqual(points[0]["center_x"],5500.0)
        self.assertEqual(points[4]["center_x"],16000.0)
        self.assertEqual(points[-1]["center_y"],27500.0)
    def test_hi_window_includes_six_metre_translation_margin(self):
        win=_window_for_bounds((110.25,210.25,170.14,270.14),100.0,300.0,1.0,1.0,pad=6)
        self.assertGreaterEqual(win["col_off"],0)
        self.assertGreaterEqual(win["row_off"],0)
        self.assertGreaterEqual(win["width"],112)
        self.assertGreaterEqual(win["height"],112)
    def test_patch_size_and_shift_grid_are_predeclared_constants(self):
        from experiments.e550_ctx_hirise_spatial_grid import BLOCK,SHIFTS,FRACTIONS
        self.assertEqual(BLOCK,5)
        self.assertEqual(FRACTIONS,(0.15,0.50,0.85))
        self.assertEqual(SHIFTS,((0.0,0.0),(-6.0,0.0),(6.0,0.0),(0.0,-6.0),(0.0,6.0)))

if __name__=="__main__": unittest.main()
