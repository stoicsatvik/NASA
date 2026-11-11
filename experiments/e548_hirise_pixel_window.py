"""E548: bounded 64x64 pixel sampling of the controlled 2020 Jezero HiRISE DTM."""
from __future__ import annotations
import argparse, hashlib, json, math, re
from pathlib import Path
from urllib.parse import urlsplit
import numpy as np
import requests
import tifffile

TIFF_URL = ("https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/"
            "JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40.tif")
LABEL_URL = ("https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/"
             "JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40_pds3.lbl")
PRODUCT_URL = ("https://astrogeology.usgs.gov/search/map/Mars/Mars2020/"
               "JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40")
DOI = "10.5066/P9REJ9JN"
HOST = "asc-pds-services.s3.us-west-2.amazonaws.com"
TIFF_PATH, LABEL_PATH = urlsplit(TIFF_URL).path, urlsplit(LABEL_URL).path
MAX_LABEL_BYTES, MAX_TIFF_TRANSFER_BYTES = 256_000, 1_000_000
WINDOW = {"col_off": 10668, "row_off": 10712, "width": 64, "height": 64}
CTX_BOUNDS = {"xmin":4573663.250853,"ymin":1079453.140188,"xmax":4605583.250853,"ymax":1109693.140188}
CTX_CRS_CODE = 103885
USER_AGENT = "Unified-Parallel-Foundry-E548/1.0"

class ProbeError(RuntimeError):
    def __init__(self, outcome, message, details=None):
        super().__init__(message); self.outcome=outcome; self.details=details or {}

def validate_url(url, expected_path):
    p=urlsplit(url)
    if (p.scheme!="https" or p.hostname!=HOST or p.port not in (None,443) or p.username or p.password
        or p.path!=expected_path or p.query or p.fragment):
        raise ValueError("URL is outside the exact pinned public USGS object allowlist")

def _read_small_label(session):
    validate_url(LABEL_URL,LABEL_PATH)
    head=session.head(LABEL_URL,headers={"User-Agent":USER_AGENT,"Accept-Encoding":"identity"},
                      timeout=(15,45),allow_redirects=False)
    try:
        if int(head.status_code)!=200: raise ProbeError(f"LABEL_HTTP_{head.status_code}","PDS3 label HEAD failed")
        raw=head.headers.get("Content-Length")
        if raw and (not raw.isdigit() or int(raw)>MAX_LABEL_BYTES):
            raise ProbeError("LABEL_TOO_LARGE","PDS3 label exceeds 256 KB cap")
        expected=int(raw) if raw and raw.isdigit() else None
    finally: head.close()
    response=session.get(LABEL_URL,headers={"User-Agent":USER_AGENT,"Accept-Encoding":"identity"},
                         timeout=(15,45),allow_redirects=False,stream=True)
    try:
        if int(response.status_code) in (301,302,303,307,308): raise ProbeError("LABEL_REDIRECT","PDS3 label redirected")
        if int(response.status_code)!=200: raise ProbeError(f"LABEL_HTTP_{response.status_code}","PDS3 label GET failed")
        body=response.raw.read(MAX_LABEL_BYTES+1,decode_content=False)
        if len(body)>MAX_LABEL_BYTES: raise ProbeError("LABEL_TOO_LARGE","PDS3 label exceeded bounded read")
        if expected is not None and len(body)!=expected: raise ProbeError("LABEL_LENGTH_MISMATCH","Label byte count differs from HEAD")
        content_type=response.headers.get("Content-Type")
    finally: response.close()
    try: text=body.decode("ascii")
    except UnicodeDecodeError: text=body.decode("utf-8",errors="replace")
    return text,{"url":LABEL_URL,"bytes":len(body),"sha256":hashlib.sha256(body).hexdigest(),"content_type":content_type}

def parse_pds3_label(text):
    fields={}
    for raw in text.splitlines():
        line=raw.split("/*",1)[0].strip()
        if "=" not in line: continue
        key,value=line.split("=",1); key=key.strip().upper(); value=value.strip().strip('"').strip()
        if re.fullmatch(r"[A-Z][A-Z0-9_]*",key): fields[key]=value
    return fields

def _first_float(value):
    if value is None: return None
    m=re.search(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?",str(value))
    return float(m.group(0)) if m else None

def _tag(page,name):
    t=page.tags.get(name); return None if t is None else t.value

def parse_geokeys(page):
    raw=_tag(page,"GeoKeyDirectoryTag")
    if raw is None: return {}
    v=[int(x) for x in raw]
    if len(v)<4 or len(v)!=4+4*v[3]: raise ProbeError("INVALID_GEOKEY_DIRECTORY","GeoKeyDirectoryTag length inconsistent")
    out={}
    for i in range(v[3]):
        key,location,count,value=v[4+4*i:8+4*i]
        if location==0 and count==1: out[key]=value
    return out

def _content_range(value):
    m=re.fullmatch(r"bytes (\d+)-(\d+)/(\d+)",value or "")
    if not m: raise ProbeError("INVALID_CONTENT_RANGE","Missing exact Content-Range")
    a,b,n=map(int,m.groups())
    if a>b or n<=b: raise ProbeError("INVALID_CONTENT_RANGE","Inconsistent Content-Range")
    return a,b,n

class RangeReader:
    """Seekable TIFF reader that consumes only exact, budgeted HTTP byte ranges."""
    def __init__(self,session,url,size,max_bytes=MAX_TIFF_TRANSFER_BYTES):
        self.session,self.url,self.size=session,url,size
        self.max_bytes=max_bytes; self.position=0; self.transferred=0; self.ranges=[]; self.closed=False
    def tell(self): return self.position
    def seek(self,offset,whence=0):
        target=offset if whence==0 else self.position+offset if whence==1 else self.size+offset if whence==2 else None
        if target is None: raise ValueError("invalid whence")
        if target<0 or target>self.size: raise ValueError("seek outside pinned TIFF")
        self.position=target; return target
    def readable(self): return True
    def seekable(self): return True
    def read(self,amount=-1):
        if self.closed: raise ValueError("reader is closed")
        if amount is None or amount<0: amount=self.size-self.position
        if amount==0 or self.position>=self.size: return b""
        amount=min(amount,self.size-self.position)
        if self.transferred+amount>self.max_bytes:
            raise ProbeError("TRANSFER_BUDGET_EXCEEDED","TIFF reads exceed 1 MB cap",
                             {"requested":amount,"transferred":self.transferred})
        start,end=self.position,self.position+amount-1
        response=self.session.get(self.url,headers={"User-Agent":USER_AGENT,"Accept-Encoding":"identity",
            "Range":f"bytes={start}-{end}"},timeout=(15,45),allow_redirects=False,stream=True)
        try:
            status=int(response.status_code)
            if status in (301,302,303,307,308): raise ProbeError("TIFF_REDIRECT","TIFF Range request redirected")
            if status==200: raise ProbeError("RANGE_IGNORED","Server ignored Range; body not consumed")
            if status in (403,404,410): raise ProbeError(f"TIFF_HTTP_{status}","Pinned TIFF returned HTTP error")
            if status!=206: raise ProbeError(f"TIFF_HTTP_{status}","Pinned TIFF did not return HTTP 206")
            if response.headers.get("Content-Encoding","identity").lower() not in ("","identity"):
                raise ProbeError("ENCODED_RANGE","Unexpected content encoding")
            if _content_range(response.headers.get("Content-Range"))!=(start,end,self.size):
                raise ProbeError("CONTENT_RANGE_MISMATCH","Content-Range differs from exact request")
            declared=response.headers.get("Content-Length")
            if declared and int(declared)!=amount: raise ProbeError("CONTENT_LENGTH_MISMATCH","Wrong Content-Length")
            body=response.raw.read(amount+1,decode_content=False)
            if len(body)!=amount: raise ProbeError("BYTE_COUNT_MISMATCH","Range body length differs")
        finally: response.close()
        self.position+=amount; self.transferred+=len(body)
        self.ranges.append({"start":start,"end":end,"bytes":len(body),"sha256":hashlib.sha256(body).hexdigest()})
        return body
    def close(self): self.closed=True

def _resolve_nodata(page,label):
    lv=_first_float(label.get("MISSING_CONSTANT"))
    tv=_tag(page,"GDAL_NODATA")
    if isinstance(tv,bytes): tv=tv.decode("ascii",errors="replace")
    rv=_first_float(tv)
    if lv is not None and rv is not None and not math.isclose(lv,rv,rel_tol=1e-7,abs_tol=0):
        raise ProbeError("NODATA_CONFLICT","PDS3 and GeoTIFF nodata values disagree",{"label":lv,"geotiff":rv})
    if lv is not None: return lv,"PDS3 MISSING_CONSTANT"
    if rv is not None: return rv,"GeoTIFF GDAL_NODATA"
    return None,"NOT FOUND"

def read_float_window(reader,page,window,nodata):
    col,row,w,h=(int(window[k]) for k in ("col_off","row_off","width","height"))
    if min(col,row)<0 or min(w,h)<=0: raise ValueError("invalid window dimensions or offsets")
    if col+w>int(page.imagewidth) or row+h>int(page.imagelength): raise ValueError("window exceeds TIFF raster bounds")
    if int(page.compression)!=1 or page.is_tiled: raise ProbeError("UNSUPPORTED_TIFF_LAYOUT","Requires uncompressed strips")
    if page.dtype.kind!="f" or page.dtype.itemsize!=4 or int(page.samplesperpixel)!=1:
        raise ProbeError("UNSUPPORTED_TIFF_SAMPLE","Requires one float32 sample per pixel")
    if int(page.rowsperstrip)!=1: raise ProbeError("UNSUPPORTED_STRIP_LAYOUT","Requires one row per strip")
    offsets=tuple(map(int,page.dataoffsets)); counts=tuple(map(int,page.databytecounts))
    if len(offsets)!=int(page.imagelength) or len(counts)!=len(offsets):
        raise ProbeError("INVALID_STRIP_TABLE","Expected one strip per raster row")
    if any(n!=int(page.imagewidth)*4 for n in counts):
        raise ProbeError("INVALID_STRIP_BYTES","Strip size differs from width × float32")
    rows=[]; sample_bytes=bytearray()
    for r in range(row,row+h):
        start=offsets[r]+col*4; end=start+w*4
        if start<offsets[r] or end>offsets[r]+counts[r]:
            raise ProbeError("WINDOW_OUTSIDE_STRIP","Window exceeds strip bounds")
        reader.seek(start); payload=reader.read(w*4); sample_bytes.extend(payload)
        rows.append(np.frombuffer(payload,dtype=page.dtype,count=w).copy())
    values=np.vstack(rows); finite=np.isfinite(values)
    missing=np.zeros(values.shape,dtype=bool) if nodata is None else values==nodata
    usable=finite & ~missing; selected=values[usable].astype("float64",copy=False)
    stats=None
    if selected.size:
        stats={"min":float(np.min(selected)),"p05":float(np.quantile(selected,.05)),
            "median":float(np.median(selected)),"mean":float(np.mean(selected)),
            "std_population":float(np.std(selected)),"p95":float(np.quantile(selected,.95)),
            "max":float(np.max(selected))}
    return {"window":dict(window),"pixels_requested":int(values.size),"finite_pixels":int(finite.sum()),
        "masked_nodata_pixels":int((finite&missing).sum()),"usable_pixels":int(usable.sum()),
        "nodata_semantics_established":nodata is not None,"statistics_raw_sample_values":stats,
        "sample_sha256":hashlib.sha256(sample_bytes).hexdigest(),"raw_pixels_retained":False}

def _geo_summary(page):
    scale,tie=_tag(page,"ModelPixelScaleTag"),_tag(page,"ModelTiepointTag")
    if scale is None or tie is None or len(scale)<2 or len(tie)<6:
        raise ProbeError("MISSING_GEOREFERENCE","Missing ModelPixelScale/ModelTiepoint")
    sx,sy=float(scale[0]),float(scale[1]); ti,tj,_,tx,ty,_=map(float,tie[:6])
    if sx<=0 or sy<=0: raise ProbeError("INVALID_GEOREFERENCE","Pixel scales must be positive")
    keys=parse_geokeys(page); raster_type=keys.get(1025); area=raster_type==1
    c,r,w,h=WINDOW["col_off"],WINDOW["row_off"],WINDOW["width"],WINDOW["height"]
    half=.5 if area else 0.0
    cx=tx+(c+(w-1)/2+half-ti)*sx; cy=ty-(r+(h-1)/2+half-tj)*sy
    xmin=tx-ti*sx; ymax=ty+tj*sy
    xmax=xmin+int(page.imagewidth)*sx; ymin=ymax-int(page.imagelength)*sy
    return {"model_pixel_scale":[sx,sy],"model_tiepoint":[ti,tj,tx,ty],
        "geokeys":{str(k):v for k,v in sorted(keys.items())},"projected_crs_code":keys.get(3072),
        "linear_units_code":keys.get(3076),"projection_transform_code":keys.get(3075),"raster_type_code":raster_type,
        "pixel_is_area":area if raster_type is not None else None,
        "raster_bounds_map_units":{"xmin":xmin,"ymin":ymin,"xmax":xmax,"ymax":ymax},
        "sample_window_center_map_units":{"x":cx,"y":cy}}

def probe(session=None):
    validate_url(TIFF_URL,TIFF_PATH); validate_url(LABEL_URL,LABEL_PATH)
    session=session or requests.Session()
    label_text,label_receipt=_read_small_label(session); label=parse_pds3_label(label_text)
    head=session.head(TIFF_URL,headers={"User-Agent":USER_AGENT,"Accept-Encoding":"identity"},
                      timeout=(15,45),allow_redirects=False)
    try:
        if int(head.status_code)!=200: raise ProbeError(f"TIFF_HEAD_HTTP_{head.status_code}","TIFF HEAD failed")
        raw=head.headers.get("Content-Length","")
        if not raw.isdigit() or int(raw)<=0: raise ProbeError("TIFF_SIZE_UNKNOWN","Missing positive Content-Length")
        size=int(raw)
        if head.headers.get("Accept-Ranges","").lower()!="bytes":
            raise ProbeError("RANGE_NOT_ADVERTISED","TIFF does not advertise byte ranges")
    finally: head.close()
    reader=RangeReader(session,TIFF_URL,size)
    with tifffile.TiffFile(reader) as tif:
        if not tif.pages: raise ProbeError("TIFF_NO_PAGES","TIFF has no pages")
        page=tif.pages[0]
        if int(page.imagewidth)!=21400 or int(page.imagelength)!=21488:
            raise ProbeError("TIFF_DIMENSION_MISMATCH","Dimensions differ from E547 receipt")
        nodata,nodata_source=_resolve_nodata(page,label)
        geo=_geo_summary(page); sample=read_float_window(reader,page,WINDOW,nodata)
        dtype=str(page.dtype); compression=int(page.compression); rows_per_strip=int(page.rowsperstrip)
    unit=next((label[k] for k in ("UNIT","UNITS","UNIT_OF_MEASURE","VERTICAL_UNITS") if k in label),None)
    same_crs=True if geo["projected_crs_code"]==CTX_CRS_CODE else None if geo["projected_crs_code"]==32767 else False
    center=geo["sample_window_center_map_units"]; rb=geo["raster_bounds_map_units"]
    overlap={"xmin":max(CTX_BOUNDS["xmin"],rb["xmin"]),"ymin":max(CTX_BOUNDS["ymin"],rb["ymin"]),
             "xmax":min(CTX_BOUNDS["xmax"],rb["xmax"]),"ymax":min(CTX_BOUNDS["ymax"],rb["ymax"])}
    inside=None
    if same_crs: inside=overlap["xmin"]<=center["x"]<=overlap["xmax"] and overlap["ymin"]<=center["y"]<=overlap["ymax"]
    return {"experiment":"E548 bounded controlled HiRISE pixel-window acquisition","outcome":"PIXEL_WINDOW_READ",
        "source":{"publisher":"USGS Astrogeology Science Center","product":"Mars 2020 TRN HiRISE DTM mosaic (2020)",
            "doi":DOI,"product_page":PRODUCT_URL,"tiff_url":TIFF_URL,"pds3_label_url":LABEL_URL,
            "distinct_from_2025_msr_mosaic":True},
        "label":{**label_receipt,"sample_type":label.get("SAMPLE_TYPE"),"sample_bits":label.get("SAMPLE_BITS"),
            "missing_constant":label.get("MISSING_CONSTANT"),"unit_field":unit,
            "map_projection_type":label.get("MAP_PROJECTION_TYPE"),"map_resolution":label.get("MAP_RESOLUTION"),
            "a_axis_radius":label.get("A_AXIS_RADIUS"),"center_latitude":label.get("CENTER_LATITUDE"),
            "center_longitude":label.get("CENTER_LONGITUDE")},
        "tiff":{"object_size_bytes":size,"width":21400,"height":21488,"dtype":dtype,
            "compression_tag":compression,"rows_per_strip":rows_per_strip,"nodata_value":nodata,
            "nodata_source":nodata_source,**geo},
        "sample":sample,"transport":{"range_requests":len(reader.ranges),"bytes_transferred":reader.transferred,
            "transfer_cap_bytes":MAX_TIFF_TRANSFER_BYTES,"sample_row_ranges":reader.ranges[-WINDOW["height"]:]},
        "comparison_context":{"ctx_source_doi":"10.5066/P906QQT8","ctx_crs_code_from_e544":CTX_CRS_CODE,
            "same_projected_crs_code":same_crs,"projected_crs_code_status":"USER_DEFINED_CODE_32767_NOT_DIRECTLY_COMPARABLE" if geo["projected_crs_code"]==32767 else "DIRECT_CODE_COMPARISON","published_metadata_overlap_bounds_map_units":overlap,
            "sample_center_inside_metadata_overlap":inside,"common_valid_pixel_support":"NOT ESTABLISHED",
            "ctx_hirise_local_registration_residual":"NOT YET MEASURED"},
        "claim_state":{"bounded_hirise_pixel_values_acquired":"SUPPORTED",
            "sample_nodata_semantics":"SUPPORTED_BY_LABEL_OR_GEOTIFF" if nodata is not None else "NOT YET ESTABLISHED",
            "vertical_units_from_label":"SUPPORTED" if unit is not None else "NOT FOUND IN LABEL",
            "cross_body_similarity":"NOT YET PROVEN","known_site_recovery":"NOT YET MEASURED",
            "novel_analogue_discovery":"NOT YET PROVEN","local_validation_advantage":"NOT YET PROVEN",
            "route_safety":"NOT CLAIMED"},
        "limitations":["One bounded sample from the 2020 TRN product, not the 2025 MSR mosaic.",
            "Metadata-envelope overlap is not common valid-pixel support.",
            "No CTX/HiRISE residual or local registration metric is computed.",
            "No cross-body similarity, E001 recovery, novel discovery or route-safety claim is made.",
            "Only summary statistics and hashes are retained; no raw pixel array is uploaded."]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    try: result=probe()
    except ProbeError as e:
        result={"experiment":"E548 bounded controlled HiRISE pixel-window acquisition",
            "outcome":e.outcome,"message":str(e),"details":e.details,
            "claim_state":{"bounded_hirise_pixel_values_acquired":"NOT YET MEASURED",
                "cross_body_similarity":"NOT YET PROVEN","known_site_recovery":"NOT YET MEASURED"}}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"experiment":result["experiment"],"outcome":result["outcome"],
        "bytes_transferred":result.get("transport",{}).get("bytes_transferred"),
        "usable_pixels":result.get("sample",{}).get("usable_pixels"),
        "sample_sha256":result.get("sample",{}).get("sample_sha256")},sort_keys=True))
    negative={"RANGE_IGNORED","TIFF_REDIRECT","LABEL_REDIRECT","TIFF_HTTP_403","TIFF_HTTP_404","TIFF_HTTP_410",
              "LABEL_HTTP_403","LABEL_HTTP_404","LABEL_HTTP_410"}
    return 0 if result["outcome"]=="PIXEL_WINDOW_READ" or result["outcome"] in negative else 1

if __name__=="__main__": raise SystemExit(main())
