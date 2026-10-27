"""E320: source-fingerprinted PAAD geodesic proximity / split-contamination audit.

This does not establish shared geology, site identity or Earth–Mars similarity.
"""
from __future__ import annotations
import argparse
import csv
import io
import json
import math
from pathlib import Path
from research.e319_paad_mars_codebook_overlap import retrieve_paad

EARTH_RADIUS_KM = 6371.0088
THRESHOLDS_KM = (25, 50, 100)

def distance_km(a: tuple[float, float], b: tuple[float, float]) -> float:
    lat1, lon1 = map(math.radians, a)
    lat2, lon2 = map(math.radians, b)
    h = (math.sin((lat2-lat1)/2)**2
         + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2)
    return 2*EARTH_RADIUS_KM*math.asin(math.sqrt(min(1.0, max(0.0, h))))

def read_sites(raw: bytes) -> list[dict]:
    reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
    required = {"Field_Site", "Center_Latitude", "Center_Longitude"}
    if not reader.fieldnames or not required <= set(reader.fieldnames):
        raise ValueError("required columns absent")
    sites, seen = [], set()
    for row in reader:
        if not any((v or "").strip() for v in row.values() if isinstance(v, str)):
            continue
        name = (row.get("Field_Site") or "").strip()
        if not name or name in seen:
            raise ValueError("missing or duplicate site name")
        seen.add(name)
        try:
            lat, lon = float(row["Center_Latitude"]), float(row["Center_Longitude"])
        except (ValueError, TypeError) as exc:
            raise ValueError("non-numeric coordinate") from exc
        if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
            raise ValueError("invalid coordinate range")
        sites.append({"name": name, "lat": lat, "lon": lon})
        if len(sites) > 5000:
            raise ValueError("site count exceeded")
    return sites

def connected_groups(n: int, edges: list[tuple[int, int]]) -> list[list[int]]:
    parent = list(range(n))
    def root(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    for a, b in edges:
        ra, rb = root(a), root(b)
        if ra != rb:
            parent[max(ra, rb)] = min(ra, rb)
    groups = {}
    for i in range(n):
        groups.setdefault(root(i), []).append(i)
    return sorted(groups.values(), key=lambda g: min(g))

def audit(sites: list[dict]) -> dict:
    if not sites or len({s["name"] for s in sites}) != len(sites):
        raise ValueError("empty or duplicate site identities")
    pairs = []
    for i, a in enumerate(sites):
        for j in range(i+1, len(sites)):
            b = sites[j]
            pairs.append((distance_km((a["lat"],a["lon"]),(b["lat"],b["lon"])),i,j))
    pairs.sort(key=lambda p: (p[0],sites[p[1]]["name"],sites[p[2]]["name"]))
    summary = {}
    for threshold in THRESHOLDS_KM:
        edges = [(i,j) for d,i,j in pairs if d <= threshold]
        groups = connected_groups(len(sites), edges)
        multis = [g for g in groups if len(g)>1]
        summary[str(threshold)] = {
            "nearby_pairs": len(edges),
            "connected_groups": len(groups),
            "multi_site_groups": len(multis),
            "sites_in_multi_site_groups": sum(map(len,multis)),
            "max_group_size": max(map(len,groups)),
            "groups_with_multiple_sites": sorted([sorted(sites[i]["name"] for i in g) for g in multis]),
        }
    return {
        "site_count": len(sites), "pair_count": len(pairs),
        "nearest_pair_km": round(pairs[0][0],6) if pairs else None,
        "nearest_pair_site_names": sorted([sites[pairs[0][1]]["name"],sites[pairs[0][2]]["name"]]) if pairs else [],
        "thresholds_km": summary,
        "interpretation": "potential spatial split contamination, NOT proven shared geology or labels",
        "geodetic_accuracy": "NOT INDEPENDENTLY VERIFIED",
        "e001_known_site_recovery": "NOT YET MEASURED",
        "cross_body_similarity": "NOT YET PROVEN",
    }

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    raw,source = retrieve_paad()
    result = audit(read_sites(raw))
    result["source_receipt"] = source
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"sites":result["site_count"],"nearest_pair_km":result["nearest_pair_km"],"thresholds":result["thresholds_km"],"sha256":source["sha256"]},sort_keys=True))

if __name__ == "__main__":
    main()
