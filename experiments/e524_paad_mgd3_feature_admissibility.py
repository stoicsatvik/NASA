from __future__ import annotations
import argparse, csv, hashlib, json
from io import StringIO
from pathlib import Path

PAAD_SHA256 = "0eb40273f9f685e4fd67181c63fa51e24e2fa348cc850cb1641d5e43af221334"
MGD3_SHA256 = "92771c23cfa4a64dfcc38f5ad29de00adfa41b9f321d3665beb2112eefe3485e"
THERMAL = "Average Bolometer nighttime thermal inertia (tiu)"
ALBEDO = "Average Daytime Albedo"
MINERALS = ("Feldspar", "High-Silica Phases", "Olivine", "Pyroxene", "Sulfate", "Carbonate", "Quartz", "Hematite ")

FEATURES = [
 {"descriptor":"dune morphology","earth_fields":["Dune_Type"],"mars_fields":["Stablity Index (SI) Fenton and Hayward (2010) Dune Classification"],"status":"NOT_ADMISSIBLE_CODEBOOK_UNVERIFIED"},
 {"descriptor":"mineral composition","earth_fields":["Composition_of_Sand"],"mars_fields":list(MINERALS),"status":"NOT_ADMISSIBLE_NARRATIVE_VS_ABUNDANCE"},
 {"descriptor":"thermal inertia","earth_fields":[],"mars_fields":[THERMAL],"status":"EARTH_SIDE_MISSING"},
 {"descriptor":"surface albedo","earth_fields":[],"mars_fields":[ALBEDO],"status":"EARTH_SIDE_MISSING"},
 {"descriptor":"elevation","earth_fields":["Elevation"],"mars_fields":[],"status":"MARS_SIDE_MISSING_IN_2018_SUMMARY"},
 {"descriptor":"areal extent","earth_fields":["Areal_Coverage"],"mars_fields":["Rank (by area)"],"status":"NOT_ADMISSIBLE_DIFFERENT_MEANING_IN_2018_SUMMARY"},
 {"descriptor":"climate","earth_fields":["Köppen_Geiger_Climate_Classification"],"mars_fields":[],"status":"MARS_SIDE_MISSING_IN_2018_SUMMARY"},
 {"descriptor":"site coordinates","earth_fields":["Center_Latitude","Center_Longitude"],"mars_fields":[],"status":"MARS_COORDINATES_NOT_IN_2018_SUMMARY"},
 {"descriptor":"sand source","earth_fields":["Sand_Source"],"mars_fields":[],"status":"MARS_SIDE_MISSING_IN_2018_SUMMARY"},
]

def _missing(value):
    return value is None or not str(value).strip() or str(value).strip().lower() in {"na","n/a","nan","null","none"}

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def audit_paad(data: bytes) -> dict:
    reader = csv.DictReader(StringIO(data.decode("utf-8-sig")))
    rows = list(reader)
    required = {"Field_Site","Center_Latitude","Center_Longitude","Dune_Type","Sand_Source","Composition_of_Sand","Elevation","Areal_Coverage","Köppen_Geiger_Climate_Classification"}
    if not required.issubset(set(reader.fieldnames or [])):
        raise ValueError("PAAD schema missing required source fields")
    names = [row["Field_Site"].strip() for row in rows]
    if len(names) != len(set(names)):
        raise ValueError("duplicate PAAD Field_Site values")
    coords = [(r["Center_Latitude"].strip(),r["Center_Longitude"].strip()) for r in rows
              if not _missing(r["Center_Latitude"]) and not _missing(r["Center_Longitude"])]
    missing = {f:sum(_missing(r[f]) for r in rows)
               for f in sorted(required-{"Field_Site","Center_Latitude","Center_Longitude","Dune_Type"})}
    return {
        "rows":len(rows),"unique_site_names":len(set(names)),
        "unique_coordinate_pairs":len(set(coords)),"coordinate_pairs_present":len(coords),
        "missing_counts":missing,"source_fields":list(reader.fieldnames or []),
        "dune_type_unique_raw_tokens":sorted({t.strip() for r in rows for t in r["Dune_Type"].split(",") if t.strip()}),
        "climate_values_are_raw_source_text":True,
    }

def audit_mgd3(data: bytes) -> dict:
    receipt=json.loads(data.decode())
    hashes=[]; tables=[]
    for item in receipt.get("file_receipts",[]):
        if item.get("status")=="DOWNLOADED" and item.get("sha256"):
            hashes.append(item["sha256"])
        for table in item.get("tables",[]):
            if "Global Summary" in table.get("file",""):
                tables.append(table)
    if not tables:
        raise ValueError("no MGD3 global-summary profiles in receipt")
    summaries=[]
    for table in tables:
        fields=table.get("nonempty_by_field",{})
        summaries.append({
            "worksheet":table["file"],
            "worksheet_rows_not_unique_sites":table.get("rows"),
            "dune_id_nonempty":fields.get("Dune ID ",0),
            "thermal_inertia_nonempty":fields.get(THERMAL,0),
            "albedo_nonempty":fields.get(ALBEDO,0),
            "mineral_field_nonempty":{field:fields.get(field,0) for field in MINERALS},
        })
    has_geometry=any(any(token in col.lower() for token in ("latitude","longitude","coordinate","footprint"))
                     for table in tables for col in table.get("columns",[]))
    return {"archive_sha256s":hashes,"global_summary_profiles":summaries,
            "worksheet_rows_are_not_unique_sites":True,"coordinate_or_footprint_fields_present":has_geometry}

def build_report(paad: bytes, mgd3: bytes, verify_hashes: bool=True) -> dict:
    paad_hash=_sha(paad); mars=audit_mgd3(mgd3)
    if verify_hashes and paad_hash != PAAD_SHA256:
        raise ValueError("PAAD normalized CSV SHA-256 mismatch")
    if verify_hashes and MGD3_SHA256 not in mars["archive_sha256s"]:
        raise ValueError("MGD3 archive SHA-256 mismatch")
    earth=audit_paad(paad)
    return {
        "experiment":"E524_PAAD_MGD3_FEATURE_ADMISSIBILITY",
        "status":"WORKBOOK_ONLY_NO_DIRECT_SHARED_DESCRIPTOR_ADMITTED",
        "source_receipts":{"paad_normalized_csv_sha256":paad_hash,"mgd3_archive_sha256":MGD3_SHA256 if MGD3_SHA256 in mars["archive_sha256s"] else mars["archive_sha256s"]},
        "paad":earth,"mgd3":mars,"feature_admissibility":FEATURES,
        "directly_comparable_descriptor_count":0,
        "negative_label_status":"NO_INDEPENDENT_NON_ANALOGUE_LABELS",
        "e001_known_site_recovery":"NOT YET MEASURED",
        "cross_body_similarity":"NOT YET PROVEN",
        "spatial_source_discovery":{
            "status":"DOCUMENTED_NOT_INGESTED",
            "source":"USGS Open-File Report 2007-1158 / Mars Global Digital Dune Database",
            "url":"https://pubs.usgs.gov/of/2007/1158/",
            "documented_features":["approximately 550 dune-field polygons","37-column attribute table","dune type","area and volume","MOLA-based average elevation","dune orientation","THEMIS infrared imagery at 100 m/pixel"],
            "coverage_caveat":"The mapped inventory is not exhaustive; small dune fields and areas without sufficient coverage are omitted. Absence from this database is not a non-analogue label.",
            "status_boundary":"Source schema is documented, not ingested or joined to the 2018 workbook.",
        },
        "interpretation":"The current PAAD CSV plus the profiled 2018 MGD3 workbook summaries provide zero directly comparable physical descriptors. This is a workbook-only result, not a conclusion about all MGD3 data: an official 2007 spatial release documents polygons, area, MOLA elevation, dune type and orientation, but that release is not yet ingested. No distance metric or E001 ranking is admissible until its geometry/attributes are ingested and joined.",
    }

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--paad",type=Path,required=True)
    parser.add_argument("--mgd3-receipt",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=build_report(args.paad.read_bytes(),args.mgd3_receipt.read_bytes())
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"status":result["status"],"paad_rows":result["paad"]["rows"],
        "mgd3_global_summary_profiles":len(result["mgd3"]["global_summary_profiles"]),
        "directly_comparable_descriptor_count":0,"e001_known_site_recovery":result["e001_known_site_recovery"]},sort_keys=True))

if __name__=="__main__":
    main()
