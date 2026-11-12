"""E591: bounded metadata-only inventory of the Grand Falls photogrammetry child item."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from urllib.parse import urlencode

from experiments.e590_grand_falls_2023_2024_probe import (
    MAX_METADATA_BYTES,
    _extract_file_records,
    _safe_file_record,
    fetch_bounded,
)

CHILD_ITEM_ID = "67b78df2d34e1a2e835b13b7"
ITEM_URL = (
    f"https://www.sciencebase.gov/catalog/item/{CHILD_ITEM_ID}?"
    + urlencode({"format": "json", "fields": "title,files,facets,spatial"})
)
RASTER_EXTENSIONS = {".tif", ".tiff", ".img", ".jp2", ".vrt", ".dem"}
ARCHIVE_EXTENSIONS = {".zip", ".7z", ".tar", ".gz"}


def summarize_document(document: dict, payload: bytes) -> dict:
    records = _extract_file_records(document, CHILD_ITEM_ID)
    inventory = [_safe_file_record(record) for record in records]
    raster_candidates = [item for item in inventory if item["extension"] in RASTER_EXTENSIONS]
    archive_candidates = [item for item in inventory if item["extension"] in ARCHIVE_EXTENSIONS]
    return {
        "experiment": "E591",
        "source_item_id": CHILD_ITEM_ID,
        "title": str(document.get("title") or ""),
        "metadata_sha256": hashlib.sha256(payload).hexdigest(),
        "metadata_bytes": len(payload),
        "file_count": len(inventory),
        "file_inventory": inventory,
        "raster_filename_candidates": raster_candidates,
        "archive_candidates": archive_candidates,
        "raster_candidate_count": len(raster_candidates),
        "archive_candidate_count": len(archive_candidates),
        "spatial_extent_present": bool(document.get("spatial") or document.get("spatialExtent")),
        "credentials_used": False,
        "file_bytes_downloaded": False,
        "raw_urls_stored": False,
        "raw_coordinates_stored": False,
        "decision": "METADATA_INVENTORY_COMPLETE" if inventory else "NO_FILE_RECORDS",
    }


def audit(fetcher=fetch_bounded) -> dict:
    result = {
        "experiment": "E591",
        "source_item_id": CHILD_ITEM_ID,
        "http_status": None,
        "decision": "METADATA_UNAVAILABLE",
        "credentials_used": False,
        "file_bytes_downloaded": False,
        "raw_urls_stored": False,
        "raw_coordinates_stored": False,
    }
    try:
        response = fetcher(ITEM_URL, limit=MAX_METADATA_BYTES)
        result["http_status"] = response["status"]
        if response["status"] != 200:
            return result
        payload = response["payload"]
        document = json.loads(payload.decode("utf-8"))
        result.update(summarize_document(document, payload))
        result["http_status"] = response["status"]
        return result
    except Exception as exc:
        result["error_type"] = type(exc).__name__
        return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": receipt.get("experiment"),
        "source_item_id": receipt.get("source_item_id"),
        "http_status": receipt.get("http_status"),
        "title": receipt.get("title"),
        "file_count": receipt.get("file_count"),
        "raster_candidate_count": receipt.get("raster_candidate_count"),
        "archive_candidate_count": receipt.get("archive_candidate_count"),
        "spatial_extent_present": receipt.get("spatial_extent_present"),
        "decision": receipt.get("decision"),
        "credentials_used": receipt.get("credentials_used"),
        "file_bytes_downloaded": receipt.get("file_bytes_downloaded"),
        "raw_urls_stored": receipt.get("raw_urls_stored"),
        "raw_coordinates_stored": receipt.get("raw_coordinates_stored"),
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
