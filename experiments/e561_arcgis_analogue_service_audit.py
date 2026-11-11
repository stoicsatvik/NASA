"""E561: bounded schema and count-only audit of the public USGS ArcGIS service."""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SERVICE_URL = (
    "https://services.arcgis.com/v01gqwM5QqNysAAi/ArcGIS/rest/services/"
    "Terrestrial_Analog_Sites_for_Planetary_Science/FeatureServer"
)
LAYER_URL = SERVICE_URL + "/0"
QUERY_URL = LAYER_URL + "/query"
SERVICE_ITEM_ID = "db564f72235f49b39c4147df36fd3308"
LAYER_NAME = "TerrestrialAnalogs"
REQUIRED_FIELDS = {"FID", "Name", "AnalogType", "Lat", "Lon", "AnalogBody"}
PROVISIONAL_FGDC_COUNT = 192
MAX_RESPONSE_BYTES = 1_000_000
TIMEOUT_SECONDS = 20
USER_AGENT = "NASA-E561-ArcGIS-schema-count-audit/1.0"
OUT = Path(".artifacts/e561")


class E561Error(RuntimeError):
    pass


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def endpoint_is_allowed(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname == "services.arcgis.com"
        and parsed.port in (None, 443)
        and parsed.path in {urllib.parse.urlsplit(SERVICE_URL).path,
                            urllib.parse.urlsplit(LAYER_URL).path,
                            urllib.parse.urlsplit(QUERY_URL).path}
        and not parsed.username
        and not parsed.password
        and not parsed.fragment
    )


def count_query_url() -> str:
    params = urllib.parse.urlencode({
        "where": "1=1",
        "returnCountOnly": "true",
        "f": "json",
    })
    return QUERY_URL + "?" + params


def fetch_json(url: str) -> dict:
    if not endpoint_is_allowed(url):
        raise E561Error("REQUEST_URL_OUTSIDE_FROZEN_ARCGIS_ALLOWLIST")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    opener = urllib.request.build_opener(NoRedirectHandler)
    try:
        response = opener.open(request, timeout=TIMEOUT_SECONDS)
    except urllib.error.HTTPError as error:
        if error.code in {301, 302, 303, 307, 308}:
            raise E561Error("ARCGIS_REDIRECT_REFUSED") from error
        raise E561Error(f"ARCGIS_HTTP_{error.code}") from error
    with response:
        if response.status != 200 or response.geturl() != url:
            raise E561Error("ARCGIS_RESPONSE_IDENTITY_MISMATCH")
        if response.headers.get_content_type() != "application/json":
            raise E561Error("ARCGIS_RESPONSE_NOT_JSON")
        length = response.headers.get("Content-Length")
        if length and int(length) > MAX_RESPONSE_BYTES:
            raise E561Error("ARCGIS_RESPONSE_DECLARED_SIZE_EXCEEDED")
        payload = response.read(MAX_RESPONSE_BYTES + 1)
        if len(payload) > MAX_RESPONSE_BYTES:
            raise E561Error("ARCGIS_RESPONSE_STREAM_SIZE_EXCEEDED")
    try:
        document = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise E561Error("ARCGIS_JSON_INVALID") from error
    if not isinstance(document, dict):
        raise E561Error("ARCGIS_JSON_ROOT_NOT_OBJECT")
    if "error" in document:
        raise E561Error("ARCGIS_SERVICE_RETURNED_ERROR")
    return document


def validate_service(document: dict) -> dict:
    if document.get("serviceItemId") != SERVICE_ITEM_ID:
        raise E561Error("ARCGIS_SERVICE_ITEM_ID_MISMATCH")
    capabilities = {
        item.strip().casefold()
        for item in str(document.get("capabilities", "")).split(",")
    }
    if "query" not in capabilities:
        raise E561Error("ARCGIS_QUERY_CAPABILITY_MISSING")
    layers = document.get("layers")
    if not isinstance(layers, list):
        raise E561Error("ARCGIS_SERVICE_LAYERS_MISSING")
    match = [
        layer for layer in layers
        if isinstance(layer, dict)
        and layer.get("id") == 0
        and layer.get("name") == LAYER_NAME
        and layer.get("type") == "Feature Layer"
    ]
    if len(match) != 1:
        raise E561Error("ARCGIS_EXPECTED_LAYER_NOT_UNIQUE")
    tracking = document.get("editorTrackingInfo") or {}
    anonymous_query = tracking.get("allowAnonymousToQuery")
    if anonymous_query is not True:
        raise E561Error("ARCGIS_ANONYMOUS_QUERY_NOT_CONFIRMED")
    return {
        "service_item_id": document["serviceItemId"],
        "query_capability": True,
        "anonymous_query_allowed": True,
        "layer_id": 0,
        "layer_name": LAYER_NAME,
    }


def validate_layer(document: dict) -> dict:
    if document.get("name") != LAYER_NAME:
        raise E561Error("ARCGIS_LAYER_NAME_MISMATCH")
    if document.get("type") != "Feature Layer":
        raise E561Error("ARCGIS_LAYER_TYPE_MISMATCH")
    if document.get("geometryType") != "esriGeometryPoint":
        raise E561Error("ARCGIS_GEOMETRY_TYPE_MISMATCH")
    fields = document.get("fields")
    if not isinstance(fields, list):
        raise E561Error("ARCGIS_LAYER_FIELDS_MISSING")
    field_names = {
        str(field.get("name"))
        for field in fields
        if isinstance(field, dict) and field.get("name")
    }
    missing = sorted(REQUIRED_FIELDS - field_names)
    if missing:
        raise E561Error("ARCGIS_REQUIRED_FIELDS_MISSING:" + ",".join(missing))
    object_id = document.get("objectIdField") or document.get("objectIdFieldName")
    if object_id != "FID":
        raise E561Error("ARCGIS_OBJECT_ID_FIELD_MISMATCH")
    spatial = document.get("extent", {}).get("spatialReference", {})
    wkid = spatial.get("latestWkid") or spatial.get("wkid")
    if wkid not in {3857, 102100}:
        raise E561Error("ARCGIS_SPATIAL_REFERENCE_UNEXPECTED")
    return {
        "name": LAYER_NAME,
        "geometry_type": "esriGeometryPoint",
        "object_id_field": object_id,
        "fields": sorted(field_names),
        "spatial_reference_wkid": wkid,
        "max_record_count": document.get("maxRecordCount"),
        "data_last_edit_date": document.get("editingInfo", {}).get("lastEditDate"),
    }


def validate_count(document: dict) -> int:
    count = document.get("count")
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise E561Error("ARCGIS_COUNT_ONLY_RESPONSE_INVALID")
    features = document.get("features")
    if features not in (None, []):
        raise E561Error("ARCGIS_COUNT_ONLY_RETURNED_FEATURE_ROWS")
    return count


def run_live() -> dict:
    service_doc = fetch_json(SERVICE_URL + "?f=json")
    service = validate_service(service_doc)
    layer_doc = fetch_json(LAYER_URL + "?f=json")
    layer = validate_layer(layer_doc)
    count = validate_count(fetch_json(count_query_url()))
    return {
        "experiment": "E561 public ArcGIS terrestrial-analogue service schema and count-only audit",
        "outcome": "PUBLIC_ARCGIS_SERVICE_SCHEMA_AND_COUNT_CONFIRMED",
        "source": {
            "service_url": SERVICE_URL,
            "service_item_id": SERVICE_ITEM_ID,
            "layer_url": LAYER_URL,
            "layer_name": LAYER_NAME,
            "publisher_link_host": "services.arcgis.com",
            "credentials_used": False,
            "token_used": False,
        },
        "service": service,
        "layer": layer,
        "count_query": {
            "url": count_query_url(),
            "where": "1=1",
            "return_count_only": True,
            "feature_rows_requested": False,
            "feature_rows_returned": False,
            "count": count,
            "provisional_fgdc_declared_count": PROVISIONAL_FGDC_COUNT,
            "matches_provisional_fgdc_count": count == PROVISIONAL_FGDC_COUNT,
        },
        "limits": {
            "max_response_bytes_each": MAX_RESPONSE_BYTES,
            "timeout_seconds_each": TIMEOUT_SECONDS,
            "redirects_followed": False,
            "feature_records_downloaded": 0,
            "geometry_downloaded": False,
            "raw_response_bodies_retained": False,
        },
        "interpretation": (
            "The public ArcGIS service schema and count-only endpoint are accessible. "
            "The FGDC declared count remains provisional because E560 recorded a "
            "ScienceBase metadata MD5 mismatch. No features, coordinates, labels, "
            "or coordinate overlap were acquired."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=OUT / "receipt.json")
    args = parser.parse_args()
    result = run_live()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "experiment": result["experiment"],
        "outcome": result["outcome"],
        "count": result["count_query"]["count"],
        "matches_provisional_fgdc_count": result["count_query"]["matches_provisional_fgdc_count"],
        "feature_rows_downloaded": 0,
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
