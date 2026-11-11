import struct
import unittest

from experiments.e546_hirise_zip_range_probe import (
    ARCHIVE_URL,
    ProbeError,
    fetch_exact_range,
    parse_central_directory,
    parse_eocd,
    parse_local_header,
    parse_zip64_eocd,
    validate_url,
)


class FakeResponse:
    def __init__(self, status, headers=None, body=b""):
        self.status_code = status
        self.headers = headers or {}
        self.content = body

    def close(self):
        pass


class FakeSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.response


def make_eocd(entries, cd_size, cd_offset, comment=b""):
    return struct.pack(
        "<4s4H2LH",
        b"PK\x05\x06", 0, 0, entries, entries, cd_size, cd_offset, len(comment)
    ) + comment


def make_central_entry(name, method=0, compressed=4, uncompressed=4, offset=0, flags=0):
    encoded = name.encode("utf-8")
    return struct.pack(
        "<4s6H3I5H2I",
        b"PK\x01\x02", 20, 20, flags | (1 << 11), method, 0, 0, 0x12345678,
        compressed, uncompressed, len(encoded), 0, 0, 0, 0, 0, offset
    ) + encoded


class E546ZipRangeTests(unittest.TestCase):
    def test_exact_archive_url_is_allowed(self):
        validate_url(ARCHIVE_URL)

    def test_url_allowlist_rejects_host_path_query_and_http_changes(self):
        for url in (
            ARCHIVE_URL.replace("https://", "http://"),
            ARCHIVE_URL.replace("asc-pds-services.s3.us-west-2.amazonaws.com", "evil.example"),
            ARCHIVE_URL + "?download=1",
            ARCHIVE_URL.replace("_mosaics.zip", "_other.zip"),
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_url(url)

    def test_exact_range_requires_http_206_and_matching_content_range(self):
        body = b"abcd"
        session = FakeSession(FakeResponse(
            206,
            {"Content-Range": "bytes 10-13/100", "Content-Length": "4"},
            body,
        ))
        data, receipt = fetch_exact_range(session, ARCHIVE_URL, 10, 13, 100)
        self.assertEqual(data, body)
        self.assertEqual(receipt["bytes"], 4)
        self.assertEqual(session.calls[0][1]["headers"]["Range"], "bytes=10-13")

    def test_range_ignored_is_a_preserved_negative_not_a_full_download(self):
        session = FakeSession(FakeResponse(200, {"Content-Length": "100"}, b""))
        with self.assertRaisesRegex(ProbeError, "ignored") as ctx:
            fetch_exact_range(session, ARCHIVE_URL, 10, 13, 100)
        self.assertEqual(ctx.exception.outcome, "RANGE_IGNORED")

    def test_redirect_is_not_followed(self):
        session = FakeSession(FakeResponse(302, {"Location": "https://evil.example/x"}, b""))
        with self.assertRaises(ProbeError) as ctx:
            fetch_exact_range(session, ARCHIVE_URL, 10, 13, 100)
        self.assertEqual(ctx.exception.outcome, "REDIRECT_NOT_ALLOWED")

    def test_content_range_mismatch_is_rejected(self):
        session = FakeSession(FakeResponse(
            206, {"Content-Range": "bytes 9-12/100", "Content-Length": "4"}, b"abcd"
        ))
        with self.assertRaises(ProbeError) as ctx:
            fetch_exact_range(session, ARCHIVE_URL, 10, 13, 100)
        self.assertEqual(ctx.exception.outcome, "CONTENT_RANGE_MISMATCH")

    def test_eocd_parser_reads_single_disk_archive(self):
        tail = b"prefix" + make_eocd(2, 40, 100)
        result = parse_eocd(tail, 1000, 1100)
        self.assertEqual(result["entries_total"], 2)
        self.assertEqual(result["central_directory_offset"], 100)
        self.assertFalse(result["zip64"])

    def test_eocd_rejects_multi_disk_archive(self):
        tail = bytearray(make_eocd(1, 20, 100))
        struct.pack_into("<H", tail, 4, 1)
        with self.assertRaises(ProbeError) as ctx:
            parse_eocd(bytes(tail), 0, 200)
        self.assertEqual(ctx.exception.outcome, "MULTI_DISK_ZIP")

    def test_central_directory_preserves_member_method_and_sizes(self):
        data = make_central_entry("DTM/Jezero_DTM.tif", method=0, compressed=1000, uncompressed=1000, offset=200)
        rows = parse_central_directory(data, 1)
        self.assertEqual(rows[0]["name"], "DTM/Jezero_DTM.tif")
        self.assertEqual(rows[0]["compression_method"], 0)
        self.assertEqual(rows[0]["local_header_offset"], 200)

    def test_central_directory_rejects_posix_and_windows_path_traversal(self):
        for name in ("../Jezero_DTM.tif", r"..\\Jezero_DTM.tif", r"C:\\temp\\Jezero_DTM.tif"):
            data = make_central_entry(name)
            with self.subTest(name=name), self.assertRaises(ProbeError) as ctx:
                parse_central_directory(data, 1)
            self.assertEqual(ctx.exception.outcome, "UNSAFE_MEMBER_PATH")

    def test_zip64_end_record_parses_large_entry_counts_and_offsets(self):
        data = struct.pack(
            "<4sQ2H2I4Q", b"PK\x06\x06", 44, 45, 45, 0, 0, 70000, 70000, 123456, 987654
        )
        result = parse_zip64_eocd(data)
        self.assertEqual(result["entries_total"], 70000)
        self.assertEqual(result["central_directory_size"], 123456)
        self.assertEqual(result["central_directory_offset"], 987654)

    def test_local_header_requires_central_directory_agreement(self):
        name = b"DTM/Jezero_DTM.tif"
        header = struct.pack(
            "<4s5H3I2H",
            b"PK\x03\x04", 20, 1 << 11, 0, 0, 0, 0, 4, 4, len(name), 0
        ) + name
        parsed = parse_local_header(header, "DTM/Jezero_DTM.tif", 0)
        self.assertEqual(parsed["compression_method"], 0)
        with self.assertRaises(ProbeError):
            parse_local_header(header, "DTM/Other.tif", 0)


if __name__ == "__main__":
    unittest.main()
