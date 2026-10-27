"""E326: independently published USGS terrestrial analogue inventory ingestion.

Read-only public 2020 Hunter catalog, not a Mars/Moon paired validation set.
Never infer negatives from unlisted sites or cross-body matches from type names.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from zipfile import ZipFile, BadZipFile

ITEM_ID = "5f88940b82cebb8c13d912ee"
DOI = "10.5066/P9J72921"
META = f"https://www.sciencebase.gov/catalog/item/{ITEM_ID}?format=json"
MAX_METADATA = 2_000_000
MAX_FILE = 30_000_000
MAX_TOTAL = 50_000_000
MAX_MEMBER = 12_000_000
MAX_ROWS = 200_000
MAX_FILES = 16


def permitted_download(url: str) -> bool:
    p = urlsplit(url)
    return (p.scheme == "https" and p.hostname in ("www.sciencebase.gov", "sciencebase.gov")
            and p.path.startswith("/catalog/file/get/") and not p.username
            and not p.password)


def read_bounded(url: str, maximum: int) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": "NASA-E326-Source-Audit/1.0"}),
                 timeout=45) as response:
        if urlsplit(response.geturl()).hostname not in ("www.sciencebase.gov", "sciencebase.gov"):
            raise ValueError("unapproved redirect host")
        data = response.read(maximum + 1)
    if len(data) > maximum:
        raise ValueError("download size limit exceeded")
    return data


def metadata_files(item: dict) -> list[dict]:
    if item.get("id") != ITEM_ID or "Known Terrestrial Analog Sites" not in item.get("title", ""):
        raise ValueError("source identity/title mismatch")
    out = []
    for f in item.get("files", [])[:MAX_FILES]:
        uri = f.get("downloadUri", "")
        out.append({
            "name": f.get("name", ""),
            "declared_bytes": f.get("size"),
            "permitted": permitted_download(uri),
            "url": uri if permitted_download(uri) else None,
        })
    return out


def profile_records(rows: list[dict], kind: str, name: str) -> dict:
    if len(rows) > MAX_ROWS:
        raise ValueError("row limit exceeded")
    keys = sorted(set().union(*(r.keys() for r in rows))) if rows else []
    class_fields = {}
    for key in keys:
        if re.search(r"analog|analogue|process|feature|type|categor|target|planet|class", key, re.I):
            counts = Counter(str(r.get(key, "")).strip() for r in rows)
            class_fields[key] = dict(sorted(counts.items(), key=lambda x: (-x[1], x[0]))[:20])
    return {
        "file": name, "format": kind, "rows": len(rows),
        "columns": keys[:100], "candidate_class_fields": class_fields,
        "coordinates_validated": False,
        "note": "Attributes alone do not establish coordinate reference, analogue semantics or negative labels",
    }


def profile_csv(raw: bytes, name: str) -> dict:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    if not reader.fieldnames or len(reader.fieldnames) > 150:
        raise ValueError("invalid CSV schema")
    rows = []
    for row in reader:
        if len(rows) >= MAX_ROWS:
            raise ValueError("row limit exceeded")
        rows.append(row)
    return profile_records(rows, "csv", name)


def profile_geojson(raw: bytes, name: str) -> dict:
    obj = json.loads(raw)
    if obj.get("type") != "FeatureCollection":
        raise ValueError("not a GeoJSON feature collection")
    features = obj.get("features", [])
    if len(features) > MAX_ROWS:
        raise ValueError("row limit exceeded")
    result = profile_records([f.get("properties") or {} for f in features], "geojson", name)
    result["geometry_types"] = dict(Counter(
        (f.get("geometry") or {}).get("type", "NULL") for f in features))
    result["coordinates_validated"] = False
    result["coordinate_reference"] = "GeoJSON standard presumed, not independently verified"
    return result


def profile_zip(raw: bytes, name: str) -> list[dict]:
    out = []
    with ZipFile(io.BytesIO(raw)) as z:
        entries = {n.filename.lower(): n for n in z.infolist() if not n.is_dir()}
        for entry in z.infolist():
            if entry.is_dir():
                continue
            low = entry.filename.lower()
            if not low.endswith((".csv", ".geojson", ".dbf")):
                continue
            if entry.file_size > MAX_MEMBER:
                out.append({"file": entry.filename, "status": "OVERSIZED_MEMBER"})
                continue
            data = z.read(entry)
            if len(data) > MAX_MEMBER:
                raise ValueError("expanded member too large")
            try:
                if low.endswith(".csv"):
                    out.append(profile_csv(data, entry.filename))
                elif low.endswith(".geojson"):
                    out.append(profile_geojson(data, entry.filename))
                else:
                    import shapefile
                    reader = shapefile.Reader(dbf=io.BytesIO(data), encoding="utf-8",
                                              encodingErrors="replace")
                    if len(reader) > MAX_ROWS:
                        raise ValueError("DBF row limit exceeded")
                    fields = [f[0] for f in reader.fields[1:]]
                    rows = [dict(zip(fields, list(rec))) for rec in reader.records()]
                    result = profile_records(rows, "shapefile_dbf", entry.filename)
                    base = low[:-4]
                    result["geometry_members_present"] = {
                        ext: base + ext in entries for ext in (".shp", ".shx", ".prj")
                    }
                    if base + ".prj" in entries:
                        prj = z.read(entries[base + ".prj"]).decode("utf-8", "replace")
                        result["projection_text_sha256"] = hashlib.sha256(prj.encode()).hexdigest()
                        result["projection_wgs84_text_hint"] = ("WGS_1984" in prj or "WGS 84" in prj)
                    out.append(result)
            except (ValueError, UnicodeError, ImportError, json.JSONDecodeError) as exc:
                out.append({"file": entry.filename, "status": "PARSE_FAILED",
                            "error_type": type(exc).__name__})
    return out


def audit(item: dict, downloader=read_bounded) -> dict:
    files = metadata_files(item)
    profiles = []
    spent = 0
    for f in files:
        uri, name, size = f["url"], f["name"], f["declared_bytes"]
        if not uri or not name.lower().endswith((".zip", ".csv", ".geojson", ".json")):
            continue
        if isinstance(size, int) and size > MAX_FILE:
            profiles.append({"file": name, "status": "DECLARED_OVERSIZED"})
            continue
        if spent >= MAX_TOTAL:
            profiles.append({"file": name, "status": "TOTAL_BUDGET_EXHAUSTED"})
            continue
        try:
            raw = downloader(uri, min(MAX_FILE, MAX_TOTAL - spent))
            spent += len(raw)
            if name.lower().endswith(".zip"):
                tables = profile_zip(raw, name)
            elif name.lower().endswith(".csv"):
                tables = [profile_csv(raw, name)]
            elif name.lower().endswith((".geojson", ".json")):
                tables = [profile_geojson(raw, name)]
            else:
                tables = []
            profiles.append({"file": name, "sha256": hashlib.sha256(raw).hexdigest(),
                             "bytes": len(raw), "tables": tables})
        except (OSError, ValueError, BadZipFile, UnicodeError) as exc:
            profiles.append({"file": name, "status": "DOWNLOAD_OR_PARSE_FAILED",
                             "error_type": type(exc).__name__})
    records = sum(t.get("rows", 0) for p in profiles for t in p.get("tables", []))
    return {
        "experiment": "E326_INDEPENDENT_USGS_TERRESTRIAL_ANALOG_INVENTORY",
        "source_doi": DOI, "source_item": ITEM_ID,
        "source_title": item["title"],
        "metadata_keys": sorted(item),
        "metadata_web_links": [{"title": str(w.get("title", ""))[:120],
                                 "uri": str(w.get("uri", ""))[:300]}
                                for w in item.get("webLinks", [])[:20]],
        "metadata_facets": [str(f.get("name", f.get("className", "")))[:100]
                            for f in item.get("facets", [])[:20]],
        "has_children": item.get("hasChildren"),
        "declared_files": [{k: v for k, v in f.items() if k != "url"} for f in files],
        "download_profiles": profiles, "tabular_rows_profiled": records,
        "status": "TABULAR_SOURCE_INGESTED" if records else "NO_TABULAR_RECORDS_INGESTED",
        "e001_known_site_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
        "limitations": [
            "This 2020 USGS inventory and 2023 PAAD share a publisher; statistical independence is not guaranteed.",
            "Cataloged analog sites are positives for diverse purposes, not matched Mars/Moon pairs.",
            "Unlisted locations cannot be labeled non-analog negatives.",
            "Field labels and coordinate reference require source-codebook validation.",
            "No Earth-Mars similarity or held-out recovery performed.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    meta_raw = read_bounded(META, MAX_METADATA)
    item = json.loads(meta_raw)
    result = audit(item)
    result["metadata_sha256"] = hashlib.sha256(meta_raw).hexdigest()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "source": DOI,
                      "rows": result["tabular_rows_profiled"],
                      "profiles": result["download_profiles"],
                      "metadata_keys": result["metadata_keys"],
                      "web_links": result["metadata_web_links"],
                      "facets": result["metadata_facets"],
                      "has_children": result["has_children"]}, sort_keys=True))


if __name__ == "__main__":
    main()
