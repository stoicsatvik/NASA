"""E320 deterministic synthetic geodesic and fail-closed controls."""
import csv
import io
import unittest
from research.e320_paad_spatial_holdout import audit, connected_groups, distance_km, read_sites

class TestE320(unittest.TestCase):
    def test_antimeridian(self):
        d=distance_km((0,179.999),(0,-179.999))
        self.assertGreater(d,0.20)
        self.assertLess(d,0.25)

    def test_polar(self):
        self.assertLess(distance_km((89.999,0),(89.999,180)),0.25)

    def test_identity(self):
        self.assertEqual(distance_km((12,34),(12,34)),0)

    def test_threshold_groups(self):
        s=[{"name":"A","lat":0.,"lon":0.},{"name":"B","lat":0.,"lon":0.1},
           {"name":"C","lat":0.,"lon":0.6},{"name":"D","lat":45.,"lon":45.}]
        x=audit(s)
        self.assertEqual(x["thresholds_km"]["25"]["sites_in_multi_site_groups"],2)
        self.assertEqual(x["thresholds_km"]["50"]["sites_in_multi_site_groups"],2)
        self.assertEqual(x["thresholds_km"]["100"]["sites_in_multi_site_groups"],3)
        self.assertEqual(x["thresholds_km"]["100"]["max_group_size"],3)

    def test_chain(self):
        self.assertEqual(connected_groups(4,[(0,1),(1,2)]),[[0,1,2],[3]])

    def test_bad_source(self):
        for rows in ([["A","0","0"],["A","1","1"]],[["B","nan","1"]],[["C","0","181"]]):
            stream=io.StringIO()
            writer=csv.writer(stream)
            writer.writerow(["Field_Site","Center_Latitude","Center_Longitude"])
            writer.writerows(rows)
            with self.assertRaises(ValueError):
                read_sites(stream.getvalue().encode())

    def test_permutation(self):
        s=[{"name":"A","lat":0.,"lon":0.},{"name":"B","lat":0.,"lon":0.2},
           {"name":"C","lat":1.,"lon":1.}]
        x,y=audit(s),audit(list(reversed(s)))
        self.assertEqual(x["nearest_pair_km"],y["nearest_pair_km"])
        for threshold in ("25","50","100"):
            self.assertEqual(x["thresholds_km"][threshold]["sites_in_multi_site_groups"],
                             y["thresholds_km"][threshold]["sites_in_multi_site_groups"])

if __name__=="__main__":
    unittest.main()
