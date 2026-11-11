"""E538: test ScienceBase's documented single-file ?name= download route.

The probe is anonymous, read-only, pinned to one DEM, size-bounded, and keeps
all downloaded bytes in a short-retention Actions artifact. No raw data is
committed and no physical units are inferred.
"""
from __future__ import annotations

import hashlib
import io
import json
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ITEM_ID = "662bccfad34ea70bd5f11f88"
DEM_NAME = "GFDF_Ripples_2023_04_18_DEM.tif"
EXPECTED_BYTES = 619_492
MAX_DOWNLOAD_BYTES = 5_000_000
TIMEOUT_SECONDS = 45
BASE_URL = "https://www.sciencebase.gov/catalog/file/get"
OUT = Path(".artifacts/e538")
USER_AGENT = "NASA-E538-ScienceBase-single-file-probe/1.0"
SCIENCEBASE_HOSTS = {"www.sciencebase.gov", "sciencebase.gov", "sciencebase.usgs.gov"}


def build_file_url(item_id: str = ITEM_ID, filename: str = DEM_NAME) -> str:
    if len(item_id) != 24 or any(ch not in "0123456789abcdef" for ch in item_id):
        raise ValueError("ScienceBase item ID must be a 24-character lowercase hex ID")
    if not filename or filename != Path(filename).name or "/" in filename or "\\" in filename:
        raise ValueError("file name must be a plain basename")
    query = urllib.parse.urlencode({"name": filename})
    return f"{BASE_URL}/{item_id}/?{query}"


def is_safe_request_url(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    query = urllib.parse.parse_qs(parsed.query, strict_parsing=True)
    return (
        parsed.scheme == "https"
        and parsed.hostname in SCIENCEBASE_HOSTS
        and parsed.path == f"/catalog/file/get/{ITEM_ID}/"
        and not parsed.username
        and not parsed.password
        and not parsed.fragment
        and query == {"name": [DEM_NAME]}
    )


def is_allowed_final_url(url: str) -> bool:
    parsed = urllib.parse.urlsplit(url)
    host = parsed.hostname or ""
    is_sciencebase = host in SCIENCEBASE_HOSTS
    is_s3 = (
        host == "s3.amazonaws.com"
        or host.endswith(".s3.amazonaws.com")
        or host == "s3.us-west-2.amazonaws.com"
        or host.endswith(".s3.us-west-2.amazonaws.com")
    )
    return parsed.scheme == "https" and (is_sciencebase or is_s3) and not parsed.username and not parsed.password


def has_tiff_magic(data: bytes) -> bool:
    return data[:4] in (b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+")


def has_zip_magic(data: bytes) -> bool:
    return data.startswith((b"PK\x03\x04", b"PK\x05\x06", b"PK\x07\x08"))


def extract_dem_payload(payload: bytes) -> tuple[bytes | None, dict]:
    if has_tiff_magic(payload):
        return payload, {"container": "raw_tiff", "member": None, "member_bytes": len(payload)}
    if not has_zip_magic(payload):
        return None, {"container": "unknown", "reason": "payload_magic_mismatch", "prefix_hex": payload[:16].hex()}
    try:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            candidates = [
                info for info in archive.infolist()
                if not info.is_dir() and Path(info.filename).name == DEM_NAME
            ]
            inventory = [
                {"member": info.filename, "size_bytes": info.file_size, "compressed_bytes": info.compress_size}
                for info in archive.infolist() if not info.is_dir()
            ]
            if len(candidates) != 1:
                return None, {"container": "zip", "reason": "expected_exactly_one_dem_member", "dem_matches": len(candidates), "members": inventory}
            selected = candidates[0]
            if selected.file_size <= 0:
                return None, {"container": "zip", "reason": "zero_byte_dem_member", "members": inventory}
            if selected.file_size > MAX_DOWNLOAD_BYTES:
                return None, {"container": "zip", "reason": "dem_member_exceeds_size_cap", "members": inventory}
            data = archive.read(selected)
            if not has_tiff_magic(data):
                return None, {"container": "zip", "reason": "dem_member_has_no_tiff_magic", "members": inventory}
            return data, {"container": "zip", "member": selected.filename, "member_bytes": len(data), "members": inventory}
    except zipfile.BadZipFile:
        return None, {"container": "zip", "reason": "invalid_zip_archive"}


def inspect_tiff(path: Path) -> dict:
    try:
        import tifffile
    except Exception as exc:
        return {"inspected": False, "reason": f"tifffile_unavailable: {type(exc).__name__}: {exc}"}
    try:
        with tifffile.TiffFile(path) as tif:
            page = tif.pages[0]
            wanted = (
                "ModelPixelScaleTag", "ModelTiepointTag", "ModelTransformationTag",
                "GeoKeyDirectoryTag", "GeoDoubleParamsTag", "GeoAsciiParamsTag",
                "GDAL_NODATA", "ImageDescription", "ResolutionUnit", "XResolution", "YResolution",
            )
            tags = {}
            for name in wanted:
                tag = page.tags.get(name)
                if tag is None:
                    continue
                value = tag.value
                if isinstance(value, bytes):
                    value = value.decode("utf-8", "replace")
                elif hasattr(value, "tolist"):
                    value = value.tolist()
                tags[name] = value
            return {
                "inspected": True,
                "page_count": len(tif.pages),
                "shape": list(page.shape),
                "dtype": str(page.dtype),
                "compression": str(page.compression),
                "geotiff_tags": tags,
                "vertical_units": "NOT ASSIGNED",
                "claim_boundary": "TIFF metadata inspection does not establish vertical datum, physical calibration, or Earth/Mars comparability.",
            }
    except Exception as exc:
        return {"inspected": False, "reason": f"tiff_read_failed: {type(exc).__name__}: {exc}"}


def run_probe(output_dir: Path = OUT) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    url = build_file_url()
    receipt = {
        "experiment": "E538",
        "source": {
            "item_id": ITEM_ID,
            "filename": DEM_NAME,
            "expected_catalogue_bytes": EXPECTED_BYTES,
            "endpoint": url,
            "method": "anonymous HTTPS single-file ?name= request",
            "method_reference": "https://github.com/esturdivant-usgs/science-base-automation",
            "max_download_bytes": MAX_DOWNLOAD_BYTES,
        },
        "outcome": "ERROR",
        "claim_boundary": "A valid Earth photogrammetry DEM may be inspected. This does not establish planetary analogue recovery, Earth/Mars physical comparability, or a novel analogue discovery.",
    }
    try:
        if not is_safe_request_url(url):
            raise ValueError("constructed URL failed the ScienceBase request allowlist")
        request = urllib.request.Request(
            url,
            headers={"User-Agent": USER_AGENT, "Accept": "image/tiff, image/geotiff, application/octet-stream, application/zip"},
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            final_url = response.geturl()
            if not is_allowed_final_url(final_url):
                raise ValueError("single-file request redirected outside the allowed ScienceBase/S3 HTTPS hosts")
            content_length = response.headers.get("Content-Length")
            if content_length:
                declared = int(content_length)
                if declared > MAX_DOWNLOAD_BYTES:
                    raise ValueError("single-file response exceeds the 5 MB safety cap")
            payload = response.read(MAX_DOWNLOAD_BYTES + 1)
            if len(payload) > MAX_DOWNLOAD_BYTES:
                raise ValueError("single-file stream exceeded the 5 MB safety cap")
            content_type = response.headers.get_content_type()
            status = response.status
        (output_dir / "response.bin").write_bytes(payload)
        receipt["download"] = {
            "http_status": status,
            "final_host": urllib.parse.urlsplit(final_url).hostname,
            "content_type": content_type,
            "content_length_header": content_length,
            "response_bytes": len(payload),
            "response_sha256": hashlib.sha256(payload).hexdigest(),
        }
        dem_bytes, unpack = extract_dem_payload(payload)
        receipt["payload"] = unpack
        receipt["download"]["catalogue_size_matches"] = bool(dem_bytes is not None and len(dem_bytes) == EXPECTED_BYTES)
        if dem_bytes is None:
            receipt["outcome"] = "SOURCE_PAYLOAD_NOT_A_VALID_DEM"
        elif len(dem_bytes) != EXPECTED_BYTES:
            receipt["outcome"] = "DEM_SIZE_MISMATCH"
            receipt["download"]["dem_bytes"] = len(dem_bytes)
        else:
            dem_path = output_dir / "dem.tif"
            dem_path.write_bytes(dem_bytes)
            receipt["download"]["dem_bytes"] = len(dem_bytes)
            receipt["download"]["dem_sha256"] = hashlib.sha256(dem_bytes).hexdigest()
            receipt["tiff"] = inspect_tiff(dem_path)
            receipt["outcome"] = "DEM_RETRIEVED" if receipt["tiff"].get("inspected") else "DEM_BYTES_RETRIEVED_METADATA_UNRESOLVED"
    except urllib.error.HTTPError as exc:
        receipt["outcome"] = "HTTP_ERROR"
        receipt["error"] = f"HTTP {exc.code}"
        receipt["http_status"] = exc.code
    except urllib.error.URLError as exc:
        receipt["outcome"] = "NETWORK_ERROR"
        receipt["error"] = f"{type(exc.reason).__name__}: {exc.reason}"
    except Exception as exc:
        receipt["outcome"] = "ERROR"
        receipt["error"] = f"{type(exc).__name__}: {exc}"
    (output_dir / "receipt.json").write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return receipt


if __name__ == "__main__":
    result = run_probe()
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["outcome"] in ("ERROR", "NETWORK_ERROR"):
        raise SystemExit(1)
