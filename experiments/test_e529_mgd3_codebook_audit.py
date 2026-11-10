from __future__ import annotations
import io, unittest, zipfile
from experiments.e529_mgd3_codebook_audit import safe_url, inspect_archive, extract_text

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

if __name__=="__main__": unittest.main()