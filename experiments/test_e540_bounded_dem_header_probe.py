"""Network-free E540 safety and response-classification tests."""
import json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from experiments.e540_bounded_dem_header_probe import (
    LIMIT, TARGET, _Redirects, _allowed, _classify, _find_file, _magic, _request, main,
)

class E540Tests(unittest.TestCase):
    def test_exact_file_match_and_fail_closed_ambiguity(self):
        rec = {"name": TARGET, "downloadUri": "https://sciencebase.usgs.gov/manager/download/file-1"}
        self.assertIs(_find_file([{"name": "other.tif"}, rec]), rec)
        with self.assertRaises(ValueError): _find_file([rec, dict(rec)])
        with self.assertRaises(ValueError): _find_file([{"name": "other.tif"}])

    def test_source_urls_are_pinned_https_and_untokenized(self):
        self.assertTrue(_allowed("https://sciencebase.usgs.gov/manager/download/file-1"))
        self.assertTrue(_allowed("https://www.sciencebase.gov/catalog/file/get/item?f=1"))
        self.assertFalse(_allowed("http://sciencebase.usgs.gov/manager/download/file-1"))
        self.assertFalse(_allowed("https://example.com/file.tif"))
        self.assertFalse(_allowed("https://sciencebase.usgs.gov/manager/download/file-1?token=secret"))

    def test_signed_usgs_redirect_only_to_exact_host(self):
        signed = "https://prod-is-usgs-sb-prod-content.s3.amazonaws.com/item/file.tif?AWSAccessKeyId=x&Expires=1&Signature=y"
        self.assertTrue(_allowed(signed, redirect=True))
        self.assertFalse(_allowed("https://example.com/file.tif", redirect=True))
        self.assertFalse(_allowed("https://evil.sciencebase.usgs.gov/manager/download/x", redirect=True))

    def test_range_request_is_exactly_32_bytes_without_auth(self):
        req = _request("https://sciencebase.usgs.gov/manager/download/file-1")
        self.assertEqual(req.get_header("Range"), f"bytes=0-{LIMIT-1}")
        self.assertIsNone(req.get_header("Authorization"))

    def test_redirect_handler_rejects_unapproved_host(self):
        with self.assertRaises(Exception): _Redirects().redirect_request(None, None, 302, "Found", {}, "https://example.com/file.tif")

    def test_tiff_and_bigtiff_magic(self):
        self.assertEqual(_magic(b"II*\x00" + b"\x00"*28), "TIFF_CLASSIC_LE")
        self.assertEqual(_magic(b"MM\x00+" + b"\x00"*28), "BIGTIFF_BE")
        self.assertIsNone(_magic(b"NOPE" + b"\x00"*28))

    def test_success_requires_206_range_magic_and_size_agreement(self):
        h = {"Content-Range": "bytes 0-31/1000", "Content-Length": "32", "Content-Type": "image/tiff"}
        good = _classify(206, h, b"II*\x00" + b"\x00"*28, 1000)
        self.assertEqual(good["decision"], "BOUNDED_TIFF_HEADER_ACQUIRED")
        self.assertFalse(good["raster_bytes_stored"])
        self.assertEqual(_classify(200, h, b"II*\x00" + b"\x00"*28, 1000)["decision"], "SERVER_IGNORED_RANGE_LIMIT")
        self.assertEqual(_classify(206, h, b"NOPE" + b"\x00"*28, 1000)["decision"], "NON_TIFF_HEADER")
        self.assertEqual(_classify(206, h, b"II*\x00" + b"\x00"*28, 999)["decision"], "METADATA_SIZE_MISMATCH")

    def test_cli_writes_network_free_receipt(self):
        expected = {"experiment":"E540", "decision":"METADATA_HTTP_503", "range_limit_bytes":32, "credentials_sent":False, "full_file_download_attempted":False, "raster_bytes_stored":False}
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)/"receipt.json"
            with patch("sys.argv", ["e540", "--out", str(out)]), patch("experiments.e540_bounded_dem_header_probe.audit", return_value=expected): main()
            self.assertEqual(json.loads(out.read_text()), expected)

if __name__ == "__main__": unittest.main()
