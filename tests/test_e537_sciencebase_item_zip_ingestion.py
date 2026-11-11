import io
import unittest
import zipfile

from experiments.e537_sciencebase_item_zip_ingestion import (
    DEM_NAME, FGDC_NAME, ITEM_ID, build_zip_url, _allowed_host, _select_members,
    parse_fgdc,
)


class E537ScienceBaseItemZipTests(unittest.TestCase):
    def test_uses_documented_server_side_item_zip_endpoint(self):
        self.assertEqual(
            build_zip_url(),
            f"https://www.sciencebase.gov/catalog/file/get/{ITEM_ID}",
        )

    def test_rejects_non_sciencebase_redirects(self):
        self.assertTrue(_allowed_host("https://www.sciencebase.gov/catalog/file/get/x"))
        self.assertTrue(_allowed_host("https://sciencebase.usgs.gov/manager/file/x"))
        self.assertFalse(_allowed_host("https://example.com/file.zip"))
        self.assertFalse(_allowed_host("http://www.sciencebase.gov/file.zip"))

    def test_archive_selection_is_exact_and_path_safe(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(f"folder/{DEM_NAME}", b"II*\\x00" + b"x" * 20)
            archive.writestr(f"folder/{FGDC_NAME}", b"<metadata/>")
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            dem, fgdc = _select_members(archive)
            self.assertEqual(dem.file_size, 24)
            self.assertEqual(fgdc.file_size, len(b"<metadata/>"))

    def test_rejects_duplicate_or_missing_dem(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr(DEM_NAME, b"II*\\x00")
            archive.writestr("copy/" + DEM_NAME, b"II*\\x00")
            archive.writestr(FGDC_NAME, b"<metadata/>")
        with zipfile.ZipFile(io.BytesIO(buffer.getvalue())) as archive:
            with self.assertRaisesRegex(ValueError, "exactly one"):
                _select_members(archive)

    def test_parses_only_explicit_fgdc_unit_and_projection_fields(self):
        xml = b"""<metadata><spref><vertdef><altsys><altdatum>Local datum</altdatum><altunits>meters</altunits></altsys></vertdef><horizsys><planar><mapproj><mapprojn>UTM</mapprojn></mapproj></planar></horizsys></spref></metadata>"""
        fields = parse_fgdc(xml)
        self.assertEqual(fields["altunits"], ["meters"])
        self.assertEqual(fields["altdatum"], ["Local datum"])
        self.assertEqual(fields["mapprojn"], ["UTM"])


if __name__ == "__main__":
    unittest.main()
