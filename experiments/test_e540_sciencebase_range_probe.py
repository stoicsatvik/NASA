import unittest
import urllib.error
from unittest.mock import patch

from experiments.e540_sciencebase_range_probe import (
    AllowlistedRedirectHandler,
    DEM_NAME,
    EXPECTED_BYTES,
    locate_dem_download_uri,
    probe_range,
    run_probe,
)


class FakeResponse:
    def __init__(self, status=206, data=None, headers=None, url="https://bucket.s3.amazonaws.com/dem.tif"):
        self.status = status
        self.headers = headers or {"Content-Range": f"bytes 0-31/{EXPECTED_BYTES}", "Content-Length": "32"}
        self.url = url
        self.data = data if data is not None else b"II*\x00" + b"\x00" * 28
        self.read_sizes = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self.url

    def read(self, size=-1):
        self.read_sizes.append(size)
        return self.data[:size]


class FakeOpener:
    def __init__(self, response):
        self.response = response
        self.request = None
        self.timeout = None

    def open(self, request, timeout=None):
        self.request = request
        self.timeout = timeout
        return self.response


def file_item(download_uri="https://bucket.s3.amazonaws.com/dem.tif", size=EXPECTED_BYTES):
    return {
        "id": "662bccfad34ea70bd5f11f88",
        "files": [{"name": DEM_NAME, "size": size, "downloadUri": download_uri}],
    }


class E540ScienceBaseRangeTests(unittest.TestCase):
    def test_selects_only_exact_dem_download_uri(self):
        result = locate_dem_download_uri([
            {"id": "other", "files": [{"name": "other.tif", "downloadUri": "https://bucket.s3.amazonaws.com/other.tif"}]},
            file_item(),
        ])
        self.assertEqual(result["status"], "READY_FOR_ANONYMOUS_RANGE_PROBE")
        self.assertEqual(result["filename"], DEM_NAME)
        self.assertEqual(result["size_bytes"], EXPECTED_BYTES)
        self.assertNotIn("downloadUri", str({k: v for k, v in result.items() if not k.startswith("_")}))

    def test_missing_download_uri_is_preserved_without_request(self):
        result = locate_dem_download_uri([file_item(download_uri=None)])
        self.assertEqual(result["status"], "DOWNLOAD_URI_MISSING")

    def test_signed_url_is_not_treated_as_anonymous_or_requested(self):
        result = run_probe(items=[file_item("https://bucket.s3.amazonaws.com/dem.tif?X-Amz-Signature=secret")])
        self.assertEqual(result["outcome"], "TOKENIZED_URL_NOT_ANONYMOUS")
        self.assertFalse(result["range_request_sent"])
        self.assertNotIn("secret", str(result))

    def test_duplicate_exact_file_records_fail_closed(self):
        result = locate_dem_download_uri([file_item(), file_item()])
        self.assertEqual(result["status"], "AMBIGUOUS_FILE_RECORD")
        self.assertEqual(result["match_count"], 2)

    def test_range_request_is_exactly_32_bytes_and_stores_only_digest(self):
        response = FakeResponse()
        opener = FakeOpener(response)
        result = probe_range("https://bucket.s3.amazonaws.com/dem.tif", opener=opener)
        self.assertEqual(result["outcome"], "RANGE_PREFIX_VALID")
        self.assertEqual(opener.request.get_header("Range"), "bytes=0-31")
        self.assertEqual(response.read_sizes, [33])
        self.assertEqual(result["response_bytes_read"], 32)
        self.assertTrue(result["tiff_magic"])
        self.assertNotIn("II*", str(result))

    def test_server_ignoring_range_is_a_negative_result(self):
        response = FakeResponse(status=200, data=b"II*\x00" + b"x" * 29)
        opener = FakeOpener(response)
        result = probe_range("https://bucket.s3.amazonaws.com/dem.tif", opener=opener)
        self.assertEqual(result["outcome"], "RANGE_NOT_HONORED")
        self.assertEqual(response.read_sizes, [33])

    def test_content_range_mismatch_is_rejected(self):
        response = FakeResponse(headers={"Content-Range": "bytes 0-31/619493", "Content-Length": "32"})
        result = probe_range("https://bucket.s3.amazonaws.com/dem.tif", opener=FakeOpener(response))
        self.assertEqual(result["outcome"], "CONTENT_RANGE_MISMATCH")

    def test_non_tiff_prefix_is_rejected(self):
        response = FakeResponse(data=b"<!doctype html>" + b"x" * 17)
        result = probe_range("https://bucket.s3.amazonaws.com/dem.tif", opener=FakeOpener(response))
        self.assertEqual(result["outcome"], "PREFIX_NOT_TIFF")

    def test_redirect_handler_rejects_unallowlisted_target(self):
        handler = AllowlistedRedirectHandler()
        request = __import__("urllib.request").request.Request("https://bucket.s3.amazonaws.com/dem.tif")
        with self.assertRaises(urllib.error.URLError):
            handler.redirect_request(request, None, 302, "Found", {}, "https://evil.example/dem.tif")


if __name__ == "__main__":
    unittest.main()
