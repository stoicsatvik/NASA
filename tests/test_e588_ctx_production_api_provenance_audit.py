import json
import unittest

from experiments.e588_ctx_production_api_provenance_audit import (
    API_HOST,
    API_ITEM_URL,
    ASSET_HOSTS,
    COLLECTION,
    ITEM_ID,
    AllowlistedRedirectHandler,
    ProbeError,
    parse_item_document,
    summarize_receipt,
    validate_url,
)


class E588Tests(unittest.TestCase):
    def test_item_url_is_exact_and_pinned(self):
        self.assertTrue(API_ITEM_URL.endswith(f"/prod/collections/{COLLECTION}/items/{ITEM_ID}"))
        validate_url(API_ITEM_URL, {API_HOST}, exact_api_path=True)

    def test_rejects_non_https_wrong_host_and_query(self):
        for url in (
            API_ITEM_URL.replace("https://", "http://"),
            API_ITEM_URL.replace(API_HOST, "example.com"),
            API_ITEM_URL + "?token=secret",
        ):
            with self.assertRaises(ProbeError):
                validate_url(url, {API_HOST}, exact_api_path=True)

    def test_rejects_nonstandard_port_and_userinfo(self):
        with self.assertRaises(ProbeError):
            validate_url(API_ITEM_URL.replace("https://", "https://user@"), {API_HOST}, exact_api_path=True)
        with self.assertRaises(ProbeError):
            validate_url(API_ITEM_URL.replace(API_HOST, API_HOST + ":8443"), {API_HOST}, exact_api_path=True)

    def test_redirect_handler_rejects_off_host_target(self):
        handler = AllowlistedRedirectHandler({API_HOST})
        with self.assertRaises(ProbeError):
            handler.redirect_request(None, None, 302, "Found", {}, "https://example.com/steal")

    def test_parses_exact_item_and_detects_provenance_asset(self):
        feature = {
            "id": ITEM_ID,
            "collection": COLLECTION,
            "properties": {"datetime": "2023-04-18T12:00:00Z"},
            "assets": {
                "dtm": {"href": "https://astrogeo-ard.s3.amazonaws.com/dtm.tif"},
                "provenance": {
                    "href": "https://astrogeo-ard.s3.amazonaws.com/provenance.txt",
                    "type": "text/plain",
                    "title": "Processing provenance",
                },
            },
            "links": [{"rel": "self", "href": API_ITEM_URL}],
        }
        summary, candidates = parse_item_document(feature)
        self.assertEqual(summary["id"], ITEM_ID)
        self.assertEqual(len(candidates), 1)
        self.assertEqual(candidates[0][0], "asset:provenance")

    def test_rejects_wrong_item(self):
        with self.assertRaises(ProbeError):
            parse_item_document({"id": "other", "collection": COLLECTION, "assets": {}, "links": []})

    def test_receipt_summary_does_not_expose_raw_paths(self):
        summary = summarize_receipt({
            "experiment": "E588",
            "decision": "NO_ITEM_SPECIFIC_PROVENANCE_EXPOSED_IN_PRODUCTION_STAC_ITEM",
            "item": {"id": ITEM_ID, "asset_keys": [], "links": [], "properties": {}},
        })
        self.assertFalse(summary["raw_item_json_stored"])
        self.assertFalse(summary["raw_provenance_stored"])
        self.assertFalse(summary["raw_paths_stored"])
        self.assertFalse(summary["signed_query_values_stored"])
        self.assertNotIn("secret", json.dumps(summary))


if __name__ == "__main__":
    unittest.main()
