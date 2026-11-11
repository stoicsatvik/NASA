"""E547: bounded Range-only inspection of a direct controlled Jezero HiRISE GeoTIFF.

This probes the 2020 Mars 2020 TRN product, not the separate 2025 MSR ZIP
examined by E546. It never downloads the full raster or decodes pixel values.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

import requests
import tifffile

SOURCE_URL = (
    "https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/"
    "HiRISE/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif"
)
SOURCE_INDEX = "https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/index.html"
SOURCE_PAGE = "https://astrogeology.usgs.gov/search/map/Mars/Mars2020/JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40"
SOURCE_DOI = "10.5066/P9QJDP48"
ALLOWED_HOST = "asc-pds-services.s3.us-west-2.amazonaws.com"
ALLOWED_PATH = (
    "/mosaic/mars2020_trn/HiRISE/"
    "JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif"
)
MAX_TOTAL_TRANSFER_BYTES = 1_000_000
MAX_SEGMENT_BYTES = 512_000
USER_AGENT = "Unified-Parallel-Foundry-E547/1.0"


class ProbeError(RuntimeError):
    def __init__(self, outcome: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.outcome = outcome
        self.details = details or {}


def validate_url(url: str = SOURCE_URL) -> None:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ALLOWED_HOST
        or parsed.port not in (None, 443)
        or parsed.username
        or parsed.password
        or parsed.path != ALLOWED_PATH
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("URL is outside the exact public USGS HiRISE DTM allowlist")


def parse_content_range(value: str | None) -> tuple[int, int, int]:
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", value or "")
    if not match:
        raise ProbeError("INVALID_CONTENT_RANGE", "Range response lacks an exact byte Content-Range")
    start, end, total = (int(part) for part in match.groups())
    if start > end or total <= end:
        raise ProbeError("INVALID_CONTENT_RANGE", "Content-Range bounds are inconsistent")
    return start, end, total


class RangeReader:
    """Minimal seekable file object backed only by bounded HTTP byte ranges."""

    def __init__(self, session, url: str, size: int, max_bytes: int = MAX_TOTAL_TRANSFER_BYTES):
        self.session = session
        self.url = url
        self.size = size
        self.max_bytes = max_bytes
        self.position = 0
        self.transferred = 0
        self.ranges: list[dict] = []
        self.closed = False

    def tell(self) -> int:
        return self.position

    def seek(self, offset: int, whence: int = 0) -> int:
        if whence == 0:
            target = offset
        elif whence == 1:
            target = self.position + offset
        elif whence == 2:
            target = self.size + offset
        else:
            raise ValueError("invalid whence")
        if target < 0 or target > self.size:
            raise ValueError("seek outside pinned object")
        self.position = target
        return target

    def readable(self) -> bool:
        return True

    def seekable(self) -> bool:
        return True

    def read(self, amount: int = -1) -> bytes:
        if self.closed:
            raise ValueError("I/O operation on closed range reader")
        if amount is None or amount < 0:
            amount = self.size - self.position
        if amount == 0 or self.position >= self.size:
            return b""
        amount = min(amount, self.size - self.position)
        if self.transferred + amount > self.max_bytes:
            raise ProbeError(
                "TRANSFER_BUDGET_EXCEEDED",
                "TIFF metadata/data reads would exceed the 1 MB transfer budget",
                {"requested_bytes": amount, "transferred_bytes": self.transferred, "cap_bytes": self.max_bytes},
            )
        start = self.position
        end = start + amount - 1
        response = self.session.get(
            self.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "identity",
                "Range": f"bytes={start}-{end}",
            },
            timeout=(15, 45),
            allow_redirects=False,
            stream=True,
        )
        try:
            status = int(response.status_code)
            if status in (301, 302, 303, 307, 308):
                raise ProbeError("RANGE_REDIRECT_NOT_ALLOWED", "Direct TIFF Range request redirected")
            if status == 200:
                raise ProbeError(
                    "RANGE_IGNORED",
                    "Server ignored Range; response body was not consumed",
                    {"full_download_refused": True},
                )
            if status in (403, 404, 410):
                raise ProbeError(f"HTTP_{status}", "Pinned public TIFF returned an HTTP error", {"http_status": status})
            if status != 206:
                raise ProbeError(f"HTTP_{status}", "Direct TIFF did not return HTTP 206")
            encoding = response.headers.get("Content-Encoding", "identity").lower()
            if encoding not in ("", "identity"):
                raise ProbeError("ENCODED_RANGE", "Range response used unexpected content encoding")
            got = parse_content_range(response.headers.get("Content-Range"))
            if got != (start, end, self.size):
                raise ProbeError(
                    "CONTENT_RANGE_MISMATCH",
                    "Content-Range differs from the requested interval or HEAD size",
                    {"expected": [start, end, self.size], "received": list(got)},
                )
            declared = response.headers.get("Content-Length")
            if declared and int(declared) != amount:
                raise ProbeError("CONTENT_LENGTH_MISMATCH", "Content-Length differs from requested range")
            body = response.raw.read(amount + 1, decode_content=False)
            if len(body) != amount:
                raise ProbeError("BYTE_COUNT_MISMATCH", "Range body length differs from requested bytes")
        finally:
            response.close()
        self.position += amount
        self.transferred += len(body)
        self.ranges.append({
            "start": start,
            "end": end,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
        })
        return body

    def readinto(self, buffer) -> int:
        data = self.read(len(buffer))
        buffer[:len(data)] = data
        return len(data)

    def close(self) -> None:
        self.closed = True


def _tag_value(page, name: str):
    tag = page.tags.get(name)
    if tag is None:
        return None
    value = tag.value
    if isinstance(value, tuple):
        return list(value[:8])
    if isinstance(value, (int, float, str)):
        return value
    return str(value)[:160]


def probe(session=None) -> dict:
    validate_url()
    session = session or requests.Session()
    head = session.head(
        SOURCE_URL,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        timeout=(15, 45),
        allow_redirects=False,
    )
    try:
        status = int(head.status_code)
        if status in (301, 302, 303, 307, 308):
            raise ProbeError("HEAD_REDIRECT_NOT_ALLOWED", "Pinned TIFF HEAD redirected")
        if status in (403, 404, 410):
            raise ProbeError(f"HTTP_{status}", "Pinned public TIFF HEAD returned an HTTP error", {"http_status": status})
        if status != 200:
            raise ProbeError(f"HTTP_{status}", "Pinned TIFF HEAD did not return HTTP 200")
        length = head.headers.get("Content-Length", "")
        if not length.isdigit() or int(length) <= 0:
            raise ProbeError("OBJECT_SIZE_UNKNOWN", "HEAD lacks a positive numeric Content-Length")
        object_size = int(length)
        accept_ranges = head.headers.get("Accept-Ranges")
        content_type = head.headers.get("Content-Type")
    finally:
        head.close()

    reader = RangeReader(session, SOURCE_URL, object_size)
    with tifffile.TiffFile(reader) as tiff:
        if not tiff.pages:
            raise ProbeError("TIFF_HAS_NO_PAGES", "TIFF contains no image pages")
        page = tiff.pages[0]
        offsets = tuple(int(x) for x in page.dataoffsets)
        bytecounts = tuple(int(x) for x in page.databytecounts)
        if len(offsets) != len(bytecounts) or not offsets:
            raise ProbeError("TIFF_SEGMENT_TABLE_INVALID", "TIFF segment offset/count arrays are empty or misaligned")
        kind = "tile" if page.is_tiled else "strip"
        candidate = next(
            (
                (offset, count, index)
                for index, (offset, count) in enumerate(zip(offsets, bytecounts))
                if 0 < count <= MAX_SEGMENT_BYTES and 0 <= offset < object_size and offset + count <= object_size
            ),
            None,
        )
        tiff_summary = {
            "page_count": len(tiff.pages),
            "width": int(page.imagewidth),
            "height": int(page.imagelength),
            "dtype": str(page.dtype),
            "bits_per_sample": list(page.bitspersample) if isinstance(page.bitspersample, tuple) else int(page.bitspersample),
            "samples_per_pixel": int(page.samplesperpixel),
            "compression": str(page.compression),
            "is_tiled": bool(page.is_tiled),
            "tile_width": int(page.tilewidth) if page.is_tiled else None,
            "tile_length": int(page.tilelength) if page.is_tiled else None,
            "rows_per_strip": int(page.rowsperstrip) if not page.is_tiled else None,
            "segment_count": len(offsets),
            "model_pixel_scale_tag": _tag_value(page, "ModelPixelScaleTag"),
            "model_tiepoint_tag": _tag_value(page, "ModelTiepointTag"),
            "geokey_directory_present": page.tags.get("GeoKeyDirectoryTag") is not None,
        }
        if candidate is None:
            outcome = "DIRECT_TIFF_METADATA_RANGE_SUPPORTED_NO_SMALL_SEGMENT"
            sample = None
        else:
            offset, count, index = candidate
            reader.seek(offset)
            payload = reader.read(count)
            sample = {
                "segment_kind": kind,
                "segment_index": index,
                "offset": offset,
                "compressed_bytes": count,
                "bytes_read": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
                "prefix_hex": payload[:16].hex(),
                "decoded_pixel_values_read": False,
            }
            outcome = "DIRECT_TIFF_SEGMENT_RANGE_READ"
    return {
        "experiment": "E547",
        "source": {
            "publisher": "USGS Astrogeology Science Center",
            "product": "Mars 2020 Terrain Relative Navigation HiRISE DTM mosaic",
            "doi": SOURCE_DOI,
            "product_page": SOURCE_PAGE,
            "directory_index": SOURCE_INDEX,
            "direct_object": SOURCE_URL,
            "is_2025_msr_mosaic": False,
        },
        "transport": {
            "http_status": status,
            "content_type": content_type,
            "object_size_bytes": object_size,
            "accept_ranges": accept_ranges,
            "range_count": len(reader.ranges),
            "transferred_bytes": reader.transferred,
            "transfer_cap_bytes": MAX_TOTAL_TRANSFER_BYTES,
            "ranges": reader.ranges,
        },
        "tiff": tiff_summary,
        "sample": sample,
        "outcome": outcome,
        "claim_state": {
            "direct_controlled_hirise_product_identified": "SUPPORTED_BY_SOURCE_CATALOGUE",
            "bounded_tiff_metadata_access": "SUPPORTED",
            "bounded_raster_segment_access": "SUPPORTED" if sample else "NOT YET MEASURED",
            "pixel_values_decoded": False,
            "2025_msr_mosaic_access": "NOT SUPPORTED THROUGH E546 ZIP MEMBER LAYOUT",
            "CTX_HiRISE_registration": "NOT YET MEASURED",
            "common_valid_pixel_support": "NOT YET ESTABLISHED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = probe()
    except ProbeError as exc:
        result = {
            "experiment": "E547",
            "outcome": exc.outcome,
            "message": str(exc),
            "details": exc.details,
            "claim_state": {
                "bounded_tiff_metadata_access": "NOT YET MEASURED",
                "bounded_raster_segment_access": "NOT YET MEASURED",
                "pixel_values_decoded": False,
                "CTX_HiRISE_registration": "NOT YET MEASURED",
                "common_valid_pixel_support": "NOT YET ESTABLISHED",
                "cross_body_similarity": "NOT YET PROVEN",
            },
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["outcome"] in {
        "DIRECT_TIFF_SEGMENT_RANGE_READ",
        "DIRECT_TIFF_METADATA_RANGE_SUPPORTED_NO_SMALL_SEGMENT",
        "RANGE_IGNORED",
        "RANGE_REDIRECT_NOT_ALLOWED",
        "HEAD_REDIRECT_NOT_ALLOWED",
        "HTTP_403",
        "HTTP_404",
        "HTTP_410",
    }:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
