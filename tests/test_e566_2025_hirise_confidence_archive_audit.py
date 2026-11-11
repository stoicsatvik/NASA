from __future__ import annotations

import io
import zipfile

import pytest

from experiments.e566_2025_hirise_confidence_archive_audit import (
    ARCHIVE_URL,
    HTTPRangeFile,
    RangeReadError,
    inspect_archive,
)


class FakeResponse:
    def __init__(self, status_code: int, headers: dict, content: bytes = b""):
        self.status_code = status_code
        self.headers = headers
        self.content = content

    def close(self):
        pass


class FakeSession:
    def __init__(
        self,
        payload: bytes,
        *,
        head_status: int = 200,
        ignore_range: bool = False,
    ):
        self.payload = payload
        self.head_status = head_status
        self.ignore_range = ignore_range
        self.requested_ranges = []

    def head(self, url, **kwargs):
        return FakeResponse(
            self.head_status,
            {
                "Content-Length": str(len(self.payload)),
                "Accept-Ranges": "bytes",
                "Content-Type": "application/zip",
                "ETag": '"fixture"',
            },
        )

    def get(self, url, **kwargs):
        headers = kwargs.get("headers", {})
        value = headers.get("Range", "")
        self.requested_ranges.append(value)
        if self.ignore_range:
            return FakeResponse(200, {"Content-Length": str(len(self.payload))}, self.payload)
        assert value.startswith("bytes=")
        start_text, end_text = value[6:].split("-", 1)
        start, end = int(start_text), int(end_text)
        body = self.payload[start : end + 1]
        return FakeResponse(
            206,
            {
                "Content-Range": "bytes " + str(start) + "-" + str(end) + "/" + str(len(self.payload)),
                "Content-Length": str(len(body)),
            },
            body,
        )


def make_archive(*, include_confidence: bool = True) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "mosaic/jezero_DTM.tif",
            b"II*\x00" + b"\x00" * 128,
        )
        if include_confidence:
            archive.writestr(
                "mosaic/jezero_Confidence.tif",
                b"MM\x00*" + b"\x00" * 128,
            )
        archive.writestr("README.txt", "fixture only")
    return buffer.getvalue()


def test_range_file_seeks_and_reads_only_the_requested_interval():
    payload = b"0123456789"
    session = FakeSession(payload)
    remote = HTTPRangeFile(session, "https://example.test/archive.zip")
    remote.seek(2)
    assert remote.read(4) == b"2345"
    assert session.requested_ranges == ["bytes=2-5"]
    assert remote.transferred == 4


def test_range_file_rejects_servers_that_ignore_range():
    session = FakeSession(b"0123456789", ignore_range=True)
    remote = HTTPRangeFile(session, "https://example.test/archive.zip")
    with pytest.raises(RangeReadError) as error:
        remote.read(4)
    assert error.value.outcome == "RANGE_HTTP_200"


def test_range_file_rejects_redirects_without_following_them():
    session = FakeSession(b"0123456789", head_status=302)
    with pytest.raises(RangeReadError) as error:
        HTTPRangeFile(session, "https://example.test/archive.zip")
    assert error.value.outcome == "ARCHIVE_HEAD_HTTP_302"


def test_archive_index_finds_dtm_and_confidence_without_full_download():
    payload = make_archive()
    session = FakeSession(payload)
    result = inspect_archive(session, "https://example.test/archive.zip")
    assert result["outcome"] == "ARCHIVE_INDEXED_WITH_DTM_AND_CONFIDENCE"
    assert result["dtm_member_count"] == 1
    assert result["confidence_member_count"] == 1
    assert result["tiff_member_count"] == 2
    assert all(item["tiff_magic_valid"] for item in result["member_samples"])
    assert result["raw_raster_bytes_retained"] is False
    assert result["pixel_values_read"] is False
    assert result["range_bytes_transferred"] < len(payload) * 8
    assert session.requested_ranges
    assert all(value.startswith("bytes=") for value in session.requested_ranges)


def test_archive_without_confidence_is_a_preserved_negative_result():
    payload = make_archive(include_confidence=False)
    result = inspect_archive(FakeSession(payload), "https://example.test/archive.zip")
    assert result["outcome"] == "ARCHIVE_INDEXED_DTM_WITHOUT_CONFIDENCE"
    assert result["dtm_member_count"] == 1
    assert result["confidence_member_count"] == 0


def test_inspection_uses_the_pinned_official_archive_by_default():
    assert ARCHIVE_URL.startswith("https://asc-pds-services.s3.us-west-2.amazonaws.com/")
