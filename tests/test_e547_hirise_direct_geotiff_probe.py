from __future__ import annotations

from io import BytesIO
import re
import unittest

import numpy as np
import tifffile

from experiments.e547_hirise_direct_geotiff_probe import (
    MAX_SEGMENT_BYTES,
    MAX_TOTAL_TRANSFER_BYTES,
    SOURCE_URL,
    ProbeError,
    RangeReader,
    probe,
    validate_url,
)


class _Raw:
    def __init__(self, body):
        self.body = body
        self.read_bytes = 0

    def read(self, amount=-1, decode_content=False):
        data = self.body if amount < 0 else self.body[:amount]
        self.read_bytes += len(data)
        return data


class _Response:
    def __init__(self, status, headers=None, body=b""):
        self.status_code = status
        self.headers = headers or {}
        self.raw = _Raw(body)
        self.closed = False

    def close(self):
        self.closed = True


class _Session:
    def __init__(self, payload, *, ignore_range=False, wrong_range=False):
        self.payload = payload
        self.ignore_range = ignore_range
        self.wrong_range = wrong_range
        self.responses = []
        self.calls = []

    def head(self, url, **kwargs):
        self.calls.append(("HEAD", url, kwargs))
        response = _Response(
            200,
            {
                "Content-Length": str(len(self.payload)),
                "Accept-Ranges": "bytes",
                "Content-Type": "image/tiff",
            },
        )
        self.responses.append(response)
        return response

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if self.ignore_range:
            response = _Response(200, {"Content-Length": str(len(self.payload))}, self.payload)
        else:
            match = re.fullmatch(r"bytes=(\d+)-(\d+)", kwargs["headers"]["Range"])
            start, end = int(match.group(1)), int(match.group(2))
            actual_start = start + 1 if self.wrong_range else start
            body = self.payload[actual_start:end + 1]
            response = _Response(
                206,
                {
                    "Content-Range": f"bytes {actual_start}-{end}/{len(self.payload)}",
                    "Content-Length": str(len(body)),
                    "Content-Encoding": "identity",
                },
                body,
            )
        self.responses.append(response)
        return response


def _tiled_tiff(shape=(32, 32), tile=(16, 16)):
    buffer = BytesIO()
    data = np.arange(shape[0] * shape[1], dtype=np.uint16).reshape(shape)
    tifffile.imwrite(buffer, data, tile=tile, metadata=None)
    return buffer.getvalue()


class E547DirectHiRISETiffTests(unittest.TestCase):
    def test_exact_public_source_url_is_allowed(self):
        validate_url(SOURCE_URL)

    def test_url_allowlist_rejects_scheme_host_path_and_query_changes(self):
        for url in (
            SOURCE_URL.replace("https://", "http://"),
            SOURCE_URL.replace("asc-pds-services.s3.us-west-2.amazonaws.com", "example.com"),
            SOURCE_URL + "?download=1",
            SOURCE_URL.replace("_blend40.tif", "_other.tif"),
        ):
            with self.subTest(url=url), self.assertRaises(ValueError):
                validate_url(url)

    def test_direct_tiled_tiff_reads_only_one_bounded_segment(self):
        payload = _tiled_tiff()
        session = _Session(payload)
        result = probe(session=session)
        self.assertEqual(result["outcome"], "DIRECT_TIFF_SEGMENT_RANGE_READ")
        self.assertTrue(result["tiff"]["is_tiled"])
        self.assertEqual(result["tiff"]["width"], 32)
        self.assertEqual(result["tiff"]["height"], 32)
        self.assertGreater(result["sample"]["bytes_read"], 0)
        self.assertLessEqual(result["sample"]["bytes_read"], MAX_SEGMENT_BYTES)
        self.assertLessEqual(result["transport"]["transferred_bytes"], MAX_TOTAL_TRANSFER_BYTES)
        self.assertFalse(result["sample"]["decoded_pixel_values_read"])
        self.assertNotIn("pixel_values", result)
        self.assertTrue(all(response.closed for response in session.responses))

    def test_large_single_tile_is_not_read_when_it_exceeds_segment_cap(self):
        payload = _tiled_tiff(shape=(512, 512), tile=(512, 512))
        session = _Session(payload)
        result = probe(session=session)
        self.assertEqual(
            result["outcome"],
            "DIRECT_TIFF_METADATA_RANGE_SUPPORTED_NO_SMALL_SEGMENT",
        )
        self.assertIsNone(result["sample"])
        self.assertTrue(result["tiff"]["is_tiled"])

    def test_server_ignoring_range_is_closed_without_consuming_body(self):
        payload = _tiled_tiff()
        session = _Session(payload, ignore_range=True)
        reader = RangeReader(session, SOURCE_URL, len(payload))
        with self.assertRaisesRegex(ProbeError, "ignored Range"):
            reader.read(16)
        self.assertEqual(session.responses[-1].raw.read_bytes, 0)
        self.assertTrue(session.responses[-1].closed)

    def test_mismatched_content_range_is_rejected(self):
        payload = _tiled_tiff()
        session = _Session(payload, wrong_range=True)
        reader = RangeReader(session, SOURCE_URL, len(payload))
        with self.assertRaisesRegex(ProbeError, "Content-Range"):
            reader.read(16)
        self.assertEqual(session.responses[-1].raw.read_bytes, 0)

    def test_transfer_cap_is_checked_before_network_request(self):
        payload = _tiled_tiff()
        session = _Session(payload)
        reader = RangeReader(session, SOURCE_URL, len(payload), max_bytes=8)
        with self.assertRaisesRegex(ProbeError, "transfer budget"):
            reader.read(16)
        self.assertEqual(session.calls, [])

    def test_segment_outside_object_is_not_read(self):
        payload = _tiled_tiff()
        reader = RangeReader(_Session(payload), SOURCE_URL, len(payload))
        with self.assertRaises(ValueError):
            reader.seek(len(payload) + 1)


if __name__ == "__main__":
    unittest.main()
