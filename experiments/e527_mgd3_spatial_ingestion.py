from __future__ import annotations

import argparse, csv, hashlib, html.parser, io, json, math, re, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

SOURCE_PAGE = "https://pubs.usgs.gov/of/2007/1158/"
SOURCE_DOI = "10.3133/ofr20071158"
USER_AGENT = "NASA-Analog-Research/0.1 (public USGS MGD3 provenance ingestion)"
MAX_SHAPEFILES_BYTES = 100 * 1024 * 1024
MAX_TABLES_BYTES = 5 * 1024 * 1024

class _Links(html.parser.HTMLParser):
    def __init__(self): super().__init__(); self.items=[]; self.href=None; self.parts=[]
    def handle_starttag(self, tag, attrs):
        if tag.lower()=="a": self.href=dict(attrs).get("href"); self.parts=[]
    def handle_data(self, data):
        if self.href is not None: self.parts.append(data)
    def handle_endtag(self, tag):
        if tag.lower()=="a" and self.href is not None:
            self.items.append((self.href," ".join(" ".join(self.parts).split()))); self.href=None; self.parts=[]

def sha256(data: bytes) -> str: return hashlib.sha256(data).hexdigest()

def safe_url(url: str) -> bool:
    p=urllib.parse.urlparse(url)
    return p.scheme=="https" and p.hostname=="pubs.usgs.gov" and p.path.startswith("/of/2007/1158/")

def discover_downloads(page: str) -> dict[str,str]:
    parser=_Links(); parser.feed(page); found={}
    for href,_ in parser.items:
        name=PurePosixPath(urllib.parse.urlparse(href).path).name.lower()
        if name in {"shapefiles.zip","tables.zip"}:
            url=urllib.parse.urljoin(SOURCE_PAGE,href)
            if safe_url(url): found[name]=url
    for name in ("shapefiles.zip","tables.zip"):
        found.setdefault(name,urllib.parse.urljoin(SOURCE_PAGE,name))
    return found

def fetch_zip(url: str, limit: int) -> tuple[bytes,dict[str,str],str]:
    if not safe_url(url): raise ValueError(f"non-canonical USGS URL: {url}")
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/zip, */*"})
    with urllib.request.urlopen(req,timeout=120) as response:
        final=response.geturl()
        if not safe_url(final): raise ValueError(f"redirect outside USGS report path: {final}")
        length=response.headers.get("Content-Length")
        if length and int(length)>limit: raise ValueError(f"archive exceeds byte limit: {length}")
        chunks=[]; total=0
        while True:
            chunk=response.read(1024*1024)
            if not chunk: break
            total+=len(chunk)
            if total>limit: raise ValueError(f"archive exceeded byte limit: {total}")
            chunks.append(chunk)
        data=b"".join(chunks); headers={k.lower():v for k,v in response.headers.items()}
    if not data.startswith(b"PK\x03\x04"): raise ValueError(f"not a ZIP archive: {url}")
    return data,headers,final

def member_path(name: str) -> PurePosixPath:
    p=PurePosixPath(name.replace("\\","/"))
    if p.is_absolute() or ".." in p.parts or not p.parts: raise ValueError(f"unsafe ZIP path: {name!r}")
    return p

def core_shapefile(names: list[str]) -> str:
    candidates=[]
    for name in names:
        p=member_path(name)
        if p.suffix.lower()==".shp" and "dune" in p.stem.lower() and "field" in p.stem.lower(): candidates.append(name)
    if not candidates: raise ValueError("Dune_Field shapefile not found")
    return sorted(candidates,key=lambda n:(PurePosixPath(n).stem.lower()!="dune_field",len(n),n))[0]

def _extract_layer(archive: zipfile.ZipFile, shp_name: str, out: Path) -> Path:
    shp=member_path(shp_name); stem=str(shp.with_suffix("")); parts={}
    for name in archive.namelist():
        p=member_path(name)
        if str(p.with_suffix(""))==stem: parts[p.suffix.lower()]=name
    missing={".shp",".shx",".dbf"}-set(parts)
    if missing: raise ValueError(f"missing shapefile components: {sorted(missing)}")
    for suffix in (".shp",".shx",".dbf",".prj",".cpg"):
        if suffix in parts:
            p=member_path(parts[suffix]); target=out.joinpath(*p.parts); target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(archive.read(parts[suffix]))
    return out.joinpath(*shp.parts)

def _norm_id(value: Any) -> str | None:
    if value is None: return None
    s=str(value).strip()
    if not s or s.lower() in {"nan","none","null","na"}: return None
    if re.fullmatch(r"\d+\.0+",s): s=s.split(".",1)[0]
    return s

def _id_field(fields: list[str]) -> str | None:
    hits=[f for f in fields if re.sub(r"[^a-z0-9]","",f.lower()) in {"duneid","dunefieldid","dfid"}]
    if not hits: hits=[f for f in fields if "dune" in f.lower() and "id" in f.lower()]
    return hits[0] if len(hits)==1 else None

def inspect_shapefile(path: Path) -> tuple[dict[str,Any],list[dict[str,Any]]]:
    import shapefile
    reader=shapefile.Reader(str(path),encoding="utf-8",encodingErrors="replace")
    try:
        specs=reader.fields[1:]; fields=[str(s[0]) for s in specs]
        records=list(reader.iterRecords()); shapes=list(reader.iterShapes())
        if not records or len(records)!=len(shapes) or len(records)!=reader.numRecords: raise ValueError("empty or inconsistent shapefile records/geometries")
        idf=_id_field(fields); ids=[]
        if idf:
            idx=fields.index(idf); ids=[_norm_id(r[idx]) for r in records]; ids=[v for v in ids if v is not None]
        prj=path.with_suffix(".prj"); cpg=path.with_suffix(".cpg")
        crs=prj.read_text(encoding="utf-8",errors="replace").strip() if prj.exists() else None
        bbox=list(reader.bbox) if reader.bbox else None
        if bbox and not all(math.isfinite(float(v)) for v in bbox): raise ValueError("non-finite shapefile bounds")
        sample=[{f: (None if r[i] is None else str(r[i])) for i,f in enumerate(fields)} for r in records[:5]]
        meta={"record_count":len(records),"geometry_count":len(shapes),"geometry_type":reader.shapeTypeName,
              "fields":[{"name":s[0],"type":s[1],"width":s[2],"decimals":s[3]} for s in specs],
              "id_field":idf,"nonempty_id_count":len(ids),"unique_id_count":len(set(ids)),
              "duplicate_id_count":len(ids)-len(set(ids)),"sample_ids":ids[:10],"crs_wkt":crs,
              "encoding":cpg.read_text(encoding="ascii",errors="replace").strip() if cpg.exists() else None,
              "bbox_native_coordinates":bbox,"sample_records":sample}
        rows=[{f: (None if r[i] is None else str(r[i])) for i,f in enumerate(fields)} for r in records]
        return meta,rows
    finally: reader.close()

def inspect_tables(payload: bytes) -> dict[str,Any]:
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        bad=z.testzip()
        if bad: raise ValueError(f"Tables.zip CRC failure: {bad}")
        entries=[{"name":str(member_path(n)),"size":z.getinfo(n).file_size} for n in z.namelist()]
        candidates=[]
        for name in z.namelist():
            if PurePosixPath(name).suffix.lower() not in {".txt",".tab",".tsv",".csv"}: continue
            raw=z.read(name)
            try: text=raw.decode("utf-8-sig")
            except UnicodeDecodeError: continue
            sample=text.splitlines()[:2]
            if not sample: continue
            delim="\t" if "\t" in sample[0] else ","
            reader=csv.reader(io.StringIO(text),delimiter=delim)
            raw_header=next(reader,None)
            if not raw_header: continue
            fields=[str(f).strip() for f in raw_header]
            rows=[row for row in reader if row and any(cell.strip() for cell in row)]
            idf=_id_field(fields)
            id_index=fields.index(idf) if idf else None
            ids=[_norm_id(row[id_index] if id_index < len(row) else None) for row in rows] if id_index is not None else []
            ids=[v for v in ids if v is not None]
            candidates.append({"name":name,"delimiter":"tab" if delim=="\t" else "comma","rows":len(rows),"fields":fields,"id_field":idf,"nonempty_id_count":len(ids),"unique_id_count":len(set(ids)),"ids":ids,"rows_data":rows})
        best=sorted(candidates,key=lambda c:(c["id_field"] is not None,c["rows"],len(c["fields"])),reverse=True)[0] if candidates else None
        return {"entries":entries,"tabular_candidates":[{k:v for k,v in c.items() if k not in {"ids","rows_data"}} for c in candidates],"best_table":best}

def build_receipt(out: Path) -> dict[str,Any]:
    page_error=None; page_html=""
    try:
        req=urllib.request.Request(SOURCE_PAGE,headers={"User-Agent":USER_AGENT})
        with urllib.request.urlopen(req,timeout=45) as response:
            page_html=response.read(5*1024*1024+1).decode("utf-8",errors="replace")
            if len(page_html)>5*1024*1024: raise ValueError("USGS page exceeds 5 MiB")
    except Exception as exc: page_error=f"{type(exc).__name__}: {exc}"
    urls=discover_downloads(page_html)
    receipt={"schema_version":"mgd3-2007-spatial-ingestion-v1","experiment":"E527_MGD3_2007_SPATIAL_INGESTION",
             "retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
             "source":{"report_url":SOURCE_PAGE,"doi":SOURCE_DOI,"publisher":"U.S. Geological Survey"},
             "page_access":{"status":"FETCHED" if page_html else "FAILED","error":page_error},"archive_urls":urls,"status":"FAILED"}
    shp_payload,shp_headers,shp_final=fetch_zip(urls["shapefiles.zip"],MAX_SHAPEFILES_BYTES)
    receipt["shapefiles_archive"]={"url":urls["shapefiles.zip"],"final_url":shp_final,"bytes":len(shp_payload),"sha256":sha256(shp_payload),"content_type":shp_headers.get("content-type")}
    with zipfile.ZipFile(io.BytesIO(shp_payload)) as z:
        bad=z.testzip()
        if bad: raise ValueError(f"Shapefiles.zip CRC failure: {bad}")
        shp_name=core_shapefile(z.namelist())
        with __import__("tempfile").TemporaryDirectory(prefix="e527-") as tmp:
            shp_path=_extract_layer(z,shp_name,Path(tmp)); layer,rows=inspect_shapefile(shp_path)
            csv_path=out/"mgd3_2007_dune_fields.csv"; csv_path.parent.mkdir(parents=True,exist_ok=True)
            with csv_path.open("w",encoding="utf-8",newline="") as f:
                writer=csv.DictWriter(f,fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    receipt["core_layer"]={"archive_member":shp_name,**layer}
    receipt["normalized_attribute_table"]={"path":csv_path.name,"rows":len(rows),"fields":list(rows[0])}
    try:
        tab_payload,tab_headers,tab_final=fetch_zip(urls["tables.zip"],MAX_TABLES_BYTES)
        tab=inspect_tables(tab_payload); best=tab["best_table"]
        receipt["tables_archive"]={"url":urls["tables.zip"],"final_url":tab_final,"bytes":len(tab_payload),"sha256":sha256(tab_payload),"content_type":tab_headers.get("content-type"),"entries":tab["entries"],"tabular_candidates":tab["tabular_candidates"]}
        if best:
            idf=layer["id_field"]; shp_ids=set()
            if idf: shp_ids={_norm_id(row.get(idf)) for row in rows}; shp_ids.discard(None)
            table_ids=set(best["ids"])
            receipt["same_release_table_join"]={"table_file":best["name"],"table_id_field":best["id_field"],"table_rows":best["rows"],"table_unique_ids":best["unique_id_count"],"shapefile_id_field":idf,"shapefile_unique_ids":len(shp_ids),"matched_ids":len(shp_ids & table_ids),"shapefile_only_ids":len(shp_ids-table_ids),"table_only_ids":len(table_ids-shp_ids)}
        else: receipt["same_release_table_join"]={"status":"NO_TABULAR_ID_CANDIDATE"}
    except Exception as exc: receipt["tables_archive"]={"status":"FAILED","error":f"{type(exc).__name__}: {exc}"}
    receipt["status"]="INGESTED" if layer["record_count"]>0 and layer["geometry_type"].startswith("POLYGON") else "REJECTED_UNEXPECTED_GEOMETRY"
    receipt["join_gate"]={"status":"READY_FOR_2018_ID_JOIN" if layer["id_field"] and layer["unique_id_count"]==layer["record_count"] else "ID_JOIN_NOT_READY","id_field":layer["id_field"],"records":layer["record_count"],"unique_ids":layer["unique_id_count"],"duplicate_ids":layer["duplicate_id_count"],"2018_workbook_join":"NOT RUN: requires source-pinned 2018 workbook records in this execution."}
    receipt["coverage_caveat"]="The 2007 MGD3 inventory is not exhaustive; absence of a polygon is not a non-analogue label. THEMIS 100 m/pixel support is not automatically the support of MOLA elevation, polygon area or orientation."
    return receipt

def main() -> int:
    p=argparse.ArgumentParser(); p.add_argument("--out",type=Path,required=True); a=p.parse_args(); a.out.mkdir(parents=True,exist_ok=True)
    path=a.out/"mgd3_2007_spatial_receipt.json"
    try:
        r=build_receipt(a.out); path.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps({"status":r["status"],"sha256":r["shapefiles_archive"]["sha256"],"records":r["core_layer"]["record_count"],"geometry":r["core_layer"]["geometry_type"],"id_field":r["core_layer"]["id_field"],"join_gate":r["join_gate"]["status"]},sort_keys=True))
        return 0 if r["status"]=="INGESTED" else 1
    except Exception as exc:
        r={"schema_version":"mgd3-2007-spatial-ingestion-v1","experiment":"E527_MGD3_2007_SPATIAL_INGESTION","retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"source":{"report_url":SOURCE_PAGE,"doi":SOURCE_DOI},"status":"FAILED","error_type":type(exc).__name__,"error":str(exc),"claim_boundary":"No ingestion is claimed when retrieval or parsing fails."}
        path.write_text(json.dumps(r,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(r,indent=2,sort_keys=True)); return 1

if __name__=="__main__": raise SystemExit(main())