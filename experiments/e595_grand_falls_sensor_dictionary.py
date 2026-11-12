"""E595: bounded extraction of the official Grand Falls sensor data dictionary."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit

from experiments.e590_grand_falls_2023_2024_probe import (
    CATALOG_RECORD_ID,
    CATALOG_RECORD_URL,
    MAX_METADATA_BYTES,
    _download_uri,
    _extract_file_records,
    _file_name,
    _file_size,
)
from experiments.e577_grand_falls_2017_2019_access_probe import (
    ALLOWED_HOSTS,
    TIMEOUT_SECONDS,
    USER_AGENT,
)

EXPERIMENT = "E595"
EXPECTED_CATALOG_METADATA_SHA256 = "ce33f7a8a18d0076d0b883f634447c0466fa8354e9c3577ff43b48171225e389"
EXPECTED_XML_NAME = "Sediment_Transport_Data.xml.xml"
EXPECTED_XML_SIZE = 41_313
MAX_XML_BYTES = 65_536

URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PATH_RE = re.compile(r"(?:[A-Za-z]:\\|/)[^\s,;]+")
COORD_PAIR_RE = re.compile(
    r"(?<![A-Za-z0-9])[-+]?\d{1,3}(?:\.\d+)?\s*,\s*[-+]?\d{1,3}(?:\.\d+)?(?![A-Za-z0-9])"
)


class ProbeError(RuntimeError):
    pass


def validate_public_url(url: str) -> None:
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ProbeError("invalid URL port") from exc
    decoded_segments = [urllib.parse.unquote(part) for part in parsed.path.split("/")]
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_HOSTS
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
        or port not in (None, 443)
        or any(part == ".." for part in decoded_segments)
    ):
        raise ProbeError("URL outside strict public ScienceBase/S3 boundary")


class StrictRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        validate_public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def fetch_strict_bounded(url: str, *, limit: int) -> dict:
    validate_public_url(url)
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json,application/xml,text/xml,*/*",
        },
    )
    opener = urllib.request.build_opener(StrictRedirectHandler())
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            payload = response.read(limit)
            final_url = response.geturl()
            validate_public_url(final_url)
            return {
                "status": response.status,
                "headers": response.headers,
                "payload": payload,
                "final_url": final_url,
            }
    except urllib.error.HTTPError as error:
        final_url = error.geturl()
        validate_public_url(final_url)
        result = {
            "status": error.code,
            "headers": error.headers,
            "payload": b"",
            "final_url": final_url,
        }
        error.close()
        return result


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].split(":")[-1].lower()


def _safe_text(value: str, limit: int = 600) -> str:
    value = " ".join(value.split())
    value = URL_RE.sub("[URL REDACTED]", value)
    value = EMAIL_RE.sub("[EMAIL REDACTED]", value)
    value = PATH_RE.sub("[PATH REDACTED]", value)
    value = COORD_PAIR_RE.sub("[COORDINATES REDACTED]", value)
    return value[:limit]


def _direct_text(element: ET.Element, names: set[str]) -> str:
    for child in list(element):
        if _local_name(child.tag) in names:
            return " ".join((child.text or "").split())
    return ""


def _field_category(label: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "", label.lower())
    if normalized in {"recordnumber", "recordno", "recordid"}:
        return "record_identifier"
    if "dateandtime" in normalized or "timestamp" in normalized:
        return "timestamp"
    if "windspeed" in normalized:
        return "wind_speed"
    if "particlecount" in normalized:
        return "particle_count"
    if "kineticenergy" in normalized:
        return "kinetic_energy"
    if "wbsne" in normalized:
        return "sediment_sensor_voltage"
    return "other"


def summarize_dictionary(payload: bytes) -> dict:
    if not payload or len(payload) > MAX_XML_BYTES:
        raise ValueError("XML payload is empty or exceeds the 64 KiB cap")
    upper = payload.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("DTD/entity declarations are not accepted")

    root = ET.fromstring(payload)
    entity_labels: list[str] = []
    attributes: list[dict] = []
    for element in root.iter():
        if _local_name(element.tag) == "enttypl":
            value = _safe_text(element.text or "", 160)
            if value and value not in entity_labels:
                entity_labels.append(value)

    for attr in (node for node in root.iter() if _local_name(node.tag) == "attr"):
        label = _direct_text(attr, {"attrlabl"})
        if not label:
            continue
        definition = _direct_text(attr, {"attrdef"})
        unit = _direct_text(attr, {"attrunit", "unitofmeasure"})
        domain_kind = None
        for child in attr.iter():
            name = _local_name(child.tag)
            if name == "rdom":
                domain_kind = "range"
                break
            if name == "codesetd":
                domain_kind = "codeset"
                break
            if name == "edom":
                domain_kind = "enumerated"
                break

        attributes.append({
            "label": _safe_text(label, 160),
            "category": _field_category(label),
            "definition": _safe_text(definition, 600) if definition else None,
            "unit": _safe_text(unit, 80) if unit else None,
            "domain_kind": domain_kind,
        })

    category_counts = Counter(item["category"] for item in attributes)
    record_fields = [item for item in attributes if item["category"] == "record_identifier"]
    timestamp_fields = [item for item in attributes if item["category"] == "timestamp"]
    channel_categories = {"wind_speed", "particle_count", "kinetic_energy", "sediment_sensor_voltage"}

    return {
        "entity_type_labels": entity_labels[:20],
        "attribute_count": len(attributes),
        "attributes": attributes[:100],
        "category_counts": dict(sorted(category_counts.items())),
        "record_number_definition_found": any(item["definition"] for item in record_fields),
        "timestamp_definition_found": any(item["definition"] for item in timestamp_fields),
        "sensor_channel_definition_count": sum(category_counts.get(name, 0) for name in channel_categories),
        "raw_xml_stored": False,
        "raw_coordinates_stored": False,
        "raw_urls_stored": False,
        "raw_contact_data_stored": False,
    }


def audit(metadata_fetcher=None, xml_fetcher=None, expected_catalog_sha256: str = EXPECTED_CATALOG_METADATA_SHA256) -> dict:
    metadata_fetcher = metadata_fetcher or fetch_strict_bounded
    xml_fetcher = xml_fetcher or fetch_strict_bounded
    result = {
        "experiment": EXPERIMENT,
        "source_item_id": CATALOG_RECORD_ID,
        "expected_metadata_file_name": EXPECTED_XML_NAME,
        "expected_metadata_file_size_bytes": EXPECTED_XML_SIZE,
        "catalog_metadata_http_status": None,
        "xml_http_status": None,
        "decision": "ACQUISITION_NOT_STARTED",
        "credentials_used": False,
        "sensor_csv_bytes_downloaded": False,
        "sensor_rows_downloaded": False,
        "raw_xml_stored": False,
        "raw_coordinates_stored": False,
        "raw_urls_stored": False,
        "raw_contact_data_stored": False,
    }

    try:
        metadata = metadata_fetcher(CATALOG_RECORD_URL, limit=MAX_METADATA_BYTES)
        result["catalog_metadata_http_status"] = metadata["status"]
        if metadata["status"] != 200:
            result["decision"] = "CATALOG_METADATA_UNAVAILABLE"
            return result

        metadata_payload = metadata["payload"]
        result["catalog_metadata_bytes"] = len(metadata_payload)
        metadata_sha256 = hashlib.sha256(metadata_payload).hexdigest()
        result["catalog_metadata_sha256"] = metadata_sha256
        if metadata_sha256 != expected_catalog_sha256:
            result["decision"] = "CATALOG_METADATA_HASH_MISMATCH"
            return result

        document = json.loads(metadata_payload.decode("utf-8"))
        item_id = document.get("id") or document.get("itemId")
        if str(item_id or "") != CATALOG_RECORD_ID:
            result["decision"] = "CATALOG_ITEM_ID_NOT_CONFIRMED"
            return result

        records = _extract_file_records(document, CATALOG_RECORD_ID)
        matches = [
            record for record in records
            if _file_name(record) == EXPECTED_XML_NAME and _file_size(record) == EXPECTED_XML_SIZE
        ]
        result["matching_xml_record_count"] = len(matches)
        if len(matches) != 1:
            result["decision"] = "EXPECTED_XML_RECORD_NOT_UNIQUE"
            return result

        uri = _download_uri(matches[0])
        if not uri:
            result["decision"] = "XML_DOWNLOAD_URI_UNAVAILABLE"
            return result
        validate_public_url(uri)

        response = xml_fetcher(uri, limit=MAX_XML_BYTES)
        result["xml_http_status"] = response["status"]
        payload = response.get("payload", b"")
        headers = response.get("headers", {})
        content_type = str(headers.get("Content-Type") or "").lower()
        try:
            content_length = int(headers.get("Content-Length"))
        except (TypeError, ValueError):
            content_length = None

        result["xml_bytes_read"] = len(payload)
        result["xml_content_type"] = content_type
        result["xml_final_host"] = urlsplit(response.get("final_url", uri)).hostname
        if response.get("final_url"):
            validate_public_url(response["final_url"])

        if (
            response["status"] != 200
            or content_length != EXPECTED_XML_SIZE
            or len(payload) != EXPECTED_XML_SIZE
            or "xml" not in content_type
        ):
            result["decision"] = "XML_RESPONSE_NOT_EXACTLY_CONFIRMED"
            return result

        result["xml_sha256"] = hashlib.sha256(payload).hexdigest()
        result.update(summarize_dictionary(payload))
        result["decision"] = "ATTRIBUTE_DICTIONARY_PARSED" if result["attribute_count"] else "NO_ATTRIBUTE_DEFINITIONS"
        return result
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        result["decision"] = "AUDIT_ERROR"
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
