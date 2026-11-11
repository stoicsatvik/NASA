"""E536: bounded, provenance-preserving ScienceBase raster acquisition probe."""
from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ITEM_ID = "662bccfad34ea70bd5f11f88"
BASE_URL = "https://www.sciencebase.gov/catalog"
MAX_ITEMS = 50
MAX_DEPTH = 2
MAX_DOWNLOAD_BYTES = 50_000_000
TIMEOUT_SECONDS = 45
OUT = Path(".artifacts/e536")
USER_AGENT = "UnifiedParallelFoundry/1.0 (public-data provenance audit)"
ALLOWED_CATALOG_HOSTS = {"www.sciencebase.gov", "sciencebase.gov"}
MAX_METADATA_BYTES = 5 * 1024 * 1024


def _request_json(url: str) -> dict:
    parsed = urllib.parse.urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname not in ALLOWED_CATALOG_HOSTS
        or not parsed.path.startswith("/catalog/")
        or parsed.username
        or parsed.password
        or parsed.fragment
    ):
        raise ValueError("request URL is outside the official ScienceBase catalog")
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        final = urllib.parse.urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname not in ALLOWED_CATALOG_HOSTS or not final.path.startswith("/catalog/"):
            raise ValueError("ScienceBase metadata request redirected outside the official catalog")
        payload = response.read(MAX_METADATA_BYTES + 1)
    if len(payload) > MAX_METADATA_BYTES:
        raise ValueError("ScienceBase metadata response exceeds the 5 MiB safety limit")
    return json.loads(payload.decode("utf-8"))


def _child_items(payload: dict) -> list[dict]:
    value = payload.get("items", [])
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        nested = value.get("items", [])
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]
    return []


def _file_entries(item: dict) -> list[dict]:
    files = item.get("files", [])
    if isinstance(files, list):
        return [entry for entry in files if isinstance(entry, dict)]
    return []


def _normalize_file(item_id: str, entry: dict) -> dict | None:
    name = entry.get("name") or entry.get("fileName") or entry.get("filename")
    url = entry.get("url") or entry.get("downloadUri") or entry.get("downloadURL")
    if not name or not url:
        return None
    if str(url).startswith("/"):
        url = urllib.parse.urljoin("https://www.sciencebase.gov", str(url))
    size = entry.get("size")
    try:
        size = int(size) if size is not None else None
    except (TypeError, ValueError):
        size = None
    return {
        "item_id": item_id,
        "name": str(name),
        "size_bytes": size,
        "url": str(url),
        "content_type": entry.get("contentType") or entry.get("mimeType"),
    }


def _is_direct_file_url(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname in ALLOWED_CATALOG_HOSTS
        and parsed.path.startswith("/catalog/file/get/")
        and not parsed.username
        and not parsed.password
        and not parsed.fragment
    )


def _has_tiff_magic(prefix: bytes) -> bool:
    return prefix[:4] in (b"II*\\x00", b"MM\\x00*", b"II+\\x00", b"MM\\x00+")


def _has_zip_magic(prefix: bytes) -> bool:
    return prefix.startswith((b"PK\\x03\\x04", b"PK\\x05\\x06", b"PK\\x07\\x08"))


def _payload_matches(filename: str, prefix: bytes) -> bool:
    suffix = Path(filename).suffix.lower()
    if suffix in (".tif", ".tiff"):
        return _has_tiff_magic(prefix)
    if suffix == ".zip":
        return _has_zip_magic(prefix)
    return False


def _catalogue_total_bytes(files: list[dict]) -> int | None:
    sizes = [file.get("size_bytes") for file in files]
    if not sizes or any(not isinstance(size, int) or size < 0 for size in sizes):
        return None
    return sum(sizes)


def _download_item_archive_bounded(item_id: str, files: list[dict], destination: Path) -> dict:
    if len(item_id) != 24 or any(ch not in "0123456789abcdef" for ch in item_id):
        return {"downloaded": False, "reason": "invalid_sciencebase_item_id"}
    catalogue_total = _catalogue_total_bytes(files)
    if catalogue_total is None:
        return {"downloaded": False, "reason": "catalogue_file_sizes_incomplete", "catalogue_total_bytes": None}
    if catalogue_total > MAX_DOWNLOAD_BYTES:
        return {"downloaded": False, "reason": "catalogue_total_exceeds_50mb_cap", "catalogue_total_bytes": catalogue_total}
    candidate = {
        "name": f"{item_id}.zip",
        "url": f"{BASE_URL}/file/get/{item_id}",
    }
    result = _download_bounded(candidate, destination)
    result["catalogue_total_bytes"] = catalogue_total
    result["download_method"] = "official_item_files_zip_endpoint"
    return result

def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_bounded(candidate: dict, destination: Path) -> dict:
    url = candidate["url"]
    if not _is_direct_file_url(url):
        parsed = urllib.parse.urlsplit(url)
        return {
            "downloaded": False,
            "reason": "not_a_direct_sciencebase_catalog_file_url",
            "url_host": parsed.hostname,
            "url_path": parsed.path,
        }
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/octet-stream, application/zip, image/tiff"})
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        final = urllib.parse.urlsplit(response.geturl())
        if final.scheme != "https" or final.hostname not in ALLOWED_CATALOG_HOSTS or not final.path.startswith("/catalog/file/get/"):
            return {"downloaded": False, "reason": "redirected_outside_official_file_endpoint", "final_host": final.hostname, "final_path": final.path}
        content_length = response.headers.get("Content-Length")
        if content_length:
            try:
                length = int(content_length)
            except ValueError:
                return {"downloaded": False, "reason": "invalid_content_length"}
            if length > MAX_DOWNLOAD_BYTES:
                return {"downloaded": False, "reason": "content_length_exceeds_50mb_cap", "content_length": length}
        content_type = response.headers.get_content_type()
        suffix = Path(candidate["name"]).suffix.lower()
        allowed_types = {
            ".tif": {"image/tiff", "image/geotiff", "application/octet-stream"},
            ".tiff": {"image/tiff", "image/geotiff", "application/octet-stream"},
            ".zip": {"application/zip", "application/x-zip-compressed", "application/octet-stream"},
        }.get(suffix, set())
        if content_type not in allowed_types:
            return {"downloaded": False, "reason": "unexpected_content_type", "content_type": content_type}
        prefix = response.read(8)
        if not _payload_matches(candidate["name"], prefix):
            return {"downloaded": False, "reason": "payload_magic_mismatch", "content_type": content_type, "prefix_hex": prefix.hex()}
        total = len(prefix)
        with destination.open("wb") as handle:
            handle.write(prefix)
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_DOWNLOAD_BYTES:
                    handle.close()
                    destination.unlink(missing_ok=True)
                    return {"downloaded": False, "reason": "stream_exceeded_50mb_cap", "bytes_seen": total}
                handle.write(chunk)
    return {
        "downloaded": True,
        "bytes": destination.stat().st_size,
        "sha256": _sha256(destination),
        "path": str(destination),
        "content_type": content_type,
    }


def _inspect_tiff(path: Path) -> dict:
    try:
        import numpy as np
        import tifffile
    except Exception as exc:
        return {"inspected": False, "reason": f"optional_tiff_dependency_unavailable: {type(exc).__name__}: {exc}"}

    try:
        with tifffile.TiffFile(path) as tif:
            page = tif.pages[0]
            wanted = (
                "ModelPixelScaleTag",
                "ModelTiepointTag",
                "ModelTransformationTag",
                "GeoKeyDirectoryTag",
                "GeoDoubleParamsTag",
                "GeoAsciiParamsTag",
                "GDAL_NODATA",
                "ImageDescription",
                "ResolutionUnit",
                "XResolution",
                "YResolution",
            )
            tags = {}
            for name in wanted:
                tag = page.tags.get(name)
                if tag is not None:
                    value = tag.value
                    if isinstance(value, bytes):
                        value = value.decode("utf-8", "replace")
                    elif hasattr(value, "tolist"):
                        value = value.tolist()
                    tags[name] = value

            array = page.asarray()
            values = np.asarray(array).astype("float64", copy=False)
            finite = np.isfinite(values)
            nodata = tags.get("GDAL_NODATA")
            if nodata is not None:
                try:
                    nodata_value = float(str(nodata).strip().strip("\x00"))
                    finite &= values != nodata_value
                except (TypeError, ValueError):
                    pass
            valid = values[finite]
            stats = None
            if valid.size:
                stats = {
                    "valid_pixel_count": int(valid.size),
                    "min": float(valid.min()),
                    "max": float(valid.max()),
                    "mean": float(valid.mean()),
                    "std_population": float(valid.std()),
                }
            return {
                "inspected": True,
                "page_count": len(tif.pages),
                "shape": list(page.shape),
                "dtype": str(page.dtype),
                "compression": str(page.compression),
                "geotiff_tags": tags,
                "pixel_statistics_unit_unassigned": stats,
            }
    except Exception as exc:
        return {"inspected": False, "reason": f"tiff_read_failed: {type(exc).__name__}: {exc}"}


def _extract_first_tiff(archive_path: Path, destination: Path) -> dict | None:
    try:
        with zipfile.ZipFile(archive_path) as archive:
            candidates = [
                info for info in archive.infolist()
                if not info.is_dir() and info.filename.lower().endswith((".tif", ".tiff"))
            ]
            if not candidates:
                return None
            selected = min(candidates, key=lambda info: info.file_size)
            if selected.file_size > MAX_DOWNLOAD_BYTES:
                return {"extracted": False, "reason": "contained_tiff_exceeds_50mb_cap", "size_bytes": selected.file_size}
            total = 0
            with archive.open(selected) as source:
                prefix = source.read(8)
                if not _has_tiff_magic(prefix):
                    return {"extracted": False, "reason": "contained_file_has_no_tiff_magic", "member": selected.filename, "prefix_hex": prefix.hex()}
                total = len(prefix)
                with destination.open("wb") as target:
                    target.write(prefix)
                    while True:
                        chunk = source.read(1024 * 1024)
                        if not chunk:
                            break
                        total += len(chunk)
                        if total > MAX_DOWNLOAD_BYTES:
                            target.close()
                            destination.unlink(missing_ok=True)
                            return {"extracted": False, "reason": "extracted_tiff_exceeds_50mb_cap"}
                        target.write(chunk)
            return {
                "extracted": True,
                "member": selected.filename,
                "bytes": destination.stat().st_size,
                "sha256": _sha256(destination),
                "path": str(destination),
            }
    except zipfile.BadZipFile:
        return {"extracted": False, "reason": "downloaded_zip_is_invalid"}


def probe() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    result = {
        "experiment": "E536",
        "item_id": ITEM_ID,
        "source_api": f"{BASE_URL}/item/{ITEM_ID}?format=json",
        "max_depth": MAX_DEPTH,
        "max_items": MAX_ITEMS,
        "max_download_bytes": MAX_DOWNLOAD_BYTES,
        "items": [],
        "files": [],
        "errors": [],
        "raw_sample_downloaded": False,
    }
    queue = [(ITEM_ID, 0)]
    seen = set()

    while queue and len(seen) < MAX_ITEMS:
        item_id, depth = queue.pop(0)
        if item_id in seen or depth > MAX_DEPTH:
            continue
        seen.add(item_id)
        try:
            item = _request_json(f"{BASE_URL}/item/{urllib.parse.quote(item_id)}?format=json")
            result["items"].append({
                "id": item.get("id") or item_id,
                "title": item.get("title"),
                "has_children": bool(item.get("hasChildren")),
                "depth": depth,
            })
            for entry in _file_entries(item):
                normalized = _normalize_file(item_id, entry)
                if normalized:
                    result["files"].append(normalized)

            if depth < MAX_DEPTH and (depth == 0 or item.get("hasChildren")):
                query = urllib.parse.urlencode({
                    "q": "",
                    "filter": f"parentId={item_id}",
                    "format": "json",
                    "max": 100,
                })
                children = _request_json(f"{BASE_URL}/items?{query}")
                for child in _child_items(children):
                    child_id = child.get("id") or child.get("itemId")
                    if child_id:
                        queue.append((str(child_id), depth + 1))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            result["errors"].append({
                "item_id": item_id,
                "error": f"{type(exc).__name__}: {exc}",
            })

    raster_candidates = [
        file for file in result["files"]
        if file["name"].lower().endswith((".tif", ".tiff"))
        and (file["size_bytes"] is None or file["size_bytes"] <= MAX_DOWNLOAD_BYTES)
    ]
    if raster_candidates:
        selected = min(
            raster_candidates,
            key=lambda file: file["size_bytes"] if file["size_bytes"] is not None else MAX_DOWNLOAD_BYTES,
        )
        result["selected_file"] = {
            "item_id": selected["item_id"],
            "name": selected["name"],
            "size_bytes_catalogue": selected["size_bytes"],
            "catalogue_url_host": urllib.parse.urlsplit(selected["url"]).hostname,
            "catalogue_url_path": urllib.parse.urlsplit(selected["url"]).path,
        }
        if _is_direct_file_url(selected["url"]):
            direct_path = OUT / selected["name"]
            direct = _download_bounded(selected, direct_path)
            result["direct_file_download"] = direct
            if direct.get("downloaded"):
                inspection = _inspect_tiff(direct_path)
                result["raster_inspection"] = inspection
                result["raw_sample_downloaded"] = bool(inspection.get("inspected"))
        else:
            result["direct_file_download"] = {
                "downloaded": False,
                "reason": "catalogue_url_is_a_manager_preview_route_not_a_direct_file_endpoint",
            }
        if not result["raw_sample_downloaded"]:
            archive_path = OUT / "item-files.zip"
            archive = _download_item_archive_bounded(ITEM_ID, result["files"], archive_path)
            result["item_archive_download"] = archive
            if archive.get("downloaded"):
                extracted = _extract_first_tiff(archive_path, OUT / "sample.tif")
                result["zip_tiff_extraction"] = extracted
                if extracted and extracted.get("extracted"):
                    inspection = _inspect_tiff(OUT / "sample.tif")
                    result["raster_inspection"] = inspection
                    result["raw_sample_downloaded"] = bool(inspection.get("inspected"))
                    result["sample_source"] = "smallest TIFF from official ScienceBase item-files ZIP"
    else:
        result["download"] = {
            "downloaded": False,
            "reason": "no_direct_geotiff_found_in_bounded_item_tree",
        }
    result["item_count"] = len(result["items"])
    result["file_count"] = len(result["files"])
    result["completed_at_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (OUT / "receipt.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    print(json.dumps(probe(), sort_keys=True))
