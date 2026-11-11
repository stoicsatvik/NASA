import io
import unittest
import zipfile

from experiments.e538_sciencebase_single_file_download import (
    DEM_NAME,
    EXPECTED_BYTES,
    ITEM_ID,
    build_file_url,
    extract_dem_payload,
    has_tiff_magic,
    is_allowed_final_url,
    is_safe_request_url,
)


class E538ScienceBaseSingleFileTests(unittest.TestCase):
    def test_builds_documented_single_file_url_with_exact_name(self):
        url = build_file_url()
        self.assertEqual(
            url,
            f"https://www.sciencebase.gov/catalog/file/get/{ITEM_ID}/?name={DEM_NAME}",
        )
        self.assertTrue(is_safe_request_url(url))

    def test_rejects_unsafe_item_ids_and_file_names(self):
        with self.assertRaises(ValueError):
            build_file_url("../" + ITEM_ID, DEM_NAME)
        with self.assertRaises(ValueError):
            build_file_url(ITEM_ID, "../dem.tif")
        self.assertFalse(is_safe_request_url("http://www.sciencebase.gov/catalog/file/get/" + ITEM_ID + "/?name=" + DEM_NAME))
        self.assertFalse(is_safe_request_url("https://evil.example/catalog/file/get/" + ITEM_ID + "/?name=" + DEM_NAME))

    def test_final_url_allowlist_accepts_sciencebase_and_s3_https_only(self):
        self.assertTrue(is_allowed_final_url("https://www.sciencebase.gov/catalog/file/get/" + ITEM_ID))
        self.assertTrue(is_allowed_final_url("https://bucket.s3.amazonaws.com/object"))
        self.assertFalse(is_allowed_final_url("http://bucket.s3.amazonaws.com/object"))
        self.assertFalse(is_allowed_final_url("https://evil.example/object"))

    def test_extracts_raw_tiff_only_with_valid_magic(self):
        tiff = b"II*\x00" + b"\x08\x00\x00\x00" + b"payload"
        extracted, info = extract_dem_payload(tiff)
        self.assertEqual(extracted, tiff)
        self.assertEqual(info["container"], "raw_tiff")
        self.assertTrue(has_tiff_magic(extracted))

    def test_extracts_exact_dem_from_zip_and_preserves_inventory(self):
        tiff = b"II*\x00" + b"\x08\x00\x00\x00" + b"x" * (EXPECTED_BYTES - 8)
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(DEM_NAME, tiff)
            archive.writestr("readme.txt", "metadata")
        extracted, info = extract_dem_payload(buffer.getvalue())
        self.assertEqual(len(extracted), EXPECTED_BYTES)
        self.assertEqual(info["member"], DEM_NAME)
        self.assertEqual(info["container"], "zip")

    def test_zero_byte_dem_member_is_a_preserved_negative_result(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(DEM_NAME, b"")
        extracted, info = extract_dem_payload(buffer.getvalue())
        self.assertIsNone(extracted)
        self.assertEqual(info["reason"], "zero_byte_dem_member")

    def test_unknown_or_html_payload_is_rejected(self):
        extracted, info = extract_dem_payload(b"<!doctype html>")
        self.assertIsNone(extracted)
        self.assertEqual(info["reason"], "payload_magic_mismatch")


if __name__ == "__main__":
    unittest.main()
