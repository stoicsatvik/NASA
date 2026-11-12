import hashlib
import json
import unittest
import urllib.request

from experiments.e595_grand_falls_sensor_dictionary import (
    EXPECTED_XML_NAME,
    EXPECTED_XML_SIZE,
    MAX_XML_BYTES,
    ProbeError,
    StrictRedirectHandler,
    audit,
    summarize_dictionary,
    validate_public_url,
)
from experiments.e590_grand_falls_2023_2024_probe import CATALOG_RECORD_ID

SAFE_URL = "https://www.sciencebase.gov/catalog/file/get/?f=fixture"
XML = b"""<?xml version="1.0"?>
<metadata xmlns="urn:fgdc:test">
  <eainfo><detailed>
    <enttyp><enttypl>Grand Falls sediment transport observations</enttypl></enttyp>
    <attr><attrlabl>Record Number</attrlabl><attrdef>Sequential identifier assigned to each instrument record.</attrdef></attr>
    <attr><attrlabl>Date_Time</attrlabl><attrdef>Timestamp associated with the record.</attrdef></attr>
    <attr><attrlabl>Wind Speed - Low (mph)</attrlabl><attrdef>Low-range wind speed.</attrdef><attrunit>miles per hour</attrunit></attr>
    <attr><attrlabl>Particle Count_Tot(1)</attrlabl><attrdef>Particle counter channel one total.</attrdef></attr>
    <attr><attrlabl>Kinetic Energy_Tot(1)</attrlabl><attrdef>Kinetic energy channel one total.</attrdef></attr>
    <attr><attrlabl>wBSNE #1 average (mV/V)</attrlabl><attrdef>Average bridge output for sediment sensor one.</attrdef><attrunit>mV/V</attrunit></attr>
  </detailed></eainfo>
</metadata>
"""


def padded_xml():
    return XML + b" " * (EXPECTED_XML_SIZE - len(XML))


def catalog_payload(item_id=CATALOG_RECORD_ID, name=EXPECTED_XML_NAME, size=EXPECTED_XML_SIZE, uri=SAFE_URL):
    document = {"id": item_id, "files": [{"name": name, "size": size, "downloadUri": uri}]}
    return json.dumps(document).encode("utf-8")


class E595DictionaryTests(unittest.TestCase):
    def test_extracts_record_timestamp_and_sensor_field_definitions(self):
        result = summarize_dictionary(XML)
        self.assertEqual(result["attribute_count"], 6)
        self.assertEqual(result["attribute_occurrence_count"], 6)
        self.assertTrue(result["record_number_definition_found"])
        self.assertTrue(result["timestamp_definition_found"])
        self.assertEqual(result["sensor_channel_definition_count"], 4)
        record = next(item for item in result["attributes"] if item["label"] == "Record Number")
        self.assertEqual(record["category"], "record_identifier")
        self.assertIn("Sequential identifier", record["definition"])

    def test_namespace_prefixes_do_not_change_field_extraction(self):
        namespaced = XML.replace(b'xmlns="urn:fgdc:test"', b'xmlns:fgdc="urn:fgdc:test"').replace(
            b"<metadata", b"<fgdc:metadata", 1
        ).replace(b"</metadata>", b"</fgdc:metadata>")
        result = summarize_dictionary(namespaced)
        self.assertEqual(result["attribute_count"], 6)
        self.assertTrue(result["record_number_definition_found"])

    def test_units_and_domain_kinds_are_summarized_without_domain_values(self):
        xml = b"""<metadata><eainfo>
        <detailed><enttyp><enttypl>File A.csv</enttypl></enttyp>
        <attr><attrlabl>Wind Speed</attrlabl><attrdef>Wind speed measurement.</attrdef>
        <attrunit>mph</attrunit><attrdomv><rdom><rdommin>0</rdommin><rdommax>20</rdommax></rdom></attrdomv></attr>
        </detailed>
        <detailed><enttyp><enttypl>File B.csv</enttypl></enttyp>
        <attr><attrlabl>Wind Speed</attrlabl><attrdef>Wind speed measurement.</attrdef>
        <attrunit>mph</attrunit><attrdomv><rdom><rdommin>0</rdommin><rdommax>20</rdommax></rdom></attrdomv></attr>
        </detailed></eainfo></metadata>"""
        result = summarize_dictionary(xml)
        self.assertEqual(result["attribute_count"], 1)
        self.assertEqual(result["attribute_occurrence_count"], 2)
        self.assertEqual(result["entity_type_count"], 2)
        self.assertEqual(result["attributes"][0]["unit"], "mph")
        self.assertEqual(result["attributes"][0]["domain_kind"], "range")
        self.assertEqual(result["attributes"][0]["entity_type_labels"], ["File A.csv", "File B.csv"])
        self.assertNotIn("rdommin", json.dumps(result))
        self.assertNotIn("rdommax", json.dumps(result))

    def test_sensitive_urls_emails_paths_and_coordinate_pairs_are_redacted(self):
        xml = b"""<metadata><eainfo><detailed>
        <attr><attrlabl>Record Number</attrlabl>
        <attrdef>Control at 35.123, -111.456; https://example.org/x; /tmp/private; owner@example.org</attrdef></attr>
        <attr><attrlabl>Date_Time</attrlabl><attrdef>Format mm/dd/yyyy hh:mm; ISO 8601.</attrdef></attr>
        <attr><attrlabl>wBSNE_1_average</attrlabl><attrdef>Voltage reported in mV/V; /tmp/private; owner@example.org</attrdef></attr>
        </detailed></eainfo></metadata>"""
        result = summarize_dictionary(xml)
        encoded = json.dumps(result)
        for forbidden in ("35.123", "-111.456", "https://example.org", "/tmp/private", "owner@example.org"):
            self.assertNotIn(forbidden, encoded)
        self.assertIn("mm/dd/yyyy", encoded)
        self.assertIn("mV/V", encoded)
        self.assertTrue(result["timestamp_definition_found"])

    def test_dtd_and_entity_declarations_are_rejected(self):
        for payload in (
            b'<!DOCTYPE x [<!ENTITY a "boom">]><metadata/>',
            b'<!ENTITY a "boom"><metadata/>',
        ):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    summarize_dictionary(payload)

    def test_empty_or_oversized_xml_is_rejected(self):
        with self.assertRaises(ValueError):
            summarize_dictionary(b"")
        with self.assertRaises(ValueError):
            summarize_dictionary(b" " * (MAX_XML_BYTES + 1))

    def test_no_attribute_definitions_is_an_explicit_negative_result(self):
        result = summarize_dictionary(b"<metadata><idinfo><citation/></idinfo></metadata>")
        self.assertEqual(result["attribute_count"], 0)
        self.assertFalse(result["record_number_definition_found"])

    def test_url_policy_rejects_unsafe_targets(self):
        for url in (
            "http://www.sciencebase.gov/file.xml",
            "https://example.org/file.xml",
            "https://www.sciencebase.gov:444/file.xml",
            "https://user@www.sciencebase.gov/file.xml",
            "https://www.sciencebase.gov/file.xml#fragment",
            "https://www.sciencebase.gov/a/../file.xml",
            "https://www.sciencebase.gov/a/%2e%2e/file.xml",
            "https://www.sciencebase.gov:bad/file.xml",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ProbeError):
                    validate_public_url(url)

        handler = StrictRedirectHandler()
        with self.assertRaises(ProbeError):
            handler.redirect_request(
                urllib.request.Request(SAFE_URL),
                None,
                302,
                "Found",
                {},
                "https://example.org/redirect.xml",
            )

    def test_url_policy_accepts_allowlisted_sciencebase_target(self):
        validate_public_url(SAFE_URL)

    def test_audit_fetches_only_exact_xml_and_returns_sanitized_receipt(self):
        metadata_bytes = catalog_payload()
        xml_bytes = padded_xml()
        calls = {"metadata": 0, "xml": 0}

        def metadata_fetcher(url, *, limit):
            calls["metadata"] += 1
            self.assertGreater(limit, len(metadata_bytes))
            return {"status": 200, "payload": metadata_bytes}

        def xml_fetcher(url, *, limit):
            calls["xml"] += 1
            self.assertEqual(url, SAFE_URL)
            self.assertEqual(limit, MAX_XML_BYTES)
            return {
                "status": 200,
                "headers": {"Content-Type": "application/fgdc+xml", "Content-Length": str(EXPECTED_XML_SIZE)},
                "payload": xml_bytes,
                "final_url": SAFE_URL,
            }

        result = audit(
            metadata_fetcher,
            xml_fetcher,
            expected_catalog_sha256=hashlib.sha256(metadata_bytes).hexdigest(),
        )
        self.assertEqual(result["decision"], "ATTRIBUTE_DICTIONARY_PARSED")
        self.assertEqual(calls, {"metadata": 1, "xml": 1})
        self.assertEqual(result["attribute_count"], 6)
        self.assertTrue(result["record_number_definition_found"])
        self.assertFalse(result["sensor_csv_bytes_downloaded"])
        self.assertFalse(result["sensor_rows_downloaded"])
        self.assertFalse(result["raw_xml_stored"])
        encoded = json.dumps(result)
        self.assertNotIn("fixture", encoded)
        self.assertNotIn("owner@example.org", encoded)

    def test_catalog_metadata_hash_mismatch_prevents_xml_request(self):
        metadata_bytes = catalog_payload()
        xml_calls = []

        def metadata_fetcher(url, *, limit):
            return {"status": 200, "payload": metadata_bytes}

        def xml_fetcher(url, *, limit):
            xml_calls.append(url)
            raise AssertionError("XML request must not run")

        result = audit(metadata_fetcher, xml_fetcher, expected_catalog_sha256="0" * 64)
        self.assertEqual(result["decision"], "CATALOG_METADATA_HASH_MISMATCH")
        self.assertEqual(xml_calls, [])

    def test_wrong_item_identity_prevents_xml_request(self):
        metadata_bytes = catalog_payload(item_id="wrong-item")
        xml_calls = []

        def metadata_fetcher(url, *, limit):
            return {"status": 200, "payload": metadata_bytes}

        result = audit(
            metadata_fetcher,
            lambda url, limit: xml_calls.append(url),
            expected_catalog_sha256=hashlib.sha256(metadata_bytes).hexdigest(),
        )
        self.assertEqual(result["decision"], "CATALOG_ITEM_ID_NOT_CONFIRMED")
        self.assertEqual(xml_calls, [])

    def test_wrong_file_name_or_size_prevents_xml_request(self):
        for kwargs in ({"name": "other.xml"}, {"size": EXPECTED_XML_SIZE + 1}):
            metadata_bytes = catalog_payload(**kwargs)
            xml_calls = []
            result = audit(
                lambda url, limit: {"status": 200, "payload": metadata_bytes},
                lambda url, limit: xml_calls.append(url),
                expected_catalog_sha256=hashlib.sha256(metadata_bytes).hexdigest(),
            )
            self.assertEqual(result["decision"], "EXPECTED_XML_RECORD_NOT_UNIQUE")
            self.assertEqual(xml_calls, [])

    def test_wrong_content_type_or_size_fails_closed(self):
        metadata_bytes = catalog_payload()
        for headers, payload in (
            ({"Content-Type": "text/html", "Content-Length": str(EXPECTED_XML_SIZE)}, padded_xml()),
            ({"Content-Type": "application/xml", "Content-Length": str(EXPECTED_XML_SIZE - 1)}, padded_xml()),
        ):
            result = audit(
                lambda url, limit: {"status": 200, "payload": metadata_bytes},
                lambda url, limit, h=headers, p=payload: {
                    "status": 200, "headers": h, "payload": p, "final_url": SAFE_URL
                },
                expected_catalog_sha256=hashlib.sha256(metadata_bytes).hexdigest(),
            )
            self.assertEqual(result["decision"], "XML_RESPONSE_NOT_EXACTLY_CONFIRMED")

    def test_untrusted_download_uri_prevents_xml_request(self):
        metadata_bytes = catalog_payload(uri="https://example.org/evil.xml")
        xml_calls = []
        result = audit(
            lambda url, limit: {"status": 200, "payload": metadata_bytes},
            lambda url, limit: xml_calls.append(url),
            expected_catalog_sha256=hashlib.sha256(metadata_bytes).hexdigest(),
        )
        self.assertEqual(result["decision"], "XML_DOWNLOAD_URI_UNAVAILABLE")
        self.assertEqual(xml_calls, [])


if __name__ == "__main__":
    unittest.main()
