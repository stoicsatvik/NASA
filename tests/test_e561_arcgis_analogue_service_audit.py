import json
import unittest
from unittest.mock import patch

from experiments.e561_arcgis_analogue_service_audit import (
    E561Error,
    LAYER_NAME,
    LAYER_URL,
    PORTAL_ITEM_URL,
    SERVICE_ITEM_ID,
    count_query_url,
    fetch_portal_item_metadata,
    fetch_json,
    endpoint_is_allowed,
    validate_count,
    validate_layer,
    validate_portal_item,
    validate_service,
)


class FakeHeaders:
    def __init__(self, content_type):
        self.content_type = content_type

    def get_content_type(self):
        return self.content_type

    def get(self, name):
        return None


class FakeResponse:
    status = 200

    def __init__(self, url, content_type, payload):
        self.url = url
        self.headers = FakeHeaders(content_type)
        self.payload = payload

    def geturl(self):
        return self.url

    def read(self, limit):
        return self.payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class FakeOpener:
    def __init__(self, response):
        self.response = response

    def open(self, request, timeout):
        return self.response


class E561Tests(unittest.TestCase):
    def test_only_frozen_https_arcgis_endpoints_are_allowed(self):
        self.assertTrue(endpoint_is_allowed(
            "https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/"
            "Terrestrial_Analog_Sites_for_Planetary_Science/FeatureServer?f=json"
        ))
        self.assertTrue(endpoint_is_allowed(
            "https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/"
            "Terrestrial_Analog_Sites_for_Planetary_Science/FeatureServer/0?f=json"
        ))
        self.assertFalse(endpoint_is_allowed("http://services.arcgis.com/example"))
        self.assertFalse(endpoint_is_allowed("https://example.com/FeatureServer"))
        self.assertFalse(endpoint_is_allowed(
            "https://services.arcgis.com/v01gqwM5QqNysAAi/other?f=json"
        ))
        self.assertFalse(endpoint_is_allowed(
            "https://user:pass@services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/"
            "Terrestrial_Analog_Sites_for_Planetary_Science/FeatureServer?f=json"
        ))
        self.assertFalse(endpoint_is_allowed(LAYER_URL + "?f=json&token=not-used"))
        self.assertFalse(endpoint_is_allowed(LAYER_URL + "?f=json&outFields=*"))
        self.assertFalse(endpoint_is_allowed(count_query_url() + "&token=not-used"))
        self.assertFalse(endpoint_is_allowed(LAYER_URL + "?f=json&f=json"))
        self.assertFalse(endpoint_is_allowed(LAYER_URL + "?f=json#fragment"))
        self.assertTrue(endpoint_is_allowed(PORTAL_ITEM_URL + "?f=json"))
        self.assertFalse(endpoint_is_allowed(PORTAL_ITEM_URL + "?f=json&token=not-used"))
        self.assertTrue(endpoint_is_allowed(PORTAL_ITEM_URL + "?f=pjson"))
        self.assertFalse(endpoint_is_allowed(PORTAL_ITEM_URL + "?f=pjson&token=not-used"))

    def test_count_query_is_strictly_count_only(self):
        from urllib.parse import parse_qs, urlsplit
        parsed = urlsplit(count_query_url())
        params = parse_qs(parsed.query)
        self.assertEqual(params, {
            "where": ["1=1"],
            "returnCountOnly": ["true"],
            "f": ["json"],
        })
        self.assertEqual(parsed.path.rsplit("/", 1)[-1], "query")

    def test_service_identity_and_anonymous_query_are_required(self):
        document = {
            "serviceItemId": SERVICE_ITEM_ID,
            "capabilities": "Query,Extract",
            "layers": [{"id": 0, "name": LAYER_NAME, "type": "Feature Layer"}],
            "editorTrackingInfo": {"allowAnonymousToQuery": True},
        }
        self.assertTrue(validate_service(document)["anonymous_query_allowed"])
        document["serviceItemId"] = "wrong"
        with self.assertRaises(E561Error):
            validate_service(document)

    def test_service_must_explicitly_allow_anonymous_query(self):
        document = {
            "serviceItemId": SERVICE_ITEM_ID,
            "capabilities": "Query,Extract",
            "layers": [{"id": 0, "name": LAYER_NAME, "type": "Feature Layer"}],
            "editorTrackingInfo": {"allowAnonymousToQuery": False},
        }
        with self.assertRaises(E561Error):
            validate_service(document)

    def test_layer_schema_and_projection_are_pinned(self):
        document = {
            "name": LAYER_NAME,
            "type": "Feature Layer",
            "geometryType": "esriGeometryPoint",
            "objectIdField": "FID",
            "fields": [{"name": name} for name in
                       ["FID", "Name", "AnalogType", "Lat", "Lon", "AnalogBody"]],
            "extent": {"spatialReference": {"wkid": 102100, "latestWkid": 3857}},
            "maxRecordCount": 2000,
            "editingInfo": {"lastEditDate": 1720636669000},
        }
        result = validate_layer(document)
        self.assertEqual(result["spatial_reference_wkid"], 3857)
        self.assertEqual(result["fields"], [
            "AnalogBody", "AnalogType", "FID", "Lat", "Lon", "Name"
        ])
        document["geometryType"] = "esriGeometryPolygon"
        with self.assertRaises(E561Error):
            validate_layer(document)

    def test_layer_missing_required_field_fails_closed(self):
        document = {
            "name": LAYER_NAME,
            "type": "Feature Layer",
            "geometryType": "esriGeometryPoint",
            "objectIdField": "FID",
            "fields": [{"name": name} for name in ["FID", "Name", "AnalogType", "Lat", "Lon"]],
            "extent": {"spatialReference": {"wkid": 102100}},
        }
        with self.assertRaises(E561Error):
            validate_layer(document)

    def test_portal_item_identity_access_owner_and_version_metadata_are_required(self):
        document = {
            "id": SERVICE_ITEM_ID,
            "title": "Terrestrial_Analog_Sites_for_Planetary_Science",
            "type": "Feature Service",
            "access": "public",
            "owner": "usgs",
            "created": 1600000000000,
            "modified": 1720636669000,
            "url": "https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/"
                   "Terrestrial_Analog_Sites_for_Planetary_Science/FeatureServer",
        }
        result = validate_portal_item(document)
        self.assertEqual(result["id"], SERVICE_ITEM_ID)
        self.assertEqual(result["access"], "public")
        self.assertFalse(result["raw_item_url_retained"])
        document["access"] = "private"
        with self.assertRaises(E561Error):
            validate_portal_item(document)

    def test_portal_item_url_must_match_exact_service_identity(self):
        document = {
            "id": SERVICE_ITEM_ID,
            "title": "Terrestrial Analog Sites for Planetary Science",
            "type": "Feature Service",
            "access": "public",
            "owner": "usgs",
            "created": 1600000000000,
            "modified": 1720636669000,
            "url": "https://services.arcgis.com/other/FeatureServer",
        }
        with self.assertRaises(E561Error):
            validate_portal_item(document)

    def test_portal_item_metadata_fallback_records_html_failure_without_aborting(self):
        valid = {
            "id": SERVICE_ITEM_ID,
            "title": "Terrestrial_Analog_Sites_for_Planetary_Science",
            "type": "Feature Service",
            "access": "public",
            "owner": "usgs",
            "created": 1600000000000,
            "modified": 1720636669000,
            "url": "https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/"
                   "Terrestrial_Analog_Sites_for_Planetary_Science/FeatureServer",
        }
        calls = []
        def fetcher(url):
            calls.append(url)
            if url.endswith("?f=json"):
                raise E561Error("ARCGIS_RESPONSE_NOT_JSON:text/html")
            return valid
        result = fetch_portal_item_metadata(fetcher)
        self.assertEqual(result["outcome"], "PORTAL_ITEM_METADATA_CONFIRMED")
        self.assertEqual(calls[-1], PORTAL_ITEM_URL + "?f=pjson")
        self.assertEqual(result["attempts"][0]["outcome"], "ARCGIS_RESPONSE_NOT_JSON:text/html")

    def test_portal_item_metadata_unavailability_is_preserved(self):
        result = fetch_portal_item_metadata(
            lambda url: (_ for _ in ()).throw(E561Error("ARCGIS_RESPONSE_NOT_JSON:text/html"))
        )
        self.assertEqual(result["outcome"], "PORTAL_ITEM_METADATA_UNAVAILABLE")
        self.assertEqual([item["format"] for item in result["attempts"]], ["json", "pjson"])
        self.assertFalse(result["raw_item_metadata_retained"])

    def test_fetch_json_accepts_arcgis_text_plain_when_body_is_valid_json(self):
        url = PORTAL_ITEM_URL + "?f=json"
        response = FakeResponse(url, "text/plain", b'{"id":"ok"}')
        with patch("experiments.e561_arcgis_analogue_service_audit.urllib.request.build_opener",
                   return_value=FakeOpener(response)):
            self.assertEqual(fetch_json(url), {"id": "ok"})

    def test_fetch_json_rejects_html_even_when_endpoint_is_allowlisted(self):
        url = PORTAL_ITEM_URL + "?f=json"
        response = FakeResponse(url, "text/html", b"<html>login</html>")
        with patch("experiments.e561_arcgis_analogue_service_audit.urllib.request.build_opener",
                   return_value=FakeOpener(response)):
            with self.assertRaises(E561Error) as caught:
                fetch_json(url)
        self.assertEqual(caught.exception.outcome, "ARCGIS_RESPONSE_NOT_JSON:text/html")

    def test_count_only_response_accepts_integer_and_rejects_rows(self):
        self.assertEqual(validate_count({"count": 192}), 192)
        with self.assertRaises(E561Error):
            validate_count({"count": True})
        with self.assertRaises(E561Error):
            validate_count({"count": -1})
        with self.assertRaises(E561Error):
            validate_count({"count": 192, "features": [{"attributes": {"FID": 1}}]})


if __name__ == "__main__":
    unittest.main()
