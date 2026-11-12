import json
import unittest

from experiments.e587_ctx_processing_provenance_audit import (
    COLLECTION,
    ITEM_ID,
    _item_summary,
    build_search_payload,
    classify_operand,
    parse_provenance_text,
    summarize_receipt,
)


class E587Tests(unittest.TestCase):
    def test_search_payload_is_pinned(self):
        self.assertEqual(
            build_search_payload(),
            {"collections": [COLLECTION], "ids": [ITEM_ID], "limit": 1},
        )

    def test_operand_classification_uses_basename_only(self):
        self.assertEqual(classify_operand("/private/path/CTX_P18_DTM.tif"), "CTX_DTM")
        self.assertEqual(classify_operand("/private/path/mola_control.csv"), "MOLA_CONTROL")
        self.assertEqual(classify_operand("/private/path/unknown.csv"), "CSV_UNKNOWN")

    def test_geodiff_default_sign_and_reverse_are_explicit(self):
        normal = parse_provenance_text(
            b"/opt/asp/geodiff /private/CTX_P18_DTM.tif /private/MOLA_control.csv -o /tmp/out\n"
        )
        reverse = parse_provenance_text(
            b"/opt/asp/geodiff --reverse /private/CTX_P18_DTM.tif /private/MOLA_control.csv -o /tmp/out\n"
        )
        self.assertEqual(normal["command_count"], 1)
        self.assertEqual(normal["commands"][0]["operand_roles"], ["CTX_DTM", "MOLA_CONTROL"])
        self.assertEqual(normal["commands"][0]["effective_sign_semantics"], "CTX_MINUS_MOLA")
        self.assertEqual(reverse["commands"][0]["effective_sign_semantics"], "MOLA_MINUS_CTX")
        serialized = json.dumps(normal)
        self.assertNotIn("/private", serialized)
        self.assertNotIn("/tmp", serialized)
        self.assertNotIn("CTX_P18_DTM", serialized)

    def test_geodiff_csv_order_does_not_change_grid_rule_claim(self):
        result = parse_provenance_text(
            b"geodiff /private/MOLA_control.csv /private/CTX_P18_DTM.tif -o /tmp/out\n"
        )
        command = result["commands"][0]
        self.assertEqual(command["operand_roles"], ["MOLA_CONTROL", "CTX_DTM"])
        self.assertEqual(command["default_sign_semantics"], "CTX_MINUS_MOLA")
        self.assertEqual(command["effective_sign_semantics"], "CTX_MINUS_MOLA")

    def test_pc_align_reference_and_source_order_are_preserved(self):
        result = parse_provenance_text(
            b"pc_align --max-displacement 100 --csv-format '1:lat 2:lon 3:radius_m' "
            b"/private/CTX_reference.tif /private/MOLA_source.csv -o /tmp/run\n"
        )
        command = result["commands"][0]
        self.assertEqual(command["tool"], "pc_align")
        self.assertEqual(command["reference_role"], "CTX_DTM")
        self.assertEqual(command["source_role"], "MOLA_CONTROL")
        self.assertTrue(command["reference_source_order_resolved"])
        self.assertNotIn("/private", json.dumps(result))

    def test_multiline_shell_continuation_is_parsed(self):
        result = parse_provenance_text(
            b"pc_align --max-displacement 100 \\\n"
            b"  /data/CTX_reference.tif /data/MOLA_source.csv -o /tmp/run\n"
        )
        self.assertEqual(result["command_count"], 1)
        self.assertEqual(result["commands"][0]["reference_role"], "CTX_DTM")

    def test_item_summary_exposes_only_metadata_and_provenance_candidates(self):
        feature = {
            "id": ITEM_ID,
            "collection": COLLECTION,
            "properties": {
                "datetime": "2023-04-18T12:00:00Z",
                "processing:software": "ASP",
                "prov:wasGeneratedBy": {"command": "secret"},
            },
            "assets": {
                "dtm": {"href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/dtm.tif"},
                "provenance": {
                    "href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/provenance.txt?token=secret",
                    "type": "text/plain",
                    "title": "Processing provenance",
                },
            },
            "links": [
                {"rel": "self", "href": "https://stac.astrogeology.usgs.gov/item"},
            ],
        }
        summary, candidates = _item_summary(feature)
        self.assertEqual(summary["id"], ITEM_ID)
        self.assertIn("prov:wasGeneratedBy", summary["properties"]["provenance_property_keys"])
        self.assertEqual(len(candidates), 1)
        serialized = json.dumps(summary)
        self.assertNotIn("secret", serialized)
        self.assertNotIn("token=secret", serialized)

    def test_receipt_summary_keeps_raw_data_and_paths_out(self):
        summary = summarize_receipt({
            "experiment": "E587",
            "decision": "NO_ITEM_SPECIFIC_PROVENANCE_EXPOSED_IN_PINNED_STAC_ITEM",
            "item": {"id": ITEM_ID, "properties": {}, "asset_keys": [], "links": []},
        })
        self.assertFalse(summary["raw_item_json_stored"])
        self.assertFalse(summary["raw_provenance_stored"])
        self.assertFalse(summary["raw_paths_stored"])
        self.assertFalse(summary["signed_query_values_stored"])


if __name__ == "__main__":
    unittest.main()
