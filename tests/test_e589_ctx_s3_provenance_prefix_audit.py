import json
import unittest

from experiments.e589_ctx_s3_provenance_prefix_audit import (
    BUCKET_URL,
    COLLECTION,
    ITEM_ID,
    ITEM_PREFIX,
    _is_provenance_candidate,
    build_list_url,
    parse_provenance_payload,
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


    def test_json_sidecar_extracts_command_roles_without_raw_values(self):
        payload = {
            "processing": [
                {
                    "program": "/usr/bin/pc_align",
                    "argv": ["/data/CTX_reference.tif", "/data/MOLA_source.csv", "-o", "/tmp/run"],
                },
                {
                    "command": "geodiff /data/CTX_reference.tif /data/MOLA_source.csv --reverse -o /tmp/diff"
                },
            ],
            "metadata": {"software": "ASP"},
        }
        result = parse_provenance_payload("provenance.json", json.dumps(payload).encode("utf-8"))
        self.assertEqual(result["decision"], "JSON_PROCESSING_COMMANDS_FOUND")
        self.assertEqual(result["command_count"], 2)
        pc = next(c for c in result["commands"] if c["tool"] == "pc_align")
        gd = next(c for c in result["commands"] if c["tool"] == "geodiff")
        self.assertEqual(pc["reference_role"], "CTX_DTM")
        self.assertEqual(pc["source_role"], "MOLA_CONTROL")
        self.assertEqual(gd["effective_sign_semantics"], "MOLA_MINUS_CTX")
        serialized = json.dumps(result)
        self.assertNotIn("/data", serialized)
        self.assertNotIn("/tmp", serialized)
        self.assertNotIn("CTX_reference", serialized)

    def test_json_sidecar_records_structure_when_no_commands_exist(self):
        payload = {"software": {"name": "ASP"}, "processes": [{"name": "bundle_adjust"}]}
        result = parse_provenance_payload("metadata.json", json.dumps(payload).encode("utf-8"))
        self.assertEqual(result["decision"], "JSON_WITHOUT_RECOGNIZED_COMMANDS")
        self.assertEqual(result["command_count"], 0)
        self.assertIn("$.processes", [entry["path"] for entry in result["command_like_key_paths"]])


    def test_json_tool_objects_with_reference_and_source_fields_are_summarized(self):
        payload = {
            "properties": {
                "processing": {
                    "pc_align": {
                        "reference": "/data/CTX_reference.tif",
                        "source": "/data/MOLA_source.csv",
                    },
                    "geodiff": {
                        "dem": "/data/CTX_reference.tif",
                        "csv": "/data/MOLA_source.csv",
                        "reverse": True,
                    },
                }
            }
        }
        result = parse_provenance_payload("provenance.json", json.dumps(payload).encode("utf-8"))
        pc = next(r for r in result["tool_records"] if r["tool"] == "pc_align")
        gd = next(r for r in result["tool_records"] if r["tool"] == "geodiff")
        self.assertEqual(pc["reference_role"], "CTX_DTM")
        self.assertEqual(pc["source_role"], "MOLA_CONTROL")
        self.assertEqual(gd["effective_sign_semantics"], "MOLA_MINUS_CTX")
        serialized = json.dumps(result)
        self.assertNotIn("/data", serialized)
        self.assertIn("$.properties.processing.pc_align", serialized)


    def test_stac_json_description_mention_is_not_a_command(self):
        payload = {
            "type": "Feature",
            "stac_version": "1.0.0",
            "id": ITEM_ID,
            "assets": {},
            "properties": {"description": "Controlled using ASP pc_align."},
            "links": [],
        }
        result = parse_provenance_payload("item.json", json.dumps(payload).encode("utf-8"))
        self.assertEqual(result["document_kind"], "STAC_ITEM_JSON")
        self.assertEqual(result["command_count"], 0)
        self.assertEqual(result["command_mentions_count"], 0)
        self.assertEqual(result["decision"], "JSON_WITHOUT_RECOGNIZED_COMMANDS")

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
