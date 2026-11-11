"""E561: bounded schema and count-only audit of the public USGS ArcGIS service."""
from __future__ import annotations

import argparse
import json
import re
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
PORTAL_ITEM_URL = "https://www.arcgis.com/sharing/rest/content/items/" + SERVICE_ITEM_ID
LAYER_NAME = "TerrestrialAnalogs"
REQUIRED_FIELDS = {"FID", "Name", "AnalogType", "Lat", "Lon", "AnalogBody"}
PROVISIONAL_FGDC_COUNT = 192
MAX_RESPONSE_BYTES = 1_000_000
TIMEOUT_SECONDS = 20
USER_AGENT = "NASA-E561-ArcGIS-schema-count-audit/1.0"
OUT = Path(".artifacts/e561")


class E561Error(RuntimeError):
    def __init__(self, outcome: str):
        super().__init__(outcome)
        self.outcome = outcome


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def endpoint_is_allowed(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    service_paths = {
        urllib.parse.urlsplit(SERVICE_URL).path,
        urllib.parse.urlsplit(LAYER_URL).path,
        urllib.parse.urlsplit(QUERY_URL).path,
    }
    portal_path = urllib.parse.urlsplit(PORTAL_ITEM_URL).path
    try:
        port = parsed.port
    except ValueError:
        return False
    if (
        parsed.scheme != "https"
        or port not in (None, 443)
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        return False
    try:
        pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True, strict_parsing=True)
    except ValueError:
        return False
    params = dict(pairs)
    if len(params) != len(pairs):
        return False
    if parsed.hostname == "services.arcgis.com" and parsed.path in service_paths:
        if parsed.path == urllib.parse.urlsplit(QUERY_URL).path:
            return params == {"where": "1=1", "returnCountOnly": "true", "f": "json"}
        return params == {"f": "json"}
    if parsed.hostname == "www.arcgis.com" and parsed.path == portal_path:
        return params in ({"f": "json"}, {"f": "pjson"})
    return False


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
        content_type = response.headers.get_content_type()
        if content_type not in {"application/json", "text/plain"}:
            raise E561Error("ARCGIS_RESPONSE_NOT_JSON:" + str(content_type))
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


def validate_portal_item(document: dict) -> dict:
    if document.get("id") != SERVICE_ITEM_ID:
        raise E561Error("ARCGIS_PORTAL_ITEM_ID_MISMATCH")
    if str(document.get("type", "")).casefold() != "feature service":
        raise E561Error("ARCGIS_PORTAL_ITEM_TYPE_MISMATCH")
    if str(document.get("access", "")).casefold() != "public":
        raise E561Error("ARCGIS_PORTAL_ITEM_NOT_PUBLIC")
    owner = document.get("owner")
    if not isinstance(owner, str) or not owner.strip():
        raise E561Error("ARCGIS_PORTAL_ITEM_OWNER_MISSING")
    title = str(document.get("title", "")).strip()
    title_words = set(re.split(r"[^a-z]+", title.casefold()))
    if not {"terrestrial", "analog", "sites", "planetary", "science"}.issubset(title_words):
        raise E561Error("ARCGIS_PORTAL_ITEM_TITLE_MISMATCH")
    service_url = urllib.parse.urlsplit(str(document.get("url", "")))
    expected_service = urllib.parse.urlsplit(SERVICE_URL)
    if (
        service_url.scheme != "https"
        or service_url.hostname != expected_service.hostname
        or service_url.port not in (None, 443)
        or service_url.path != expected_service.path
        or service_url.username
        or service_url.password
        or service_url.fragment
    ):
        raise E561Error("ARCGIS_PORTAL_ITEM_SERVICE_URL_MISMATCH")
    try:
        item_url_pairs = urllib.parse.parse_qsl(service_url.query, keep_blank_values=True, strict_parsing=True)
    except ValueError as error:
        raise E561Error("ARCGIS_PORTAL_ITEM_SERVICE_URL_QUERY_INVALID") from error
    item_query_names = sorted({key for key, _ in item_url_pairs})
    created = document.get("created")
    modified = document.get("modified")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in (created, modified)):
        raise E561Error("ARCGIS_PORTAL_ITEM_TIMESTAMPS_INVALID")
    return {
        "id": SERVICE_ITEM_ID,
        "title": title,
        "type": "Feature Service",
        "access": "public",
        "owner": owner,
        "created_unix_ms": created,
        "modified_unix_ms": modified,
        "service_url_identity": expected_service.hostname + expected_service.path,
        "service_url_query_parameter_names": item_query_names,
        "service_url_has_token_parameter": "token" in item_query_names,
        "raw_item_url_retained": False,
        "raw_item_metadata_retained": False,
    }


def fetch_portal_item_metadata(fetcher=fetch_json) -> dict:
    attempts = []
    for response_format in ("json", "pjson"):
        try:
            document = fetcher(PORTAL_ITEM_URL + "?f=" + response_format)
            item = validate_portal_item(document)
            return {
                "outcome": "PORTAL_ITEM_METADATA_CONFIRMED",
                "item": item,
                "attempts": attempts + [{"format": response_format, "outcome": "JSON_AND_IDENTITY_VALID"}],
            }
        except E561Error as error:
            attempts.append({"format": response_format, "outcome": error.outcome})
    return {
        "outcome": "PORTAL_ITEM_METADATA_UNAVAILABLE",
        "attempts": attempts,
        "raw_item_url_retained": False,
        "raw_item_metadata_retained": False,
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
    portal_item = fetch_portal_item_metadata()
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
        "portal_item": portal_item,
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
