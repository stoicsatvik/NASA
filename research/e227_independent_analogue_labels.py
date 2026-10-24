"""E227: independent NASA analogue-pair evidence audit and USGS access spike.

Pre-event, read-only research. NASA examples are NOT E001 ground-truth
recoveries; do not treat analyst modality tags as NASA-authored labels.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
import re
import hashlib
import xml.etree.ElementTree as ET
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlsplit, urlunsplit

DATA = Path(__file__).parent / "data/e227_nasa_analogue_pairs.json"
USGS_ITEM = "5f88940b82cebb8c13d912ee"
USGS_URL = f"https://www.sciencebase.gov/catalog/item/{USGS_ITEM}?format=json"
EXPECTED_BODIES = {"Moon": 3, "Mars": 6, "Venus": 1, "Enceladus": 1}


def audit(source: dict) -> dict:
    if source.get("schema") != "nasa/e227/analogue-pair-source-audit/v1":
        raise ValueError("Unexpected source schema")
    if source.get("source") != "https://science.nasa.gov/solar-system/analog-explorer/":
        raise ValueError("Missing authoritative NASA source")
    pairs = source.get("pairs", [])
    if len(pairs) != 11 or len({p["id"] for p in pairs}) != 11:
        raise ValueError("Expected 11 unique NASA gallery examples")
    for p in pairs:
        if not p.get("source_heading") or not p.get("primary_basis"):
            raise ValueError("Missing traceable source heading or analyst basis")
        if p.get("latitude") is not None or p.get("longitude") is not None:
            raise ValueError("No invented geocoding permitted")
        if not isinstance(p.get("static_surface_morphology_component"), bool):
            raise ValueError("Unclassified morphology component")
    bodies = Counter(p["target_body"] for p in pairs)
    if dict(bodies) != EXPECTED_BODIES:
        raise ValueError("NASA gallery body coverage changed")
    morphology = sum(p["static_surface_morphology_component"] for p in pairs)
    return {
        "source": source["source"],
        "examples": len(pairs),
        "target_bodies": dict(sorted(bodies.items())),
        "moon_mars_examples": bodies["Moon"] + bodies["Mars"],
        "analyst_marked_surface_morphology_component": morphology,
        "analyst_marked_without_surface_morphology_component": len(pairs) - morphology,
        "primary_basis_counts": dict(sorted(Counter(p["primary_basis"] for p in pairs).items())),
        "interpretation": "Analyst source-taxonomy audit only; not an ML accuracy result.",
        "claim": "NASA documents process-specific analog pairs; static DEM-only recovery NOT YET PROVEN",
        "e001_known_site_recovery": "NOT YET MEASURED",
    }



def safe_public_service_url(uri: str) -> str | None:
    """Strip embedded URL credentials; never copy ScienceBase token parameters."""
    parts = urlsplit(uri)
    if (parts.scheme == "https" and parts.hostname == "services.arcgis.com"
            and parts.path.endswith("/FeatureServer")):
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    return None


def probe_public_arcgis(service_url: str | None) -> dict:
    """Unauthenticated, bounded public feature sample only. Never reuse metadata tokens."""
    if not service_url:
        return {"status": "NO_PUBLIC_SERVICE", "point_features_ingested": 0}
    query = urlencode({
        "where": "1=1", "outFields": "*", "returnGeometry": "true",
        "f": "geojson", "resultRecordCount": "100",
    })
    url = f"{service_url}/0/query?{query}"
    try:
        with urlopen(Request(url, headers={"User-Agent": "NASA-E227-Research/1.0", "Accept": "application/geo+json"}), timeout=30) as response:
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("ArcGIS sample exceeds bounded limit")
        data = json.loads(raw)
        if data.get("error"):
            return {"status": "SERVICE_ERROR", "error_code": data["error"].get("code"),
                    "point_features_ingested": 0}
        if data.get("type") != "FeatureCollection":
            raise ValueError("Unexpected ArcGIS response format")
        features = data.get("features", [])
        valid = []
        for feature in features:
            geom = feature.get("geometry") or {}
            xy = geom.get("coordinates")
            if geom.get("type") != "Point" or not isinstance(xy, list) or len(xy) < 2:
                continue
            lon, lat = xy[:2]
            if not isinstance(lon, (int, float)) or not isinstance(lat, (int, float)):
                continue
            if not (-180 <= lon <= 180 and -90 <= lat <= 90):
                continue
            valid.append({"longitude": lon, "latitude": lat,
                          "attributes": feature.get("properties") or {}})
        return {"status": "PUBLIC_SAMPLE_INGESTED" if valid else "NO_VALID_POINTS",
                "feature_count_returned": len(features), "point_features_ingested": len(valid),
                "raw_sha256": hashlib.sha256(raw).hexdigest(),
                "first_five_points": valid[:5],
                "sample_not_complete_catalog": True,
                "authenticated": False}
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "UNAUTHENTICATED_ACCESS_FAILED",
                "error_type": type(exc).__name__, "error": str(exc)[:180],
                "point_features_ingested": 0, "authenticated": False}



def probe_public_arcgis_layers(service_url: str | None) -> dict:
    """Enumerate bounded public layer samples without an ArcGIS access token."""
    if not service_url:
        return {"status": "NO_PUBLIC_SERVICE", "layers": []}
    try:
        with urlopen(Request(service_url + "?f=json", headers={
            "User-Agent": "NASA-E227-Research/1.0", "Accept": "application/json",
        }), timeout=25) as response:
            raw = response.read(500_001)
        if len(raw) > 500_000:
            raise ValueError("Service metadata exceeds bound")
        info = json.loads(raw)
        if info.get("error"):
            return {"status": "SERVICE_ERROR", "error_code": info["error"].get("code"), "layers": []}
        layers = info.get("layers", [])
        if not isinstance(layers, list) or len(layers) > 30:
            raise ValueError("Unexpected layer count")
        summaries = []
        for layer in layers:
            lid = layer.get("id")
            if not isinstance(lid, int) or lid < 0:
                continue
            query = urlencode({
                "where": "1=1", "outFields": "*", "returnGeometry": "true",
                "f": "geojson", "resultRecordCount": "100",
            })
            with urlopen(Request(f"{service_url}/{lid}/query?{query}", headers={
                "User-Agent": "NASA-E227-Research/1.0",
            }), timeout=30) as response:
                layer_raw = response.read(2_000_001)
            if len(layer_raw) > 2_000_000:
                raise ValueError("Layer sample exceeds bound")
            data = json.loads(layer_raw)
            if data.get("error"):
                summaries.append({"id": lid, "name": layer.get("name"),
                                  "status": "SERVICE_ERROR",
                                  "error_code": data["error"].get("code")})
                continue
            features = data.get("features", [])
            valid = []
            for feature in features:
                geometry = feature.get("geometry") or {}
                xy = geometry.get("coordinates")
                if geometry.get("type") != "Point" or not isinstance(xy, list) or len(xy) < 2:
                    continue
                lon, lat = xy[:2]
                if (isinstance(lon, (int, float)) and isinstance(lat, (int, float))
                        and -180 <= lon <= 180 and -90 <= lat <= 90):
                    valid.append({"longitude": lon, "latitude": lat,
                                  "attributes": feature.get("properties") or {}})
            summaries.append({
                "id": lid, "name": layer.get("name"), "status": "SAMPLED",
                "features_returned": len(features), "valid_points": len(valid),
                "sample_limit": 100, "possibly_truncated": len(features) == 100,
                "raw_sha256": hashlib.sha256(layer_raw).hexdigest(),
                "first_two_points": valid[:2],
            })
        return {"status": "LAYERS_ENUMERATED", "layers": summaries,
                "total_valid_sample_points": sum(x.get("valid_points", 0) for x in summaries),
                "no_access_token_used": True}
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "LAYER_ENUMERATION_FAILED", "error_type": type(exc).__name__,
                "error": str(exc)[:180], "layers": [], "no_access_token_used": True}


def parse_usgs_metadata(item: dict) -> dict:
    if "Known Terrestrial Analog Sites for Planetary Science" not in item.get("title", ""):
        raise ValueError("USGS item title mismatch")
    files = []
    for f in item.get("files", []):
        files.append({
            "name": f.get("name"),
            "size_bytes": f.get("size"),
            "download_uri": f.get("downloadUri"),
            "content_type": f.get("contentType"),
        })
    return {
        "status": "METADATA_VERIFIED",
        "item_id": item.get("id"),
        "title": item["title"],
        "file_count": len(files),
        "files": files,
        "web_links": [{"title": w.get("title"), "uri": safe_public_service_url(w.get("uri") or "")} for w in item.get("webLinks", [])],
        "identifiers": [{"type": i.get("type"), "key": i.get("key")} for i in item.get("identifiers", [])],
        "coordinates_ingested": 0,
        "claim": "Metadata access only; no point-layer records parsed.",
    }




def probe_metadata_xml(files: list[dict]) -> dict:
    """Read the public USGS FGDC metadata and extract declared distribution URLs."""
    xml_files = [f for f in files if f.get("name", "").lower().endswith(".xml")]
    if not xml_files:
        return {"status": "NO_XML", "links": []}
    uri = xml_files[0].get("download_uri") or ""
    if not uri.startswith("https://www.sciencebase.gov/catalog/file/get/"):
        return {"status": "UNTRUSTED_URI", "links": []}
    try:
        with urlopen(Request(uri, headers={"User-Agent": "NASA-E227-Research/1.0"}), timeout=25) as response:
            raw = response.read(100_001)
        if len(raw) > 100_000:
            raise ValueError("FGDC metadata exceeds bounded limit")
        root = ET.fromstring(raw)
        links = []
        for element in root.iter():
            tag = element.tag.rsplit("}", 1)[-1].lower()
            value = (element.text or "").strip()
            if tag in {"onlink", "networkr", "linkage"} and value:
                links.append(value[:500])
        return {"status": "XML_VERIFIED", "bytes": len(raw),
                "links": sorted(set(links))[:40],
                "mentions_arcgis": bool(re.search(rb"arcgis|featureserver|shapefile", raw, re.I))}
    except (HTTPError, URLError, TimeoutError, ValueError, ET.ParseError) as exc:
        return {"status": "XML_ACCESS_FAILED", "error_type": type(exc).__name__,
                "error": str(exc)[:240], "links": []}


def probe_usgs_children() -> dict:
    """Discover actual data child items; the parent may hold only FGDC metadata."""
    url = (
        "https://www.sciencebase.gov/catalog/items?"
        f"filter=parentId={USGS_ITEM}&format=json&max=100"
    )
    try:
        with urlopen(Request(url, headers={"User-Agent": "NASA-E227-Research/1.0", "Accept": "application/json"}), timeout=25) as response:
            raw = response.read(3_000_001)
        if len(raw) > 3_000_000:
            raise ValueError("USGS child index exceeds bounded limit")
        index = json.loads(raw)
        children = []
        for item in index.get("items", [])[:20]:
            child_id = item.get("id")
            if not child_id:
                continue
            with urlopen(Request(
                f"https://www.sciencebase.gov/catalog/item/{child_id}?format=json",
                headers={"User-Agent": "NASA-E227-Research/1.0", "Accept": "application/json"},
            ), timeout=25) as response:
                child = json.loads(response.read(2_000_001))
            children.append({
                "id": child_id,
                "title": child.get("title"),
                "files": [
                    {"name": f.get("name"), "size_bytes": f.get("size"),
                     "download_uri": f.get("downloadUri"), "content_type": f.get("contentType")}
                    for f in child.get("files", [])
                ],
            })
        return {
            "status": "CHILD_INDEX_VERIFIED",
            "total_children_reported": index.get("total"),
            "children_examined": len(children),
            "children": children,
            "point_features_ingested": 0,
        }
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return {"status": "CHILD_INDEX_ACCESS_FAILED", "error_type": type(exc).__name__,
                "error": str(exc)[:240], "point_features_ingested": 0}


def probe_usgs() -> dict:
    req = Request(USGS_URL, headers={"User-Agent": "NASA-E227-Research/1.0", "Accept": "application/json"})
    try:
        with urlopen(req, timeout=25) as response:
            if response.status != 200:
                raise ValueError(f"Unexpected HTTP status {response.status}")
            raw = response.read(2_000_001)
        if len(raw) > 2_000_000:
            raise ValueError("Metadata exceeds bounded response limit")
        result = parse_usgs_metadata(json.loads(raw))
        result["child_index"] = probe_usgs_children()
        result["metadata_xml"] = probe_metadata_xml(result["files"])
        services = [w["uri"] for w in result["web_links"] if w.get("uri")]
        result["arcgis_public_sample"] = probe_public_arcgis(services[0] if services else None)
        result["arcgis_layers"] = probe_public_arcgis_layers(services[0] if services else None)
        return result
    except (HTTPError, URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
        return {
            "status": "ACCESS_FAILED",
            "item_id": USGS_ITEM,
            "source_url": USGS_URL,
            "error_type": type(exc).__name__,
            "error": str(exc)[:240],
            "coordinates_ingested": 0,
            "claim": "USGS point layer NOT INGESTED",
        }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DATA)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--probe-usgs", action="store_true")
    args = parser.parse_args()
    source = json.loads(args.input.read_text(encoding="utf-8"))
    result = {"experiment": "E227 independent analogue label access gate", "nasa_gallery": audit(source)}
    if args.probe_usgs:
        result["usgs"] = probe_usgs()
    payload = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    else:
        print(payload, end="")


if __name__ == "__main__":
    main()
