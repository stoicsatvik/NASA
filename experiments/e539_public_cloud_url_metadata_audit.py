"""E539: inspect public ScienceBase/USGS metadata for explicit direct cloud URLs.

This is metadata-only. It never follows file URLs, downloads rasters, stores
raw metadata, or records query values that could contain signed credentials.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ITEM_ID = "662bccfad34ea70bd5f11f88"
SCIENCEBASE = "https://www.sciencebase.gov/catalog"
USGS_XML = "https://data.usgs.gov/datacatalog/metadata/USGS.662bccfad34ea70bd5f11f88.xml"
SCIENCEBASE_HOSTS = {"www.sciencebase.gov", "sciencebase.gov"}
ALLOWED_METADATA_HOSTS = SCIENCEBASE_HOSTS | {"data.usgs.gov"}
MAX_METADATA_BYTES = 5 * 1024 * 1024
TIMEOUT = 30
USER_AGENT = "UnifiedParallelFoundry-E539-public-metadata-audit/1.0"
TOKEN_QUERY_KEYS = {
    "token", "access_token", "auth", "authorization", "key", "api_key",
    "signature", "sig", "x-amz-signature", "x-amz-credential",
    "x-amz-security-token", "expires", "se", "sp", "sv",
}


def _fetch_metadata(url: str) -> tuple[int, bytes, str]:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_METADATA_HOSTS
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise ValueError("metadata URL is outside the pinned public HTTPS hosts")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/xml"},
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            final = urllib.parse.urlsplit(response.geturl())
            if (
                final.scheme != "https"
                or final.hostname not in ALLOWED_METADATA_HOSTS
                or final.username
                or final.password
                or final.fragment
            ):
                raise ValueError("metadata redirect left the public host allowlist")
            payload = response.read(MAX_METADATA_BYTES + 1)
            if len(payload) > MAX_METADATA_BYTES:
                raise ValueError("metadata response exceeds the 5 MiB cap")
            return response.status, payload, response.geturl()
    except urllib.error.HTTPError as error:
        payload = error.read(MAX_METADATA_BYTES + 1)
        return error.code, payload[:MAX_METADATA_BYTES], error.geturl()


def _url_record(value: str, source: str) -> dict | None:
    parsed = urllib.parse.urlsplit(value.strip())
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        return None
    query_keys = sorted({key.lower() for key, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)})
    token_like = bool(TOKEN_QUERY_KEYS.intersection(query_keys))
    host = parsed.hostname.lower()
    path = parsed.path or "/"

    if host in SCIENCEBASE_HOSTS and path.startswith("/manager/item/"):
        classification = "manager_preview_not_direct"
    elif host in SCIENCEBASE_HOSTS and path.startswith("/catalog/file/get/"):
        classification = "sciencebase_catalog_file_endpoint"
    elif token_like:
        classification = "signed_or_tokenized_url_not_anonymous"
    elif parsed.scheme == "https":
        classification = "external_https_candidate_not_verified"
    else:
        classification = "non_https_url_rejected"

    return {
        "source_field": source,
        "scheme": parsed.scheme,
        "host": host,
        "path": path,
        "query_key_names": query_keys,
        "token_like_query_present": token_like,
        "classification": classification,
        "direct_url_candidate_unverified": (
            parsed.scheme == "https"
            and not token_like
            and classification in {
                "sciencebase_catalog_file_endpoint",
                "external_https_candidate_not_verified",
            }
        ),
    }


def _walk_urls(value, path: str = "$"):
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{path}.{key}"
            key_lower = str(key).lower()
            if isinstance(child, str) and any(token in key_lower for token in ("url", "uri", "link", "href")):
                yield child_path, child
            else:
                yield from _walk_urls(child, child_path)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from _walk_urls(child, f"{path}[{index}]")


def _items(payload: dict) -> list[dict]:
    values = payload.get("items", [])
    if isinstance(values, dict):
        values = values.get("items", [])
    return [item for item in values if isinstance(item, dict)] if isinstance(values, list) else []


def _fetch_sciencebase_items() -> tuple[list[dict], list[dict]]:
    errors = []
    root_url = f"{SCIENCEBASE}/item/{ITEM_ID}?format=json"
    status, raw, final_url = _fetch_metadata(root_url)
    if status != 200:
        return [], [{"source": "sciencebase_root", "http_status": status, "url": _url_record(final_url, "final_url")}]
    root = json.loads(raw.decode("utf-8"))
    items = [root]

    query = urllib.parse.urlencode({
        "q": "",
        "filter": f"parentId={ITEM_ID}",
        "format": "json",
        "max": 100,
    })
    child_status, child_raw, child_final = _fetch_metadata(f"{SCIENCEBASE}/items?{query}")
    if child_status == 200:
        children = _items(json.loads(child_raw.decode("utf-8")))
        for child in children:
            child_id = child.get("id") or child.get("itemId")
            if not child_id:
                continue
            item_status, item_raw, item_final = _fetch_metadata(
                f"{SCIENCEBASE}/item/{urllib.parse.quote(str(child_id))}?format=json"
            )
            if item_status == 200:
                items.append(json.loads(item_raw.decode("utf-8")))
            else:
                errors.append({
                    "source": f"sciencebase_child:{child_id}",
                    "http_status": item_status,
                    "final_host": urllib.parse.urlsplit(item_final).hostname,
                    "final_path": urllib.parse.urlsplit(item_final).path,
                })
    else:
        errors.append({
            "source": "sciencebase_children",
            "http_status": child_status,
            "final_host": urllib.parse.urlsplit(child_final).hostname,
            "final_path": urllib.parse.urlsplit(child_final).path,
        })
    return items, errors


def _audit_xml_metadata() -> dict:
    status, raw, final_url = _fetch_metadata(USGS_XML)
    result = {
        "http_status": status,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "final_host": urllib.parse.urlsplit(final_url).hostname,
        "final_path": urllib.parse.urlsplit(final_url).path,
        "url_candidates": [],
    }
    if status != 200:
        return result
    root = ET.fromstring(raw)
    for element in root.iter():
        if element.text and element.text.strip().startswith(("https://", "http://")):
            record = _url_record(element.text.strip(), f"xml:{element.tag}")
            if record:
                result["url_candidates"].append(record)
        for key, value in element.attrib.items():
            if value.startswith(("https://", "http://")):
                record = _url_record(value, f"xml-attribute:{element.tag}.{key}")
                if record:
                    result["url_candidates"].append(record)
    return result


def audit() -> dict:
    items, errors = _fetch_sciencebase_items()
    candidates = []
    item_summary = []
    for item in items:
        item_id = str(item.get("id") or item.get("itemId") or "")
        item_summary.append({
            "item_id": item_id,
            "title_present": bool(item.get("title")),
            "file_count": len(item.get("files", [])) if isinstance(item.get("files"), list) else 0,
            "top_level_keys": sorted(str(key) for key in item.keys()),
        })
        for source, value in _walk_urls(item, f"item:{item_id}"):
            record = _url_record(value, source)
            if record:
                candidates.append(record)

    xml = _audit_xml_metadata()
    candidates.extend(xml["url_candidates"])
    unique = {}
    for item in candidates:
        key = (
            item["source_field"], item["host"], item["path"],
            tuple(item["query_key_names"]), item["classification"],
        )
        unique[key] = item
    candidates = sorted(
        unique.values(),
        key=lambda item: (item["classification"], item["host"], item["path"], item["source_field"]),
    )
    direct = [
        item for item in candidates
        if item["direct_url_candidate_unverified"]
        and item["classification"] != "manager_preview_not_direct"
    ]
    return {
        "experiment": "E539",
        "item_id": ITEM_ID,
        "sciencebase_items_inspected": len(items),
        "items": item_summary,
        "metadata_errors": errors,
        "usgs_xml_metadata": {key: value for key, value in xml.items() if key != "url_candidates"},
        "url_candidate_count": len(candidates),
        "url_candidates": candidates,
        "unverified_direct_url_candidates": direct,
        "decision": (
            "UNVERIFIED_DIRECT_URL_CANDIDATE_FOUND_IN_PUBLIC_METADATA"
            if direct else
            "NO_UNVERIFIED_DIRECT_URL_CANDIDATE_FOUND_IN_PUBLIC_METADATA"
        ),
        "raw_metadata_stored": False,
        "query_values_stored": False,
        "file_urls_followed": False,
        "binary_files_downloaded": False,
        "interpretation": (
            "This run inventories only URL-like fields explicitly present in public item/XML metadata. "
            "It does not prove anonymous access for any candidate and does not follow file URLs. "
            "Manager preview routes and signed/tokenized URLs are not treated as anonymous direct links."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e539/public-url-audit.json"))
    args = parser.parse_args()
    result = audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": result["experiment"],
        "sciencebase_items_inspected": result["sciencebase_items_inspected"],
        "url_candidate_count": result["url_candidate_count"],
        "unverified_direct_url_candidate_count": len(result["unverified_direct_url_candidates"]),
        "decision": result["decision"],
        "raw_metadata_stored": result["raw_metadata_stored"],
        "file_urls_followed": result["file_urls_followed"],
        "binary_files_downloaded": result["binary_files_downloaded"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
