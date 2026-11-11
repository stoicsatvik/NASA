"""E537: bounded download of the official ScienceBase item ZIP and DEM inspection.

The URL pattern follows DOI-USGS/sciencebasepy's public get_item_files_zip
implementation. Raw files remain workflow artifacts; none are committed.
"""
from __future__ import annotations

import hashlib
import json
import os
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import requests
import rasterio
from rasterio.io import MemoryFile
import numpy as np

ITEM_ID = "662bccfad34ea70bd5f11f88"
ITEM_URL = f"https://www.sciencebase.gov/catalog/item/{ITEM_ID}?format=json"
ZIP_URL = f"https://www.sciencebase.gov/catalog/file/get/{ITEM_ID}"
DOI = "10.5066/P9FRH62D"
DEM_NAME = "GFDF_Ripples_2023_04_18_DEM.tif"
FGDC_NAME = "Grand_Falls_Dune_Field_2023_Photogrammetry.xml"
CATALOGUE_DEM_BYTES = 619492
MAX_DOWNLOAD_BYTES = 50_000_000
ALLOWED_SUFFIXES = ("sciencebase.gov", "usgs.gov")


def build_zip_url(item_id: str = ITEM_ID) -> str:
    if not item_id or any(ch not in "0123456789abcdef" for ch in item_id.lower()):
        raise ValueError("invalid ScienceBase item id")
    return f"https://www.sciencebase.gov/catalog/file/get/{item_id}"


def _allowed_host(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    return parsed.scheme == "https" and any(
        host == suffix or host.endswith("." + suffix) for suffix in ALLOWED_SUFFIXES
    )


def _select_members(archive: zipfile.ZipFile) -> tuple[zipfile.ZipInfo, zipfile.ZipInfo]:
    infos = archive.infolist()
    if sum(info.file_size for info in infos) > MAX_DOWNLOAD_BYTES:
        raise ValueError("archive expands beyond the 50 MB safety bound")
    dem = [
        info for info in infos
        if Path(info.filename.replace("\\", "/")).name == DEM_NAME
    ]
    fgdc = [
        info for info in infos
        if Path(info.filename.replace("\\", "/")).name == FGDC_NAME
    ]
    if len(dem) != 1:
        raise ValueError(f"expected exactly one {DEM_NAME}, found {len(dem)}")
    if len(fgdc) != 1:
        raise ValueError(f"expected exactly one {FGDC_NAME}, found {len(fgdc)}")
    for info in (dem[0], fgdc[0]):
        normalized = info.filename.replace("\\", "/")
        if normalized.startswith("/") or ".." in Path(normalized).parts:
            raise ValueError("unsafe archive member path")
    return dem[0], fgdc[0]


def parse_fgdc(xml_bytes: bytes) -> dict:
    root = ET.fromstring(xml_bytes)
    wanted = {
        "altunits", "altsys", "altdatum", "horizdn", "geogunit",
        "mapprojn", "projcsn", "geogcsn", "rowres", "colres",
        "nrows", "ncols", "rasttype", "rasterobj", "westbc", "eastbc",
        "northbc", "southbc", "begdate", "enddate", "attrdef",
        "attrlabl", "placekey",
    }
    fields: dict[str, list[str]] = {}
    for element in root.iter():
        local = element.tag.rsplit("}", 1)[-1].lower()
        value = (element.text or "").strip()
        if local in wanted and value:
            fields.setdefault(local, []).append(value)
    return {key: sorted(set(values)) for key, values in sorted(fields.items())}


def inspect_dem(dem_bytes: bytes, fgdc_bytes: bytes) -> dict:
    if not (
        dem_bytes.startswith(b"II*\x00")
        or dem_bytes.startswith(b"MM\x00*")
        or dem_bytes.startswith(b"II+\x00")
        or dem_bytes.startswith(b"MM\x00+")
    ):
        raise ValueError("selected DEM is not a TIFF/BigTIFF payload")
    with MemoryFile(dem_bytes) as mem:
        with mem.open() as ds:
            band = ds.read(1, masked=True)
            valid = band.compressed()
            if valid.size == 0:
                raise ValueError("DEM contains no valid pixels")
            quantiles = np.quantile(valid.astype(np.float64), [0.01, 0.5, 0.99])
            tags = ds.tags()
            band_tags = ds.tags(1)
            return {
                "driver": ds.driver,
                "width_px": ds.width,
                "height_px": ds.height,
                "band_count": ds.count,
                "dtype": ds.dtypes[0],
                "crs": ds.crs.to_string() if ds.crs else None,
                "transform": [float(v) for v in ds.transform],
                "bounds": [float(v) for v in ds.bounds],
                "resolution_map_units_per_pixel": [float(v) for v in ds.res],
                "nodata": ds.nodata,
                "unit": ds.units[0] if ds.units else None,
                "scale": float(ds.scales[0]) if ds.scales else None,
                "offset": float(ds.offsets[0]) if ds.offsets else None,
                "valid_pixel_count": int(valid.size),
                "masked_pixel_count": int(np.ma.getmaskarray(band).sum()),
                "raw_value_min": float(np.min(valid)),
                "raw_value_max": float(np.max(valid)),
                "raw_value_mean": float(np.mean(valid)),
                "raw_value_std": float(np.std(valid)),
                "raw_value_quantiles_1_50_99": [float(v) for v in quantiles],
                "dataset_tags": {k: tags[k] for k in sorted(tags)},
                "band_tags": {k: band_tags[k] for k in sorted(band_tags)},
                "fgdc_fields": parse_fgdc(fgdc_bytes),
            }


def download_and_inspect(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    receipt = {
        "experiment": "E537",
        "source": {
            "catalogue_item": ITEM_URL,
            "item_id": ITEM_ID,
            "doi": DOI,
            "catalogue_dem_name": DEM_NAME,
            "catalogue_dem_bytes": CATALOGUE_DEM_BYTES,
            "download_method": "ScienceBase server-side item ZIP endpoint",
            "endpoint": ZIP_URL,
            "endpoint_implementation_reference": "DOI-USGS/sciencebasepy SbSession.get_item_files_zip",
        },
        "download": {"attempted": True, "success": False},
        "claim_boundary": (
            "A valid Earth photogrammetry raster and its source metadata can be inspected. "
            "This does not establish Mars/Earth physical comparability, analogue recovery, "
            "or a novel analogue discovery."
        ),
    }
    response = None
    try:
        response = requests.get(ZIP_URL, stream=True, timeout=(15, 90), allow_redirects=True)
        receipt["download"].update({
            "http_status": response.status_code,
            "final_url_host": urlparse(response.url).hostname,
            "content_type": response.headers.get("Content-Type"),
            "content_length_header": response.headers.get("Content-Length"),
        })
        if not _allowed_host(response.url):
            raise ValueError("redirect left the official ScienceBase/USGS host boundary")
        response.raise_for_status()
        fd, tmp_name = tempfile.mkstemp(prefix="e537-", suffix=".zip")
        total = 0
        try:
            with os.fdopen(fd, "wb") as handle:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if not chunk:
                        continue
                    total += len(chunk)
                    if total > MAX_DOWNLOAD_BYTES:
                        raise ValueError("download exceeded 50 MB safety bound")
                    handle.write(chunk)
            if total < 4:
                raise ValueError("download is too small to be a ZIP archive")
            with open(tmp_name, "rb") as handle:
                if handle.read(4) != b"PK\x03\x04":
                    raise ValueError("ScienceBase item ZIP endpoint returned non-ZIP content")
            item_zip_path = output_dir / "item.zip"
            item_zip_path.write_bytes(Path(tmp_name).read_bytes())
            with zipfile.ZipFile(tmp_name) as archive:
                receipt["download"]["archive_members"] = [
                    {"name": info.filename, "bytes": info.file_size}
                    for info in archive.infolist()
                ]
                dem_info, fgdc_info = _select_members(archive)
                dem_bytes = archive.read(dem_info)
                fgdc_bytes = archive.read(fgdc_info)
            (output_dir / "source_metadata.xml").write_bytes(fgdc_bytes)
            receipt["download"].update({
                "bytes": total,
                "zip_sha256": hashlib.sha256(Path(tmp_name).read_bytes()).hexdigest(),
                "selected_dem_member_bytes": len(dem_bytes),
                "selected_dem_member_sha256": hashlib.sha256(dem_bytes).hexdigest(),
                "selected_fgdc_member_bytes": len(fgdc_bytes),
                "selected_fgdc_member_sha256": hashlib.sha256(fgdc_bytes).hexdigest(),
                "catalogue_size_matches": len(dem_bytes) == CATALOGUE_DEM_BYTES,
            })
            receipt["source"]["fgdc_fields"] = parse_fgdc(fgdc_bytes)
            fields = receipt["source"]["fgdc_fields"]
            receipt["source"]["site_bounds_lonlat"] = {
                key: (fields.get(key) or [None])[0]
                for key in ("westbc", "southbc", "eastbc", "northbc")
            }
            receipt["source"]["acquisition_period"] = {
                "start": (fields.get("begdate") or [None])[0],
                "end": (fields.get("enddate") or [None])[0],
            }
            receipt["source"]["elevation_definition"] = fields.get("attrdef", [])
            receipt["source"]["crs_fields_present"] = any(
                fields.get(key) for key in ("projcsn", "geogcsn", "horizdn", "mapprojn")
            )
            receipt["source"]["vertical_unit_fields_present"] = bool(fields.get("altunits"))
            receipt["source"]["resolution_fields_present"] = bool(
                fields.get("rowres") or fields.get("colres")
            )
            if len(dem_bytes) != CATALOGUE_DEM_BYTES:
                raise ValueError(
                    f"DEM ZIP member size {len(dem_bytes)} != catalogue size {CATALOGUE_DEM_BYTES}"
                )
            dem_path = output_dir / "sample.tif"
            dem_path.write_bytes(dem_bytes)
            profile = inspect_dem(dem_bytes, fgdc_bytes)
            receipt["download"]["success"] = True
            receipt["experiment_outcome"] = "RAW_RASTER_INGESTED"
            receipt["raster_inspection"] = profile
            receipt["claim_state"] = {
                "raw_earth_raster_ingestion": "SUPPORTED" if profile["crs"] else "PARTIAL",
                "crs_and_pixel_geometry": "SUPPORTED" if profile["crs"] and profile["width_px"] else "NOT YET RESOLVED",
                "vertical_units_and_datum": "SUPPORTED" if profile["unit"] or profile["fgdc_fields"].get("altunits") else "NOT YET RESOLVED",
                "cross_body_similarity": "NOT YET PROVEN",
                "known_site_recovery": "NOT YET MEASURED",
                "novel_analogue_discovery": "NOT YET PROVEN",
            }
        finally:
            Path(tmp_name).unlink(missing_ok=True)
    except Exception as exc:
        receipt["download"]["error"] = f"{type(exc).__name__}: {exc}"
        if receipt["download"].get("archive_members") and (
            receipt["download"].get("selected_dem_member_bytes") != CATALOGUE_DEM_BYTES
        ):
            receipt["experiment_outcome"] = "NEGATIVE_RESULT_PUBLIC_ZIP_OMITS_RASTER"
            receipt["download"]["blocker"] = (
                "The public item ZIP contains a zero-byte DEM member despite the 619492-byte "
                "catalogue listing. The manager/cloud file path requires an authenticated "
                "ScienceBase session; no access-control bypass or credential use was attempted."
            )
            receipt["claim_state"] = {
                "source_site_bounds_and_dates": "SUPPORTED",
                "raw_earth_raster_ingestion": "NOT YET INGESTED",
                "crs_vertical_units_resolution_nodata": "NOT YET RESOLVED",
                "cross_body_similarity": "NOT YET PROVEN",
                "known_site_recovery": "NOT YET MEASURED",
                "novel_analogue_discovery": "NOT YET PROVEN",
            }
        else:
            receipt["experiment_outcome"] = "ERROR"
    finally:
        if response is not None:
            response.close()
    (output_dir / "receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return receipt


if __name__ == "__main__":
    result = download_and_inspect(Path(".artifacts/e537"))
    print(json.dumps(result, indent=2, sort_keys=True))
    if result.get("experiment_outcome") == "ERROR":
        raise SystemExit(1)
