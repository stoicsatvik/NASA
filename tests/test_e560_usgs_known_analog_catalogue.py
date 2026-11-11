import io, json, unittest, zipfile
from experiments.e560_usgs_known_analog_catalogue import (
    ITEM_ID, METADATA_URL, metadata_files, normalise, overlap,
    parse_geojson, parse_vector, safe_file_url, safe_metadata_url,
)

class E560Tests(unittest.TestCase):
    def test_exact_metadata_endpoint(self):
        self.assertTrue(safe_metadata_url(METADATA_URL))
        self.assertIn(ITEM_ID,METADATA_URL)
        self.assertFalse(safe_metadata_url(METADATA_URL+"&x=1"))
        self.assertFalse(safe_metadata_url(METADATA_URL.replace("https://","http://")))
        self.assertFalse(safe_metadata_url(METADATA_URL.replace(ITEM_ID,"0"*24)))

    def test_file_allowlist(self):
        self.assertTrue(safe_file_url("https://www.sciencebase.gov/catalog/file/get/x"))
        self.assertTrue(safe_file_url("https://bucket.s3.amazonaws.com/data.zip"))
        self.assertFalse(safe_file_url("http://www.sciencebase.gov/x"))
        self.assertFalse(safe_file_url("https://example.com/data.zip"))
        self.assertFalse(safe_file_url("https://user:pass@www.sciencebase.gov/x"))

    def test_metadata_files_and_vector_candidates(self):
        rows=metadata_files({"files":[{"name":"readme.txt","size":10},{"name":"sites.zip","size":"123","url":"https://www.sciencebase.gov/x","md5":"abc"}]})
        self.assertEqual(len(rows),2)
        self.assertEqual(rows[1]["size_bytes"],123)
        self.assertEqual(rows[1]["checksum"],"abc")
        self.assertEqual(rows[0]["url"],None)

    def test_geojson_schema(self):
        data=json.dumps({"type":"FeatureCollection","features":[
            {"type":"Feature","id":"a","geometry":{"type":"Point","coordinates":[1,2]},"properties":{"site_name":"Lonar Crater","kind":"impact"}},
            {"type":"Feature","id":"b","geometry":{"type":"Point","coordinates":[3,4]},"properties":{"site_name":"Atacama Desert","kind":"aeolian"}}
        ]}).encode()
        result=parse_geojson(data)
        self.assertEqual(result["feature_count"],2)
        self.assertEqual(result["geometry_types"],["Point"])
        self.assertEqual(result["feature_ids_present"],2)
        self.assertEqual(result["candidate_name_values"],["Atacama Desert","Lonar Crater"])

    def test_zip_geojson_member(self):
        data=json.dumps({"type":"FeatureCollection","features":[{"type":"Feature","geometry":{"type":"Point","coordinates":[1,2]},"properties":{"name":"Test Site"}}]}).encode()
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,"w") as z: z.writestr("sites.geojson",data)
        result=parse_vector("sites.zip",stream.getvalue())
        self.assertEqual(result["feature_count"],1)
        self.assertEqual(result["archive_member"],"sites.geojson")

    def test_overlap_is_name_only_and_exact(self):
        result=overlap({"Atacama Desert"},{"LeCussan16":{"Atacama Desert","Dallol"},"PAAD":{"atacama-desert"}})
        self.assertEqual(result["LeCussan16"]["exact"],["Atacama Desert"])
        self.assertEqual(result["PAAD"]["normalized_full_string"],[("Atacama Desert","atacama-desert")])
        self.assertIn("not coordinate",result["PAAD"]["meaning"])
        self.assertEqual(normalise("Lonar Crater, India"),"lonarcraterindia")

if __name__=="__main__": unittest.main()
