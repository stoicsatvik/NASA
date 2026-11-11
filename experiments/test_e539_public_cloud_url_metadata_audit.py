"""E539 metadata URL inventory tests; no live requests."""
import unittest

from experiments.e539_public_cloud_url_metadata_audit import (
    _url_record,
    _walk_urls,
)


class PublicUrlMetadataAuditTests(unittest.TestCase):
    def test_sciencebase_manager_download_is_a_file_uri_candidate(self):
        record = _url_record(
            "https://sciencebase.usgs.gov/manager/download/abc",
            "item:abc.files[4].downloadUri",
        )
        self.assertEqual(record["classification"], "sciencebase_manager_download_candidate")
        self.assertTrue(record["file_download_uri_candidate"])

    def test_manager_preview_is_not_a_file_download_candidate(self):
        record = _url_record(
            "https://sciencebase.usgs.gov/manager/item/abc/file/123",
            "item:abc.files[4].url",
        )
        self.assertEqual(record["classification"], "manager_preview_or_ui_not_direct")
        self.assertFalse(record["file_download_uri_candidate"])

    def test_catalog_file_route_requires_file_specific_query_and_field(self):
        record = _url_record(
            "https://www.sciencebase.gov/catalog/file/get/abc?f=123",
            "item:abc.files[0].downloadUri",
        )
        self.assertEqual(record["classification"], "sciencebase_catalog_file_endpoint")
        self.assertTrue(record["file_download_uri_candidate"])

    def test_item_wide_zip_route_is_not_a_file_specific_candidate(self):
        record = _url_record(
            "https://www.sciencebase.gov/catalog/file/get/abc",
            "item:abc.distributionLinks[0].uri",
        )
        self.assertFalse(record["file_download_uri_candidate"])

    def test_signed_cloud_url_is_not_anonymous_candidate(self):
        record = _url_record(
            "https://example-bucket.s3.amazonaws.com/dem.tif?X-Amz-Signature=secret&X-Amz-Credential=secret",
            "item:abc.files[4].downloadUri",
        )
        self.assertEqual(record["classification"], "signed_or_tokenized_url_not_anonymous")
        self.assertFalse(record["file_download_uri_candidate"])
        self.assertEqual(
            record["query_key_names"],
            ["x-amz-credential", "x-amz-signature"],
        )

    def test_query_values_are_never_recorded(self):
        record = _url_record(
            "https://www.sciencebase.gov/catalog/file/get/abc?f=do-not-store&download=1",
            "item:abc.files[0].downloadUri",
        )
        self.assertNotIn("do-not-store", str(record))
        self.assertEqual(record["query_key_names"], ["download", "f"])

    def test_recursive_walker_finds_only_url_like_fields(self):
        payload = {
            "files": [{"name": "dem.tif", "downloadURL": "https://example.org/dem.tif"}],
            "links": [{"href": "https://example.org/metadata.xml"}],
            "notes": "https://not-a-url-field.example/ignored",
        }
        found = list(_walk_urls(payload))
        self.assertEqual(len(found), 2)
        self.assertTrue(any("downloadURL" in path for path, _ in found))
        self.assertTrue(any("href" in path for path, _ in found))

    def test_non_https_candidate_is_not_anonymous(self):
        record = _url_record(
            "http://sciencebase.usgs.gov/manager/download/abc",
            "item:abc.files[4].downloadUri",
        )
        self.assertFalse(record["file_download_uri_candidate"])


if __name__ == "__main__":
    unittest.main()
