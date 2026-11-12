import copy
import unittest

from experiments.e585_ctx_bbox_overlap_audit import (
    analyze,
    intersection_bbox,
    spherical_rectangle_area_m2,
    validate_bbox,
)


def fixture():
    rows = [
        ("N02_063242_1988_XN_18N283W__N03_063532_1988_XN_18N283W",
         [76.76631507961969, 18.274198017266198, 77.36482295765892, 19.04816389097364],
         21.4381, 21.0239, 13.9730),
        ("N03_063453_1982_XN_18N282W__N03_063519_1982_XN_18N282W",
         [76.89545517010949, 17.705022479652627, 77.4762591179978, 18.465812299846124],
         21.2787, 22.0458, 13.4709),
        ("N04_063809_1982_XN_18N282W__N05_064231_1982_XN_18N282W",
         [76.84069919206058, 17.713072988245518, 77.41663990926094, 18.435509545061567],
         37.0019, 37.2683, 12.9054),
        ("N04_064020_1983_XN_18N283W__N04_063954_1982_XN_18N283W",
         [76.68637364730407, 17.648444079042495, 77.2752174940917, 18.42581903782146],
         24.9900, 23.7453, 12.1603),
        ("N09_065774_1988_XN_18N283W__N10_066196_1987_XN_18N283W",
         [76.12377741994237, 18.216870346105082, 76.71092229309578, 18.98200344468166],
         27.3646, 26.9863, 15.6490),
        ("N15_068162_1984_XN_18N283W__N12_067159_1988_XN_18N283W",
         [76.3841464361562, 18.286009083916607, 76.9726387838785, 19.06751708840715],
         40.5091, 40.0418, 12.8508),
        ("P02_001820_1984_XI_18N282W__P06_003442_1987_XI_18N282W",
         [77.0410114626152, 17.879622711821042, 77.62151018726807, 18.651612805452483],
         38.1975, 37.2336, 15.0610),
        ("P05_002809_1975_XI_17N283W__P13_006000_1974_XI_17N283W",
         [75.91771659930976, 14.65135146010114, 77.0480588583663, 19.777888275132497],
         28.4886, 27.9154, 15.0384),
        ("P18_007925_1987_XN_18N282W__P19_008650_1987_XI_18N282W",
         [77.21281144352704, 17.757789235602306, 77.90597708129924, 19.342308862718042],
         27.3687, 26.7783, 10.9340),
    ]
    return {
        "experiment": "E583",
        "bbox_wgs84_lon_lat": [76.69, 17.41, 78.69, 19.41],
        "credentials_used": False,
        "qa_success_count": 9,
        "items": [
            {
                "id": item_id,
                "bbox": bbox,
                "http_status": 200,
                "metrics": {
                    "metric_count": 6,
                    "mean_difference_m": mean,
                    "median_difference_m": median,
                    "stddev_difference_m": sd,
                },
            }
            for item_id, bbox, mean, median, sd in rows
        ],
    }


class E585Tests(unittest.TestCase):
    def test_bbox_validation_and_spherical_area(self):
        bbox = validate_bbox([0, 0, 1, 1])
        self.assertGreater(spherical_rectangle_area_m2(bbox), 0)
        self.assertEqual(intersection_bbox(bbox, (1, 0, 2, 1)), None)
        self.assertEqual(intersection_bbox(bbox, (0.5, 0.5, 2, 2)), (0.5, 0.5, 1.0, 1.0))

    def test_six_items_are_bbox_contained_and_three_are_partial(self):
        result = analyze(fixture())
        self.assertEqual(result["strict_bbox_contained_count"], 6)
        self.assertEqual(result["partial_bbox_intersection_count"], 3)
        partial = {
            item["id"].split("_")[0]
            for item in result["items"]
            if item["bbox_intersection_fraction_of_item"] < 0.99
        }
        self.assertEqual(partial, {"N09", "N15", "P05"})
        ratios = {
            item["id"].split("_")[0]: item["bbox_intersection_fraction_of_item"]
            for item in result["items"]
        }
        self.assertAlmostEqual(ratios["N09"], 0.0356, places=3)
        self.assertAlmostEqual(ratios["N15"], 0.4803, places=3)
        self.assertAlmostEqual(ratios["P05"], 0.1228, places=3)

    def test_positive_residual_pattern_persists_in_strict_subset(self):
        result = analyze(fixture())
        subset = result["strict_bbox_contained_subset"]
        self.assertEqual(subset["mean_difference_m"]["positive_count"], 6)
        self.assertEqual(subset["median_difference_m"]["positive_count"], 6)
        self.assertAlmostEqual(subset["mean_difference_m"]["median"], 26.17935, places=5)
        self.assertAlmostEqual(subset["median_difference_m"]["median"], 25.2618, places=4)
        self.assertAlmostEqual(subset["stddev_difference_m"]["median"], 13.18815, places=5)

    def test_bbox_overlap_warns_against_independence(self):
        result = analyze(fixture())
        all_pairs = result["all_selected_items_pairwise_bbox_overlap"]
        subset_pairs = result["strict_bbox_contained_subset"]["pairwise_bbox_overlap"]
        self.assertEqual(all_pairs["total_pairs"], 36)
        self.assertEqual(all_pairs["bbox_intersecting_pairs"], 28)
        self.assertEqual(all_pairs["bbox_iou_ge_0_1_pairs"], 14)
        self.assertAlmostEqual(all_pairs["maximum_bbox_iou"], 0.782143, places=5)
        self.assertEqual(subset_pairs["total_pairs"], 15)
        self.assertEqual(subset_pairs["bbox_intersecting_pairs"], 15)
        self.assertEqual(subset_pairs["bbox_iou_ge_0_1_pairs"], 12)

    def test_rejects_duplicate_ids_and_wrong_receipt(self):
        data = fixture()
        data["items"][1]["id"] = data["items"][0]["id"]
        with self.assertRaisesRegex(ValueError, "unique"):
            analyze(data)
        with self.assertRaisesRegex(ValueError, "E583 receipt"):
            analyze({"experiment": "E584"})

    def test_rejects_bad_bbox_or_failed_qa_asset(self):
        data = fixture()
        data["items"][0]["bbox"] = [float("nan"), 0, 1, 1]
        with self.assertRaisesRegex(ValueError, "finite"):
            analyze(data)
        data = fixture()
        data["items"][0]["http_status"] = 403
        with self.assertRaisesRegex(ValueError, "did not succeed"):
            analyze(data)

    def test_rejects_incomplete_or_credentialed_receipts(self):
        data = fixture()
        data["items"].pop()
        with self.assertRaisesRegex(ValueError, "exactly nine"):
            analyze(data)
        data = fixture()
        data["credentials_used"] = True
        with self.assertRaisesRegex(ValueError, "credentialed"):
            analyze(data)


if __name__ == "__main__":
    unittest.main()
