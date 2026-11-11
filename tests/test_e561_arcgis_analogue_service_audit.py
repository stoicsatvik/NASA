import unittest

from experiments.e561_arcgis_analogue_service_audit import (
    E561Error,
    LAYER_NAME,
    LAYER_URL,
    SERVICE_ITEM_ID,
    count_query_url,
    endpoint_is_allowed,
    validate_count,
    validate_layer,
    validate_service,
)


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
