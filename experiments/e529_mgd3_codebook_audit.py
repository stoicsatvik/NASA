from __future__ import annotations
import argparse, hashlib, html.parser, json, re, urllib.parse, urllib.request, zipfile, io
from datetime import datetime, timezone
from pathlib import Path

BASE = "https://pubs.usgs.gov/of/2007/1158/"
ARCHIVES = {"metadata": (BASE + "Metadata.zip", 2 * 1024 * 1024), "documentation": (BASE + "Documentation.zip", 20 * 1024 * 1024)}
USER_AGENT = "NASA-Analog-Research/0.1 (public USGS MGD3 codebook audit)"
TERMS = ("dune_id", "dune id", "dune field lon+lat id", "dune_latitude", "dune_longitude", "mean_dune_height", "mean dune height", "dune_type", "dune type", "areal_coverage", "area_km2", "positional accuracy", "barchan", "barchanoid", "transverse", "longitudinal", "parabolic", "sand sheet", "average elevation", "MDHeight", "CcDcAzimut", "MOLA", "THEMIS", "100m/pixel")

class TextOnly(html.parser.HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self, data): self.parts.append(data)
    def text(self): return " ".join(" ".join(self.parts).split())

def safe_url(url: str) -> bool:
    p=urllib.parse.urlparse(url)
    return p.scheme=="https" and p.hostname=="pubs.usgs.gov" and p.path.startswith("/of/2007/1158/") and p.path.lower().endswith(".zip")

def fetch(url: str, limit: int) -> bytes:
    if not safe_url(url): raise ValueError(f"non-canonical USGS URL: {url}")
    req=urllib.request.Request(url,headers={"User-Agent":USER_AGENT,"Accept":"application/zip, */*"})
    with urllib.request.urlopen(req,timeout=90) as response:
        if not safe_url(response.geturl()): raise ValueError("redirect outside official USGS 2007 report path")
        length=response.headers.get("Content-Length")
        if length and int(length)>limit: raise ValueError("archive exceeds bound")
        data=response.read(limit+1)
    if len(data)>limit: raise ValueError("archive exceeded bound")
    if not data.startswith(b"PK\x03\x04"): raise ValueError("response is not a ZIP archive")
    return data

def extract_text(name: str, raw: bytes) -> str | None:
    suffix=Path(name).suffix.lower()
    if suffix not in {".txt",".html",".htm",".xml"}: return None
    text=raw.decode("utf-8-sig",errors="replace")
    if "\\ufffd" in text:
        text=raw.decode("cp1252",errors="replace")
    if suffix in {".html",".htm",".xml"}:
        parser=TextOnly(); parser.feed(text); text=parser.text()
    return text


def extract_field_definitions(text: str) -> list[dict]:
    """Extract complete numbered field definitions without assigning code equivalence."""
    normalized=text.replace("\\r\\n","\\n").replace("\\r","\\n").replace("\\f","\\n")
    starts=list(re.finditer(r"(?im)^\\s*Field\\s+(\\d+)\\s*:\\s*",normalized))
    definitions=[]
    for index,match in enumerate(starts):
        end=starts[index+1].start() if index+1<len(starts) else len(normalized)
        block=normalized[match.end():end].strip()
        lines=[" ".join(line.split()) for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        first=lines[0]
        separator=re.search(r"\\s+(?:–|—|-)\\s+",first)
        if separator:
            label=first[:separator.start()].strip()
            definition_parts=[first[separator.end():].strip(),*lines[1:]]
        else:
            label=first
            definition_parts=lines[1:]
        alias=re.search(r"\\(([^()]+)\\)\\s*$",label)
        short_name=alias.group(1).strip() if alias else None
        if alias:
            label=label[:alias.start()].strip()
        definitions.append({
            "field_number":int(match.group(1)),
            "label":label,
            "short_name":short_name,
            "definition":" ".join(part for part in definition_parts if part),
        })
    return definitions

def inspect_archive(kind: str, payload: bytes) -> dict:
    docs=[]; names=[]; field_docs=[]
    with zipfile.ZipFile(io.BytesIO(payload)) as z:
        bad=z.testzip()
        if bad: raise ValueError(f"{kind} archive CRC failure at {bad}")
        for info in z.infolist():
            name=info.filename.replace("\\","/")
            if info.is_dir(): continue
            if name.startswith("/") or ".." in Path(name).parts: raise ValueError(f"unsafe archive path: {name}")
            names.append({"name":name,"bytes":info.file_size})
            raw=z.read(info); text=extract_text(name,raw)
            if text is None: continue
            if Path(name).name.lower() in {"readme_gis.txt","readme_softcopy.txt"}:
                fields=extract_field_definitions(text)
                field_docs.append({
                    "name":name,
                    "bytes":len(raw),
                    "sha256":hashlib.sha256(raw).hexdigest(),
                    "field_count":len(fields),
                    "fields":fields,
                })
            low=text.lower(); matches=[]
            for term in TERMS:
                start=0
                while len(matches)<80:
                    index=low.find(term.lower(),start)
                    if index<0: break
                    matches.append({"term":term,"excerpt":text[max(0,index-180):min(len(text),index+420)]})
                    start=index+len(term)
            if matches: docs.append({"name":name,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),"matches":matches})
    return {
        "entries":names,
        "text_documents_with_relevant_terms":docs,
        "field_definition_documents":field_docs,
        "field_definition_count":sum(item["field_count"] for item in field_docs),
    }

def audit(fetcher=fetch) -> dict:
    receipts={}
    for kind,(url,limit) in ARCHIVES.items():
        raw=fetcher(url,limit)
        receipts[kind]={"url":url,"bytes":len(raw),"sha256":hashlib.sha256(raw).hexdigest(),**inspect_archive(kind,raw)}
    return {"schema_version":"mgd3-2007-codebook-audit-v1","experiment":"E529_MGD3_2007_CODEBOOK_AND_UNITS_AUDIT","retrieved_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),"source":"USGS Open-File Report 2007-1158","status":"ARCHIVES_INSPECTED","archives":receipts,"interpretation_boundary":"Text matches are source excerpts, not automatic code mappings. Do not harmonize PAAD and MGD3 categories unless definitions establish equivalence.","next_gate":"Use the extracted full GIS and softcopy field definitions to verify units and Dune_Type codes; create a conservative PAAD crosswalk with explicit unmatched categories."}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--output",type=Path,required=True); a=p.parse_args(); a.output.parent.mkdir(parents=True,exist_ok=True)
    try:
        result=audit(); a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        print(json.dumps({"status":result["status"],"metadata_entries":len(result["archives"]["metadata"]["entries"]),"documentation_entries":len(result["archives"]["documentation"]["entries"]),"text_docs":sum(len(x["text_documents_with_relevant_terms"]) for x in result["archives"].values())},sort_keys=True)); return 0
    except Exception as exc:
        result={"experiment":"E529_MGD3_2007_CODEBOOK_AND_UNITS_AUDIT","status":"FAILED","error_type":type(exc).__name__,"error":str(exc),"claim_boundary":"No codebook mapping is claimed when official metadata cannot be inspected."}
        a.output.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n",encoding="utf-8"); print(json.dumps(result,sort_keys=True)); return 1

if __name__=="__main__": raise SystemExit(main())