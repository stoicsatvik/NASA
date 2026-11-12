"""E594 parser and safety tests; no network calls or credentials."""
import unittest

from experiments.e594_firms_keyless_modis_viirs_probe import (
    COMMON_FIELDS,
    MAX_BYTES,
    probe_directory_listing,
    SOURCES,
    summarize_csv_prefix,
    validate_url,
)


class E594FirmsProbeTests(unittest.TestCase):
    def test_modis_fixture_exposes_common_fields_and_sensor_bands(self):
        fixture = (
            "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,"
            "confidence,version,bright_t31,frp,daynight\n"
            "34.1,-117.2,330.5,1.0,1.0,2026-11-11,123,Terra,MODIS,80,6.1NRT,290.2,4.2,D\n"
        ).encode()
        result = summarize_csv_prefix(fixture)
        self.assertTrue(result["is_csv"])
        self.assertEqual(result["row_count_in_prefix"], 1)
        self.assertEqual(result["missing_common_fields"], [])
        self.assertEqual(set(result["brightness_fields"]), {"brightness", "bright_t31"})
        self.assertEqual(set(result["common_field_coverage"]), COMMON_FIELDS)
        self.assertFalse(result["raw_coordinates_retained"])

    def test_viirs_fixture_preserves_distinct_band_names_and_confidence(self):
        fixture = (
            "latitude,longitude,bright_ti4,scan,track,acq_date,acq_time,satellite,instrument,"
            "confidence,version,bright_ti5,frp,daynight\n"
            "18.5,73.8,342.1,0.4,0.4,2026-11-11,45,NOAA-20,VIIRS,nominal,2.0NRT,301.4,2.1,N\n"
        ).encode()
        result = summarize_csv_prefix(fixture)
        self.assertTrue(result["is_csv"])
        self.assertEqual(result["row_count_in_prefix"], 1)
        self.assertEqual(result["missing_common_fields"], [])
        self.assertEqual(set(result["brightness_fields"]), {"bright_ti4", "bright_ti5"})
        self.assertEqual(result["confidence_value_counts"], {"nominal": 1})

    def test_invalid_coordinates_are_separate_and_incomplete_rows_are_dropped(self):
        fixture = (
            "latitude,longitude,brightness,scan,track,acq_date,acq_time,satellite,instrument,"
            "confidence,version,bright_t31,frp,daynight\n"
            "999,181,330,1,1,2026-11-11,123,Terra,MODIS,80,6.1NRT,290,4,D\n"
            "34.1,-117.2,330,1,1,2026-11-11,123,Terra,MODIS,80,6.1NRT,290,4\n"
        ).encode()
        result = summarize_csv_prefix(fixture)
        self.assertEqual(result["row_count_in_prefix"], 1)
        self.assertEqual(result["incomplete_rows_dropped"], 1)
        self.assertEqual(result["valid_coordinate_rows"], 0)

    def test_probe_boundary_rejects_credentials_queries_and_other_hosts(self):
        for url in (
            "http://firms.modaps.eosdis.nasa.gov/data/active_fire/a.csv",
            "https://user@firms.modaps.eosdis.nasa.gov/data/active_fire/a.csv",
            "https://firms.modaps.eosdis.nasa.gov/data/active_fire/a.csv?MAP_KEY=secret",
            "https://example.com/data/active_fire/a.csv",
        ):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    validate_url(url)

    def test_all_sources_are_fixed_official_https_endpoints(self):
        self.assertEqual(set(SOURCES), {"MODIS_C61", "VIIRS_SNPP"})
        for source in SOURCES.values():
            validate_url(source["url"])
            self.assertTrue(source["url"].startswith("https://firms.modaps.eosdis.nasa.gov/"))
        self.assertEqual(MAX_BYTES, 256 * 1024)

    def test_directory_listing_parser_keeps_only_same_host_paths(self):
        from unittest.mock import patch

        from email.message import Message

        with patch("experiments.e594_firms_keyless_modis_viirs_probe.urllib.request.build_opener") as build:
            class Response:
                status = 200
                headers = Message()
                headers["Content-Type"] = "text/html"
                headers["Last-Modified"] = "Thu, 12 Nov 2026 00:00:00 GMT"
                def __enter__(self): return self
                def __exit__(self, *args): return False
                def read(self, limit):
                    return b'<a href="viirs-noaa20-1/">N20</a><a href="https://example.com/out.csv">bad</a><a href="../private/">bad</a>'

            class Opener:
                def open(self, request, timeout):
                    return Response()

            build.return_value = Opener()
            result = probe_directory_listing(
                "https://firms.modaps.eosdis.nasa.gov/data/active_fire/"
            )
        self.assertEqual(result["status"], 200)
        self.assertEqual(
            result["links"],
            ["https://firms.modaps.eosdis.nasa.gov/data/active_fire/viirs-noaa20-1/"],
        )



if __name__ == "__main__":
    unittest.main()
