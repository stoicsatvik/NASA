from __future__ import annotations
import io, unittest, zipfile
from experiments.e529_mgd3_codebook_audit import (
    safe_url,
    inspect_archive,
    extract_text,
    extract_field_definitions,
)

class E529Tests(unittest.TestCase):
    def test_source_scope_is_exact(self):
        self.assertTrue(safe_url("https://pubs.usgs.gov/of/2007/1158/Metadata.zip"))
        self.assertFalse(safe_url("https://example.com/of/2007/1158/Metadata.zip"))
        self.assertFalse(safe_url("https://pubs.usgs.gov/of/2007/1159/Metadata.zip"))
        self.assertFalse(safe_url("http://pubs.usgs.gov/of/2007/1158/Metadata.zip"))

    def test_archive_preserves_codebook_context(self):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w") as z:
            z.writestr("Metadata/Dune_Field.html","<html><body><b>Dune_Type</b><td>B</td><td>Barchan</td><td>Bd</td><td>Barchanoid</td></body></html>")
            z.writestr("Metadata/other.bin",b"x")
        result=inspect_archive("fixture",buf.getvalue())
        self.assertEqual(len(result["entries"]),2)
        doc=result["text_documents_with_relevant_terms"][0]
        self.assertIn("Barchan",doc["matches"][0]["excerpt"])

    def test_html_text_extraction(self):
        text=extract_text("x.html",b"<p>Average elevation (m)</p>")
        self.assertIn("Average elevation (m)",text)

    def test_field_definition_extraction_preserves_units_aliases_and_codes(self):
        source = (
            "Field 4: Dune Type - This field lists dune forms.\n"
            "B - barchan dune.\n"
            "Bd - barchanoid dune.\n"
            "Field 15: Dune Field Area (km2) - area of polygon (km2).\n"
            "Field 19: Dune_Area_km2_sinu (Area_sinu_) - area of polygon (km2).\n"
            "Field 20: Mean_Dune_Height (MDHeight) - mean height in metres (m).\n"
        )
        fields = extract_field_definitions(source)
        self.assertEqual([item["field_number"] for item in fields], [4, 15, 19, 20])
        self.assertEqual(fields[0]["label"], "Dune Type")
        self.assertIn("B - barchan dune", fields[0]["definition"])
        self.assertIn("Bd - barchanoid dune", fields[0]["definition"])
        self.assertEqual(fields[1]["label"], "Dune Field Area (km2)")
        self.assertIsNone(fields[1]["short_name"])
        self.assertEqual(fields[2]["short_name"], "Area_sinu_")
        self.assertIn("km2", fields[2]["definition"])
        self.assertEqual(fields[3]["short_name"], "MDHeight")
        self.assertIn("(m)", fields[3]["definition"])

    def test_archive_exposes_full_field_definitions_with_source_hash(self):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w") as z:
            z.writestr(
                "Documentation/ReadMe_GIS.txt",
                "Field 19: Dune_Area_km2_sinu (Area_sinu_) - polygon area (km2).\n"
                "Field 20: Mean_Dune_Height (MDHeight) - height in metres (m).\n",
            )
        result=inspect_archive("documentation",buf.getvalue())
        document=result["field_definition_documents"][0]
        self.assertEqual(document["field_count"],2)
        self.assertEqual(len(document["sha256"]),64)
        self.assertEqual(document["fields"][0]["short_name"],"Area_sinu_")
        self.assertEqual(result["field_definition_count"],2)

    def test_cp1252_documentation_decodes_en_dash_without_replacement(self):
        text=extract_text("ReadMe_GIS.txt",b"Field 1: Dune - height \x96 value")
        self.assertIn("–",text)
        self.assertNotIn("�",text)

    def test_archive_audit_captures_identity_coordinate_and_height_semantics(self):
        buf=io.BytesIO()
        with zipfile.ZipFile(buf,"w") as z:
            z.writestr(
                "Metadata/dune_field.txt",
                "Dune_ID: unique site identifier.\n"
                "Dune Field Lon+Lat ID is the table identifier.\n"
                "Dune_Latitude_Aerocentric records latitude.\n"
                "Dune_Longitude_East records longitude.\n"
                "Mean_Dune_Height is derived from MOLA elevation.\n",
            )
        result=inspect_archive("metadata",buf.getvalue())
        matches=result["text_documents_with_relevant_terms"][0]["matches"]
        terms={match["term"] for match in matches}
        self.assertIn("dune_id",terms)
        self.assertIn("dune field lon+lat id",terms)
        self.assertIn("dune_latitude",terms)
        self.assertIn("dune_longitude",terms)
        self.assertIn("mean_dune_height",terms)

if __name__=="__main__": unittest.main()