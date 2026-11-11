import io, json, unittest, zipfile
from experiments.e560_usgs_known_analog_catalogue import (
    ITEM_ID, EXPECTED_TITLE, METADATA_URL, NoRedirectHandler, checksum_status,
    metadata_files, normalise, overlap, parse_fgdc_metadata, parse_geojson,
    parse_vector, safe_file_url, safe_metadata_url, validate_item_identity,
    xml_urls, vector_url_candidates,
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

    def test_item_identity_is_exact(self):
        self.assertEqual(validate_item_identity({"id": ITEM_ID, "title": EXPECTED_TITLE}), ITEM_ID)
        with self.assertRaises(ValueError):
            validate_item_identity({"id": "different", "title": EXPECTED_TITLE})
        with self.assertRaises(ValueError):
            validate_item_identity({"id": ITEM_ID, "title": "Wrong title"})

    def test_redirect_handler_refuses_redirects(self):
        handler = NoRedirectHandler()
        self.assertIsNone(handler.redirect_request(None, None, 302, "Found", {}, "https://www.sciencebase.gov/other"))

    def test_checksum_status_preserves_mismatch(self):
        import hashlib
        payload = b"metadata"
        good = checksum_status({"type": "MD5", "value": hashlib.md5(payload).hexdigest()}, payload)
        bad = checksum_status({"type": "MD5", "value": "0" * 32}, payload)
        self.assertTrue(good["matches"])
        self.assertFalse(bad["matches"])
        self.assertEqual(bad["status"], "MISMATCH")

    def test_fgdc_metadata_summary_preserves_use_and_accuracy_limits(self):
        xml = b"""<metadata>
          <idinfo><citation><citeinfo><origin>USGS</origin><pubdate>20201218</pubdate><title>Known Terrestrial Analog Sites for Planetary Science</title></citeinfo></citation>
          <descript><purpose>For identification of research areas, not for analysis</purpose></descript>
          <status><progress>In work</progress><update>As needed</update></status><accconst>Public domain.</accconst></idinfo>
          <dataqual><complete>Limited to verified NASA-funded sites.</complete><posacc><horizpa><horizpar>May have errors up to 10km from centroid.</horizpar></horizpa></posacc>
          <lineage><procstep><procdesc>None</procdesc><procdate>Unknown</procdate></procstep></lineage></dataqual>
          <spdoinfo><ptvctinf><sdtsterm><sdtstype>Entity point</sdtstype><ptvctcnt>192</ptvctcnt></sdtsterm></ptvctinf></spdoinfo>
          <spref><horizsys><planar><mapproj><mapprojn>Mercator_1SP</mapprojn></mapproj><planci><coordrep><absres>0.6096</absres><ordres>0.6096</ordres></coordrep><plandu>meters</plandu></planci></planar><geodetic><horizdn>WGS_1984</horizdn></geodetic></horizsys></spref>
          <eainfo><detailed><attr><attrlabl>Name</attrlabl></attr><attr><attrlabl>AnalogType</attrlabl><attrdomv><edomv>Impact Crater</edomv></attrdomv><attrdomv><edomv>Dunes</edomv></attrdomv></attr></detailed></eainfo>
        </metadata>"""
        summary = parse_fgdc_metadata(xml)
        self.assertEqual(summary["declared_feature_count"], 192)
        self.assertEqual(summary["maximum_accuracy_error_km"], 10.0)
        self.assertFalse(summary["analysis_use_allowed"])
        self.assertEqual(summary["projection"], "Mercator_1SP")
        self.assertEqual(summary["analog_type_values"], ["Dunes", "Impact Crater"])
        self.assertNotIn("email", str(summary).lower())

    def test_geojson_requires_feature_collection(self):
        with self.assertRaises(ValueError):
            parse_geojson(b'{"type":"Feature","features":[]}')

    def test_metadata_xml_exposes_only_allowlisted_vector_links(self):
        xml=b'<metadata><onlink>https://www.sciencebase.gov/catalog/file/get/123/sites.zip</onlink><onlink>https://doi.org/10.5066/P9J72921</onlink></metadata>'
        urls=xml_urls(xml)
        candidates=vector_url_candidates(urls)
        self.assertEqual(len(candidates),1)
        self.assertEqual(candidates[0]["name"],"sites.zip")
        self.assertEqual(candidates[0]["url"],"https://www.sciencebase.gov/catalog/file/get/123/sites.zip")

if __name__=="__main__": unittest.main()
