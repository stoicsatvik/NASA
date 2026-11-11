"""E560: bounded public acquisition of the USGS known-analogue point layer."""
from __future__ import annotations
import csv, hashlib, io, json, re, urllib.error, urllib.parse, urllib.request, zipfile, xml.etree.ElementTree as ET
from pathlib import Path

ITEM_ID="5f88940b82cebb8c13d912ee"
DOI="10.5066/P9J72921"
EXPECTED_TITLE="Known Terrestrial Analog Sites for Planetary Science"
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

class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def bounded_get(url, cap, metadata=False):
    if metadata and not safe_metadata_url(url): raise ValueError("metadata URL failed exact allowlist")
    if not metadata and not safe_file_url(url): raise ValueError("file URL failed HTTPS host allowlist")
    req=urllib.request.Request(url,headers={"User-Agent":"NASA-E560-USGS-catalogue/1.0","Accept":"application/json" if metadata else "application/octet-stream, application/zip, application/geo+json, application/json"})
    opener=urllib.request.build_opener(NoRedirectHandler)
    with opener.open(req,timeout=25) as r:
        final_url=r.geturl()
        final=urllib.parse.urlsplit(final_url)
        if final_url!=url or (metadata and not safe_metadata_url(final_url)) or (not metadata and not safe_file_url(final_url)):
            raise ValueError("response URL changed outside the exact frozen request")
        if metadata and r.headers.get_content_type()!="application/json":
            raise ValueError("ScienceBase item endpoint did not return application/json")
        length=r.headers.get("Content-Length")
        if length and int(length)>cap: raise ValueError("declared response exceeds byte cap")
        data=r.read(cap+1)
        if len(data)>cap: raise ValueError("response stream exceeds byte cap")
        return {"status":r.status,"host":final.hostname,"content_type":r.headers.get_content_type(),"content_length":length,"bytes":data}

def validate_item_identity(doc):
    if not isinstance(doc,dict):
        raise ValueError("ScienceBase item response must be a JSON object")
    returned=doc.get("id") or doc.get("itemId") or doc.get("item_id")
    if not returned or str(returned).lower()!=ITEM_ID:
        raise ValueError("ScienceBase item ID is missing or does not match the frozen release")
    if doc.get("title")!=EXPECTED_TITLE:
        raise ValueError("ScienceBase item title does not match the frozen release")
    return str(returned).lower()


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
        for value in re.findall(r"https?://[^\s<>\"']+",node.text.strip()):
            found.add(value.rstrip(".,);]"))
    return sorted(found)

def checksum_status(expected, payload):
    if not isinstance(expected,dict):
        return {"status":"NOT_PROVIDED","matches":None}
    kind=str(expected.get("type") or "").upper()
    value=str(expected.get("value") or "").lower()
    if kind=="MD5":
        actual=hashlib.md5(payload).hexdigest()
    elif kind in {"SHA256","SHA-256"}:
        actual=hashlib.sha256(payload).hexdigest()
    else:
        return {"type":kind or None,"expected":value or None,"matches":None,"status":"UNSUPPORTED_CHECKSUM"}
    return {"type":kind,"expected":value,"actual":actual,"matches":actual==value,"status":"MATCH" if actual==value else "MISMATCH"}


def parse_fgdc_metadata(payload):
    root=ET.fromstring(payload)
    def value(path):
        node=root.find(path)
        return node.text.strip() if node is not None and node.text else None
    fields=[]
    analog_types=[]
    for attr in root.findall(".//eainfo/detailed/attr"):
        label=attr.findtext("attrlabl")
        if label:
            fields.append(label.strip())
            if label.strip()=="AnalogType":
                analog_types=sorted({x.text.strip() for x in attr.findall(".//edomv") if x.text and x.text.strip()})
    count=value(".//spdoinfo/ptvctinf/sdtsterm/ptvctcnt")
    accuracy=value(".//dataqual/posacc/horizpa/horizpar")
    match=re.search(r"up to\s+(\d+(?:\.\d+)?)\s*km",accuracy or "",re.IGNORECASE)
    absres=value(".//spref/horizsys/planar/planci/coordrep/absres")
    ordres=value(".//spref/horizsys/planar/planci/coordrep/ordres")
    return {
        "title":value(".//idinfo/citation/citeinfo/title"),
        "author":value(".//idinfo/citation/citeinfo/origin"),
        "publication_date":value(".//idinfo/citation/citeinfo/pubdate"),
        "metadata_date":value(".//metainfo/metd"),
        "purpose":value(".//idinfo/descript/purpose"),
        "analysis_use_allowed":not ("not for analysis" in (value(".//idinfo/descript/purpose") or "").casefold()),
        "progress":value(".//idinfo/status/progress"),
        "update_frequency":value(".//idinfo/status/update"),
        "declared_geometry":value(".//spdoinfo/ptvctinf/sdtsterm/sdtstype"),
        "declared_feature_count":int(count) if count and count.isdigit() else None,
        "horizontal_accuracy_statement":accuracy,
        "maximum_accuracy_error_km":float(match.group(1)) if match else None,
        "completeness_statement":value(".//dataqual/complete"),
        "lineage_process_description":value(".//dataqual/lineage/procstep/procdesc"),
        "lineage_process_date":value(".//dataqual/lineage/procstep/procdate"),
        "projection":value(".//spref/horizsys/planar/mapproj/mapprojn"),
        "horizontal_datum":value(".//spref/horizsys/geodetic/horizdn"),
        "coordinate_units":value(".//spref/horizsys/planar/planci/plandu"),
        "coordinate_resolution_m":float(absres) if absres and ordres and absres==ordres else None,
        "attribute_fields":fields,
        "analog_type_values":analog_types,
        "access_constraints":value(".//idinfo/accconst"),
        "use_constraints":value(".//idinfo/useconst"),
    }


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
    if not isinstance(doc,dict) or doc.get("type")!="FeatureCollection": raise ValueError("GeoJSON type must be FeatureCollection")
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

def summarize_web_links(values):
    out=[]
    if not isinstance(values,list):
        return out
    for item in values:
        if not isinstance(item,dict):
            continue
        raw=item.get("uri") or item.get("url") or item.get("link")
        parsed=urllib.parse.urlsplit(raw) if isinstance(raw,str) else None
        out.append({
            "title":item.get("title"),
            "type":item.get("type"),
            "host":parsed.hostname if parsed else None,
            "path":parsed.path if parsed else None,
            "query_parameter_names":sorted({key for key,_ in urllib.parse.parse_qsl(parsed.query,keep_blank_values=True)}) if parsed else [],
            "url_sha256":hashlib.sha256(raw.encode()).hexdigest() if isinstance(raw,str) else None,
        })
    return out


def run_live():
    r={"experiment":"E560","source":{"item_id":ITEM_ID,"doi":DOI,"metadata_url":METADATA_URL},"outcome":"NOT_STARTED","claim_boundary":"Candidate-positive catalogue only; not ground truth or negative controls."}
    try:
        meta=bounded_get(METADATA_URL,MAX_META,metadata=True)
        doc=json.loads(meta["bytes"].decode("utf-8"))
        returned=validate_item_identity(doc)
        files=metadata_files(doc)
        candidates=[x for x in files if Path(x.get("name") or "").suffix.lower() in {".zip",".geojson",".json",".gpkg",".shp",".kml"}]
        r["metadata"]={
            "status":meta["status"],"host":meta["host"],"bytes":len(meta["bytes"]),
            "sha256":hashlib.sha256(meta["bytes"]).hexdigest(),"title":doc.get("title"),
            "returned_item_id":returned,"top_level_keys":sorted(doc.keys()),
            "system_type":doc.get("systemType"),"access_level":doc.get("accessLevel"),
            "has_children":doc.get("hasChildren"),"parent_id":doc.get("parentId"),
            "web_link_count":len(doc.get("webLinks",[])) if isinstance(doc.get("webLinks"),list) else None,
            "web_links":summarize_web_links(doc.get("webLinks")),
            "file_count":len(files),
            "files":[{"name":x["name"],"size_bytes":x["size_bytes"],"checksum":x["checksum"],"url_host":urllib.parse.urlsplit(x["url"]).hostname if x["url"] else None,"url_path":urllib.parse.urlsplit(x["url"]).path if x["url"] else None,"url_sha256":hashlib.sha256(x["url"].encode()).hexdigest() if x["url"] else None} for x in files]
        }
        if not candidates:
            xmls=[x for x in files if (x.get("name") or "").lower().endswith(".xml") and x.get("url")]
            if len(xmls)==1:
                xml_response=bounded_get(xmls[0]["url"],500_000,metadata=False)
                xml_payload=xml_response["bytes"]
                OUT.mkdir(parents=True,exist_ok=True)
                (OUT/"metadata.xml").write_bytes(xml_payload)
                links=xml_urls(xml_payload)
                candidates=vector_url_candidates(links)
                expected_size=xmls[0].get("size_bytes")
                checksum=checksum_status(xmls[0].get("checksum"),xml_payload)
                r["metadata_xml"]={
                    "name":xmls[0]["name"],"status":xml_response["status"],"host":xml_response["host"],
                    "bytes":len(xml_payload),"sha256":hashlib.sha256(xml_payload).hexdigest(),
                    "catalogue_size_bytes":expected_size,
                    "catalogue_size_matches":expected_size is not None and len(xml_payload)==expected_size,
                    "catalogue_checksum":checksum,
                    "links":[{"host":urllib.parse.urlsplit(x).hostname,"path":urllib.parse.urlsplit(x).path,"url_sha256":hashlib.sha256(x.encode()).hexdigest()} for x in links],
                    "vector_link_count":len(candidates),
                    "fgdc_summary":parse_fgdc_metadata(xml_payload),
                }
                if checksum.get("matches") is False:
                    r["outcome"]="METADATA_XML_CHECKSUM_MISMATCH"
                    r["secondary_outcome"]="METADATA_XML_NO_VECTOR_LINK" if not candidates else "VECTOR_LINKS_NOT_FOLLOWED"
                    return write_receipt(r)
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
        if e.code in {301,302,303,307,308}:
            location=e.headers.get("Location","")
            target=urllib.parse.urlsplit(location)
            r["outcome"]="REDIRECT_REFUSED"; r["http_status"]=e.code
            r["redirect_target"]={"host":target.hostname,"path":target.path}
        else:
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
