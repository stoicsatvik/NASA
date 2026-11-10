import unittest
from experiments.e530_crossbody_feature_admissibility import missing, tokens, summarize

class E530Tests(unittest.TestCase):
    def fixture(self):
        paad = [
            {"Field_Site":"A","Dune_Type":"B, S, SS","Sand_Source":"x","Composition_of_Sand":"NaN","Elevation":"100","Areal_Coverage":"12"},
            {"Field_Site":"B","Dune_Type":"B, TR, P","Sand_Source":"y","Composition_of_Sand":"quartz","Elevation":"","Areal_Coverage":""},
        ]
        mgd3 = [
            {"Dune_ID":"1","Dune_Type":"B, Bd","Area_sinu_":"10","Avg_El":"-1000"},
            {"Dune_ID":"2","Dune_Type":"S, SS","Area_sinu_":"20","Avg_El":"-2000"},
            {"Dune_ID":"3","Dune_Type":"T","Area_sinu_":"30","Avg_El":"-3000"},
        ]
        join = [
            {"workbook":"ofr20181164_dunedatabase/MGD3_Equatorial_DuneDatabase.xlsx","sheet":"Global Summary ocks <7000","dune_id":"1","matched_2007_spatial":"True","row_json":'{"Dune ID":"1","Average Bolometer nighttime thermal inertia (tiu)":"300","Average Daytime Albedo":"0.2","Feldspar":"20"}'},
            {"workbook":"ofr20181164_dunedatabase/MGD3_Equatorial_DuneDatabase.xlsx","sheet":"Stability Index","dune_id":"1","matched_2007_spatial":"True","row_json":'{"Dune_ID":"1"}'},
        ]
        return paad, mgd3, join

    def test_literal_nan_and_blank_are_missing(self):
        self.assertTrue(missing("NaN"))
        self.assertTrue(missing(" "))
        self.assertFalse(missing("0"))

    def test_code_tokens_are_normalized(self):
        self.assertEqual(tokens(" B, SS , L "), ["B", "SS", "L"])

    def test_e001_fails_closed_without_labels_or_controls(self):
        paad, mgd3, join = self.fixture()
        result = summarize(paad, mgd3, join)
        self.assertFalse(result["e001_readiness"]["ready"])
        self.assertFalse(result["paad"]["target_body_label_field_present"])
        self.assertEqual(result["paad"]["non_analogue_control_labels"], 0)
        self.assertEqual(result["feature_admissibility"]["directly_shared_quantitative_features"], [])

    def test_ambiguous_barchan_token_is_not_admitted(self):
        paad, mgd3, join = self.fixture()
        result = summarize(paad, mgd3, join)
        crosswalk = result["dune_type_crosswalk"]
        self.assertEqual(crosswalk["strict_name_matches"], ["S", "SS"])
        self.assertEqual(crosswalk["ambiguous_matches_rejected"], ["B"])
        self.assertEqual(crosswalk["candidate_semantic_matches_not_admitted"], ["L"])
        self.assertEqual(crosswalk["coverage_sensitivity"]["strict_exact"]["paad_sites"], 1)
        self.assertEqual(crosswalk["coverage_sensitivity"]["naive_including_B"]["paad_sites"], 2)

    def test_matched_2018_ids_must_belong_to_2007_spatial_inventory(self):
        paad, mgd3, join = self.fixture()
        join[0]["dune_id"] = "999"
        with self.assertRaisesRegex(ValueError, "absent from the 2007 MGD3 spatial inventory"):
            summarize(paad, mgd3, join)

    def test_duplicate_source_ids_are_rejected(self):
        paad, mgd3, join = self.fixture()
        mgd3.append(dict(mgd3[0]))
        with self.assertRaisesRegex(ValueError, "not unique"):
            summarize(paad, mgd3, join)

    def test_2018_join_rows_are_counted_by_unique_site_and_sheet(self):
        paad, mgd3, join = self.fixture()
        result = summarize(paad, mgd3, join)
        block = result["mgd3_2018_equatorial_join"]
        self.assertEqual(block["unique_2007_dune_ids_matched"], 1)
        self.assertEqual(block["stability_index_rows"], 1)
        self.assertEqual(block["global_summary_sheets"]["Global Summary ocks <7000"]["thermal_inertia"], 1)

if __name__ == "__main__":
    unittest.main()
