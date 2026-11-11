"""Deterministic E540 source-selection and download-safety tests."""
import unittest

from experiments.e540_grand_falls_direct_dem_download import (
    DEM_NAME,
    EXPECTED_BYTES,
    _allowed_host,
    _sanitized_url,
    _select_dem,
    _valid_download_uri,
)


class DirectDemDownloadTests(unittest.TestCase):
    def test_exact_public_download_uri_is_accepted(self):
        url = "https://sciencebase.usgs.gov/manager/download/clxpf5ngp004c16pfdvioav65"
        self.assertTrue(_valid_download_uri(url))

    def test_preview_url_is_not_accepted_as_download_uri(self):
        url = "https://sciencebase.usgs.gov/manager/item/abc/file/123"
        self.assertFalse(_valid_download_uri(url))

    def test_query_or_userinfo_is_rejected(self):
        self.assertFalse(
            _valid_download_uri(
                "https://sciencebase.usgs.gov/manager/download/abc?token=secret"
            )
        )
        self.assertFalse(
            _valid_download_uri(
                "https://user@sciencebase.usgs.gov/manager/download/abc"
            )
        )

    def test_exact_dem_name_and_size_are_required(self):
        item = {
            "files": [
                {
                    "name": DEM_NAME,
                    "size": EXPECTED_BYTES,
                    "downloadUri": "https://sciencebase.usgs.gov/manager/download/abc",
                }
            ]
        }
        selected = _select_dem(item)
        self.assertEqual(selected["name"], DEM_NAME)
        self.assertEqual(selected["catalogue_size_bytes"], EXPECTED_BYTES)

    def test_ambiguous_or_mismatched_metadata_fails_closed(self):
        entry = {
            "name": DEM_NAME,
            "size": EXPECTED_BYTES,
            "downloadUri": "https://sciencebase.usgs.gov/manager/download/abc",
        }
        with self.assertRaises(ValueError):
            _select_dem({"files": [entry, entry]})
        with self.assertRaises(ValueError):
            _select_dem({"files": [{**entry, "size": EXPECTED_BYTES + 1}]})

    def test_redirect_allowlist_is_limited_to_sciencebase_and_s3(self):
        self.assertTrue(_allowed_host("sciencebase.usgs.gov"))
        self.assertTrue(_allowed_host("s3.us-west-2.amazonaws.com"))
        self.assertFalse(_allowed_host("example.com"))

    def test_sanitized_url_never_keeps_query_values(self):
        result = _sanitized_url(
            "https://s3.amazonaws.com/bucket/file.tif?X-Amz-Signature=secret&part=1"
        )
        self.assertEqual(result["query_key_names"], ["part", "x-amz-signature"])
        self.assertNotIn("secret", str(result))
        self.assertFalse(result["query_values_stored"])


if __name__ == "__main__":
    unittest.main()
