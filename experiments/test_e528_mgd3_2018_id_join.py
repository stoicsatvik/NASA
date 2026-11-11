from __future__ import annotations
import io, tempfile, unittest
from pathlib import Path
from openpyxl import Workbook
from experiments.e528_mgd3_2018_id_join import safe_archive_url, normalize_id, decode_dune_id, read_spatial_ids, profile_workbook


class E528Tests(unittest.TestCase):
    def test_only_official_2018_archive_url_is_admitted(self):
        self.assertTrue(safe_archive_url("https://pubs.usgs.gov/of/2018/1164/ofr20181164_dunedatabase.zip"))
        self.assertFalse(safe_archive_url("https://example.com/of/2018/1164/data.zip"))
        self.assertFalse(safe_archive_url("http://pubs.usgs.gov/of/2018/1164/data.zip"))
        self.assertFalse(safe_archive_url("https://pubs.usgs.gov/of/2018/1165/data.zip"))

    def test_id_normalization_preserves_dune_codes(self):
        self.assertEqual(normalize_id(" 0289+501 "), "0289+501")
        self.assertEqual(normalize_id(101.0), "101")
        self.assertIsNone(normalize_id("NaN"))

    def test_dune_id_decodes_documented_centroid_encoding(self):
        self.assertEqual(
            decode_dune_id("1225-345"),
            {"longitude_east_deg": 122.5, "latitude_aerocentric_deg": -34.5},
        )
        self.assertEqual(
            decode_dune_id("1167-722"),
            {"longitude_east_deg": 116.7, "latitude_aerocentric_deg": -72.2},
        )
        self.assertIsNone(decode_dune_id("Asterisk indicates a new Dune Field ID"))

    def test_spatial_index_accepts_actual_long_usgs_field_name(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "spatial.csv"
            p.write_text(
                "Dune  Field Lon+Lat ID,Crater centroid to Dune centroid Azimuth\n"
                "0289+501,12.5\n"
                "0301+502,14.0\n",
                encoding="utf-8",
            )
            self.assertEqual(read_spatial_ids(p), {"0289+501", "0301+502"})

    def test_spatial_index_rejects_missing_or_ambiguous_dune_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "spatial.csv"
            p.write_text("site,Area\nA,1\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "lacks Dune_ID"):
                read_spatial_ids(p)
            p.write_text(
                "Dune Field Lon+Lat ID,Dune Center ID\nA,B\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "lacks Dune_ID"):
                read_spatial_ids(p)

    def test_workbook_profile_reports_overlap_duplicates_and_unmatched(self):
        wb = Workbook()
        ws = wb.active
        ws.title = "Equatorial <7000"
        ws.append(["Dune ID", "Thermal Inertia", "Albedo"])
        ws.append(["1225-345", 100, 0.2])
        ws.append(["0289+501", 110, 0.3])
        ws.append(["0289+501", 111, 0.31])
        ws.append(["1000+756", 120, 0.4])
        ws.append(["Asterisk indicates a new Dune Field ID because this site is not part of the original release.", None, None])
        data = io.BytesIO()
        wb.save(data)
        wb.close()
        profiles, rows = profile_workbook(data.getvalue(), "fixture.xlsx", {"1225-345", "0289+501", "1200+100"})
        p = profiles[0]
        self.assertEqual(p["worksheet_rows_not_unique_sites"], 5)
        self.assertEqual(p["nonempty_id_rows"], 5)
        self.assertEqual(p["valid_dune_id_rows"], 4)
        self.assertEqual(p["non_data_note_rows"], 1)
        self.assertEqual(p["unique_ids"], 3)
        self.assertEqual(p["duplicate_id_rows"], 1)
        self.assertEqual(p["matched_2007_spatial_unique_ids"], 2)
        self.assertEqual(p["unmatched_2018_unique_ids"], 1)
        self.assertEqual(p["2007_spatial_ids_absent_from_sheet"], 1)
        self.assertEqual(p["decoded_id_geography"]["within_2007_65S_65N_count"], 2)
        self.assertEqual(p["decoded_id_geography"]["north_of_65N_count"], 1)
        self.assertEqual(p["unparsed_encoding_id_rows"], 0)
        self.assertEqual(len(rows), 4)


if __name__ == "__main__":
    unittest.main()
