"""E593: bounded extraction of the official Grand Falls photogrammetry XML metadata."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

from experiments.e590_grand_falls_2023_2024_probe import (
    MAX_METADATA_BYTES,
    _download_uri,
    _extract_file_records,
    _file_name,
    _file_size,
)
from experiments.e591_grand_falls_photogrammetry_metadata import CHILD_ITEM_ID, ITEM_URL
from experiments.e577_grand_falls_2017_2019_access_probe import (
    ALLOWED_HOSTS,
    TIMEOUT_SECONDS,
    USER_AGENT,
)

EXPERIMENT = "E593"
EXPECTED_ITEM_METADATA_SHA256 = "f466468ba4b700ecb2a613727483100a9f62f14e8d26dfc8ba840b0122049424"
EXPECTED_XML_NAME = "Photogrammetry_GFDF_ripples_2024.xml"
EXPECTED_XML_SIZE = 12_658
MAX_XML_BYTES = 65_536

FIELD_CATEGORIES = {
    "title": "product_description",
    "pubdate": "acquisition_dates",
    "begdate": "acquisition_dates",
    "enddate": "acquisition_dates",
    "caldate": "acquisition_dates",
    "procdate": "processing_lineage",
    "horizdn": "horizontal_reference",
    "ellips": "horizontal_reference",
    "geogcsn": "horizontal_reference",
    "projcsn": "horizontal_reference",
    "mapprojn": "horizontal_reference",
    "plandu": "horizontal_reference",
    "geogunit": "horizontal_reference",
    "semiaxis": "horizontal_reference",
    "denflat": "horizontal_reference",
    "altdatum": "vertical_reference",
    "altunits": "vertical_reference",
    "altenc": "vertical_reference",
    "depthdn": "vertical_reference",
    "depthdu": "vertical_reference",
    "depthres": "vertical_reference",
    "absres": "grid_resolution",
    "ordres": "grid_resolution",
    "latres": "grid_resolution",
    "longres": "grid_resolution",
    "cellsize": "grid_resolution",
    "resolution": "grid_resolution",
    "resolutn": "grid_resolution",
    "nodatavalue": "nodata",
    "nodata": "nodata",
    "missing": "nodata",
    "fillvalue": "nodata",
    "nullvalue": "nodata",
    "formname": "raster_representation",
    "format": "raster_representation",
    "rasttype": "raster_representation",
    "rastdtyp": "raster_representation",
    "rastband": "raster_representation",
    "rowcount": "raster_representation",
    "colcount": "raster_representation",
    "enttypl": "raster_representation",
    "procdesc": "processing_lineage",
    "srcused": "processing_lineage",
    "srcprod": "processing_lineage",
    "srccontr": "processing_lineage",
    "description": "processing_lineage",
    "code": "reference_identifier",
    "codespace": "reference_identifier",
    "unitofmeasure": "grid_resolution",
    "distance": "grid_resolution",
}
FORBIDDEN_PATH_PARTS = {
    "spdom", "bounding", "westbc", "eastbc", "northbc", "southbc",
    "coordinates", "coordinate", "polygon", "point", "easting", "northing",
    "latitude", "longitude", "lat", "long",
}
URL_RE = re.compile(r"https?://\S+", re.IGNORECASE)
EMAIL_RE = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")
PATH_RE = re.compile(r"(?:[A-Za-z]:\\|/)[^\s,;]+")
COORD_PAIR_RE = re.compile(
    r"(?<![A-Za-z0-9])[-+]?\d{1,3}(?:\.\d+)?\s*[,/]\s*[-+]?\d{1,3}(?:\.\d+)?(?![A-Za-z0-9])"
)


class ProbeError(RuntimeError):
    pass


def validate_public_url(url: str) -> None:
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ProbeError("invalid URL port") from exc
    decoded_segments = [unquote(part) for part in parsed.path.split("/")]
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
        headers={"User-Agent": USER_AGENT, "Accept": "application/json,application/xml,text/xml,*/*"},
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


def _safe_text(value: str, *, limit: int = 600) -> str:
    value = " ".join(value.split())
    value = URL_RE.sub("[URL REDACTED]", value)
    value = EMAIL_RE.sub("[EMAIL REDACTED]", value)
    value = PATH_RE.sub("[PATH REDACTED]", value)
    value = COORD_PAIR_RE.sub("[COORDINATE PAIR REDACTED]", value)
    return value[:limit]


def _category_for(tag: str, path: tuple[str, ...]) -> str | None:
    if tag in {"code", "codespace"}:
        if any("vertical" in part or "alt" in part for part in path):
            return "vertical_reference"
        if any("reference" in part or "spatialref" in part for part in path):
            return "horizontal_reference"
        return "reference_identifier"
    if tag in {"distance", "unitofmeasure", "value"} and any(
        "resolution" in part or "distance" in part for part in path
    ):
        return "grid_resolution"
    if tag == "description" and any("lineage" in part or "process" in part for part in path):
        return "processing_lineage"
    if tag == "date" and any("acquisition" in part or "timeperd" in part for part in path):
        return "acquisition_dates"
    return FIELD_CATEGORIES.get(tag)


def summarize_xml(payload: bytes) -> dict:
    if not payload or len(payload) > MAX_XML_BYTES:
        raise ValueError("XML payload empty or over the 64 KiB cap")
    upper = payload.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise ValueError("DTD/entity declarations are not accepted")

    root = ET.fromstring(payload)
    tag_counts: Counter[str] = Counter()
    selected: list[dict] = []

    def walk(element: ET.Element, parents: tuple[str, ...] = ()) -> None:
        tag = _local_name(element.tag)
        path = parents + (tag,)
        tag_counts[tag] += 1
        children = list(element)
        if children:
            for child in children:
                walk(child, path)
            return

        raw_value = element.text or ""
        value = " ".join(raw_value.split())
        if not value:
            return
        if any(part in FORBIDDEN_PATH_PARTS for part in path):
            return

        category = _category_for(tag, path)
        if category is None:
            return
        if tag == "attrlabl" and not re.search(r"no[\s_-]*data|missing|fill", value, re.IGNORECASE):
            return
        safe = _safe_text(value, limit=1000 if category == "processing_lineage" else 600)
        if not safe:
            return
        selected.append({
            "category": category,
            "tag": tag,
            "path": "/" + "/".join(path),
            "value": safe,
        })

    walk(root)
    selected.sort(key=lambda item: (item["category"], item["path"], item["value"]))
    category_counts = Counter(item["category"] for item in selected)
    by_category = {
        category: [item for item in selected if item["category"] == category][:30]
        for category in sorted(category_counts)
    }
    return {
        "xml_root_tag": _local_name(root.tag),
        "xml_tag_inventory": [
            {"tag": tag, "count": count}
            for tag, count in sorted(tag_counts.items(), key=lambda item: (-item[1], item[0]))[:80]
        ],
        "selected_field_count": len(selected),
        "field_counts_by_category": dict(sorted(category_counts.items())),
        "horizontal_reference_fields": by_category.get("horizontal_reference", []),
        "vertical_reference_fields": by_category.get("vertical_reference", []),
        "grid_resolution_fields": by_category.get("grid_resolution", []),
        "nodata_fields": by_category.get("nodata", []),
        "acquisition_date_fields": by_category.get("acquisition_dates", []),
        "processing_lineage_fields": by_category.get("processing_lineage", []),
        "raster_representation_fields": by_category.get("raster_representation", []),
        "product_description_fields": by_category.get("product_description", []),
        "reference_identifier_fields": by_category.get("reference_identifier", []),
        "metadata_categories_present": {
            "horizontal_reference": bool(by_category.get("horizontal_reference")),
            "vertical_reference": bool(by_category.get("vertical_reference")),
            "grid_resolution": bool(by_category.get("grid_resolution")),
            "nodata": bool(by_category.get("nodata")),
            "acquisition_dates": bool(by_category.get("acquisition_dates")),
            "processing_lineage": bool(by_category.get("processing_lineage")),
            "raster_representation": bool(by_category.get("raster_representation")),
        },
        "raw_xml_stored": False,
        "raw_coordinates_stored": False,
    }


def audit(item_fetcher=None, xml_fetcher=None, expected_item_sha256: str = EXPECTED_ITEM_METADATA_SHA256) -> dict:
    if item_fetcher is None:
        item_fetcher = fetch_strict_bounded
    if xml_fetcher is None:
        xml_fetcher = fetch_strict_bounded

    result = {
        "experiment": EXPERIMENT,
        "source_item_id": CHILD_ITEM_ID,
        "expected_item_metadata_sha256": expected_item_sha256,
        "item_metadata_http_status": None,
        "xml_http_status": None,
        "metadata_file_name": EXPECTED_XML_NAME,
        "expected_metadata_file_size_bytes": EXPECTED_XML_SIZE,
        "decision": "ACQUISITION_NOT_STARTED",
        "credentials_used": False,
        "metadata_xml_bytes_downloaded": False,
        "archive_bytes_downloaded": False,
        "raster_bytes_downloaded": False,
        "raw_xml_stored": False,
        "raw_coordinates_stored": False,
        "raw_urls_stored": False,
        "raw_file_paths_stored": False,
    }

    try:
        item_response = item_fetcher(ITEM_URL, limit=MAX_METADATA_BYTES)
        result["item_metadata_http_status"] = item_response["status"]
        if item_response["status"] != 200:
            result["decision"] = "ITEM_METADATA_UNAVAILABLE"
            return result
        item_payload = item_response["payload"]
        if len(item_payload) > MAX_METADATA_BYTES:
            result["decision"] = "ITEM_METADATA_OVER_CAP"
            return result
        item_content_type = str(item_response["headers"].get("Content-Type") or "").lower()
        if "text/html" in item_content_type:
            result["decision"] = "ITEM_METADATA_HTML_RESPONSE"
            return result
        result["item_metadata_sha256"] = hashlib.sha256(item_payload).hexdigest()
        if result["item_metadata_sha256"] != expected_item_sha256:
            result["decision"] = "ITEM_METADATA_CHANGED_SINCE_E591"
            return result

        document = json.loads(item_payload.decode("utf-8"))
        item_id = document.get("id") or document.get("itemId")
        if str(item_id or "") != CHILD_ITEM_ID:
            result["decision"] = "CHILD_ITEM_ID_NOT_CONFIRMED"
            return result

        records = _extract_file_records(document, CHILD_ITEM_ID)
        matches = [
            record for record in records
            if _file_name(record) == EXPECTED_XML_NAME
            and _file_size(record) == EXPECTED_XML_SIZE
        ]
        result["matching_xml_file_record_count"] = len(matches)
        if len(matches) != 1:
            result["decision"] = "EXPECTED_XML_FILE_RECORD_NOT_UNIQUE"
            return result

        uri = _download_uri(matches[0])
        if not uri:
            result["decision"] = "XML_DOWNLOAD_URI_UNAVAILABLE"
            return result
        validate_public_url(uri)

        xml_response = xml_fetcher(uri, limit=MAX_XML_BYTES + 1)
        result["xml_http_status"] = xml_response["status"]
        if xml_response["status"] != 200:
            result["decision"] = "XML_METADATA_UNAVAILABLE"
            return result

        xml_payload = xml_response["payload"]
        content_type = str(xml_response["headers"].get("Content-Type") or "").lower()
        content_length = xml_response["headers"].get("Content-Length")
        result["xml_content_type"] = content_type
        result["xml_bytes_read"] = len(xml_payload)
        result["xml_final_host"] = urlsplit(xml_response["final_url"]).hostname
        if "text/html" in content_type:
            result["decision"] = "XML_HTML_RESPONSE"
            return result
        if len(xml_payload) > MAX_XML_BYTES:
            result["decision"] = "XML_METADATA_OVER_CAP"
            return result
        if len(xml_payload) != EXPECTED_XML_SIZE:
            result["decision"] = "XML_SIZE_MISMATCH"
            return result
        if content_length not in (None, "") and int(content_length) != EXPECTED_XML_SIZE:
            result["decision"] = "XML_CONTENT_LENGTH_MISMATCH"
            return result

        result["metadata_xml_bytes_downloaded"] = True
        result["xml_sha256"] = hashlib.sha256(xml_payload).hexdigest()
        result["xml_summary"] = summarize_xml(xml_payload)
        result["decision"] = (
            "XML_METADATA_PARSED"
            if result["xml_summary"]["selected_field_count"] > 0
            else "XML_METADATA_NO_RECOGNIZED_FIELDS"
        )
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
    summary = {
        "experiment": receipt.get("experiment"),
        "decision": receipt.get("decision"),
        "item_metadata_http_status": receipt.get("item_metadata_http_status"),
        "xml_http_status": receipt.get("xml_http_status"),
        "xml_bytes_read": receipt.get("xml_bytes_read"),
        "xml_sha256": receipt.get("xml_sha256"),
        "xml_summary": receipt.get("xml_summary"),
        "metadata_xml_bytes_downloaded": receipt.get("metadata_xml_bytes_downloaded"),
        "archive_bytes_downloaded": receipt.get("archive_bytes_downloaded"),
        "raster_bytes_downloaded": receipt.get("raster_bytes_downloaded"),
        "raw_xml_stored": receipt.get("raw_xml_stored"),
        "raw_coordinates_stored": receipt.get("raw_coordinates_stored"),
    }
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
