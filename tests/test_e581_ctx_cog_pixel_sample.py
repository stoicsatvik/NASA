import json
import unittest
import numpy as np
from rasterio.io import MemoryFile
from rasterio.transform import from_origin

from experiments.e581_ctx_cog_pixel_sample import (
    COLLECTION,
    ITEM_ID,
    ProbeError,
    build_search_payload,
    inspect_geotiff,
    parse_item,
    safe_url_summary,
    summarize_receipt,
    validate_public_url,
)


class E581Tests(unittest.TestCase):
    def _item(self, item_id=ITEM_ID):
        return {
            "type": "FeatureCollection",
            "features": [{
                "type": "Feature",
                "id": item_id,
                "collection": COLLECTION,
                "geometry": {"type": "Polygon", "coordinates": []},
                "bbox": [77.2, 17.7, 77.9, 19.3],
                "properties": {
                    "datetime": "2023-04-18T12:00:00Z",
                    "proj:shape": [128, 128],
                    "proj:transform": [0, 20, 0, 2560, 0, -20],
                    "proj:wkt2": "fixture WKT2",
                },
                "assets": {
                    "dtm": {
                        "href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/test.tif",
                        "type": "image/tiff; application=geotiff",
                        "raster:bands": [{"unit": "m", "data_type": "float32", "nodata": -9999}],
                    },
                    "qa_metrics": {"href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/qa.txt"},
                },
            }],
        }

    def _geotiff(self, include_unit=True):
        data = np.arange(128 * 128, dtype=np.float32).reshape(128, 128)
        data[:10, :10] = -9999
        with MemoryFile() as memory_file:
            with memory_file.open(
                driver="GTiff",
                height=128,
                width=128,
                count=1,
                dtype="float32",
                crs="EPSG:3857",
                transform=from_origin(0, 2560, 20, 20),
                nodata=-9999,
            ) as dataset:
                dataset.write(data, 1)
                if include_unit:
                    dataset.update_tags(1, UNITTYPE="meters")
            return memory_file.read()

    def test_search_payload_pins_collection_and_exact_item(self):
        payload = build_search_payload()
        self.assertEqual(payload["collections"], [COLLECTION])
        self.assertEqual(payload["ids"], [ITEM_ID])
        self.assertEqual(payload["limit"], 1)

    def test_safe_url_summary_redacts_query_values(self):
        summary = safe_url_summary(
            "https://astrogeo-ard.s3.amazonaws.com/a.tif?X-Amz-Signature=secret"
        )
        self.assertEqual(summary["query_key_names"], ["x-amz-signature"])
        self.assertNotIn("secret", str(summary))
        self.assertFalse(summary["query_values_stored"])

    def test_public_host_allowlist(self):
        validate_public_url("https://stac.astrogeology.usgs.gov/api/search")
        validate_public_url("https://astrogeo-ard.s3-us-west-2.amazonaws.com/a.tif")
        with self.assertRaises(ProbeError):
            validate_public_url("https://evil.example/a.tif")

    def test_parse_pinned_item_and_preserve_band_metadata(self):
        summary, href, asset = parse_item(self._item())
        self.assertEqual(summary["id"], ITEM_ID)
        self.assertEqual(summary["proj_shape"], [128, 128])
        self.assertTrue(summary["proj_wkt2_present"])
        self.assertEqual(asset["raster:bands"][0]["unit"], "m")
        self.assertIn("dtm", summary["asset_keys"])
        self.assertTrue(href.endswith("test.tif"))

    def test_parse_rejects_different_item(self):
        with self.assertRaises(ProbeError):
            parse_item(self._item(item_id="OTHER_ITEM"))

    def test_inspection_reads_real_geotiff_metadata_and_valid_windows(self):
        payload = self._geotiff(include_unit=True)
        item_summary, _, asset = parse_item(self._item())
        result = inspect_geotiff(payload, item_summary, asset)
        self.assertEqual(result["width"], 128)
        self.assertEqual(result["height"], 128)
        self.assertEqual(result["dtype"], "float32")
        self.assertEqual(result["nodata"], -9999)
        self.assertTrue(result["stac_shape_matches_raster"])
        self.assertTrue(result["stac_transform_matches_raster"])
        self.assertGreater(result["valid_pixels_sampled"], 0)
        self.assertEqual(len(result["sample_windows"]), 5)
        self.assertTrue(result["slope_computed"])
        self.assertEqual(result["vertical_unit"], "m")

    def test_slope_is_not_computed_without_explicit_vertical_unit(self):
        payload = self._geotiff(include_unit=False)
        item_summary, _, asset = parse_item(self._item())
        asset = {"href": asset["href"], "raster:bands": []}
        result = inspect_geotiff(payload, item_summary, asset)
        self.assertFalse(result["slope_computed"])
        self.assertEqual(result["vertical_unit"], "unknown")

    def test_receipt_summary_is_null_safe_and_never_claims_raw_data(self):
        summary = summarize_receipt({"decision": "ACQUISITION_OR_INSPECTION_ERROR"})
        self.assertFalse(summary["credentials_used"])
        self.assertFalse(summary["raw_raster_stored"])
        self.assertFalse(summary["raw_pixel_arrays_stored"])
        self.assertIsNone(summary["item_id"])


if __name__ == "__main__":
    unittest.main()
