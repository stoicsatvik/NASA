import json
import unittest

from experiments.e589_ctx_s3_provenance_prefix_audit import (
    BUCKET_URL,
    COLLECTION,
    ITEM_ID,
    ITEM_PREFIX,
    _is_provenance_candidate,
    build_list_url,
    parse_s3_listing,
    summarize_receipt,
)


class E589Tests(unittest.TestCase):
    def test_prefix_is_derived_from_verified_item_id(self):
        self.assertTrue(ITEM_PREFIX.startswith("mars/mro/ctx/controlled/usgs/"))
        self.assertTrue(ITEM_PREFIX.endswith(ITEM_ID + "/"))
        self.assertIn(COLLECTION, json.dumps({"collection": COLLECTION}))

    def test_list_url_is_bounded_and_has_no_credentials(self):
        url = build_list_url()
        self.assertTrue(url.startswith(BUCKET_URL))
        self.assertIn("list-type=2", url)
        self.assertIn("max-keys=100", url)
        self.assertIn("prefix=", url)
        self.assertNotIn("token=", url)

    def test_candidate_detection_excludes_known_qa_and_mola_files(self):
        self.assertTrue(_is_provenance_candidate("provenance.txt"))
        self.assertTrue(_is_provenance_candidate("processing_commands.json"))
        self.assertFalse(_is_provenance_candidate("qa_metrics.txt"))
        self.assertFalse(_is_provenance_candidate(ITEM_ID.lower() + "_mola_shots.csv"))
        self.assertFalse(_is_provenance_candidate("image.tif"))

    def test_parses_listing_without_persisting_full_keys(self):
        xml = f'''<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
          <IsTruncated>false</IsTruncated>
          <Contents><Key>{ITEM_PREFIX}dtm.tif</Key><Size>1234</Size><ETag>"abc"</ETag><LastModified>2026-11-12T00:00:00.000Z</LastModified></Contents>
          <Contents><Key>{ITEM_PREFIX}provenance.txt</Key><Size>88</Size><ETag>"def"</ETag><LastModified>2026-11-12T00:00:00.000Z</LastModified></Contents>
        </ListBucketResult>'''
        result = parse_s3_listing(xml.encode("utf-8"))
        self.assertEqual(result["object_count"], 2)
        self.assertEqual(result["objects"][0]["name"], "dtm.tif")
        self.assertEqual(result["objects"][1]["name"], "provenance.txt")
        self.assertTrue(result["objects"][1]["provenance_candidate"])
        serialized = json.dumps(result)
        self.assertNotIn(ITEM_PREFIX, serialized)
        self.assertNotIn("<Key>", serialized)
        self.assertFalse(result["full_object_keys_stored"])

    def test_listing_error_is_fail_closed(self):
        xml = b'''<Error xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><Code>AccessDenied</Code><Message>Denied</Message></Error>'''
        result = parse_s3_listing(xml)
        self.assertEqual(result["decision"], "S3_ERROR_XML")
        self.assertEqual(result["error_code"], "AccessDenied")

    def test_truncated_listing_is_preserved(self):
        xml = f'''<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
          <IsTruncated>true</IsTruncated>
          <Contents><Key>{ITEM_PREFIX}provenance.txt</Key><Size>88</Size></Contents>
        </ListBucketResult>'''
        result = parse_s3_listing(xml.encode("utf-8"))
        self.assertTrue(result["truncated"])

    def test_receipt_summary_contains_no_raw_keys_or_credentials(self):
        summary = summarize_receipt({
            "experiment": "E589",
            "decision": "NO_PROVENANCE_SIDECAR_IN_LISTED_PREFIX",
            "collection": COLLECTION,
            "item_id": ITEM_ID,
            "listing": {"object_count": 0, "objects": [], "truncated": False},
        })
        self.assertFalse(summary["raw_s3_xml_stored"])
        self.assertFalse(summary["full_object_keys_stored"])
        self.assertFalse(summary["raw_provenance_stored"])
        self.assertFalse(summary["local_paths_stored"])
        self.assertFalse(summary["signed_query_values_stored"])


if __name__ == "__main__":
    unittest.main()
