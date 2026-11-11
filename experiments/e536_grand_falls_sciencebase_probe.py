"""E536: inspect public ScienceBase item/file metadata without downloading data files.

The probe is deliberately metadata-only. It records item/child identifiers,
file names, sizes and URL origins, but never downloads raw DEMs, imagery or
time-series files and never stores URL query strings.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

API_ROOT = "https://www.sciencebase.gov/catalog"
ALLOWED_HOSTS = {"www.sciencebase.gov", "sciencebase.gov"}
MAX_METADATA_BYTES = 5 * 1024 * 1024
MAX_CHILDREN = 100

ITEMS = (
    {
        "item_id": "662bccfad34ea70bd5f11f88",
        "doi": "10.5066/P9FRH62D",
        "role": "2022-2023 ripple photogrammetry",
    },
    {
        "item_id": "67bf94acd34e8876fcbfc91b",
        "doi": "10.5066/P13HPPYM",
        "role": "2023-2024 integrated sediment transport release",
    },
    {
        "item_id": "67b78df2d34e1a2e835b13b7",
        "doi": "10.5066/P13HPPYM",
        "role": "2024 photogrammetry component of the same parent DOI",
    },
    {
        "item_id": "68c05cbbd4be025f1dac0cd4",
        "doi": "10.5066/P1TJFD9N",
        "role": "2009-2014 long-term meteorology",
    },
    {
        "item_id": "662ac4a0d34ea70bd5f0bc9c",
        "doi": "10.5066/P9YQLHHB",
        "role": "2023 April-July meteorological component",
    },
)


def safe_sciencebase_url(url: str) -> bool:
    parsed = urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname in ALLOWED_HOSTS
        and parsed.path.startswith("/catalog/")
        and not parsed.username
        and not parsed.password
        and not parsed.fragment
    )


def item_url(item_id: str) -> str:
    if len(item_id) != 24 or not all(ch in "0123456789abcdef" for ch in item_id):
        raise ValueError("ScienceBase item ID must be a 24-character lowercase hex ID")
    return f"{API_ROOT}/item/{item_id}?format=json"


def children_url(item_id: str) -> str:
    if len(item_id) != 24 or not all(ch in "0123456789abcdef" for ch in item_id):
        raise ValueError("ScienceBase item ID must be a 24-character lowercase hex ID")
    query = urlencode({
        "q": "",
        "filter": f"parentId={item_id}",
        "format": "json",
        "max": "1000",
    })
    return f"{API_ROOT}/items?{query}"


def fetch_json(url: str) -> dict:
    if not safe_sciencebase_url(url):
        raise ValueError("request URL is outside the official ScienceBase catalog")
    request = Request(
        url,
        headers={
            "User-Agent": "NASA-E536-ScienceBase-metadata-audit/1.0",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=45) as response:
            status = response.status
            final_url = response.geturl()
            payload = response.read(MAX_METADATA_BYTES + 1)
    except HTTPError as error:
        status = error.code
        final_url = error.geturl()
        payload = error.read(MAX_METADATA_BYTES + 1)
    except URLError as error:
        return {
            "status": None,
            "error": type(error.reason).__name__,
            "response_sha256": None,
            "response_bytes": 0,
            "document": None,
        }

    if not safe_sciencebase_url(final_url):
        raise ValueError("ScienceBase metadata request redirected outside the official catalog")
    if len(payload) > MAX_METADATA_BYTES:
        raise ValueError("ScienceBase metadata response exceeds the 5 MiB safety limit")
    result = {
        "status": status,
        "response_sha256": hashlib.sha256(payload).hexdigest(),
        "response_bytes": len(payload),
        "document": None,
    }
    if status == 200:
        result["document"] = json.loads(payload.decode("utf-8"))
    return result


def _file_records(item: dict) -> list[dict]:
    candidates = list(item.get("files", []) or [])
    for facet in item.get("facets", []) or []:
        if isinstance(facet, dict):
            candidates.extend(facet.get("files", []) or [])
    records = []
    seen = set()
    for file_info in candidates:
        if not isinstance(file_info, dict):
            continue
        url = file_info.get("url") or file_info.get("downloadURL")
        parsed = urlparse(url) if isinstance(url, str) else None
        record = {
            "name": file_info.get("name"),
            "size_bytes": file_info.get("size"),
            "content_type": file_info.get("contentType"),
            "url_host": parsed.hostname if parsed else None,
            "url_path": parsed.path if parsed else None,
            "url_query_stored": False,
        }
        key = (
            record["name"],
            record["size_bytes"],
            record["content_type"],
            record["url_host"],
            record["url_path"],
        )
        if key not in seen:
            seen.add(key)
            records.append(record)
    return records


def _child_records(document: dict) -> list[dict]:
    children = document.get("items", [])
    if not isinstance(children, list):
        return []
    records = []
    for child in children[:MAX_CHILDREN]:
        if not isinstance(child, dict):
            continue
        records.append({
            "id": child.get("id"),
            "title": child.get("title"),
            "has_children": child.get("hasChildren"),
            "access_level": child.get("accessLevel"),
            "file_count_in_listing": len(child.get("files", []) or []),
        })
    return records


def run_probe() -> dict:
    results = []
    for spec in ITEMS:
        item_id = spec["item_id"]
        item_response = fetch_json(item_url(item_id))
        record = {
            **spec,
            "item_url": item_url(item_id),
            "item_http_status": item_response["status"],
            "item_response_sha256": item_response["response_sha256"],
            "item_response_bytes": item_response["response_bytes"],
            "item_title": None,
            "item_access_level": None,
            "item_id_matches": None,
            "grand_falls_title_match": None,
            "doi_string_in_item_json": None,
            "direct_file_count": 0,
            "direct_files": [],
            "children_http_status": None,
            "child_response_sha256": None,
            "child_count": 0,
            "children": [],
            "raw_data_downloaded": False,
        }
        document = item_response["document"]
        if document is not None:
            record["item_title"] = document.get("title")
            record["item_access_level"] = document.get("accessLevel")
            record["item_id_matches"] = str(document.get("id", "")).lower() == item_id
            record["grand_falls_title_match"] = "grand falls" in str(document.get("title", "")).lower()
            record["doi_string_in_item_json"] = spec["doi"] in json.dumps(document, ensure_ascii=False)
            files = _file_records(document)
            record["direct_file_count"] = len(files)
            record["direct_files"] = files[:MAX_CHILDREN]

            child_response = fetch_json(children_url(item_id))
            record["children_http_status"] = child_response["status"]
            record["child_response_sha256"] = child_response["response_sha256"]
            child_document = child_response["document"]
            if child_document is not None:
                children = _child_records(child_document)
                record["child_count"] = len(children)
                record["children"] = children

        results.append(record)

    accessible = all(item["item_http_status"] == 200 for item in results)
    return {
        "experiment": "E536",
        "catalog": API_ROOT,
        "items": results,
        "all_item_metadata_accessible": accessible,
        "raw_data_downloaded": False,
        "raster_or_timeseries_values_read": False,
        "claim_boundary": (
            "This is a public metadata/file-listing probe only. It does not download "
            "or validate DEMs, imagery, meteorological time series, CRS, resolution, "
            "units, nodata, calibration, or physical comparability to Mars."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e536/sciencebase.json"))
    args = parser.parse_args()
    receipt = run_probe()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": receipt["experiment"],
        "all_item_metadata_accessible": receipt["all_item_metadata_accessible"],
        "items": [
            {
                "item_id": item["item_id"],
                "item_http_status": item["item_http_status"],
                "item_title": item["item_title"],
                "direct_file_count": item["direct_file_count"],
                "children_http_status": item["children_http_status"],
                "child_count": item["child_count"],
            }
            for item in receipt["items"]
        ],
        "raw_data_downloaded": receipt["raw_data_downloaded"],
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
