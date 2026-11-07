"""E502 bounded PDS download and physical-claim guards, synthetic only."""
import io
import unittest
from unittest.mock import patch as mock_patch

from research.e502_mola_real_ingest import (
    bounded_read, fetch_product, patch, PRODUCTS, MAX_IMAGE, MAX_LABEL,
)


class FakeResponse(io.BytesIO):
    def __init__(self, data, url):
        super().__init__(data)
        self.url = url

    def geturl(self):
        return self.url


class E502Tests(unittest.TestCase):
    def test_exact_size_accepted(self):
        self.assertEqual(bounded_read(io.BytesIO(b"x" * 8), 8), b"x" * 8)

    def test_oversize_rejected_without_unbounded_buffer(self):
        stream = io.BytesIO(b"x" * 50)
        with self.assertRaisesRegex(ValueError, "exceeds"):
            bounded_read(stream, 8)
        self.assertEqual(stream.tell(), 9)

    def test_empty_and_invalid_limits_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            bounded_read(io.BytesIO(b""), 10)
        with self.assertRaisesRegex(ValueError, "limit"):
            bounded_read(io.BytesIO(b"x"), 0)

    def test_product_allowlist(self):
        with self.assertRaisesRegex(ValueError, "unapproved"):
            fetch_product("../secret")

    def test_redirect_to_other_host_rejected(self):
        with mock_patch("research.e502_mola_real_ingest.urlopen", return_value=FakeResponse(
            b"abc", "https://attacker.example/file"
        )):
            with self.assertRaisesRegex(ValueError, "redirected"):
                fetch_product(PRODUCTS[0])

    def test_real_host_accepted_for_fixture(self):
        url = "https://pds-geosciences.wustl.edu/test"
        with mock_patch("research.e502_mola_real_ingest.urlopen", return_value=FakeResponse(b"abc", url)):
            self.assertEqual(fetch_product(PRODUCTS[2]), b"abc")

    def test_patch_row_major_indexing(self):
        a = tuple(range(7 * 7))
        self.assertEqual(patch(a, 7, 7, 3, 3)[0], [8, 9, 10, 11, 12])
        self.assertEqual(patch(a, 7, 7, 3, 3)[4], [36, 37, 38, 39, 40])

    def test_patch_boundary_rejected(self):
        with self.assertRaisesRegex(ValueError, "bounds"):
            patch(tuple(range(49)), 7, 7, 1, 3)

    def test_limits_small_and_explicit(self):
        self.assertLessEqual(MAX_IMAGE, 8 * 1024 * 1024)
        self.assertLessEqual(MAX_LABEL, 128 * 1024)


if __name__ == "__main__":
    unittest.main()
