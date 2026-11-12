import io
import struct
import unittest
import zipfile
from urllib.parse import parse_qs, urlsplit

from experiments.e578_known_terrestrial_analog_sites_probe import (
    DOI,
    ITEM_FIELDS,
    ITEM_ID,
    ITEM_URL,
    choose_candidate,
    classify_shapefile_layer,
    parse_dbf_header,
    parse_shapefile_header,
    summarize_receipt,
    summarize_zip,
)


def dbf_fixture():
    fields = []
    for name, kind, width in (("SITE_NAME", "C", 24), ("ANALOG_TYPE", "C", 16)):
        field = bytearray(32)
        field[:len(name)] = name.encode("ascii")
        field[11] = ord(kind)
        field[16] = width
        fields.append(bytes(field))
    header_length = 32 + 32 * len(fields) + 1
    payload = bytearray(header_length)
    payload[0] = 3
    struct.pack_into("<I", payload, 4, 7)
    struct.pack_into("<H", payload, 8, header_length)
    struct.pack_into("<H", payload, 10, 41)
    offset = 32
    for field in fields:
        payload[offset:offset + 32] = field
        offset += 32
    payload[offset] = 0x0D
    return bytes(payload)


def shp_fixture(shape_type=1):
    payload = bytearray(100)
    struct.pack_into(">i", payload, 0, 9994)
    struct.pack_into(">i", payload, 24, 50)
    struct.pack_into("<i", payload, 28, 1000)
    struct.pack_into("<i", payload, 32, shape_type)
    struct.pack_into("<4d", payload, 36, -120.0, 25.0, 15.0, 70.0)
    return bytes(payload)


class E578Tests(unittest.TestCase):
    def test_source_identity_and_bounded_metadata_projection(self):
        self.assertEqual(ITEM_ID, "5f88940b82cebb8c13d912ee")
        self.assertEqual(DOI, "10.5066/P9J72921")
        query = parse_qs(urlsplit(ITEM_URL).query)
        self.assertEqual(query["format"], ["json"])
        self.assertEqual(query["fields"], [ITEM_FIELDS])
        self.assertNotIn("previewImage", ITEM_FIELDS)

    def test_candidate_requires_explicit_download_uri_and_small_supported_type(self):
        files = [
            {"name": "preview.zip", "size": 100, "url": "https://sciencebase.gov/manager/item/x"},
            {"name": "large.zip", "size": 9_000_000, "downloadUri": "https://sciencebase.gov/manager/download/y"},
            {"name": "sites.zip", "size": 4096, "downloadUri": "https://sciencebase.gov/manager/download/z"},
        ]
        self.assertEqual(choose_candidate(files)["name"], "sites.zip")

    def test_dbf_header_preserves_only_schema_and_record_count(self):
        result = parse_dbf_header(dbf_fixture())
        self.assertEqual(result["record_count"], 7)
        self.assertEqual([field["name"] for field in result["fields"]], ["SITE_NAME", "ANALOG_TYPE"])
        self.assertNotIn("rows", result)

    def test_shapefile_header_checks_signature_and_bounds(self):
        result = parse_shapefile_header(shp_fixture())
        self.assertEqual(result["file_code"], 9994)
        self.assertEqual(result["version"], 1000)
        self.assertEqual(result["shape_type"], 1)
        self.assertEqual(result["bounds"], [-120.0, 25.0, 15.0, 70.0])
        self.assertEqual(result["declared_bytes"], 100)

    def test_zip_summary_reports_member_schema_without_raw_records(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("analog_sites.shp", shp_fixture())
            archive.writestr("analog_sites.dbf", dbf_fixture())
            archive.writestr("analog_sites.prj", 'GEOGCS["WGS 84",AUTHORITY["EPSG","4326"]]')
        result = summarize_zip(buffer.getvalue())
        self.assertEqual(result["dbf"]["record_count"], 7)
        self.assertEqual(result["shapefile"]["shape_type"], 1)
        self.assertEqual(result["projection"]["epsg_authority_candidates"], ["4326"])
        self.assertNotIn("rows", result)

    def test_receipt_summary_never_exposes_raw_rows_or_credentials(self):
        summary = summarize_receipt({
            "experiment": "E578",
            "decision": "PUBLIC_ANALOG_POINT_LAYER_ACQUIRED_SCHEMA_VERIFIED",
            "metadata_http_status": 200,
            "file_count": 1,
            "selected_file": {"name": "sites.zip"},
            "data_sample": {
                "vector_summary": {
                    "dbf": {"record_count": 7, "fields": [{"name": "SITE_NAME"}]},
                    "shapefile": {"shape_type": 1},
                }
            },
        })
        self.assertEqual(summary["record_count"], 7)
        self.assertEqual(summary["dbf_fields"], ["SITE_NAME"])
        self.assertFalse(summary["credentials_used"])
        self.assertFalse(summary["raw_rows_stored"])
        self.assertNotIn("coordinates", summary)


    def test_point_shapefile_requires_identity_type_and_crs(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("analog_sites.shp", shp_fixture())
            archive.writestr("analog_sites.dbf", dbf_fixture())
            archive.writestr("analog_sites.prj", 'GEOGCS["WGS 84",AUTHORITY["EPSG","4326"]]')
        summary = summarize_zip(buffer.getvalue())
        self.assertEqual(
            classify_shapefile_layer(summary),
            "PUBLIC_ANALOG_POINT_LAYER_ACQUIRED_SCHEMA_VERIFIED",
        )

    def test_polygon_shapefile_is_not_admitted_as_point_layer(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("analog_sites.shp", shp_fixture(shape_type=5))
            archive.writestr("analog_sites.dbf", dbf_fixture())
            archive.writestr("analog_sites.prj", 'GEOGCS["WGS 84",AUTHORITY["EPSG","4326"]]')
        summary = summarize_zip(buffer.getvalue())
        self.assertEqual(
            classify_shapefile_layer(summary),
            "PUBLIC_VECTOR_LAYER_ACQUIRED_NON_POINT_GEOMETRY",
        )

    def test_point_shapefile_without_identity_type_or_crs_is_incomplete(self):
        summary = {
            "dbf": {"record_count": 7, "fields": [{"name": "SITE_NAME"}]},
            "shapefile": {"shape_type": 1},
            "projection": None,
        }
        self.assertEqual(
            classify_shapefile_layer(summary),
            "PUBLIC_ANALOG_POINT_LAYER_ACQUIRED_SCHEMA_INCOMPLETE",
        )

if __name__ == "__main__":
    unittest.main()
