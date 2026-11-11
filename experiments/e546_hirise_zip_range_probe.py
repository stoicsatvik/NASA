"""E546: bounded HTTP-range inspection of the official 2025 HiRISE mosaic ZIP.

This experiment reads only the ZIP tail, central directory, one local header and
four bytes at the selected member offset. It never downloads or extracts the
multi-gigabyte archive or a raster.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import struct
from pathlib import Path
from urllib.parse import urlsplit

import requests

ARCHIVE_URL = (
    "https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/Mars/"
    "MSR_TRN_HiRISE_soc_003_USGS_release_aug2024/"
    "MSR_TRN_HiRISE_soc_003_USGS_release_aug2024_mosaics.zip"
)
ALLOWED_HOST = "asc-pds-services.s3.us-west-2.amazonaws.com"
ALLOWED_PATH = (
    "/mosaic/Mars/MSR_TRN_HiRISE_soc_003_USGS_release_aug2024/"
    "MSR_TRN_HiRISE_soc_003_USGS_release_aug2024_mosaics.zip"
)
MAX_TAIL_BYTES = 65_557
MAX_CENTRAL_DIRECTORY_BYTES = 8 * 1024 * 1024
MAX_LOCAL_HEADER_BYTES = 65_536
MAX_TOTAL_TRANSFER_BYTES = 8_520_000
USER_AGENT = "Unified-Parallel-Foundry-E546/1.0"
TIFF_MAGICS = {b"II*\x00", b"MM\x00*", b"II+\x00", b"MM\x00+"}


class ProbeError(RuntimeError):
    def __init__(self, outcome: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.outcome = outcome
        self.details = details or {}


def validate_url(url: str = ARCHIVE_URL) -> None:
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
        raise ValueError("URL is outside the exact public USGS HiRISE archive allowlist")


def _content_range(value: str | None) -> tuple[int, int, int]:
    match = re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)", value or "")
    if not match:
        raise ProbeError("INVALID_CONTENT_RANGE", "Range response lacks an exact byte Content-Range")
    start, end, total = (int(part) for part in match.groups())
    if start > end or total <= end:
        raise ProbeError("INVALID_CONTENT_RANGE", "Content-Range bounds are inconsistent")
    return start, end, total


def fetch_exact_range(session, url: str, start: int, end: int, total: int) -> tuple[bytes, dict]:
    validate_url(url)
    expected = end - start + 1
    if start < 0 or expected <= 0 or expected > MAX_CENTRAL_DIRECTORY_BYTES:
        raise ValueError("invalid or over-limit byte range")
    response = session.get(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/octet-stream",
            "Accept-Encoding": "identity",
            "Range": f"bytes={start}-{end}",
        },
        timeout=(15, 60),
        allow_redirects=False,
        stream=True,
    )
    try:
        status = int(response.status_code)
        if 300 <= status < 400:
            raise ProbeError(
                "REDIRECT_NOT_ALLOWED",
                "The pinned S3 archive redirected; no redirect target was followed",
                {"http_status": status},
            )
        if status == 200:
            raise ProbeError(
                "RANGE_IGNORED",
                "The server ignored the bounded Range request; full archive transfer was refused",
                {"http_status": status, "full_download_refused": True},
            )
        if status in (403, 404, 410):
            raise ProbeError(
                f"HTTP_{status}",
                "The pinned public archive returned an HTTP error",
                {"http_status": status},
            )
        if status != 206:
            raise ProbeError(
                f"HTTP_{status}",
                "The archive did not return HTTP 206 for the exact byte range",
                {"http_status": status},
            )
        encoding = response.headers.get("Content-Encoding", "identity").lower()
        if encoding not in ("", "identity"):
            raise ProbeError("ENCODED_RANGE", "Range response used unexpected content encoding")
        got = _content_range(response.headers.get("Content-Range"))
        if got != (start, end, total):
            raise ProbeError(
                "CONTENT_RANGE_MISMATCH",
                "Content-Range did not match the requested offsets and HEAD size",
                {"expected": [start, end, total], "received": list(got)},
            )
        declared = response.headers.get("Content-Length")
        if declared and int(declared) != expected:
            raise ProbeError("CONTENT_LENGTH_MISMATCH", "Content-Length differs from the requested range")
        body = response.content
        if len(body) != expected:
            raise ProbeError("BYTE_COUNT_MISMATCH", "Returned byte count differs from the requested range")
        return body, {
            "start": start,
            "end": end,
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "http_status": status,
        }
    finally:
        response.close()


def parse_eocd(tail: bytes, tail_start: int, archive_size: int) -> dict:
    signature = b"PK\x05\x06"
    pos = tail.rfind(signature)
    if pos < 0 or pos + 22 > len(tail):
        raise ProbeError("EOCD_NOT_FOUND", "ZIP end-of-central-directory record was not found in bounded tail")
    fields = struct.unpack_from("<4s4H2LH", tail, pos)
    _, disk, cd_disk, entries_disk, entries_total, cd_size, cd_offset, comment_len = fields
    if pos + 22 + comment_len > len(tail):
        raise ProbeError("TRUNCATED_EOCD", "ZIP end record comment exceeds the bounded tail")
    if disk != 0 or cd_disk != 0 or entries_disk != entries_total:
        raise ProbeError("MULTI_DISK_ZIP", "Multi-disk ZIP archives are not admitted")
    result = {
        "entries_total": entries_total,
        "central_directory_size": cd_size,
        "central_directory_offset": cd_offset,
        "zip64": False,
        "eocd_absolute_offset": tail_start + pos,
    }
    if entries_total == 0xFFFF or cd_size == 0xFFFFFFFF or cd_offset == 0xFFFFFFFF:
        locator_pos = pos - 20
        if locator_pos < 0 or tail[locator_pos:locator_pos + 4] != b"PK\x06\x07":
            raise ProbeError("ZIP64_LOCATOR_MISSING", "ZIP64 sentinel fields lack a locator")
        _, zip64_disk, zip64_offset, disk_count = struct.unpack_from("<4sIQI", tail, locator_pos)
        if zip64_disk != 0 or disk_count != 1:
            raise ProbeError("MULTI_DISK_ZIP64", "Multi-disk ZIP64 archives are not admitted")
        result.update({"zip64": True, "zip64_eocd_offset": zip64_offset})
    if result["central_directory_offset"] + result["central_directory_size"] > archive_size:
        raise ProbeError("CENTRAL_DIRECTORY_OUT_OF_BOUNDS", "Central directory exceeds archive size")
    return result


def parse_zip64_eocd(data: bytes) -> dict:
    if len(data) < 56 or data[:4] != b"PK\x06\x06":
        raise ProbeError("ZIP64_EOCD_INVALID", "ZIP64 end record signature or length is invalid")
    _, record_size, _made, _needed, disk, cd_disk, entries_disk, entries_total, cd_size, cd_offset = (
        struct.unpack_from("<4sQ2H2I4Q", data, 0)
    )
    if record_size < 44 or disk != 0 or cd_disk != 0 or entries_disk != entries_total:
        raise ProbeError("ZIP64_EOCD_INVALID", "ZIP64 end record fields are inconsistent")
    return {
        "entries_total": entries_total,
        "central_directory_size": cd_size,
        "central_directory_offset": cd_offset,
    }


def _zip64_values(extra: bytes, need_uncompressed: bool, need_compressed: bool, need_offset: bool):
    pos = 0
    payload = None
    while pos + 4 <= len(extra):
        tag, size = struct.unpack_from("<HH", extra, pos)
        pos += 4
        value = extra[pos:pos + size]
        if len(value) != size:
            raise ProbeError("TRUNCATED_EXTRA_FIELD", "ZIP extra field is truncated")
        if tag == 0x0001:
            payload = value
            break
        pos += size
    if payload is None:
        raise ProbeError("ZIP64_EXTRA_MISSING", "ZIP64 sentinel lacks its ZIP64 extra field")
    cursor = 0
    values = []
    for needed in (need_uncompressed, need_compressed, need_offset):
        if needed:
            if cursor + 8 > len(payload):
                raise ProbeError("ZIP64_EXTRA_TRUNCATED", "ZIP64 extra field lacks a required 64-bit value")
            values.append(struct.unpack_from("<Q", payload, cursor)[0])
            cursor += 8
        else:
            values.append(None)
    return values


def parse_central_directory(data: bytes, expected_entries: int) -> list[dict]:
    rows = []
    pos = 0
    for _ in range(expected_entries):
        if pos + 46 > len(data) or data[pos:pos + 4] != b"PK\x01\x02":
            raise ProbeError("CENTRAL_DIRECTORY_INVALID", "Central-directory entry signature is invalid")
        fields = struct.unpack_from("<4s6H3I5H2I", data, pos)
        (
            _sig, _made, _needed, flags, method, _time, _date, crc,
            compressed, uncompressed, name_len, extra_len, comment_len,
            disk_start, _internal, _external, local_offset
        ) = fields
        start = pos + 46
        name_bytes = data[start:start + name_len]
        extra = data[start + name_len:start + name_len + extra_len]
        comment = data[start + name_len + extra_len:start + name_len + extra_len + comment_len]
        if len(name_bytes) != name_len or len(extra) != extra_len or len(comment) != comment_len:
            raise ProbeError("CENTRAL_DIRECTORY_TRUNCATED", "Central-directory variable fields are truncated")
        encoding = "utf-8" if flags & (1 << 11) else "cp437"
        try:
            name = name_bytes.decode(encoding)
        except UnicodeDecodeError as exc:
            raise ProbeError("FILENAME_ENCODING_INVALID", "ZIP member filename is not decodable") from exc
        if name.startswith(("/", "\\")) or ".." in Path(name).parts:
            raise ProbeError("UNSAFE_MEMBER_PATH", "Archive contains an absolute or traversal member path")
        if disk_start != 0:
            raise ProbeError("MULTI_DISK_MEMBER", "Member references another ZIP disk")
        if compressed == 0xFFFFFFFF or uncompressed == 0xFFFFFFFF or local_offset == 0xFFFFFFFF:
            z_uncompressed, z_compressed, z_offset = _zip64_values(
                extra,
                uncompressed == 0xFFFFFFFF,
                compressed == 0xFFFFFFFF,
                local_offset == 0xFFFFFFFF,
            )
            if z_uncompressed is not None:
                uncompressed = z_uncompressed
            if z_compressed is not None:
                compressed = z_compressed
            if z_offset is not None:
                local_offset = z_offset
        rows.append({
            "name": name,
            "flags": flags,
            "compression_method": method,
            "crc32": f"{crc:08x}",
            "compressed_size": compressed,
            "uncompressed_size": uncompressed,
            "local_header_offset": local_offset,
            "encrypted": bool(flags & 1),
        })
        pos = start + name_len + extra_len + comment_len
    if pos > len(data):
        raise ProbeError("CENTRAL_DIRECTORY_OVERFLOW", "Parsed entries exceed central-directory bytes")
    return rows


def parse_local_header(data: bytes, expected_name: str, expected_method: int) -> dict:
    if len(data) < 30 or data[:4] != b"PK\x03\x04":
        raise ProbeError("LOCAL_HEADER_INVALID", "ZIP local-file header signature is invalid")
    fields = struct.unpack_from("<4s5H3I2H", data, 0)
    _, _version, flags, method, _time, _date, _crc, _csize, _usize, name_len, extra_len = fields
    if len(data) != 30 + name_len + extra_len:
        raise ProbeError("LOCAL_HEADER_LENGTH_MISMATCH", "Local-file header range has an unexpected length")
    encoding = "utf-8" if flags & (1 << 11) else "cp437"
    name = data[30:30 + name_len].decode(encoding)
    if name != expected_name or method != expected_method:
        raise ProbeError("LOCAL_CENTRAL_HEADER_MISMATCH", "Local and central ZIP headers disagree")
    return {
        "flags": flags,
        "compression_method": method,
        "header_bytes": len(data),
        "data_offset_delta": len(data),
        "encrypted": bool(flags & 1),
    }


def classify_tiff_members(rows: list[dict]) -> list[dict]:
    candidates = []
    for row in rows:
        lower = row["name"].lower()
        if lower.endswith((".tif", ".tiff")) and ("dtm" in lower or "dem" in lower):
            if not any(token in lower for token in ("ortho", "confidence", "hillshade")):
                candidates.append(row)
    return candidates


def probe(session=None) -> dict:
    validate_url()
    session = session or requests.Session()
    head = session.head(
        ARCHIVE_URL,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        timeout=(15, 45),
        allow_redirects=False,
    )
    status = int(head.status_code)
    if status in (301, 302, 303, 307, 308):
        raise ProbeError("HEAD_REDIRECT_NOT_ALLOWED", "Pinned S3 HEAD redirected; no redirect followed", {"http_status": status})
    if status in (403, 404, 410):
        raise ProbeError(f"HTTP_{status}", "Pinned public archive HEAD returned an HTTP error", {"http_status": status})
    if status != 200:
        raise ProbeError(f"HTTP_{status}", "Pinned archive HEAD did not return HTTP 200", {"http_status": status})
    size_header = head.headers.get("Content-Length")
    if not size_header or not size_header.isdigit():
        raise ProbeError("ARCHIVE_SIZE_UNKNOWN", "HEAD response lacks a numeric Content-Length")
    archive_size = int(size_header)
    if archive_size <= 0:
        raise ProbeError("ARCHIVE_SIZE_INVALID", "Archive size must be positive")
    tail_start = max(0, archive_size - MAX_TAIL_BYTES)
    tail, tail_receipt = fetch_exact_range(session, ARCHIVE_URL, tail_start, archive_size - 1, archive_size)
    eocd = parse_eocd(tail, tail_start, archive_size)
    cd_offset = eocd["central_directory_offset"]
    cd_size = eocd["central_directory_size"]
    if cd_size > MAX_CENTRAL_DIRECTORY_BYTES:
        raise ProbeError(
            "CENTRAL_DIRECTORY_OVER_LIMIT",
            "ZIP central directory exceeds the 8 MiB inspection cap",
            {"central_directory_bytes": cd_size, "cap": MAX_CENTRAL_DIRECTORY_BYTES},
        )
    if eocd["zip64"]:
        zip64_offset = eocd["zip64_eocd_offset"]
        zip64_data, zip64_receipt = fetch_exact_range(session, ARCHIVE_URL, zip64_offset, zip64_offset + 55, archive_size)
        zip64 = parse_zip64_eocd(zip64_data)
        eocd.update(zip64)
        tail_receipt = {"tail": tail_receipt, "zip64_eocd": zip64_receipt}
        cd_offset = zip64["central_directory_offset"]
        cd_size = zip64["central_directory_size"]
    if cd_size > MAX_CENTRAL_DIRECTORY_BYTES or cd_offset + cd_size > archive_size:
        raise ProbeError("CENTRAL_DIRECTORY_OUT_OF_BOUNDS", "ZIP64 central directory is outside the bounded archive")
    central, central_receipt = fetch_exact_range(session, ARCHIVE_URL, cd_offset, cd_offset + cd_size - 1, archive_size)
    rows = parse_central_directory(central, eocd["entries_total"])
    names = [row["name"] for row in rows]
    if len(names) != len(set(names)):
        raise ProbeError("DUPLICATE_MEMBER_NAMES", "Archive contains duplicate member names")
    candidates = classify_tiff_members(rows)
    if not candidates:
        outcome = "NO_DTM_TIFF_MEMBER_FOUND"
        selected = None
    elif len(candidates) != 1:
        outcome = "AMBIGUOUS_DTM_TIFF_MEMBERS"
        selected = None
    else:
        selected = candidates[0]
        outcome = "DTM_MEMBER_IDENTIFIED"
    result = {
        "archive": {
            "host": ALLOWED_HOST,
            "path": ALLOWED_PATH,
            "size_bytes": archive_size,
            "head_http_status": status,
            "accept_ranges_header": head.headers.get("Accept-Ranges"),
            "zip64": eocd["zip64"],
            "entry_count": eocd["entries_total"],
            "central_directory_bytes": cd_size,
        },
        "range_receipts": {"tail": tail_receipt, "central_directory": central_receipt},
        "member_summary": [
            {
                "name": row["name"],
                "compression_method": row["compression_method"],
                "compressed_size": row["compressed_size"],
                "uncompressed_size": row["uncompressed_size"],
                "local_header_offset": row["local_header_offset"],
                "encrypted": row["encrypted"],
            }
            for row in rows
            if row["name"].lower().endswith((".tif", ".tiff"))
        ],
        "dtm_candidate_count": len(candidates),
        "outcome": outcome,
    }
    transferred = tail_receipt["bytes"] + central_receipt["bytes"]
    if isinstance(tail_receipt, dict) and "zip64_eocd" in tail_receipt:
        transferred += tail_receipt["zip64_eocd"]["bytes"]
    if selected is not None:
        if selected["encrypted"]:
            result["outcome"] = "ENCRYPTED_DTM_MEMBER"
        else:
            local_start = selected["local_header_offset"]
            prefix, prefix_receipt = fetch_exact_range(session, ARCHIVE_URL, local_start, local_start + 29, archive_size)
            if prefix[:4] != b"PK\x03\x04":
                raise ProbeError("LOCAL_HEADER_INVALID", "Selected DTM member has no local ZIP header")
            name_len, extra_len = struct.unpack_from("<HH", prefix, 26)
            header_size = 30 + name_len + extra_len
            if header_size > MAX_LOCAL_HEADER_BYTES:
                raise ProbeError("LOCAL_HEADER_OVER_LIMIT", "ZIP local header exceeds the 64 KiB cap")
            header, header_receipt = fetch_exact_range(
                session, ARCHIVE_URL, local_start, local_start + header_size - 1, archive_size
            )
            local = parse_local_header(header, selected["name"], selected["compression_method"])
            data_offset = local_start + header_size
            magic, magic_receipt = fetch_exact_range(session, ARCHIVE_URL, data_offset, data_offset + 3, archive_size)
            result["selected_member"] = {
                **{key: selected[key] for key in (
                    "name", "compression_method", "compressed_size", "uncompressed_size",
                    "local_header_offset", "encrypted"
                )},
                "local_header": local,
                "data_offset": data_offset,
                "first_four_bytes_hex": magic.hex(),
                "tiff_magic": magic in TIFF_MAGICS,
            }
            result["range_receipts"]["local_header"] = header_receipt
            result["range_receipts"]["member_magic"] = magic_receipt
            transferred += header_receipt["bytes"] + magic_receipt["bytes"]
            if selected["compression_method"] == 0 and magic in TIFF_MAGICS:
                result["outcome"] = "RANGE_ACCESSIBLE_STORED_TIFF"
            elif selected["compression_method"] == 8:
                result["outcome"] = "ZIP_DEFLATED_MEMBER_NOT_RANDOM_ACCESSIBLE"
            else:
                result["outcome"] = "UNSUPPORTED_MEMBER_COMPRESSION"
    result["transferred_bytes"] = transferred
    if transferred > MAX_TOTAL_TRANSFER_BYTES:
        raise ProbeError("TRANSFER_BUDGET_EXCEEDED", "Actual bounded transfer exceeded the 8.52 MB cap")
    result["claim_state"] = {
        "archive_range_access": "SUPPORTED" if tail_receipt else "NOT YET MEASURED",
        "raster_random_access": (
            "SUPPORTED_FOR_PINNED_MEMBER" if result["outcome"] == "RANGE_ACCESSIBLE_STORED_TIFF"
            else "NOT_SUPPORTED_BY_THIS_ZIP_MEMBER_LAYOUT"
            if result["outcome"] == "ZIP_DEFLATED_MEMBER_NOT_RANDOM_ACCESSIBLE"
            else "NOT YET MEASURED"
        ),
        "raster_values_inspected": False,
        "CTX_HiRISE_registration": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "known_site_recovery": "NOT YET MEASURED",
        "novel_analogue_discovery": "NOT YET PROVEN",
        "challenge_selection_superiority": "NOT YET PROVEN",
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = probe()
    except ProbeError as exc:
        result = {
            "outcome": exc.outcome,
            "message": str(exc),
            "details": exc.details,
            "claim_state": {
                "archive_range_access": "NOT SUPPORTED FOR THIS REQUEST" if exc.outcome == "RANGE_IGNORED" else "NOT YET MEASURED",
                "raster_random_access": "NOT YET MEASURED",
                "raster_values_inspected": False,
                "CTX_HiRISE_registration": "NOT YET MEASURED",
                "cross_body_similarity": "NOT YET PROVEN",
                "known_site_recovery": "NOT YET MEASURED",
                "novel_analogue_discovery": "NOT YET PROVEN",
                "challenge_selection_superiority": "NOT YET PROVEN",
            },
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    if result["outcome"] in {
        "RANGE_ACCESSIBLE_STORED_TIFF",
        "ZIP_DEFLATED_MEMBER_NOT_RANDOM_ACCESSIBLE",
        "UNSUPPORTED_MEMBER_COMPRESSION",
        "NO_DTM_TIFF_MEMBER_FOUND",
        "AMBIGUOUS_DTM_TIFF_MEMBERS",
        "ENCRYPTED_DTM_MEMBER",
        "RANGE_IGNORED",
        "REDIRECT_NOT_ALLOWED",
        "HEAD_REDIRECT_NOT_ALLOWED",
        "HTTP_403",
        "HTTP_404",
        "HTTP_410",
    }:
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
