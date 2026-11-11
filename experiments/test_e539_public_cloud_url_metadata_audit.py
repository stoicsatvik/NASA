"""E539 metadata URL inventory tests; no live requests."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from experiments.e539_public_cloud_url_metadata_audit import (
    _url_record,
    _walk_urls,
    main,
)


class PublicUrlMetadataAuditTests(unittest.TestCase):
    def test_manager_preview_is_not_direct(self):
        record = _url_record(
            "https://www.sciencebase.gov/manager/item/abc/file/123",
            "fixture.manager",
        )
        self.assertEqual(record["classification"], "manager_preview_not_direct")
        self.assertFalse(record["anonymous_candidate"])

    def test_catalog_file_endpoint_is_only_a_candidate(self):
        record = _url_record(
            "https://www.sciencebase.gov/catalog/file/get/abc",
            "fixture.file",
        )
        self.assertEqual(record["classification"], "sciencebase_catalog_file_endpoint")
        self.assertTrue(record["anonymous_candidate"])

    def test_signed_cloud_url_is_not_anonymous(self):
        record = _url_record(
            "https://example-bucket.s3.amazonaws.com/dem.tif?X-Amz-Signature=secret&X-Amz-Credential=secret",
            "fixture.cloud",
        )
        self.assertEqual(record["classification"], "signed_or_tokenized_url_not_anonymous")
        self.assertFalse(record["anonymous_candidate"])
        self.assertEqual(
            record["query_key_names"],
            ["x-amz-credential", "x-amz-signature"],
        )

    def test_query_values_are_never_recorded(self):
        record = _url_record(
            "https://example.org/file.tif?token=do-not-store&download=1",
            "fixture.query",
        )
        self.assertNotIn("do-not-store", str(record))
        self.assertEqual(record["query_key_names"], ["download", "token"])

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
        record = _url_record("http://example.org/file.tif", "fixture.http")
        self.assertEqual(record["classification"], "non_https_url_rejected")
        self.assertFalse(record["anonymous_candidate"])

    def test_cli_writes_receipt_without_network_access(self):
        expected = {
            "experiment": "E539",
            "url_candidate_count": 0,
            "raw_metadata_stored": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "receipt.json"
            with patch("sys.argv", ["e539", "--out", str(output)]):
                with patch(
                    "experiments.e539_public_cloud_url_metadata_audit.audit",
                    return_value=expected,
                ):
                    main()
            self.assertEqual(json.loads(output.read_text(encoding="utf-8")), expected)


if __name__ == "__main__":
    unittest.main()
