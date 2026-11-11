"""E549: compare area-matched CTX and HiRISE elevation samples at Jezero."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
from urllib.parse import urlsplit, urljoin
import numpy as np
import pyproj
import rasterio
from rasterio.io import MemoryFile
from rasterio.windows import Window
import requests
import tifffile

from experiments.e548_hirise_pixel_window import (
    RangeReader, TIFF_URL, LABEL_URL, _read_small_label, parse_pds3_label,
    _resolve_nodata, _geo_summary, _first_float, ProbeError
)

CTX_URL=("https://planetarymaps.usgs.gov/mosaic/mars2020_trn/CTX/"
         "JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif")
CTX_PATH=urlsplit(CTX_URL).path
CTX_S3_HOST="asc-pds-services.s3.us-west-2.amazonaws.com"
CTX_S3_PATH=("/mosaic/mars2020_trn/CTX/"
             "JEZ_ctx_B_soc_008_DTM_MOLAtopography_DeltaGeoid_20m_Eqc_latTs0_lon0.tif")
CTX_SHA256="16a1aa66c3f48c1bca252795827db7b417876217aff0f5e1aff18027fab2327b"
CTX_DOI="10.5066/P906QQT8"
HI_DOI="10.5066/P9REJ9JN"
CTX_PAGE="https://astrogeology.usgs.gov/search/map/mars_2020_terrain_relative_navigation_ctx_dtm_mosaic"
HI_PAGE=("https://astrogeology.usgs.gov/search/map/Mars/Mars2020/"
         "JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40")
MAX_CTX_BYTES=20_000_000
MAX_HIRISE_BYTES=1_000_000
CENTER={"x":4588066.0,"y":1095874.0}
BLOCK_SIZE=10
SHIFTS=(-6.0,0.0,6.0)
USER_AGENT="Unified-Parallel-Foundry-E549/1.0"

class ExperimentError(RuntimeError):
    def __init__(self,outcome,message,details=None):
        super().__init__(message); self.outcome=outcome; self.details=details or {}

def _read_ctx(session):
    p=urlsplit(CTX_URL)
    if p.scheme!="https" or p.hostname!="planetarymaps.usgs.gov" or p.path!=CTX_PATH or p.query or p.fragment:
        raise ValueError("CTX URL is outside exact USGS source allowlist")
    response=session.get(CTX_URL,headers={"User-Agent":USER_AGENT,"Accept-Encoding":"identity"},
                         timeout=(15,90),allow_redirects=False,stream=True)
    try:
        status=int(response.status_code)
        if status in (301,302,303,307,308):
            location=urljoin(CTX_URL,response.headers.get("Location",""))
            q=urlsplit(location)
            if q.scheme!="https" or q.hostname!=CTX_S3_HOST or q.path!=CTX_S3_PATH or q.query or q.fragment:
                raise ExperimentError("CTX_REDIRECT_OUTSIDE_ALLOWLIST","CTX redirected outside exact official S3 object")
        elif status==200:
            location=CTX_URL
        elif status in (403,404,410):
            raise ExperimentError(f"CTX_HTTP_{status}","Pinned CTX object returned an HTTP error")
        else:
            raise ExperimentError(f"CTX_HTTP_{status}","Pinned CTX request failed")
    finally:
        response.close()
    if location!=CTX_URL:
        response=session.get(location,headers={"User-Agent":USER_AGENT,"Accept-Encoding":"identity"},
                             timeout=(15,90),allow_redirects=False,stream=True)
    else:
        response=session.get(CTX_URL,headers={"User-Agent":USER_AGENT,"Accept-Encoding":"identity"},
                             timeout=(15,90),allow_redirects=False,stream=True)
    try:
        if int(response.status_code)!=200:
            raise ExperimentError(f"CTX_FINAL_HTTP_{response.status_code}","Exact final CTX object did not return HTTP 200")
        raw=response.headers.get("Content-Length")
        if raw and (not raw.isdigit() or int(raw)>MAX_CTX_BYTES):
            raise ExperimentError("CTX_TOO_LARGE","CTX exceeds 20 MB acquisition cap")
        body=response.raw.read(MAX_CTX_BYTES+1,decode_content=False)
        if len(body)>MAX_CTX_BYTES: raise ExperimentError("CTX_TOO_LARGE","CTX exceeded 20 MB read cap")
        if raw and len(body)!=int(raw): raise ExperimentError("CTX_LENGTH_MISMATCH","CTX byte count differs from Content-Length")
        final_type=response.headers.get("Content-Type","").split(";",1)[0].lower()
    finally: response.close()
    digest=hashlib.sha256(body).hexdigest()
    if digest!=CTX_SHA256: raise ExperimentError("CTX_HASH_MISMATCH","CTX bytes differ from E544 pinned source hash",{"sha256":digest})
    if body[:4] not in (bytes((73,73,42,0)), bytes((77,77,0,42)), bytes((73,73,43,0)), bytes((77,77,0,43))):
        raise ExperimentError("CTX_NON_TIFF","Pinned CTX object lacks TIFF magic")
    return body,{"url":location,"bytes":len(body),"sha256":digest,"content_type":final_type}

def _read_hirise_array(reader,page,window):
    c,r,w,h=(int(window[k]) for k in ("col_off","row_off","width","height"))
    if c<0 or r<0 or w<=0 or h<=0 or c+w>int(page.imagewidth) or r+h>int(page.imagelength):
        raise ValueError("HiRISE window outside raster")
    if int(page.compression)!=1 or page.is_tiled or int(page.rowsperstrip)!=1:
        raise ExperimentError("UNSUPPORTED_HIRISE_LAYOUT","Expected uncompressed one-row float32 strips")
    if page.dtype.kind!="f" or page.dtype.itemsize!=4 or int(page.samplesperpixel)!=1:
        raise ExperimentError("UNSUPPORTED_HIRISE_SAMPLE","Expected one float32 sample per pixel")
    offsets=tuple(map(int,page.dataoffsets)); counts=tuple(map(int,page.databytecounts))
    if len(offsets)!=int(page.imagelength) or len(counts)!=len(offsets) or any(x!=int(page.imagewidth)*4 for x in counts):
        raise ExperimentError("INVALID_HIRISE_STRIP_TABLE","Expected one width×4-byte strip per row")
    rows=[]; raw=bytearray()
    for rr in range(r,r+h):
        start=offsets[rr]+c*4
        reader.seek(start); payload=reader.read(w*4)
        raw.extend(payload); rows.append(np.frombuffer(payload,dtype=page.dtype,count=w).copy())
    return np.vstack(rows),hashlib.sha256(raw).hexdigest()

def _overlap_weights(data,window,grid_origin_x,grid_origin_y,scale_x,scale_y,
                     bounds,dx=0.0,dy=0.0,nodata=None):
    xmin,xmax,ymin,ymax=bounds
    x0=grid_origin_x+dx; y0=grid_origin_y-dy
    c0=math.floor((xmin-x0)/scale_x); c1=math.ceil((xmax-x0)/scale_x)
    r0=math.floor((y0-ymax)/scale_y); r1=math.ceil((y0-ymin)/scale_y)
    if c0<window["col_off"] or r0<window["row_off"] or c1>window["col_off"]+window["width"] or r1>window["row_off"]+window["height"]:
        raise ExperimentError("HIRISE_SAMPLE_TOO_SMALL","HiRISE range sample does not cover requested CTX cell")
    cols=np.arange(c0,c1); rows=np.arange(r0,r1)
    wx=np.maximum(0.0,np.minimum(xmax,x0+(cols+1)*scale_x)-np.maximum(xmin,x0+cols*scale_x))
    wy=np.maximum(0.0,np.minimum(ymax,y0-rows*scale_y)-np.maximum(ymin,y0-(rows+1)*scale_y))
    arr=data[r0-window["row_off"]:r1-window["row_off"],c0-window["col_off"]:c1-window["col_off"]]
    weights=wy[:,None]*wx[None,:]
    valid=np.isfinite(arr)
    if nodata is not None: valid &= arr!=nodata
    valid_area=float(weights[valid].sum())
    total_area=float((xmax-xmin)*(ymax-ymin))
    coverage=valid_area/total_area if total_area else 0.0
    if valid_area<=0: return None,coverage
    return float((arr[valid].astype("float64")*weights[valid]).sum()/valid_area),coverage

def _stats(diffs,coverage):
    a=np.asarray(diffs,dtype="float64")
    if not len(a): return {"n":0,"median":None,"mean":None,"std":None,"mae":None,"rmse":None,"p95_abs":None}
    return {"n":int(len(a)),"median":float(np.median(a)),"mean":float(np.mean(a)),
        "std":float(np.std(a)),"mae":float(np.mean(np.abs(a))),
        "rmse":float(np.sqrt(np.mean(a*a))),"p95_abs":float(np.quantile(np.abs(a),.95)),
        "min":float(np.min(a)),"max":float(np.max(a)),
        "coverage_min":float(np.min(coverage)),"coverage_median":float(np.median(coverage))}

def run():
    session=requests.Session()
    label_text,label_receipt=_read_small_label(session)
    label=parse_pds3_label(label_text)
    radius_a=_first_float(label.get("A_AXIS_RADIUS"))
    radius_c=_first_float(label.get("C_AXIS_RADIUS"))
    center_lat=_first_float(label.get("CENTER_LATITUDE"))
    center_lon=_first_float(label.get("CENTER_LONGITUDE"))
    map_resolution=_first_float(label.get("MAP_RESOLUTION"))
    projection=(label.get("MAP_PROJECTION_TYPE") or "").upper()
    if None in (radius_a,center_lat,center_lon,map_resolution) or projection!="EQUIRECTANGULAR":
        raise ExperimentError("HIRISE_PROJECTION_INCOMPLETE","PDS3 label lacks required equirectangular parameters")
    radius_m=radius_a*1000.0
    derived_pixel_m=2*math.pi*radius_m/(360.0*map_resolution)
    if radius_c is not None and not math.isclose(radius_a,radius_c,rel_tol=1e-9):
        raise ExperimentError("HIRISE_ELLIPSOID_NOT_SPHERICAL","Current E549 transform assumes the published equal A/C radii")
    hi_crs=pyproj.CRS.from_proj4(
        f"+proj=eqc +lat_ts={center_lat} +lat_0={center_lat} +lon_0={center_lon} "
        f"+x_0=0 +y_0=0 +a={radius_m} +b={radius_m} +units=m +no_defs +type=crs"
    )
    ctx_bytes,ctx_transport=_read_ctx(session)
    with MemoryFile(ctx_bytes) as mem:
        with mem.open() as ds:
            if ds.driver!="GTiff" or ds.width!=1596 or ds.height!=1512 or ds.count<1:
                raise ExperimentError("CTX_RASTER_CONTRACT_MISMATCH","CTX dimensions/driver differ from E544")
            if abs(ds.transform.a-20)>1e-9 or abs(ds.transform.e+20)>1e-9 or abs(ds.transform.b)>1e-9 or abs(ds.transform.d)>1e-9:
                raise ExperimentError("CTX_TRANSFORM_UNSUPPORTED","Expected north-up 20 m CTX grid")
            ctx_crs=pyproj.CRS.from_wkt(ds.crs.to_wkt())
            crs_equal=ctx_crs.equals(hi_crs,ignore_axis_order=True)
            if not crs_equal:
                raise ExperimentError("CRS_NOT_EQUIVALENT","PDS3-derived HiRISE CRS differs from E544 CTX CRS",
                    {"ctx_proj4":ctx_crs.to_proj4(),"hirise_proj4":hi_crs.to_proj4()})
            col_center=(CENTER["x"]-ds.transform.c)/ds.transform.a
            row_center=(CENTER["y"]-ds.transform.f)/ds.transform.e
            col0=int(round(col_center))-BLOCK_SIZE//2
            row0=int(round(row_center))-BLOCK_SIZE//2
            if col0<0 or row0<0 or col0+BLOCK_SIZE>ds.width or row0+BLOCK_SIZE>ds.height:
                raise ExperimentError("CTX_WINDOW_OUTSIDE_RASTER","Selected CTX block outside raster")
            ctx_window=Window(col0,row0,BLOCK_SIZE,BLOCK_SIZE)
            ctx_values=ds.read(1,window=ctx_window).astype("float64",copy=False)
            ctx_mask=(ds.read_masks(1,window=ctx_window)>0)&np.isfinite(ctx_values)
            if ds.nodata is not None: ctx_mask &= ctx_values!=ds.nodata
            transform=ds.transform
            block_xmin=transform.c+col0*transform.a
            block_xmax=transform.c+(col0+BLOCK_SIZE)*transform.a
            block_ymax=transform.f+row0*transform.e
            block_ymin=transform.f+(row0+BLOCK_SIZE)*transform.e
            ctx_meta={"crs":ds.crs.to_string(),"transform":[transform.a,transform.b,transform.c,transform.d,transform.e,transform.f],
                "bounds":[float(ds.bounds.left),float(ds.bounds.bottom),float(ds.bounds.right),float(ds.bounds.top)],
                "nodata":ds.nodata,"unit_tag":ds.units[0] if ds.units else None}
    if not math.isclose(derived_pixel_m,1.0,rel_tol=1e-6):
        raise ExperimentError("HIRISE_SCALE_MISMATCH","PDS3 map resolution does not imply 1 m pixels",{"derived_pixel_m":derived_pixel_m})
    # Reopen the pinned HiRISE TIFF through exact byte ranges and read only the area needed by the CTX block.
    head=session.head(TIFF_URL,headers={"User-Agent":USER_AGENT,"Accept-Encoding":"identity"},
                      timeout=(15,45),allow_redirects=False)
    try:
        if int(head.status_code)!=200: raise ExperimentError(f"HIRISE_HEAD_HTTP_{head.status_code}","HiRISE HEAD failed")
        size=int(head.headers.get("Content-Length","0"))
        if size<=0 or head.headers.get("Accept-Ranges","").lower()!="bytes":
            raise ExperimentError("HIRISE_RANGE_UNAVAILABLE","HiRISE object size/range support unavailable")
    finally: head.close()
    hi_x0=geo["raster_bounds_map_units"]["xmin"]; hi_y0=geo["raster_bounds_map_units"]["ymax"]; hi_sx,hi_sy=geo["model_pixel_scale"]
    hi_window={
        "col_off":math.floor((block_xmin-hi_x0)/hi_sx)-6,
        "row_off":math.floor((hi_y0-block_ymax)/hi_sy)-6,
        "width":math.ceil((block_xmax-hi_x0)/hi_sx)+6-math.floor((block_xmin-hi_x0)/hi_sx)+6,
        "height":math.ceil((hi_y0-block_ymin)/hi_sy)+6-math.floor((hi_y0-block_ymax)/hi_sy)+6,
    }
    reader=RangeReader(session,TIFF_URL,size,max_bytes=MAX_HIRISE_BYTES)
    with tifffile.TiffFile(reader) as tif:
        page=tif.pages[0]
        if int(page.imagewidth)!=21400 or int(page.imagelength)!=21488:
            raise ExperimentError("HIRISE_DIMENSION_MISMATCH","HiRISE dimensions differ from E547")
        geo=_geo_summary(page)
        if geo["projected_crs_code"]!=32767 or geo["projection_transform_code"]!=17:
            raise ExperimentError("HIRISE_GEOKEY_CONTRACT_MISMATCH","Expected user-defined equirectangular GeoKeys")
        nodata,nd_source=_resolve_nodata(page,label)
        hi_values,hi_hash=_read_hirise_array(reader,page,hi_window)
    # Each CTX 20 m cell is compared with the area-weighted mean of its overlapping 1 m HiRISE pixels.
    def cell_bounds(r,c):
        xl=transform.c+c*transform.a; xr=xl+transform.a
        yt=transform.f+r*transform.e; yb=yt+transform.e
        return (xl,xr,yb,yt)
    ctx_pairs=[]
    for rr in range(BLOCK_SIZE):
        for cc in range(BLOCK_SIZE):
            if ctx_mask[rr,cc]:
                ctx_pairs.append((row0+rr,col0+cc,float(ctx_values[rr,cc])))
    shifts=[]
    for dy in SHIFTS:
        for dx in SHIFTS:
            diffs=[]; coverages=[]; matched=0
            for r,c,ctx_value in ctx_pairs:
                mean,cov=_overlap_weights(hi_values,hi_window,hi_x0,hi_y0,hi_sx,hi_sy,
                    cell_bounds(r,c),dx=dx,dy=dy,nodata=nodata)
                coverages.append(cov)
                if mean is not None and cov>=0.99:
                    diffs.append(ctx_value-mean); matched+=1
            shifts.append({"dx_m":dx,"dy_m":dy,**_stats(diffs,coverages),"matched_cells":matched})
    zero=next(x for x in shifts if x["dx_m"]==0 and x["dy_m"]==0)
    ctx_valid=ctx_values[ctx_mask]
    return {
        "experiment":"E549 matched-support Jezero CTX versus HiRISE elevation comparison",
        "outcome":"MATCHED_SUPPORT_COMPARISON" if zero["matched_cells"]==BLOCK_SIZE*BLOCK_SIZE else "PARTIAL_SUPPORT_COMPARISON",
        "sources":{"ctx":{"publisher":"USGS Astrogeology Science Center","doi":CTX_DOI,"product_page":CTX_PAGE,
                **ctx_transport,"sha256_expected_from_E544":CTX_SHA256},
            "hirise":{"publisher":"USGS Astrogeology Science Center","doi":HI_DOI,"product_page":HI_PAGE,
                "tiff_url":TIFF_URL,"pds3_label":LABEL_URL,"label_sha256":label_receipt["sha256"],
                "label_bytes":label_receipt["bytes"]}},
        "projection_audit":{"label_projection":projection,"radius_a_m":radius_m,
            "radius_c_m":radius_c*1000 if radius_c is not None else None,
            "center_latitude_deg":center_lat,"center_longitude_deg":center_lon,
            "map_resolution_pixels_per_degree":map_resolution,"derived_hirise_pixel_size_m":derived_pixel_m,
            "hirise_projected_crs_geokey":32767,"hirise_projection_transform_geokey":17,
            "ctx_crs":ctx_meta["crs"],"pyproj_crs_equivalent":crs_equal,
            "ctx_hirise_map_definition_match":"SUPPORTED" if crs_equal else "NOT SUPPORTED"},
        "patch":{"ctx_window":{"col_off":col0,"row_off":row0,"width":BLOCK_SIZE,"height":BLOCK_SIZE,
                "valid_cells":int(ctx_mask.sum()),"total_cells":BLOCK_SIZE*BLOCK_SIZE,
                "bounds_map_units":[block_xmin,block_ymin,block_xmax,block_ymax],
                "sample_sha256":hashlib.sha256(ctx_values.tobytes()).hexdigest(),
                "valid_min":float(np.min(ctx_valid)) if ctx_valid.size else None,
                "valid_median":float(np.median(ctx_valid)) if ctx_valid.size else None,
                "valid_max":float(np.max(ctx_valid)) if ctx_valid.size else None},
            "hirise_window":hi_window,"hirise_sample_sha256":hi_hash,
            "hirise_nodata":nodata,"hirise_nodata_source":nd_source,
            "hirise_finite_pixels":int(np.isfinite(hi_values).sum()),
            "hirise_usable_pixels":int((np.isfinite(hi_values)&(hi_values!=nodata)).sum()) if nodata is not None else int(np.isfinite(hi_values).sum()),
            "common_valid_area_cells_at_zero_shift":zero["matched_cells"]},
        "zero_shift_residual_ctx_minus_hirise_m":zero,
        "translation_sensitivity_grid_m":shifts,
        "transport":{"hirise_range_requests":len(reader.ranges),"hirise_bytes_transferred":reader.transferred,
            "hirise_transfer_cap_bytes":MAX_HIRISE_BYTES,"ctx_bytes_downloaded":ctx_transport["bytes"]},
        "ctx_raster_metadata":ctx_meta,
        "published_context":{"hirise_ctx_median_vertical_offset_m_approx":0.4,
            "source":"USGS HiRISE product metadata; CTX mosaic reported to float above HiRISE",
            "not_reproduced_by_metadata_only":True,
            "horizontal_feature_alignment_context":"USGS reports 94.1% of matched orthomosaic features below 6 m; not a DEM residual."},
        "claim_state":{"CTX_HiRISE_projection_parameter_equivalence":"SUPPORTED" if crs_equal else "NOT SUPPORTED",
            "common_valid_area_support_for_this_200m_patch":"SUPPORTED" if zero["matched_cells"]==100 else "PARTIAL",
            "local_vertical_difference_for_this_patch":"MEASURED",
            "local_horizontal_registration_residual":"NOT YET MEASURED",
            "cross_body_similarity":"NOT YET PROVEN","known_site_recovery":"NOT YET MEASURED",
            "novel_analogue_discovery":"NOT YET PROVEN","route_safety":"NOT CLAIMED"},
        "limitations":["One 200 m × 200 m Jezero patch; not a global product comparison.",
            "The shift grid is a sensitivity analysis, not a fitted registration or an estimate of true displacement.",
            "The residual is descriptive and does not independently validate the USGS control network or vertical datum.",
            "No raw raster or pixel arrays are committed or uploaded.",
            "No Earth/Moon/Mars analogue similarity or E001 recovery is measured."]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    try: result=run()
    except (ExperimentError,ProbeError) as e:
        result={"experiment":"E549 matched-support Jezero CTX versus HiRISE comparison",
            "outcome":e.outcome,"message":str(e),"details":e.details,
            "claim_state":{"CTX_HiRISE_projection_parameter_equivalence":"NOT YET MEASURED",
                "common_valid_area_support_for_this_patch":"NOT ESTABLISHED",
                "cross_body_similarity":"NOT YET PROVEN","known_site_recovery":"NOT YET MEASURED"}}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"experiment":result["experiment"],"outcome":result["outcome"],
        "ctx_hirise_crs_equal":result.get("projection_audit",{}).get("pyproj_crs_equivalent"),
        "common_cells":result.get("patch",{}).get("common_valid_area_cells_at_zero_shift"),
        "median_residual_m":result.get("zero_shift_residual_ctx_minus_hirise_m",{}).get("median"),
        "hirise_bytes":result.get("transport",{}).get("bytes_transferred")},sort_keys=True))
    return 0 if result["outcome"] in ("MATCHED_SUPPORT_COMPARISON","PARTIAL_SUPPORT_COMPARISON") else 1

if __name__=="__main__": raise SystemExit(main())
