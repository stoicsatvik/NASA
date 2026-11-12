import hashlib
import json
import unittest

from experiments.e593_grand_falls_xml_metadata_audit import (
    CHILD_ITEM_ID,
    EXPECTED_XML_NAME,
    EXPECTED_XML_SIZE,
    MAX_XML_BYTES,
    ProbeError,
    audit,
    summarize_xml,
    validate_public_url,
)

SAFE_URL = "https://www.sciencebase.gov/catalog/file/get/?f=fixture-secret"


FGDC_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<metadata>
  <idinfo>
    <citation><citeinfo>
      <title>Grand Falls ripple photogrammetry</title>
      <pubdate>20240725</pubdate>
    </citeinfo></citation>
    <timeperd><timeinfo><rngdates>
      <begdate>20240220</begdate>
      <enddate>20240725</enddate>
    </rngdates></timeinfo></timeperd>
  </idinfo>
  <spref>
    <horizsys>
      <geodetic>
        <horizdn>WGS 84</horizdn>
        <ellips>WGS 84</ellips>
      </geodetic>
      <planar>
        <mapproj><mapprojn>Universal Transverse Mercator</mapprojn></mapproj>
        <plandu>meters</plandu>
        <planci><coordrep>
          <absres>0.02</absres>
          <ordres>0.02</ordres>
        </coordrep></planci>
      </planar>
    </horizsys>
    <vertdef><altsys>
      <altdatum>Local ground control datum</altdatum>
      <altunits>meters</altunits>
    </altsys></vertdef>
  </spref>
  <dataqual><lineage><procstep>
    <procdesc>Processed from control point 33.5,-111.7; see https://example.com/private?token=secret and /tmp/run/points.csv</procdesc>
    <procdate>20240725</procdate>
  </procstep></lineage></dataqual>
  <eainfo><detailed><enttyp><enttypl>Raster elevation surface</enttypl></enttyp>
    <attr><attrlabl>NoData</attrlabl></attr>
  </detailed></eainfo>
</metadata>
"""


def padded_xml(size=EXPECTED_XML_SIZE):
    if len(FGDC_XML) > size:
        raise AssertionError("fixture larger than expected XML file")
    return FGDC_XML + b" " * (size - len(FGDC_XML))


def item_payload(name=EXPECTED_XML_NAME, size=EXPECTED_XML_SIZE, item_id=CHILD_ITEM_ID, url=SAFE_URL):
    document = {
        "id": item_id,
        "files": [{"name": name, "size": size, "downloadUri": url}],
    }
    return json.dumps(document).encode("utf-8")


class E593XmlMetadataTests(unittest.TestCase):
    def test_fgdc_fields_are_extracted_by_category(self):
        result = summarize_xml(FGDC_XML)
        self.assertTrue(result["metadata_categories_present"]["horizontal_reference"])
        self.assertTrue(result["metadata_categories_present"]["vertical_reference"])
        self.assertTrue(result["metadata_categories_present"]["grid_resolution"])
        self.assertTrue(result["metadata_categories_present"]["acquisition_dates"])
        self.assertTrue(result["metadata_categories_present"]["processing_lineage"])
        self.assertTrue(result["metadata_categories_present"]["raster_representation"])
        self.assertTrue(result["metadata_categories_present"]["nodata_label"])
        self.assertFalse(result["metadata_categories_present"]["nodata"])
        horizontal = json.dumps(result["horizontal_reference_fields"])
        self.assertIn("WGS 84", horizontal)
        self.assertIn("Universal Transverse Mercator", horizontal)
        self.assertEqual(len(result["grid_resolution_fields"]), 2)

    def test_coordinate_urls_emails_and_paths_are_not_retained(self):
        result = summarize_xml(FGDC_XML)
        encoded = json.dumps(result)
        self.assertNotIn("33.5,-111.7", encoded)
        self.assertNotIn("example.com", encoded)
        self.assertNotIn("private?token=secret", encoded)
        self.assertNotIn("/tmp/run/points.csv", encoded)
        self.assertFalse(result["raw_coordinates_stored"])

    def test_namespace_prefixes_are_normalized(self):
        xml = (
            b'<gmd:metadata xmlns:gmd="urn:test">'
            b"<gmd:title>Projected DEM metadata</gmd:title>"
            b"</gmd:metadata>"
        )
        result = summarize_xml(xml)
        self.assertEqual(result["xml_root_tag"], "metadata")
        self.assertEqual(result["product_description_fields"][0]["value"], "Projected DEM metadata")

    def test_dtd_and_entity_declarations_are_rejected(self):
        xml = b'<!DOCTYPE metadata [<!ENTITY x SYSTEM "file:///etc/passwd">]><metadata>&x;</metadata>'
        with self.assertRaises(ValueError):
            summarize_xml(xml)

    def test_xml_over_cap_is_rejected(self):
        with self.assertRaises(ValueError):
            summarize_xml(b"<metadata/>" + b" " * (MAX_XML_BYTES + 1))

    def test_url_policy_rejects_untrusted_or_ambiguous_targets(self):
        for url in (
            "http://www.sciencebase.gov/file.xml",
            "https://example.com/file.xml",
            "https://www.sciencebase.gov:444/file.xml",
            "https://user@www.sciencebase.gov/file.xml",
            "https://www.sciencebase.gov/file.xml#fragment",
            "https://www.sciencebase.gov/a/%2e%2e/file.xml",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ProbeError):
                    validate_public_url(url)

    def test_url_policy_accepts_allowlisted_https_targets(self):
        validate_public_url(SAFE_URL)
        validate_public_url("https://prod-is-usgs-sb-prod-content.s3.amazonaws.com/object.xml")

    def test_audit_fetches_only_exact_xml_and_stores_aggregate_fields(self):
        metadata = item_payload()
        xml = padded_xml()
        calls = {"item": 0, "xml": 0}

        def item_fetcher(url, *, limit):
            calls["item"] += 1
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "payload": metadata,
                "final_url": "https://www.sciencebase.gov/catalog/item/fixture",
            }

        def xml_fetcher(url, *, limit):
            calls["xml"] += 1
            self.assertEqual(url, SAFE_URL)
            self.assertEqual(limit, MAX_XML_BYTES + 1)
            return {
                "status": 200,
                "headers": {
                    "Content-Type": "application/xml",
                    "Content-Length": str(EXPECTED_XML_SIZE),
                },
                "payload": xml,
                "final_url": SAFE_URL,
            }

        result = audit(
            item_fetcher,
            xml_fetcher,
            expected_item_sha256=hashlib.sha256(metadata).hexdigest(),
        )
        self.assertEqual(result["decision"], "XML_METADATA_PARSED")
        self.assertEqual(calls, {"item": 1, "xml": 1})
        self.assertTrue(result["metadata_xml_bytes_downloaded"])
        self.assertFalse(result["archive_bytes_downloaded"])
        self.assertFalse(result["raster_bytes_downloaded"])
        self.assertFalse(result["raw_xml_stored"])
        self.assertFalse(result["raw_coordinates_stored"])
        encoded = json.dumps(result)
        self.assertNotIn("fixture-secret", encoded)
        self.assertNotIn("33.5,-111.7", encoded)
        self.assertNotIn("example.com", encoded)

    def test_item_metadata_hash_mismatch_prevents_xml_request(self):
        metadata = item_payload()
        xml_calls = []

        def item_fetcher(url, *, limit):
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "payload": metadata,
                "final_url": "https://www.sciencebase.gov/catalog/item/fixture",
            }

        def xml_fetcher(url, *, limit):
            xml_calls.append(url)
            raise AssertionError("XML request must not run after metadata drift")

        result = audit(item_fetcher, xml_fetcher, expected_item_sha256="0" * 64)
        self.assertEqual(result["decision"], "ITEM_METADATA_CHANGED_SINCE_E591")
        self.assertEqual(xml_calls, [])

    def test_wrong_item_id_prevents_xml_request(self):
        metadata = item_payload(item_id="wrong-item")
        xml_calls = []

        def item_fetcher(url, *, limit):
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "payload": metadata,
                "final_url": "https://www.sciencebase.gov/catalog/item/fixture",
            }

        def xml_fetcher(url, *, limit):
            xml_calls.append(url)
            raise AssertionError("XML request must not run")

        result = audit(item_fetcher, xml_fetcher, expected_item_sha256=hashlib.sha256(metadata).hexdigest())
        self.assertEqual(result["decision"], "CHILD_ITEM_ID_NOT_CONFIRMED")
        self.assertEqual(xml_calls, [])

    def test_wrong_xml_filename_or_size_prevents_download(self):
        metadata = item_payload(size=EXPECTED_XML_SIZE - 1)
        xml_calls = []

        def item_fetcher(url, *, limit):
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "payload": metadata,
                "final_url": "https://www.sciencebase.gov/catalog/item/fixture",
            }

        def xml_fetcher(url, *, limit):
            xml_calls.append(url)
            raise AssertionError("XML request must not run")

        result = audit(item_fetcher, xml_fetcher, expected_item_sha256=hashlib.sha256(metadata).hexdigest())
        self.assertEqual(result["decision"], "EXPECTED_XML_FILE_RECORD_NOT_UNIQUE")
        self.assertEqual(xml_calls, [])

    def test_unsafe_download_uri_prevents_xml_request(self):
        metadata = item_payload(url="https://www.sciencebase.gov:444/catalog/file/get/?f=x")
        xml_calls = []

        def item_fetcher(url, *, limit):
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "payload": metadata,
                "final_url": "https://www.sciencebase.gov/catalog/item/fixture",
            }

        def xml_fetcher(url, *, limit):
            xml_calls.append(url)
            raise AssertionError("unsafe URL must be rejected before request")

        result = audit(item_fetcher, xml_fetcher, expected_item_sha256=hashlib.sha256(metadata).hexdigest())
        self.assertEqual(result["decision"], "AUDIT_ERROR")
        self.assertEqual(result["error_type"], "ProbeError")
        self.assertEqual(xml_calls, [])

    def test_html_or_wrong_size_xml_response_is_not_parsed(self):
        metadata = item_payload()

        def item_fetcher(url, *, limit):
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "payload": metadata,
                "final_url": "https://www.sciencebase.gov/catalog/item/fixture",
            }

        def html_fetcher(url, *, limit):
            return {
                "status": 200,
                "headers": {"Content-Type": "text/html", "Content-Length": str(EXPECTED_XML_SIZE)},
                "payload": padded_xml(),
                "final_url": SAFE_URL,
            }

        result = audit(item_fetcher, html_fetcher, expected_item_sha256=hashlib.sha256(metadata).hexdigest())
        self.assertEqual(result["decision"], "XML_HTML_RESPONSE")
        self.assertNotIn("xml_summary", result)

        def short_fetcher(url, *, limit):
            return {
                "status": 200,
                "headers": {"Content-Type": "application/xml", "Content-Length": "100"},
                "payload": b"<metadata/>",
                "final_url": SAFE_URL,
            }

        result = audit(item_fetcher, short_fetcher, expected_item_sha256=hashlib.sha256(metadata).hexdigest())
        self.assertEqual(result["decision"], "XML_SIZE_MISMATCH")
        self.assertNotIn("xml_summary", result)


if __name__ == "__main__":
    unittest.main()
