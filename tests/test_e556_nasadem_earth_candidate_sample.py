import struct
import unittest

from experiments.e556_nasadem_earth_candidate_sample import (
    DATA_HOST,
    EXPECTED_TILE_BYTES,
    WINDOW,
    _summarize_patch,
    parse_cmr_tile,
    parse_content_range,
    sample_patch,
    tile_name,
    validate_data_url,
    E556Error,
)


PUBLIC_URL = (
    "https://data.lpdaac.earthdatacloud.nasa.gov/"
    "lp-prod-public/MEASURES/NASADEM_HGT.001/2000.02.11/N19E076.hgt"
)


class FakeRaw:
    def __init__(self, body):
        self.body = body

    def read(self, size=-1, decode_content=False):
        return self.body if size < 0 else self.body[:size]


class FakeResponse:
    def __init__(self, url, start, end, body):
        self.url = url
        self.status_code = 206
        self.headers = {
            "Content-Range": f"bytes {start}-{end}/{EXPECTED_TILE_BYTES}",
            "Content-Length": str(len(body)),
        }
        self.raw = FakeRaw(body)

    def close(self):
        pass


class FakeSession:
    def get(self, url, headers, **kwargs):
        start, end = [int(value) for value in headers["Range"].removeprefix("bytes=").split("-")]
        first_sample = start // 2
        count = (end - start + 1) // 2
        row = first_sample // 3601
        column = first_sample % 3601
        values = [row + column + offset for offset in range(count)]
        body = struct.pack(">" + "h" * len(values), *values)
        return FakeResponse(url, start, end, body)


class E556Tests(unittest.TestCase):
    def test_coordinate_maps_to_one_degree_hgt_tile(self):
        self.assertEqual(tile_name(19.975, 76.509), "N19E076")
        self.assertEqual(tile_name(-12.4, -45.2), "S13W046")

    def test_coordinate_outside_nasadem_extent_is_rejected(self):
        with self.assertRaises(ValueError):
            tile_name(70.0, 10.0)

    def test_cmr_selects_exact_tile_and_direct_data_url(self):
        payload = {
            "items": [
                {
                    "meta": {"collection-concept-id": "C2763264762-LPCLOUD"},
                    "umm": {
                        "GranuleUR": "NASADEM_HGT_N19E076",
                        "DataGranule": {"Identifiers": [{"Identifier": "N19E076"}]},
                        "RelatedUrls": [
                            {"Type": "GET DATA", "Subtype": "DIRECT DOWNLOAD", "URL": PUBLIC_URL}
                        ],
                    },
                }
            ]
        }
        result = parse_cmr_tile(payload, "N19E076")
        self.assertEqual(result["granule_ur"], "NASADEM_HGT_N19E076")
        self.assertEqual(result["data_urls"], [PUBLIC_URL])

    def test_cmr_does_not_guess_a_neighbouring_tile(self):
        payload = {
            "items": [
                {
                    "umm": {
                        "GranuleUR": "NASADEM_HGT_N19E075",
                        "RelatedUrls": [{"Type": "GET DATA", "URL": PUBLIC_URL.replace("N19E076", "N19E075")}],
                    }
                }
            ]
        }
        with self.assertRaises(E556Error) as caught:
            parse_cmr_tile(payload, "N19E076")
        self.assertEqual(caught.exception.outcome, "CMR_TILE_NOT_FOUND")

    def test_public_url_allowlist_and_protected_path(self):
        self.assertEqual(validate_data_url(PUBLIC_URL, "N19E076"), PUBLIC_URL)
        with self.assertRaises(E556Error) as caught:
            validate_data_url(PUBLIC_URL.replace(DATA_HOST, "example.com"), "N19E076")
        self.assertEqual(caught.exception.outcome, "DATA_URL_OUTSIDE_ALLOWLIST")
        protected = PUBLIC_URL.replace("/lp-prod-public/", "/lp-prod-protected/")
        with self.assertRaises(E556Error) as caught:
            validate_data_url(protected, "N19E076")
        self.assertEqual(caught.exception.outcome, "EARTHDATA_AUTH_REQUIRED")

    def test_content_range_requires_exact_valid_span(self):
        self.assertEqual(parse_content_range(f"bytes 0-1/{EXPECTED_TILE_BYTES}"), (0, 1, EXPECTED_TILE_BYTES))
        with self.assertRaises(E556Error):
            parse_content_range("bytes 0-2/2")

    def test_patch_summary_preserves_void_count_and_descriptive_statistics(self):
        rows = [[1000 + row + column for column in range(WINDOW)] for row in range(WINDOW)]
        rows[0][0] = -32768
        result = _summarize_patch(rows, 19.975, 76.509, 90, 1836, "a" * 64)
        self.assertEqual(result["valid_sample_count"], WINDOW * WINDOW - 1)
        self.assertEqual(result["void_sentinel_count"], 1)
        self.assertEqual(result["elevation_min_m"], 1001)
        self.assertEqual(result["elevation_max_m"], 1032)
        self.assertIsNotNone(result["central_horn_slope_deg"])
        self.assertFalse(result["raw_patch_retained"])

    def test_bounded_patch_reads_only_the_requested_rows(self):
        site = {
            "site_id": "lonar_literature_lead",
            "latitude": 19.975,
            "longitude": 76.509,
            "role": "literature_lead_not_validated_positive",
        }
        budget = {"body_bytes": 0, "requests": 0}
        result = sample_patch(FakeSession(), PUBLIC_URL, site, budget)
        self.assertEqual(result["valid_sample_count"], WINDOW * WINDOW)
        self.assertEqual(budget["requests"], WINDOW)
        self.assertEqual(budget["body_bytes"], WINDOW * WINDOW * 2)
        self.assertEqual(len(result["patch_sha256"]), 64)
        self.assertEqual(result["site_role"], "literature_lead_not_validated_positive")


if __name__ == "__main__":
    unittest.main()
