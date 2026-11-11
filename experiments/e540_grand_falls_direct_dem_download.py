"""E540: verify the exact public ScienceBase downloadUri for the Grand Falls DEM.

The URI is selected from the public item metadata by exact file name and
catalogue size. Redirects are restricted to official ScienceBase hosts and
Amazon S3; query values are never written to the receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ITEM_ID = "662bccfad34ea70bd5f11f88"
DEM_NAME = "GFDF_Ripples_2023_04_18_DEM.tif"
EXPECTED_BYTES = 619_492
SCIENCEBASE_URL = f"https://www.sciencebase.gov/catalog/item/{ITEM_ID}?format=json"
SCIENCEBASE_HOSTS = {"www.sciencebase.gov", "sciencebase.gov", "sciencebase.usgs.gov"}
MAX_DOWNLOAD_BYTES = 5_000_000
TIMEOUT = 45
USER_AGENT = "UnifiedParallelFoundry-E540-public-DEM-validation/1.0"


def _allowed_host(host: str | None) -> bool:
    host = (host or "").lower()
    return (
        host in SCIENCEBASE_HOSTS
        or host.endswith(".amazonaws.com")
    )


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if (
            parsed.scheme != "https"
            or not _allowed_host(parsed.hostname)
            or parsed.username
            or parsed.password
            or parsed.fragment
        ):
            raise urllib.error.HTTPError(
                newurl, code, "redirect target outside official ScienceBase/S3 allowlist",
                headers, fp,
            )
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _sanitized_url(url: str) -> dict:
    parsed = urllib.parse.urlsplit(url)
    return {
        "scheme": parsed.scheme,
        "host": parsed.hostname,
        "path": parsed.path,
        "query_key_names": sorted({
            key.lower()
            for key, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        }),
        "query_values_stored": False,
    }


def _valid_download_uri(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname == "sciencebase.usgs.gov"
        and parsed.path.startswith("/manager/download/")
        and not parsed.username
        and not parsed.password
        and not parsed.query
        and not parsed.fragment
    )


def _select_dem(item: dict) -> dict:
    files = item.get("files", [])
    matches = [
        entry for entry in files
        if isinstance(entry, dict)
        and entry.get("name") == DEM_NAME
        and int(entry.get("size") or -1) == EXPECTED_BYTES
    ]
    if len(matches) != 1:
        raise ValueError(
            f"expected exactly one DEM file with the pinned name and size; found {len(matches)}"
        )
    entry = matches[0]
    url = entry.get("downloadUri")
    if not isinstance(url, str) or not _valid_download_uri(url):
        raise ValueError("the exact DEM entry has no allowlisted public downloadUri")
    return {
        "name": entry["name"],
        "catalogue_size_bytes": int(entry["size"]),
        "download_uri": url,
        "download_uri_source_field": "files[].downloadUri",
    }


def _fetch_item_metadata() -> tuple[dict, dict]:
    request = urllib.request.Request(
        SCIENCEBASE_URL,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    opener = urllib.request.build_opener(SafeRedirectHandler())
    with opener.open(request, timeout=TIMEOUT) as response:
        final = urllib.parse.urlsplit(response.geturl())
        if response.status != 200 or final.scheme != "https" or not _allowed_host(final.hostname):
            raise RuntimeError("ScienceBase item metadata request failed its host/status gate")
        raw = response.read(5 * 1024 * 1024 + 1)
        if len(raw) > 5 * 1024 * 1024:
            raise ValueError("ScienceBase item metadata exceeds 5 MiB")
    return json.loads(raw.decode("utf-8")), {
        "http_status": 200,
        "bytes": len(raw),
        "sha256": hashlib.sha256(raw).hexdigest(),
        "final_url": _sanitized_url(response.geturl()),
    }


def _download_dem(url: str, destination: Path) -> dict:
    if not _valid_download_uri(url):
        raise ValueError("download URI is not the exact allowlisted public metadata field")
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/octet-stream, image/tiff, image/geotiff",
        },
    )
    opener = urllib.request.build_opener(SafeRedirectHandler())
    try:
        with opener.open(request, timeout=TIMEOUT) as response:
            final_url = response.geturl()
            final = urllib.parse.urlsplit(final_url)
            if response.status != 200 or final.scheme != "https" or not _allowed_host(final.hostname):
                raise RuntimeError("download response failed the status/redirect host gate")
            content_length = response.headers.get("Content-Length")
            declared_length = int(content_length) if content_length else None
            if declared_length is not None and declared_length > MAX_DOWNLOAD_BYTES:
                raise ValueError("download exceeds the 5 MB cap")
            payload = response.read(MAX_DOWNLOAD_BYTES + 1)
            if len(payload) > MAX_DOWNLOAD_BYTES:
                raise ValueError("streamed download exceeds the 5 MB cap")
            content_type = response.headers.get_content_type()
    except urllib.error.HTTPError as error:
        return {
            "downloaded": False,
            "http_status": error.code,
            "error": str(error.reason),
            "final_url": _sanitized_url(error.geturl()),
        }

    tiff_magic = payload[:4] in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")
    result = {
        "downloaded": False,
        "http_status": 200,
        "content_type": content_type,
        "declared_content_length": declared_length,
        "received_bytes": len(payload),
        "expected_catalogue_bytes": EXPECTED_BYTES,
        "size_matches_catalogue": len(payload) == EXPECTED_BYTES,
        "tiff_magic": tiff_magic,
        "first_eight_bytes_hex": payload[:8].hex(),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "final_url": _sanitized_url(final_url),
    }
    if not tiff_magic or len(payload) != EXPECTED_BYTES:
        return result

    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(payload)
    try:
        import numpy as np
        import tifffile
        with tifffile.TiffFile(destination) as tif:
            page = tif.pages[0]
            wanted = (
                "ModelPixelScaleTag", "ModelTiepointTag", "ModelTransformationTag",
                "GeoKeyDirectoryTag", "GeoDoubleParamsTag", "GeoAsciiParamsTag",
                "GDAL_NODATA", "ImageDescription", "ResolutionUnit", "XResolution",
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
            array = np.asarray(page.asarray()).astype("float64", copy=False)
            finite = np.isfinite(array)
            nodata = tags.get("GDAL_NODATA")
            if nodata is not None:
                try:
                    finite &= array != float(str(nodata).strip().strip("\x00"))
                except (TypeError, ValueError):
                    pass
            valid = array[finite]
            stats = None
            if valid.size:
                stats = {
                    "valid_pixel_count": int(valid.size),
                    "min_unit_unassigned": float(valid.min()),
                    "max_unit_unassigned": float(valid.max()),
                    "mean_unit_unassigned": float(valid.mean()),
                    "std_population_unit_unassigned": float(valid.std()),
                }
            result["tiff_inspection"] = {
                "inspected": True,
                "page_count": len(tif.pages),
                "shape": list(page.shape),
                "dtype": str(page.dtype),
                "compression": str(page.compression),
                "geotiff_tags": tags,
                "pixel_statistics_unit_unassigned": stats,
            }
            result["downloaded"] = True
    except Exception as exc:
        destination.unlink(missing_ok=True)
        result["tiff_inspection"] = {
            "inspected": False,
            "reason": f"{type(exc).__name__}: {exc}",
        }
    return result


def run(out_dir: Path) -> dict:
    item, metadata_receipt = _fetch_item_metadata()
    selected = _select_dem(item)
    download = _download_dem(selected["download_uri"], out_dir / DEM_NAME)
    selected.pop("download_uri")
    return {
        "experiment": "E540",
        "item_id": ITEM_ID,
        "source_item_url": _sanitized_url(SCIENCEBASE_URL),
        "metadata_receipt": metadata_receipt,
        "selected_file": selected,
        "download": download,
        "raw_sample_downloaded": bool(download.get("downloaded")),
        "raw_file_committed": False,
        "credentials_or_cookies_used": False,
        "redirects_restricted_to_sciencebase_and_s3": True,
        "max_download_bytes": MAX_DOWNLOAD_BYTES,
        "interpretation": (
            "A successful TIFF read establishes acquisition and file-level metadata only. "
            "Do not assign vertical units or infer Earth/Mars physical comparability unless "
            "the GeoTIFF tags and source documentation establish them."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", type=Path, default=Path(".artifacts/e540"))
    args = parser.parse_args()
    receipt = run(args.out_dir)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "experiment": receipt["experiment"],
        "raw_sample_downloaded": receipt["raw_sample_downloaded"],
        "download": receipt["download"],
    }, sort_keys=True))


if __name__ == "__main__":
    main()
