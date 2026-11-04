import importlib.util
import itertools
import unittest
from pathlib import Path
import numpy as np

SCRIPT = Path(__file__).resolve().parents[1] / 'research' / 'e492_gistemp_block_null.py'
if not SCRIPT.exists():
    SCRIPT = Path(__file__).resolve().parent / 'e492_gistemp_block_null.py'
spec = importlib.util.spec_from_file_location('e492_gistemp_block_null', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class TestE492(unittest.TestCase):
    def test_constant_series(self):
        r=mod.block_permutation_test(np.ones(25))
        self.assertEqual(r['observed_c_per_decade'],0)
        self.assertEqual(r['two_sided_p'],1)
    def test_linear_trend(self):
        self.assertAlmostEqual(mod.trend(np.arange(25)*0.02,np.arange(25)),0.2)
    def test_exhaustive_orders(self):
        self.assertEqual(len(set(itertools.permutations(range(5)))),120)
    def test_reversal_symmetry(self):
        y=np.array([0,1,2,3,4]*5,dtype=float)
        self.assertEqual(mod.block_permutation_test(y)['two_sided_p'],mod.block_permutation_test(y[::-1])['two_sided_p'])
    def test_pinned_rows_and_units(self):
        r=mod.run();self.assertEqual(r['source_git_blob'],'0f8109a63a1e3b683a67d83bbb6ef8840ccfad45')
        self.assertTrue(0.25<r['series']['global']['ols_c_per_decade']<0.27)
    def test_determinism(self):
        self.assertEqual(mod.run(),mod.run())

if __name__=='__main__': unittest.main()
