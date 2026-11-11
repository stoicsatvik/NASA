"""E560: bounded public acquisition of the USGS known-analogue point layer."""
from __future__ import annotations
import csv, hashlib, io, json, re, urllib.error, urllib.parse, urllib.request, zipfile, xml.etree.ElementTree as ET
from pathlib import Path

ITEM_ID="5f88940b82cebb8c13d912ee"
DOI="10.5066/P9J72921"
METADATA_URL=f"https://www.sciencebase.gov/catalog/item/{ITEM_ID}?format=json"
MAX_META=2_000_000
MAX_FILE=25_000_000
MAX_UNPACKED=100_000_000
OUT=Path(".artifacts/e560")
SB={"www.sciencebase.gov","sciencebase.gov","sciencebase.usgs.gov"}
PAAD=(Path("research/E533_CANDIDATE_LABEL_SOURCE_REVIEW_20261111.csv"),Path("research/E534_REMAINING_CANDIDATE_SOURCE_REVIEW_20261111.csv"))
LE=Path("research/E558_PUBLIC_ANALOGUE_CATALOGUE_AUDIT_20261111.md")
AE=Path("data/nasa_analog_explorer_pairs.csv")

def allowed_host(host):
    return host in SB or host=="s3.amazonaws.com" or host.endswith(".s3.amazonaws.com") or host=="s3.us-west-2.amazonaws.com" or host.endswith(".s3.us-west-2.amazonaws.com")

def safe_metadata_url(url):
    p=urllib.parse.urlsplit(url)
    return p.scheme=="https" and p.hostname in SB and p.path==f"/catalog/item/{ITEM_ID}" and p.port in (None,443) and not p.username and not p.password and not p.fragment and urllib.parse.parse_qs(p.query)=={"format":["json"]}

def safe_file_url(url):
    p=urllib.parse.urlsplit(url)
    return p.scheme=="https" and allowed_host(p.hostname) and p.port in (None,443) and not p.username and not p.password and not p.fragment

def bounded_get(url, cap, metadata=False):
    if metadata and not safe_metadata_url(url): raise ValueError("metadata URL failed exact allowlist")
    if not metadata and not safe_file_url(url): raise ValueError("file URL failed HTTPS host allowlist")
    req=urllib.request.Request(url,headers={"User-Agent":"NASA-E560-USGS-catalogue/1.0","Accept":"application/json" if metadata else "application/octet-stream, application/zip, application/geo+json, application/json"})
    with urllib.request.urlopen(req,timeout=25) as r:
        final=urllib.parse.urlsplit(r.geturl())
        if final.scheme!="https" or not allowed_host(final.hostname) or (metadata and final.hostname not in SB) or final.port not in (None,443) or final.username or final.password or final.fragment:
            raise ValueError("redirect left the ScienceBase/S3 HTTPS allowlist")
        length=r.headers.get("Content-Length")
        if length and int(length)>cap: raise ValueError("declared response exceeds byte cap")
        data=r.read(cap+1)
        if len(data)>cap: raise ValueError("response stream exceeds byte cap")
        return {"status":r.status,"host":final.hostname,"content_type":r.headers.get_content_type(),"content_length":length,"bytes":data}

def metadata_files(doc):
    raw=doc.get("files")
    if not isinstance(raw,list): raw=doc.get("file")
    if not isinstance(raw,list): return []
    out=[]
    for f in raw:
        if not isinstance(f,dict): continue
        name=f.get("name") or f.get("fileName") or f.get("filename")
        url=f.get("url") or f.get("downloadUri") or f.get("downloadUrl") or f.get("downloadURL") or f.get("fileUrl")
        size=f.get("size") or f.get("sizeBytes") or f.get("fileSize")
        try: size=int(size) if size is not None else None
        except (TypeError,ValueError): size=None
        out.append({"name":str(name) if name else None,"url":str(url) if url else None,"size_bytes":size,"checksum":f.get("checksum") or f.get("md5") or f.get("sha256")})
    return out



def xml_urls(payload):
    root=ET.fromstring(payload)
    found=set()
    for node in root.iter():
        local=str(node.tag).split("}")[-1].lower()
        if local not in {"onlink","linkage","networkr","networka","url"} or not node.text:
            continue
        for value in re.findall(r"https?://\S+",node.text.strip()):
            found.add(value.rstrip(".,);]"))
    return sorted(found)

def vector_url_candidates(urls):
    allowed={".zip",".geojson",".json",".gpkg",".shp",".kml"}
    result=[]
    for url in urls:
        if not safe_file_url(url):
            continue
        parsed=urllib.parse.urlsplit(url)
        filename=Path(parsed.path).name
        for values in urllib.parse.parse_qs(parsed.query).values():
            for value in values:
                if Path(value).suffix.lower() in allowed:
                    filename=Path(value).name
        if Path(filename).suffix.lower() in allowed:
            result.append({"name":filename,"url":url,"size_bytes":None,"checksum":None})
    return result

def normalise(s):
    return re.sub(r"[^a-z0-9]+","",s.casefold())

def local_catalogues():
    paad=set()
    for path in PAAD:
        if path.exists():
            with path.open(newline="",encoding="utf-8") as h:
                for row in csv.DictReader(h):
                    for key in ("site_id","source_title"):
                        if row.get(key): paad.add(row[key].strip())
    le=set()
    if LE.exists():
        inside=False
        for line in LE.read_text(encoding="utf-8").splitlines():
            if line.startswith("| Site |"): inside=True; continue
            if inside and not line.startswith("|"): break
            if inside and line.startswith("|") and "---" not in line:
                cells=[x.strip() for x in line.strip("|").split("|")]
                if cells and cells[0] and cells[0]!="Site": le.add(cells[0])
    ae=set()
    if AE.exists():
        with AE.open(newline="",encoding="utf-8") as h:
            for row in csv.DictReader(h):
                for key in ("earth_site","earth_region"):
                    if row.get(key): ae.add(row[key].strip())
    return {"PAAD":paad,"LeCussan16":le,"NASAAnalogExplorer":ae}

def overlap(source_names,catalogues):
    norm={normalise(x):x for x in source_names if normalise(x)}
    out={}
    for label,names in catalogues.items():
        out[label]={"exact":sorted(source_names & names),"normalized_full_string":sorted((norm[normalise(x)],x) for x in names if normalise(x) in norm),"meaning":"name-only overlap; not coordinate or feature equivalence"}
    return out

def parse_geojson(data):
    doc=json.loads(data.decode("utf-8"))
    features=doc.get("features")
    if not isinstance(features,list): raise ValueError("GeoJSON FeatureCollection features missing")
    fields=set(); names=set(); geoms=set()
    for f in features:
        if not isinstance(f,dict): continue
        g=f.get("geometry") or {}
        if g.get("type"): geoms.add(str(g["type"]))
        props=f.get("properties") or {}
        if isinstance(props,dict):
            fields.update(map(str,props))
            for k,v in props.items():
                if isinstance(v,str) and any(t in str(k).casefold() for t in ("name","site","local","place")) and v.strip(): names.add(v.strip())
    return {"format":"GeoJSON","feature_count":len(features),"geometry_types":sorted(geoms),"property_fields":sorted(fields),"candidate_name_values":sorted(names),"crs":doc.get("crs") or "RFC7946 default WGS84 if conformant","feature_ids_present":sum(1 for f in features if isinstance(f,dict) and f.get("id") is not None)}

def parse_vector(name,data):
    ext=Path(name).suffix.lower()
    if ext in (".json",".geojson"): return parse_geojson(data)
    if ext!=".zip": raise ValueError("unsupported vector file extension")
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        infos=[x for x in z.infolist() if not x.is_dir()]
        if len(infos)>200 or sum(x.file_size for x in infos)>MAX_UNPACKED: raise ValueError("archive expansion cap exceeded")
        if any(Path(x.filename).is_absolute() or ".." in Path(x.filename).parts for x in infos): raise ValueError("unsafe archive path")
        gj=[x for x in infos if x.filename.lower().endswith((".geojson",".json"))]
        if len(gj)==1:
            result=parse_geojson(z.read(gj[0])); result["archive_member"]=gj[0].filename; return result
        shp=[x for x in infos if x.filename.lower().endswith(".shp")]
        if len(shp)!=1: raise ValueError("archive must contain exactly one shapefile or one GeoJSON")
        stem=shp[0].filename[:-4]
        bylower={x.filename.lower():x for x in infos}
        dbf=bylower.get((stem+".dbf").lower()); shx=bylower.get((stem+".shx").lower()); prj=bylower.get((stem+".prj").lower())
        if not dbf or not shx: raise ValueError("shapefile DBF/SHX missing")
        import shapefile
        reader=shapefile.Reader(shp=io.BytesIO(z.read(shp[0])),shx=io.BytesIO(z.read(shx)),dbf=io.BytesIO(z.read(dbf)))
        fields=[x[0] for x in reader.fields[1:]]
        records=reader.records(); candidates=[x for x in fields if any(t in x.casefold() for t in ("name","site","local","place"))]
        names=set()
        for row in records:
            for key in candidates:
                value=row[fields.index(key)]
                if value is not None and str(value).strip(): names.add(str(value).strip())
        return {"format":"ESRI Shapefile","feature_count":len(records),"geometry_type":shapefile.SHAPETYPE_LOOKUP.get(reader.shapeType,str(reader.shapeType)),"property_fields":fields,"candidate_name_values":sorted(names),"crs":z.read(prj).decode("utf-8","replace") if prj else "MISSING .prj","shp_member":shp[0].filename}

def write_receipt(receipt):
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/"receipt.json").write_text(json.dumps(receipt,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    return receipt

def run_live():
    r={"experiment":"E560","source":{"item_id":ITEM_ID,"doi":DOI,"metadata_url":METADATA_URL},"outcome":"NOT_STARTED","claim_boundary":"Candidate-positive catalogue only; not ground truth or negative controls."}
    try:
        meta=bounded_get(METADATA_URL,MAX_META,metadata=True)
        doc=json.loads(meta["bytes"].decode("utf-8"))
        returned=doc.get("id") or doc.get("itemId") or doc.get("item_id")
        if returned and str(returned).lower()!=ITEM_ID: raise ValueError("ScienceBase returned a different item ID")
        files=metadata_files(doc)
        candidates=[x for x in files if Path(x.get("name") or "").suffix.lower() in {".zip",".geojson",".json",".gpkg",".shp",".kml"}]
        r["metadata"]={"status":meta["status"],"host":meta["host"],"bytes":len(meta["bytes"]),"sha256":hashlib.sha256(meta["bytes"]).hexdigest(),"title":doc.get("title"),"returned_item_id":returned,"file_count":len(files),"files":[{"name":x["name"],"size_bytes":x["size_bytes"],"checksum":x["checksum"],"url_host":urllib.parse.urlsplit(x["url"]).hostname if x["url"] else None,"url_path":urllib.parse.urlsplit(x["url"]).path if x["url"] else None,"url_sha256":hashlib.sha256(x["url"].encode()).hexdigest() if x["url"] else None} for x in files]}
        if not candidates:
            xmls=[x for x in files if (x.get("name") or "").lower().endswith(".xml") and x.get("url")]
            if len(xmls)==1:
                xml_response=bounded_get(xmls[0]["url"],500_000,metadata=False)
                xml_payload=xml_response["bytes"]
                OUT.mkdir(parents=True,exist_ok=True)
                (OUT/"metadata.xml").write_bytes(xml_payload)
                links=xml_urls(xml_payload)
                candidates=vector_url_candidates(links)
                r["metadata_xml"]={"name":xmls[0]["name"],"status":xml_response["status"],"host":xml_response["host"],"bytes":len(xml_payload),"sha256":hashlib.sha256(xml_payload).hexdigest(),"links":[{"host":urllib.parse.urlsplit(x).hostname,"path":urllib.parse.urlsplit(x).path,"url_sha256":hashlib.sha256(x.encode()).hexdigest()} for x in links],"vector_link_count":len(candidates)}
            if not candidates:
                r["outcome"]="METADATA_XML_NO_VECTOR_LINK" if xmls else "METADATA_ONLY_NO_VECTOR_FILE"
                return write_receipt(r)
        if len(candidates)!=1: r["outcome"]="AMBIGUOUS_VECTOR_FILES"; return write_receipt(r)
        f=candidates[0]
        if not f.get("url"): r["outcome"]="VECTOR_FILE_URL_NOT_EXPOSED"; return write_receipt(r)
        if f.get("size_bytes") and f["size_bytes"]>MAX_FILE: r["outcome"]="VECTOR_FILE_EXCEEDS_SIZE_CAP"; return write_receipt(r)
        data=bounded_get(f["url"],MAX_FILE,metadata=False)
        payload=data["bytes"]; OUT.mkdir(parents=True,exist_ok=True); (OUT/"source.bin").write_bytes(payload)
        parsed=parse_vector(f["name"] or "",payload)
        parsed["catalogue_name_overlap"]=overlap(set(parsed.get("candidate_name_values",[])),local_catalogues())
        r["download"]={"status":data["status"],"host":data["host"],"content_type":data["content_type"],"bytes":len(payload),"sha256":hashlib.sha256(payload).hexdigest(),"catalogue_size_bytes":f.get("size_bytes"),"catalogue_size_matches":f.get("size_bytes") is not None and len(payload)==f["size_bytes"]}
        r["vector"]=parsed; r["outcome"]="VECTOR_ACQUIRED_AND_PARSED"
    except urllib.error.HTTPError as e:
        r["outcome"]="HTTP_ERROR"; r["http_status"]=e.code; r["error"]=f"HTTP {e.code}"
    except urllib.error.URLError as e:
        r["outcome"]="NETWORK_ERROR"; r["error"]=f"{type(e.reason).__name__}: {e.reason}"
    except Exception as e:
        r["outcome"]="ERROR"; r["error"]=f"{type(e).__name__}: {e}"
    return write_receipt(r)

if __name__=="__main__":
    result=run_live()
    print(json.dumps(result,indent=2,sort_keys=True))
    if result["outcome"]=="ERROR": raise SystemExit(1)
