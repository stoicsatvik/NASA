from __future__ import annotations
import csv, json, unittest
from io import StringIO
from experiments.e524_paad_mgd3_feature_admissibility import audit_paad, audit_mgd3, build_report

def paad_fixture():
    stream=StringIO()
    writer=csv.DictWriter(stream,fieldnames=["Field_Site","Center_Latitude","Center_Longitude","Dune_Type","Sand_Source","Composition_of_Sand","Elevation","Areal_Coverage","Köppen_Geiger_Climate_Classification"])
    writer.writeheader()
    writer.writerow({"Field_Site":"a","Center_Latitude":"1","Center_Longitude":"2","Dune_Type":"B","Sand_Source":"river","Composition_of_Sand":"","Elevation":"10","Areal_Coverage":"~20","Köppen_Geiger_Climate_Classification":"Hot arid desert"})
    writer.writerow({"Field_Site":"b","Center_Latitude":"3","Center_Longitude":"4","Dune_Type":"TR","Sand_Source":"","Composition_of_Sand":"quartz","Elevation":"","Areal_Coverage":"","Köppen_Geiger_Climate_Classification":"Cold arid desert"})
    return stream.getvalue().encode()

def mgd3_fixture():
    return json.dumps({"file_receipts":[{"status":"DOWNLOADED","sha256":"test-hash","tables":[{"file":"Mars:Global Summary all ocks","rows":2,"columns":["Dune ID ","Average Bolometer nighttime thermal inertia (tiu)","Average Daytime Albedo","Feldspar"],"nonempty_by_field":{"Dune ID ":2,"Average Bolometer nighttime thermal inertia (tiu)":2,"Average Daytime Albedo":2,"Feldspar":1}}]}]}).encode()

class E524Tests(unittest.TestCase):
    def test_paad_missingness_and_unique_sites(self):
        result=audit_paad(paad_fixture())
        self.assertEqual(result["rows"],2)
        self.assertEqual(result["unique_site_names"],2)
        self.assertEqual(result["unique_coordinate_pairs"],2)
        self.assertEqual(result["missing_counts"]["Composition_of_Sand"],1)
        self.assertEqual(result["missing_counts"]["Sand_Source"],1)

    def test_nan_strings_are_counted_as_missing(self):
        raw=paad_fixture().decode().replace(",quartz,",",NaN,")
        result=audit_paad(raw.encode())
        self.assertEqual(result["missing_counts"]["Composition_of_Sand"],2)

    def test_mgd3_rows_are_not_unique_sites(self):
        result=audit_mgd3(mgd3_fixture())
        self.assertEqual(result["global_summary_profiles"][0]["worksheet_rows_not_unique_sites"],2)
        self.assertTrue(result["worksheet_rows_are_not_unique_sites"])
        self.assertFalse(result["coordinate_or_footprint_fields_present"])

    def test_report_does_not_infer_direct_comparability_or_negatives(self):
        result=build_report(paad_fixture(),mgd3_fixture(),verify_hashes=False)
        self.assertEqual(result["directly_comparable_descriptor_count"],0)
        self.assertEqual(result["negative_label_status"],"NO_INDEPENDENT_NON_ANALOGUE_LABELS")
        self.assertEqual(result["e001_known_site_recovery"],"NOT YET MEASURED")

    def test_spatial_source_is_documented_not_ingested(self):
        result=build_report(paad_fixture(),mgd3_fixture(),verify_hashes=False)
        self.assertEqual(result["spatial_source_discovery"]["status"],"DOCUMENTED_NOT_INGESTED")
        self.assertIn("MOLA-based average elevation",result["spatial_source_discovery"]["documented_features"])

    def test_missing_mgd3_summary_fails_closed(self):
        with self.assertRaises(ValueError):
            audit_mgd3(json.dumps({"file_receipts":[]}).encode())

    def test_duplicate_paad_site_names_fail_closed(self):
        raw=paad_fixture().decode().replace("b,3,4","a,3,4")
        with self.assertRaises(ValueError):
            audit_paad(raw.encode())

    def test_hash_gate_rejects_unpinned_inputs(self):
        with self.assertRaises(ValueError):
            build_report(paad_fixture(),mgd3_fixture(),verify_hashes=True)

if __name__=="__main__":
    unittest.main()
