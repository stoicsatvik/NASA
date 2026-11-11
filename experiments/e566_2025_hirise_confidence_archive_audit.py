"""E566: bounded HTTP-range audit of the 2025 USGS Jezero HiRISE DTM archive.

The archive is 5.3 GB. This experiment reads only HTTP headers, the ZIP
central directory, local headers, and a 16-byte prefix from selected TIFF
members. It never downloads the archive or stores raster pixels.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

import requests

ARCHIVE_URL = (
    "https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/Mars/"
    "MSR_TRN_HiRISE_soc_003_USGS_release_aug2024/"
    "MSR_TRN_HiRISE_soc_003_USGS_release_aug2024_mosaics.zip"
)
PRODUCT_PAGE = (
    "https://astrogeology.usgs.gov/search/map/"
    "mars-sample-return-terrain-relative-navigation-hirise-dtm-mosaic"
)
DOI = "10.5066/P13CPYYU"
USER_AGENT = "Unified-Parallel-Foundry-E566/1.0"
MAX_REQUEST_BYTES = 16 * 1024 * 1024
MAX_TOTAL_RANGE_BYTES = 32 * 1024 * 1024
MAX_TIFF_MEMBERS = 24
TIFF_MAGICS = {b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"}


class RangeReadError(RuntimeError):
    def __init__(self, outcome: str, message: str):
        super().__init__(message)
        self.outcome = outcome


class HTTPRangeFile:
    """Small seekable file adapter backed only by exact HTTP byte ranges."""

    def __init__(self, session: requests.Session, url: str):
        self.session = session
        self.url = url
        self.position = 0
        self.closed = False
        self.transferred = 0
        self.ranges: list[dict] = []
        response = session.head(
            url,
            headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
            timeout=(15, 45),
            allow_redirects=False,
        )
        try:
            if response.status_code != 200:
                raise RangeReadError(
                    "ARCHIVE_HEAD_HTTP_" + str(response.status_code),
                    "Pinned archive HEAD did not return HTTP 200",
                )
            length = response.headers.get("Content-Length", "")
            if not length.isdigit() or int(length) <= 0:
                raise RangeReadError(
                    "ARCHIVE_SIZE_UNKNOWN",
                    "Pinned archive has no positive Content-Length",
                )
            self.size = int(length)
            self.accept_ranges = response.headers.get("Accept-Ranges", "")
            self.content_type = response.headers.get("Content-Type", "")
            self.etag = response.headers.get("ETag")
            self.last_modified = response.headers.get("Last-Modified")
        finally:
            response.close()

    def seek(self, offset: int, whence: int = 0) -> int:
        if self.closed:
            raise ValueError("I/O operation on closed range file")
        if whence == 0:
            target = offset
        elif whence == 1:
            target = self.position + offset
        elif whence == 2:
            target = self.size + offset
        else:
            raise ValueError("invalid whence")
        if target < 0 or target > self.size:
            raise ValueError("seek outside archive bounds")
        self.position = int(target)
        return self.position

    def tell(self) -> int:
        return self.position

    def readable(self) -> bool:
        return not self.closed

    def seekable(self) -> bool:
        return not self.closed

    def read(self, size: int = -1) -> bytes:
        if self.closed:
            raise ValueError("I/O operation on closed range file")
        if size is None or size < 0:
            size = self.size - self.position
        size = min(int(size), self.size - self.position)
        if size <= 0:
            return b""
        if size > MAX_REQUEST_BYTES:
            raise RangeReadError(
                "RANGE_REQUEST_TOO_LARGE",
                "A single requested range exceeds the frozen byte cap",
            )
        if self.transferred + size > MAX_TOTAL_RANGE_BYTES:
            raise RangeReadError(
                "RANGE_TRANSFER_CAP_EXCEEDED",
                "The cumulative range-read cap would be exceeded",
            )
        start = self.position
        end = start + size - 1
        response = self.session.get(
            self.url,
            headers={
                "User-Agent": USER_AGENT,
                "Accept-Encoding": "identity",
                "Range": "bytes=" + str(start) + "-" + str(end),
            },
            timeout=(15, 60),
            allow_redirects=False,
        )
        try:
            if response.status_code != 206:
                raise RangeReadError(
                    "RANGE_HTTP_" + str(response.status_code),
                    "Server did not honor the exact HTTP Range request",
                )
            content_range = response.headers.get("Content-Range", "")
            match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", content_range)
            if not match:
                raise RangeReadError(
                    "CONTENT_RANGE_MALFORMED",
                    "Content-Range is missing or malformed",
                )
            actual_start, actual_end, actual_total = map(int, match.groups())
            if (actual_start, actual_end, actual_total) != (start, end, self.size):
                raise RangeReadError(
                    "CONTENT_RANGE_MISMATCH",
                    "Content-Range does not match the requested archive interval",
                )
            payload = response.content
            if len(payload) != size:
                raise RangeReadError(
                    "RANGE_BYTE_COUNT_MISMATCH",
                    "Range body length differs from the requested interval",
                )
        finally:
            response.close()
        self.position += size
        self.transferred += size
        self.ranges.append({"start": start, "end": end, "bytes": size})
        return payload

    def readinto(self, buffer) -> int:
        payload = self.read(len(buffer))
        buffer[: len(payload)] = payload
        return len(payload)

    def close(self) -> None:
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.close()


def _role(name: str) -> str:
    lower = name.lower()
    if "confidence" in lower:
        return "confidence"
    if "dtm" in lower or "dem" in lower:
        return "dtm"
    if "ortho" in lower:
        return "orthoimage"
    return "other_tiff"


def inspect_archive(session: requests.Session, url: str = ARCHIVE_URL) -> dict:
    remote = HTTPRangeFile(session, url)
    result = {
        "archive_url": url,
        "archive_size_bytes": remote.size,
        "accept_ranges": remote.accept_ranges,
        "content_type": remote.content_type,
        "etag": remote.etag,
        "last_modified": remote.last_modified,
        "member_count": 0,
        "tiff_member_count": 0,
        "dtm_member_count": 0,
        "confidence_member_count": 0,
        "member_samples": [],
        "raw_raster_bytes_retained": False,
        "pixel_values_read": False,
    }
    try:
        with zipfile.ZipFile(remote, mode="r") as archive:
            infos = archive.infolist()
            result["member_count"] = len(infos)
            tiffs = [
                info for info in infos
                if info.filename.lower().endswith((".tif", ".tiff"))
            ]
            result["tiff_member_count"] = len(tiffs)
            selected = tiffs[:MAX_TIFF_MEMBERS]
            samples = []
            for info in selected:
                role = _role(info.filename)
                if role == "dtm":
                    result["dtm_member_count"] += 1
                elif role == "confidence":
                    result["confidence_member_count"] += 1
                prefix = b""
                prefix_error = None
                try:
                    with archive.open(info, "r") as member:
                        prefix = member.read(16)
                except Exception as exc:
                    prefix_error = type(exc).__name__ + ": " + str(exc)[:240]
                samples.append(
                    {
                        "name": info.filename,
                        "role": role,
                        "zip_compression_method": int(info.compress_type),
                        "compressed_size_bytes": int(info.compress_size),
                        "uncompressed_size_bytes": int(info.file_size),
                        "crc32": format(info.CRC, "08x"),
                        "header_prefix_bytes_read": len(prefix),
                        "header_magic_hex": prefix[:4].hex(),
                        "tiff_magic_valid": prefix[:4] in TIFF_MAGICS,
                        "prefix_error": prefix_error,
                        "random_access_inside_zip_member": (
                            "POSSIBLE_IF_TIFF_LAYOUT_SUPPORTS_RANGES"
                            if info.compress_type == zipfile.ZIP_STORED
                            else "NOT_WITHOUT_MEMBER_DECOMPRESSION"
                        ),
                    }
                )
            result["member_samples"] = samples
            result["range_requests"] = len(remote.ranges)
            result["range_bytes_transferred"] = remote.transferred
            result["range_transfer_cap_bytes"] = MAX_TOTAL_RANGE_BYTES
            if result["dtm_member_count"] and result["confidence_member_count"]:
                result["outcome"] = "ARCHIVE_INDEXED_WITH_DTM_AND_CONFIDENCE"
            elif result["dtm_member_count"]:
                result["outcome"] = "ARCHIVE_INDEXED_DTM_WITHOUT_CONFIDENCE"
            else:
                result["outcome"] = "ARCHIVE_INDEXED_EXPECTED_MEMBERS_NOT_FOUND"
    except RangeReadError as exc:
        result["outcome"] = exc.outcome
        result["error"] = {"kind": type(exc).__name__, "message": str(exc)}
    except (zipfile.BadZipFile, OSError, RuntimeError) as exc:
        result["outcome"] = "ZIP_PARSE_OR_MEMBER_READ_FAILED"
        result["error"] = {"kind": type(exc).__name__, "message": str(exc)[:500]}
    finally:
        result["range_requests"] = len(remote.ranges)
        result["range_bytes_transferred"] = remote.transferred
        remote.close()
    return result


def run() -> dict:
    receipt = {
        "experiment": "E566_2025_HIRISE_DTM_CONFIDENCE_ARCHIVE_RANGE_AUDIT",
        "date": "2026-11-12",
        "product_page": PRODUCT_PAGE,
        "doi": DOI,
        "published_product": (
            "Mars Sample Return Terrain Relative Navigation HiRISE DTM "
            "and Orthoimage Mosaics"
        ),
        "published_archive_size_description": "5.3 GB",
        "published_nominal_resolution_m_per_pixel": 1.0,
        "published_coverage_bbox_degrees": {
            "west": 77.057,
            "east": 77.380,
            "south": 18.135,
            "north": 18.588,
        },
        "published_quality": {
            "completed_stereo_pairs": 8,
            "planned_stereo_pairs": 10,
            "alignment_to_ctx_below_6m_at_percentile": 93,
            "alignment_to_ctx_below_10_2m_at_percentile": 99,
            "crater_rim_vertical_offset_exception": True,
        },
        "outcome": "NOT_RUN",
        "claim_state": {
            "2025_archive_range_access": "NOT YET MEASURED",
            "2025_dtm_member_presence": "NOT YET MEASURED",
            "confidence_member_presence": "NOT YET MEASURED",
            "2025_member_random_access": "NOT YET MEASURED",
            "replacement_of_2020_hirise_nodata": "NOT YET MEASURED",
            "independent_horizontal_registration": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "This is an archive-structure and bounded-access test, not a raster coverage or elevation comparison.",
            "The 2025 mosaic is aligned to the CTX reference; it is not an independent horizontal control network.",
            "The published 8/10 stereo-pair completion and crater-rim vertical-offset exception remain material limitations.",
            "A confidence member's presence does not establish that its semantics are a calibrated uncertainty measure.",
            "No full archive, raster pixels, point coordinates, credentials or raw member contents are retained.",
        ],
    }
    session = requests.Session()
    try:
        receipt.update(inspect_archive(session))
    except Exception as exc:
        receipt["outcome"] = "ERROR"
        receipt["error"] = {"kind": type(exc).__name__, "message": str(exc)[:500]}
    finally:
        session.close()
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    receipt = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        json.dumps(receipt, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "experiment": receipt["experiment"],
                "outcome": receipt["outcome"],
                "archive_size_bytes": receipt.get("archive_size_bytes"),
                "dtm_members": receipt.get("dtm_member_count"),
                "confidence_members": receipt.get("confidence_member_count"),
                "range_bytes": receipt.get("range_bytes_transferred"),
            },
            sort_keys=True,
        )
    )
    # Negative access results are valid research outcomes and must not be hidden.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
