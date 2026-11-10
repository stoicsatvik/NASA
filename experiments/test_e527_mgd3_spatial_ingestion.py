from __future__ import annotations
import io, tempfile, unittest, zipfile
from pathlib import Path
import shapefile
from experiments.e527_mgd3_spatial_ingestion import discover_downloads, core_shapefile, safe_url, member_path, inspect_shapefile, inspect_tables, _extract_layer, _id_field

class E527Tests(unittest.TestCase):
    def test_discover_only_official_archives(self):
        links=discover_downloads('<a href="Shapefiles.zip">x</a><a href="Tables.zip">y</a><a href="https://evil.test/Shapefiles.zip">bad</a>')
        self.assertEqual(links["shapefiles.zip"],"https://pubs.usgs.gov/of/2007/1158/Shapefiles.zip")
        self.assertEqual(links["tables.zip"],"https://pubs.usgs.gov/of/2007/1158/Tables.zip")
        self.assertEqual(len(links),2)

    def test_source_url_scope(self):
        self.assertTrue(safe_url("https://pubs.usgs.gov/of/2007/1158/Shapefiles.zip"))
        self.assertFalse(safe_url("http://pubs.usgs.gov/of/2007/1158/Shapefiles.zip"))
        self.assertFalse(safe_url("https://example.test/of/2007/1158/Shapefiles.zip"))
        self.assertFalse(safe_url("https://pubs.usgs.gov/of/2007/1159/Shapefiles.zip"))

    def test_reject_path_traversal(self):
        with self.assertRaisesRegex(ValueError,"unsafe ZIP path"):
            member_path("../../escape.txt")

    def test_reject_windows_style_path_traversal(self):
        with self.assertRaisesRegex(ValueError,"unsafe ZIP path"):
            member_path("..\\..\\escape.txt")

    def test_id_field_prefers_one_canonical_alias_over_noncanonical_id(self):
        self.assertEqual(_id_field(["Dune Field ID", "Dune Center ID"]), "Dune Field ID")

    def test_id_field_rejects_multiple_canonical_aliases(self):
        self.assertIsNone(_id_field(["Dune Field ID", "Dune_ID"]))

    def test_core_layer_selection(self):
        self.assertEqual(core_shapefile(["background/outline.shp","layers/Dune_Field.shp","layers/Dune_Field_Craters.shp"]),"layers/Dune_Field.shp")

    def test_id_field_does_not_confuse_centroid_with_id(self):
        fields=["Dune  Field Lon+Lat ID","Crater centroid to Dune centroid Azimuth"]
        self.assertEqual(_id_field(fields),"Dune  Field Lon+Lat ID")

    def test_full_attribute_table_beats_repeated_image_index(self):
        payload=io.BytesIO()
        with zipfile.ZipFile(payload,"w") as z:
            z.writestr("Tables/THEMIS_IR_ImageList.txt","Dune Field Lon+Lat ID\tTHEMIS IR Images\nA\tI1\nA\tI2\nB\tI3\n")
            z.writestr("Tables/Softcopy.txt","Dune  Field Lon+Lat ID\tDune Type\tArea (km2)\nA\tB\t1.0\nB\tD\t2.0\n")
        table=inspect_tables(payload.getvalue())["best_table"]
        self.assertEqual(table["name"],"Tables/Softcopy.txt")
        self.assertEqual(table["rows"],2)
        self.assertEqual(table["unique_id_count"],2)

    def test_tables_archive_recovers_full_name_id_column(self):
        payload=io.BytesIO()
        with zipfile.ZipFile(payload,"w") as z:
            z.writestr("Dune_Field.txt","Dune ID\tArea (km2)\n101\t1.0\n102\t2.0\n")
        result=inspect_tables(payload.getvalue())
        table=result["best_table"]
        self.assertEqual(table["id_field"],"Dune ID")
        self.assertEqual(table["unique_id_count"],2)
        self.assertEqual(set(table["ids"]),{"101","102"})

    def test_extract_and_inspect_polygon_layer(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); shp=root/"Dune_Field.shp"
            w=shapefile.Writer(str(shp),shapeType=shapefile.POLYGON); w.field("Dune_ID","N",8,0); w.field("Area_km2","N",12,3)
            w.poly([[[0,0],[1,0],[1,1],[0,1],[0,0]]]); w.record(101,1.0)
            w.poly([[[2,2],[3,2],[3,3],[2,3],[2,2]]]); w.record(102,2.0); w.close()
            (root/"Dune_Field.prj").write_text('GEOGCS["Mars 2000"]',encoding="utf-8")
            buf=io.BytesIO()
            with zipfile.ZipFile(buf,"w") as z:
                for p in root.glob("Dune_Field.*"): z.write(p,f"layers/{p.name}")
            with zipfile.ZipFile(io.BytesIO(buf.getvalue())) as z:
                path=_extract_layer(z,"layers/Dune_Field.shp",root/"out")
            meta,rows=inspect_shapefile(path)
            self.assertEqual(meta["record_count"],2); self.assertEqual(meta["geometry_type"],"POLYGON")
            self.assertEqual(meta["id_field"],"Dune_ID"); self.assertEqual(meta["unique_id_count"],2)
            self.assertIn("Mars 2000",meta["crs_wkt"]); self.assertEqual(len(rows),2)

if __name__=="__main__": unittest.main()