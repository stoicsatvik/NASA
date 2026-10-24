"""E214: real Earth DEM provenance and source-processing sensitivity, not analogue discovery."""
from __future__ import annotations
import argparse, hashlib, json, math
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import from_bounds

SITES={"lonar_lead":(19.975,76.51),"western_ghats_lead":(18.6,73.5),"ladakh_lead":(34.2,77.6)}
R=6371008.8
BASE="https://s3.amazonaws.com/elevation-tiles-prod/skadi"

def tile_name(lat,lon):
    if not (-90<=lat<90 and -180<=lon<180): raise ValueError("invalid coordinates")
    a,b=math.floor(lat),math.floor(lon)
    return f"{'N' if a>=0 else 'S'}{abs(a):02d}{'E' if b>=0 else 'W'}{abs(b):03d}"

def source_url(site,product="MAPZEN_SKADI"):
    if product!="MAPZEN_SKADI": raise ValueError("unsupported product")
    name=tile_name(*SITES[site])
    return f"{BASE}/{name[:3]}/{name}.hgt.gz"

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

def inspect_tile(path,site,product="MAPZEN_SKADI",width_km=4.0):
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
    for name in ("lonar","ghats","ladakh"): p.add_argument("--"+name,type=Path,required=True)
    args=p.parse_args()
    tiles=((args.lonar,"lonar_lead"),(args.ghats,"western_ghats_lead"),(args.ladakh,"ladakh_lead"))
    rows=[inspect_tile(path,site,width_km=km) for path,site in tiles for km in (2.,4.)]
    comparisons={}
    for site in SITES:
        a=next(r["metrics"] for r in rows if r["site"]==site and r["physical_window_km"]==2.)
        b=next(r["metrics"] for r in rows if r["site"]==site and r["physical_window_km"]==4.)
        comparisons[site]={k:{"two_km":a[k],"four_km":b[k],
                         "relative_change":(b[k]-a[k])/a[k] if a[k] else None}
                         for k in ("plane_detrended_relief_std_m","slope_p50_dimensionless","slope_p90_dimensionless")}
    print(json.dumps({"experiment":"E214 real Earth SRTM-derived Mapzen Skadi ingestion and footprint sensitivity",
        "claim_state":"REAL EARTH INGESTION ONLY; E001 NOT YET MEASURED; CROSS-BODY SIMILARITY NOT YET PROVEN",
        "source_note":"Mapzen Skadi AWS public terrain tiles, derived mainly from SRTM in India; not official NASADEM, not independent validation",
        "sites":rows,"within_site_2km_vs_4km_sensitivity":comparisons,
        "limitations":["NASADEM OpenTopography public mirror returned HTTP 404 in prior CI; not ingested.",
          "Site coordinates are research leads, not validated analogue labels.",
          "Mapzen may blend SRTM with other sources and void fills; provenance is dataset-level, not per pixel.",
          "2/4 km footprints do not validate crater-scale or planetary morphology.",
          "Moon/Mars comparison and E001 known-site recovery NOT performed."]},indent=2,sort_keys=True))
if __name__=="__main__": main()
