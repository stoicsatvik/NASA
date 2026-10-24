"""E214: real Earth DEM provenance and source-processing sensitivity, not analogue discovery."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import from_bounds

SITES={"lonar_lead":(19.975,76.51),"western_ghats_lead":(18.6,73.5),"ladakh_lead":(34.2,77.6)}
R=6371008.8
BASE="https://opentopography.s3.sdsc.edu/raster"

def tile_name(lat,lon):
    if not (-90<=lat<90 and -180<=lon<180): raise ValueError("invalid coordinates")
    a,b=math.floor(lat),math.floor(lon)
    return f"{'N' if a>=0 else 'S'}{abs(a):02d}{'E' if b>=0 else 'W'}{abs(b):03d}"

def source_url(site,product="NASADEM"):
    name=tile_name(*SITES[site])
    if product=="NASADEM": return f"{BASE}/NASADEM/NASADEM_be/NASADEM_HGT_{name.lower()}.tif"
    if product=="SRTM_GL1": return f"{BASE}/SRTM_GL1/SRTM_GL1_srtm/{name}.tif"
    raise ValueError("unsupported product")

def square_bounds(lat,lon,width_km):
    if not all(math.isfinite(v) for v in (lat,lon,width_km)) or not (-89<lat<89 and -180<lon<180 and 0<width_km<=20):
        raise ValueError("invalid geometry")
    half=width_km*500/R
    a,b=math.degrees(half),math.degrees(half/math.cos(math.radians(lat)))
    return lon-b,lat-a,lon+b,lat+a

def sha256(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""): h.update(block)
    return h.hexdigest()

def physical_metrics(z,valid,dx,dy):
    if z.ndim!=2 or z.shape!=valid.shape or min(z.shape)<5: raise ValueError("invalid DEM/mask geometry")
    if not all(math.isfinite(v) and v>0 for v in (dx,dy)): raise ValueError("invalid physical resolution")
    coverage=float(np.mean(valid))
    if coverage<0.99: raise ValueError(f"insufficient valid DEM coverage: {coverage:.5f}")
    if not np.isfinite(z[valid]).all(): raise ValueError("nonfinite valid elevation")
    # Exclude derivative stencils touching nodata. Never fill voids silently.
    inner=valid[1:-1,1:-1]&valid[1:-1,:-2]&valid[1:-1,2:]&valid[:-2,1:-1]&valid[2:,1:-1]
    if not inner.any(): raise ValueError("no fully observed derivative stencil")
    gx=(z[1:-1,2:]-z[1:-1,:-2])/(2*dx)
    gy=(z[2:,1:-1]-z[:-2,1:-1])/(2*dy)
    slopes=np.hypot(gx,gy)[inner]
    yy,xx=np.indices(z.shape,dtype=float)
    X=np.column_stack((xx[valid]*dx,yy[valid]*dy,np.ones(int(valid.sum()))))
    coeff,*_=np.linalg.lstsq(X,z[valid],rcond=None)
    residual=z[valid]-X@coeff
    return {"shape":list(z.shape),"valid_fraction":coverage,
            "pixel_m":{"east_west":float(dx),"north_south":float(dy)},
            "elevation_range_m":float(np.ptp(z[valid])),
            "plane_detrended_relief_std_m":float(np.std(residual)),
            "slope_p50_dimensionless":float(np.percentile(slopes,50)),
            "slope_p90_dimensionless":float(np.percentile(slopes,90)),
            "derivative_valid_fraction":float(inner.mean())}

def inspect_tile(path,site,product,width_km=4.0):
    lat,lon=SITES[site]
    bounds=square_bounds(lat,lon,width_km)
    with rasterio.open(path) as ds:
        if ds.count!=1 or ds.crs is None or ds.crs.to_epsg()!=4326:
            raise ValueError(f"unexpected DEM CRS/bands: {ds.crs}, {ds.count}")
        if not (ds.bounds.left<=bounds[0]<bounds[2]<=ds.bounds.right and
                ds.bounds.bottom<=bounds[1]<bounds[3]<=ds.bounds.top):
            raise ValueError("physical footprint crosses tile boundary; adjacent tile required")
        win=from_bounds(*bounds,transform=ds.transform).round_offsets().round_lengths()
        a=ds.read(1,window=win,masked=True)
        z=np.asarray(a.data,dtype=float)
        valid=~np.ma.getmaskarray(a)
        if ds.nodata is not None: valid &= z!=ds.nodata
        dx=abs(ds.transform.a)*math.pi/180*R*math.cos(math.radians(lat))
        dy=abs(ds.transform.e)*math.pi/180*R
        return {"site":site,"site_lat_lon":[lat,lon],"label":"research lead only; NOT validated analogue ground truth",
                "product":product,"source_url":source_url(site,product),"sha256":sha256(path),
                "raster_crs":str(ds.crs),"vertical_units":"metres; planetary vertical datums differ",
                "source_nodata":ds.nodata,"full_tile_shape":[ds.height,ds.width],
                "tile_bounds_lon_lat":list(ds.bounds),"physical_window_km":width_km,
                "physical_window_bounds_lon_lat":list(bounds),
                "metrics":physical_metrics(z,valid,dx,dy)}

def main():
    p=argparse.ArgumentParser()
    for name in ("nasadem-lonar","nasadem-ghats","nasadem-ladakh","srtm-lonar"):
        p.add_argument("--"+name,type=Path,required=True)
    args=p.parse_args()
    rows=[inspect_tile(args.nasadem_lonar,"lonar_lead","NASADEM"),
          inspect_tile(args.nasadem_ghats,"western_ghats_lead","NASADEM"),
          inspect_tile(args.nasadem_ladakh,"ladakh_lead","NASADEM"),
          inspect_tile(args.srtm_lonar,"lonar_lead","SRTM_GL1")]
    a,b=rows[0]["metrics"],rows[3]["metrics"]
    keys=("plane_detrended_relief_std_m","slope_p50_dimensionless","slope_p90_dimensionless")
    comparison={k:{"nasadem":a[k],"srtm_gl1":b[k],
                   "relative_difference":(a[k]-b[k])/b[k] if b[k] else None} for k in keys}
    print(json.dumps({"experiment":"E214 real Earth NASADEM/SRTM_GL1 ingestion and processing-sensitivity audit",
        "claim_state":"REAL EARTH INGESTION ONLY; E001 NOT YET MEASURED; CROSS-BODY SIMILARITY NOT YET PROVEN",
        "source_note":"OpenTopography public mirror of NASA-derived DEMs; no Earthdata credentials or field data",
        "sites":rows,"same_site_processing_sensitivity":comparison,
        "limitations":["Coordinates are research leads, not validated analogue labels.",
          "NASADEM and SRTM_GL1 share mission ancestry; agreement is not independent instrumental replication.",
          "DEM may include void filling, vegetation and building effects.",
          "Four-kilometre windows do not validate site- or crater-scale morphology.",
          "Moon/Mars comparison and E001 known-site recovery NOT performed."]},indent=2,sort_keys=True))
if __name__=="__main__": main()
