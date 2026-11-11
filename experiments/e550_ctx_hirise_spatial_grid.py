"""E550: spatially replicate the local CTX/HiRISE residual across nine preregistered patches."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import pyproj
import rasterio
from rasterio.io import MemoryFile
from rasterio.windows import Window
import requests
import tifffile

from experiments.e548_hirise_pixel_window import (
    RangeReader, TIFF_URL, _read_small_label, parse_pds3_label, _resolve_nodata,
    _geo_summary, _first_float, ProbeError
)
from experiments.e549_ctx_hirise_matched_support import (
    _read_ctx, _read_hirise_array, _overlap_weights, _stats,
    CTX_DOI, HI_DOI, CTX_PAGE, HI_PAGE, MAX_HIRISE_BYTES, CENTER
)

BLOCK=5
FRACTIONS=(0.15,0.50,0.85)
SHIFTS=((0.0,0.0),(-6.0,0.0),(6.0,0.0),(0.0,-6.0),(0.0,6.0))
USER_AGENT="Unified-Parallel-Foundry-E550/1.0"

class E550Error(RuntimeError):
    def __init__(self,outcome,message,details=None):
        super().__init__(message); self.outcome=outcome; self.details=details or {}

def _grid_centers(overlap):
    xmin,xmax,ymin,ymax=overlap
    return [{"patch_id":f"x{int(fx*100):02d}_y{int(fy*100):02d}",
             "fraction_x":fx,"fraction_y":fy,
             "center_x":xmin+fx*(xmax-xmin),"center_y":ymin+fy*(ymax-ymin)}
            for fy in FRACTIONS for fx in FRACTIONS]

def _window_for_bounds(bounds,x0,y0,sx,sy,pad=6):
    xmin,xmax,ymin,ymax=bounds
    c0=math.floor((xmin-x0)/sx)-pad
    c1=math.ceil((xmax-x0)/sx)+pad
    r0=math.floor((y0-ymax)/sy)-pad
    r1=math.ceil((y0-ymin)/sy)+pad
    return {"col_off":c0,"row_off":r0,"width":c1-c0,"height":r1-r0}

def _cell_bounds(transform,row,col):
    xl=transform.c+col*transform.a; xr=xl+transform.a
    yt=transform.f+row*transform.e; yb=yt+transform.e
    return (xl,xr,yb,yt)

def _linear_spatial_trend(rows):
    if len(rows)<3: return {"status":"INSUFFICIENT_PATCHES"}
    x=np.asarray([r["center_x"] for r in rows],dtype="float64")
    y=np.asarray([r["center_y"] for r in rows],dtype="float64")
    z=np.asarray([r["median_residual_m"] for r in rows],dtype="float64")
    x0,y0=float(x.mean()),float(y.mean())
    design=np.column_stack([np.ones(len(x)),(x-x0)/1000.0,(y-y0)/1000.0])
    coef=np.linalg.lstsq(design,z,rcond=None)[0]
    pred=design@coef
    return {"intercept_m_at_grid_center":float(coef[0]),
            "slope_x_m_per_km":float(coef[1]),"slope_y_m_per_km":float(coef[2]),
            "r2_descriptive":float(1-np.sum((z-pred)**2)/np.sum((z-z.mean())**2)) if np.var(z)>0 else None,
            "n_patches":len(rows),"not_a_geophysical_model":True}

def run():
    session=requests.Session()
    label_text,label_receipt=_read_small_label(session)
    label=parse_pds3_label(label_text)
    radius_a=_first_float(label.get("A_AXIS_RADIUS"))
    radius_c=_first_float(label.get("C_AXIS_RADIUS"))
    lat0=_first_float(label.get("CENTER_LATITUDE"))
    lon0=_first_float(label.get("CENTER_LONGITUDE"))
    resolution=_first_float(label.get("MAP_RESOLUTION"))
    projection=(label.get("MAP_PROJECTION_TYPE") or "").upper()
    if None in (radius_a,lat0,lon0,resolution) or projection!="EQUIRECTANGULAR":
        raise E550Error("HIRISE_PROJECTION_INCOMPLETE","PDS3 label lacks required projection parameters")
    radius_m=radius_a*1000.0
    pixel_m=2*math.pi*radius_m/(360.0*resolution)
    if not math.isclose(pixel_m,1.0,rel_tol=1e-6):
        raise E550Error("HIRISE_SCALE_MISMATCH","PDS3 map resolution does not imply 1 m pixels")
    if radius_c is not None and not math.isclose(radius_a,radius_c,rel_tol=1e-9):
        raise E550Error("HIRISE_ELLIPSOID_NOT_SPHERICAL","Expected equal A/C radii")
    hi_crs=pyproj.CRS.from_proj4(
        f"+proj=eqc +lat_ts={lat0} +lat_0={lat0} +lon_0={lon0} "
        f"+x_0=0 +y_0=0 +a={radius_m} +b={radius_m} +units=m +no_defs +type=crs"
    )
    ctx_bytes,ctx_transport=_read_ctx(session)
    with MemoryFile(ctx_bytes) as mem:
      with mem.open() as ds:
        if ds.driver!="GTiff" or ds.width!=1596 or ds.height!=1512:
            raise E550Error("CTX_RASTER_CONTRACT_MISMATCH","CTX raster differs from E544 contract")
        if abs(ds.transform.a-20)>1e-9 or abs(ds.transform.e+20)>1e-9 or abs(ds.transform.b)>1e-9 or abs(ds.transform.d)>1e-9:
            raise E550Error("CTX_TRANSFORM_UNSUPPORTED","Expected north-up 20 m CTX grid")
        ctx_crs=pyproj.CRS.from_wkt(ds.crs.to_wkt())
        if not ctx_crs.equals(hi_crs,ignore_axis_order=True):
            raise E550Error("CRS_NOT_EQUIVALENT","PDS3-derived HiRISE CRS differs from CTX")
        ctx_bounds={"xmin":float(ds.bounds.left),"ymin":float(ds.bounds.bottom),
                    "xmax":float(ds.bounds.right),"ymax":float(ds.bounds.top)}
        # Open the HiRISE TIFF once, then fetch only nine small windows by exact byte ranges.
        head=session.head(TIFF_URL,headers={"User-Agent":USER_AGENT,"Accept-Encoding":"identity"},
                          timeout=(15,45),allow_redirects=False)
        try:
            if int(head.status_code)!=200: raise E550Error(f"HIRISE_HEAD_HTTP_{head.status_code}","HiRISE HEAD failed")
            size=int(head.headers.get("Content-Length","0"))
            if size<=0 or head.headers.get("Accept-Ranges","").lower()!="bytes":
                raise E550Error("HIRISE_RANGE_UNAVAILABLE","HiRISE byte ranges unavailable")
        finally: head.close()
        reader=RangeReader(session,TIFF_URL,size,max_bytes=MAX_HIRISE_BYTES)
        with tifffile.TiffFile(reader) as tif:
            page=tif.pages[0]
            geo=_geo_summary(page)
            if geo["projected_crs_code"]!=32767 or geo["projection_transform_code"]!=17:
                raise E550Error("HIRISE_GEOKEY_CONTRACT_MISMATCH","Expected user-defined equirectangular GeoKeys")
            nodata,nodata_source=_resolve_nodata(page,label)
            hi_x0=geo["raster_bounds_map_units"]["xmin"]
            hi_y0=geo["raster_bounds_map_units"]["ymax"]
            hi_sx,hi_sy=geo["model_pixel_scale"]
            overlap=(max(ctx_bounds["xmin"],geo["raster_bounds_map_units"]["xmin"]),
                     min(ctx_bounds["xmax"],geo["raster_bounds_map_units"]["xmax"]),
                     max(ctx_bounds["ymin"],geo["raster_bounds_map_units"]["ymin"]),
                     min(ctx_bounds["ymax"],geo["raster_bounds_map_units"]["ymax"]))
            centers=_grid_centers(overlap)
            patches=[]; all_zero_diffs=[]; all_zero_coverages=[]
            for point in centers:
                col_center=(point["center_x"]-ds.transform.c)/ds.transform.a
                row_center=(point["center_y"]-ds.transform.f)/ds.transform.e
                col0=int(round(col_center))-BLOCK//2
                row0=int(round(row_center))-BLOCK//2
                if col0<0 or row0<0 or col0+BLOCK>ds.width or row0+BLOCK>ds.height:
                    raise E550Error("CTX_PATCH_OUTSIDE_RASTER","Preregistered patch falls outside CTX raster",point)
                win=Window(col0,row0,BLOCK,BLOCK)
                ctx=ds.read(1,window=win).astype("float64",copy=False)
                mask=(ds.read_masks(1,window=win)>0)&np.isfinite(ctx)
                if ds.nodata is not None: mask &= ctx!=ds.nodata
                x_min=ds.transform.c+col0*ds.transform.a
                x_max=ds.transform.c+(col0+BLOCK)*ds.transform.a
                y_max=ds.transform.f+row0*ds.transform.e
                y_min=ds.transform.f+(row0+BLOCK)*ds.transform.e
                bounds=(x_min,x_max,y_min,y_max)
                hi_window=_window_for_bounds(bounds,hi_x0,hi_y0,hi_sx,hi_sy,pad=6)
                hi_data,hi_hash=_read_hirise_array(reader,page,hi_window)
                cells=[]
                for rr in range(BLOCK):
                    for cc in range(BLOCK):
                        if not mask[rr,cc]: continue
                        row,col=row0+rr,col0+cc
                        cbounds=_cell_bounds(ds.transform,row,col)
                        mean,cov=_overlap_weights(hi_data,hi_window,hi_x0,hi_y0,hi_sx,hi_sy,
                                                   cbounds,nodata=nodata)
                        residual=None if mean is None or cov<0.99 else float(ctx[rr,cc]-mean)
                        cells.append({"row":row,"col":col,"ctx_m":float(ctx[rr,cc]),
                                      "hirise_area_mean_m":mean,"coverage":cov,"residual_ctx_minus_hirise_m":residual})
                        if residual is not None:
                            all_zero_diffs.append(residual); all_zero_coverages.append(cov)
                zero=[c["residual_ctx_minus_hirise_m"] for c in cells if c["residual_ctx_minus_hirise_m"] is not None]
                coverage=[c["coverage"] for c in cells]
                shift_results=[]
                for dx,dy in SHIFTS:
                    diffs=[]; covs=[]
                    for cell in cells:
                        if not mask[cell["row"]-row0,cell["col"]-col0]: continue
                        cbounds=_cell_bounds(ds.transform,cell["row"],cell["col"])
                        mean,cov=_overlap_weights(hi_data,hi_window,hi_x0,hi_y0,hi_sx,hi_sy,
                                                   cbounds,dx=dx,dy=dy,nodata=nodata)
                        covs.append(cov)
                        if mean is not None and cov>=0.99:
                            diffs.append(cell["ctx_m"]-mean)
                    shift_results.append({"dx_m":dx,"dy_m":dy,**_stats(diffs,covs)})
                patch_stats=_stats(zero,coverage)
                patches.append({"patch_id":point["patch_id"],"fraction_x":point["fraction_x"],
                    "fraction_y":point["fraction_y"],"center_x":point["center_x"],"center_y":point["center_y"],
                    "ctx_window":{"col_off":col0,"row_off":row0,"width":BLOCK,"height":BLOCK},
                    "bounds_map_units":[x_min,y_min,x_max,y_max],"ctx_valid_cells":int(mask.sum()),
                    "common_valid_cells_at_zero_shift":len(zero),"zero_shift":patch_stats,
                    "shift_sensitivity":shift_results,"hirise_window":hi_window,
                    "hirise_sample_sha256":hi_hash,"per_cell_residuals":cells})
            ctx_meta={"crs":ds.crs.to_string(),"transform":[ds.transform.a,ds.transform.b,ds.transform.c,
                ds.transform.d,ds.transform.e,ds.transform.f],"nodata":ds.nodata}
    zero_global=_stats(all_zero_diffs,all_zero_coverages)
    patch_medians=[{"center_x":p["center_x"],"center_y":p["center_y"],
                    "median_residual_m":p["zero_shift"]["median"]} for p in patches if p["zero_shift"]["n"]]
    trend=_linear_spatial_trend(patch_medians)
    total_cells=sum(p["ctx_valid_cells"] for p in patches)
    matched=sum(p["common_valid_cells_at_zero_shift"] for p in patches)
    return {"experiment":"E550 nine-patch spatial CTX/HiRISE residual campaign",
        "outcome":"NINE_PATCHES_MEASURED" if len(patches)==9 else "INCOMPLETE_PATCH_GRID",
        "sources":{"ctx":{"doi":CTX_DOI,"product_page":CTX_PAGE,**ctx_transport},
                   "hirise":{"doi":HI_DOI,"product_page":HI_PAGE,"label_url":LABEL_URL,
                    "label_bytes":label_receipt["bytes"],"label_sha256":label_receipt["sha256"]}},
        "projection_audit":{"label_projection":projection,"radius_a_m":radius_m,
            "radius_c_m":radius_c*1000 if radius_c is not None else None,"center_latitude_deg":lat0,
            "center_longitude_deg":lon0,"map_resolution_pixels_per_degree":resolution,
            "derived_hirise_pixel_size_m":pixel_m,"ctx_crs":ctx_meta["crs"],
            "pyproj_crs_equivalent":True,"hirise_projected_crs_geokey":32767,
            "hirise_projection_transform_geokey":17,"overlap_bounds_map_units":list(overlap)},
        "design":{"grid_fractions":list(FRACTIONS),"patches":9,"ctx_cells_per_patch":BLOCK*BLOCK,
            "patch_size_m_nominal":BLOCK*20,"minimum_hirise_area_coverage":0.99,
            "fixed_translation_sensitivity_m":[list(x) for x in SHIFTS],
            "no_fitted_registration_shift":True},
        "aggregate_zero_shift_ctx_minus_hirise_m":zero_global,
        "spatial_trend_across_patch_medians":trend,
        "patches":patches,
        "transport":{"ctx_bytes_downloaded":ctx_transport["bytes"],
            "ctx_sha256":ctx_transport["sha256"],"hirise_range_requests":len(reader.ranges),
            "hirise_bytes_transferred":reader.transferred,"hirise_transfer_cap_bytes":MAX_HIRISE_BYTES},
        "claim_state":{"CTX_HiRISE_projection_parameter_equivalence":"SUPPORTED",
            "spatially_replicated_common_valid_area_support":"SUPPORTED" if matched==total_cells else "PARTIAL",
            "spatial_distribution_of_local_vertical_residual":"MEASURED",
            "global_vertical_offset_reproduction":"NOT ESTABLISHED",
            "local_horizontal_registration_residual":"NOT YET MEASURED",
            "cross_body_similarity":"NOT YET PROVEN","known_site_recovery":"NOT YET MEASURED",
            "novel_analogue_discovery":"NOT YET PROVEN","route_safety":"NOT CLAIMED"},
        "published_context":{"expected_global_median_offset_m_approx":0.4,
            "reported_direction":"CTX mosaic floats above HiRISE mosaic",
            "source":"USGS HiRISE TRN DTM product metadata; not treated as local ground truth"},
        "limitations":["Nine 100 m patches are a spatial diagnostic, not a global product validation.",
            "The fixed translation grid is sensitivity analysis, not a fitted registration.",
            "Local vertical differences do not independently validate the USGS control network or vertical datum.",
            "No raw rasters or pixel arrays are retained; only per-cell derived residuals and hashes.",
            "No cross-body similarity or E001 known-site recovery is measured."]}

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--out",type=Path,required=True); args=ap.parse_args()
    try: result=run()
    except (E550Error,ProbeError) as e:
        result={"experiment":"E550 nine-patch spatial CTX/HiRISE residual campaign",
            "outcome":e.outcome,"message":str(e),"details":e.details,
            "claim_state":{"spatially_replicated_common_valid_area_support":"NOT ESTABLISHED",
                "cross_body_similarity":"NOT YET PROVEN","known_site_recovery":"NOT YET MEASURED"}}
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    print(json.dumps({"experiment":result["experiment"],"outcome":result["outcome"],
        "patches":len(result.get("patches",[])),"matched_cells":sum(p.get("common_valid_cells_at_zero_shift",0) for p in result.get("patches",[])),
        "global_median_m":result.get("aggregate_zero_shift_ctx_minus_hirise_m",{}).get("median"),
        "hirise_bytes":result.get("transport",{}).get("hirise_bytes_transferred")},sort_keys=True))
    return 0 if result["outcome"]=="NINE_PATCHES_MEASURED" else 1

if __name__=="__main__": raise SystemExit(main())
