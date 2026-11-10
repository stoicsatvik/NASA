from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import re
import shutil
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


ITEM_ID = "64d418c3d34ef477cf3ced10"
DOI = "10.5066/P9IFVZEX"
SOURCE_PAGE = "https://www.usgs.gov/data/paad-planetary-aeolian-analog-database"
ITEM_URL = f"https://www.sciencebase.gov/catalog/item/{ITEM_ID}?format=json"
DOWNLOAD_URL = f"https://www.sciencebase.gov/catalog/file/get/{ITEM_ID}"
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024
USER_AGENT = "NASA-Analog-Research/0.1 (public USGS PAAD provenance ingestion)"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch_bytes(url: str, *, max_bytes: int = MAX_DOWNLOAD_BYTES) -> tuple[bytes, dict[str, str]]:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/zip, */*"},
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        length = response.headers.get("Content-Length")
        if length and int(length) > max_bytes:
            raise ValueError(f"download exceeds {max_bytes} byte safety limit: {length}")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise ValueError(f"stream exceeded {max_bytes} byte safety limit")
            chunks.append(chunk)
        headers = {key.lower(): value for key, value in response.headers.items()}
    payload = b"".join(chunks)
    if not payload:
        raise RuntimeError(f"empty response from {url}")
    return payload, headers


def collect_file_info(item: dict[str, Any]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def add(files: Any) -> None:
        if not isinstance(files, list):
            return
        for entry in files:
            if not isinstance(entry, dict):
                continue
            name = str(entry.get("name") or "").strip()
            url = str(entry.get("url") or "").strip()
            if not name or not url:
                continue
            key = (name, url)
            if key in seen:
                continue
            seen.add(key)
            found.append({
                "name": name,
                "url": url,
                "size": entry.get("size"),
                "content_type": entry.get("contentType"),
            })

    add(item.get("files"))
    facets = item.get("facets")
    if isinstance(facets, list):
        for facet in facets:
            if isinstance(facet, dict):
                add(facet.get("files"))
    elif isinstance(facets, dict):
        for facet in facets.values():
            if isinstance(facet, dict):
                add(facet.get("files"))
    return found


def validate_item(item: dict[str, Any]) -> None:
    if str(item.get("id") or "") != ITEM_ID:
        raise ValueError("ScienceBase item ID does not match the frozen PAAD source")
    title = str(item.get("title") or "")
    if "PAAD" not in title.upper() and "PLANETARY AEOLIAN ANALOG DATABASE" not in title.upper():
        raise ValueError(f"unexpected ScienceBase item title: {title!r}")


def safe_extract_zip(payload: bytes, destination: Path) -> list[Path]:
    extracted: list[Path] = []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"corrupt archive member: {bad}")
        for info in archive.infolist():
            raw = info.filename.replace("\\", "/")
            member = PurePosixPath(raw)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError(f"unsafe archive path rejected: {info.filename!r}")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == 0o120000:
                raise ValueError(f"symlink archive member rejected: {info.filename!r}")
            if not member.parts:
                continue
            target = destination.joinpath(*member.parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as src, target.open("wb") as dst:
                shutil.copyfileobj(src, dst)
            extracted.append(target)
    return extracted


def extract_nested_zips(root: Path, *, max_depth: int = 3) -> None:
    for _ in range(max_depth):
        archives = sorted(path for path in root.rglob("*.zip") if path.is_file())
        pending = [path for path in archives if not path.with_suffix("").joinpath(".extracted").exists()]
        if not pending:
            return
        for archive_path in pending:
            target = archive_path.with_suffix("")
            target.mkdir(parents=True, exist_ok=True)
            payload = archive_path.read_bytes()
            safe_extract_zip(payload, target)
            (target / ".extracted").write_text("ok\n", encoding="utf-8")


def missing_counts(rows: list[dict[str, Any]], fields: list[str]) -> dict[str, int]:
    missing_tokens = {"", "na", "n/a", "null", "none", "nan"}
    result: dict[str, int] = {}
    for field in fields:
        count = 0
        for row in rows:
            value = row.get(field)
            if value is None or (isinstance(value, str) and value.strip().lower() in missing_tokens):
                count += 1
        result[field] = count
    return result


def normalise_key(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def inspect_csv(path: Path) -> dict[str, Any] | None:
    delimiter = "\t" if path.suffix.lower() in {".tsv", ".tab"} else ","
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            if not reader.fieldnames:
                return None
            fields = [str(value) for value in reader.fieldnames]
            rows = [dict(row) for row in reader]
    except (UnicodeDecodeError, csv.Error):
        return None
    if not rows:
        return None
    return {
        "source_file": str(path),
        "format": "tsv" if delimiter == "\t" else "csv",
        "record_count": len(rows),
        "fields": fields,
        "field_metadata": [{"name": field, "type": "source-text", "unit_status": "NOT_DOCUMENTED_IN_SOURCE_SCHEMA"} for field in fields],
        "missing_counts": missing_counts(rows, fields),
        "sample_rows": rows[:5],
        "rows": rows,
        "crs_wkt": None,
        "geometry_type": None,
        "bbox": None,
    }


def inspect_geojson(path: Path) -> dict[str, Any] | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None
    features = data.get("features") if isinstance(data, dict) else data
    if not isinstance(features, list) or not features:
        return None
    rows: list[dict[str, Any]] = []
    fields: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            continue
        properties = feature.get("properties") or {}
        if not isinstance(properties, dict):
            properties = {}
        row = dict(properties)
        geometry = feature.get("geometry")
        if geometry is not None:
            row["__geometry_json"] = json.dumps(geometry, sort_keys=True, separators=(",", ":"))
        rows.append(row)
        fields.update(row)
    ordered = sorted(fields)
    if not rows:
        return None
    return {
        "source_file": str(path),
        "format": "geojson",
        "record_count": len(rows),
        "fields": ordered,
        "field_metadata": [{"name": field, "type": "source-json", "unit_status": "NOT_DOCUMENTED_IN_SOURCE_SCHEMA"} for field in ordered],
        "missing_counts": missing_counts(rows, ordered),
        "sample_rows": rows[:5],
        "rows": rows,
        "crs_wkt": None,
        "geometry_type": "GeoJSON",
        "bbox": data.get("bbox") if isinstance(data, dict) else None,
    }


def inspect_shapefile(path: Path) -> dict[str, Any] | None:
    try:
        import shapefile
    except ImportError as exc:
        raise RuntimeError("pyshp is required to inspect PAAD shapefiles") from exc
    reader = shapefile.Reader(str(path))
    field_specs = reader.fields[1:]
    fields = [str(spec[0]) for spec in field_specs]
    rows: list[dict[str, Any]] = []
    for record, shape in zip(reader.records(), reader.shapes()):
        row = dict(zip(fields, list(record)))
        row["__geometry_json"] = json.dumps(shape.__geo_interface__, sort_keys=True, separators=(",", ":"))
        rows.append(row)
    if not rows:
        return None
    prj = path.with_suffix(".prj")
    crs_wkt = prj.read_text(encoding="utf-8", errors="replace").strip() if prj.exists() else None
    bbox = list(reader.bbox) if reader.bbox else None
    return {
        "source_file": str(path),
        "format": "shapefile",
        "record_count": len(rows),
        "fields": fields + ["__geometry_json"],
        "field_metadata": [
            {"name": str(spec[0]), "type": str(spec[1]), "width": spec[2], "decimals": spec[3], "unit_status": "NOT_DOCUMENTED_IN_SOURCE_SCHEMA"}
            for spec in field_specs
        ] + [{"name": "__geometry_json", "type": "geometry", "unit_status": "SEE_CRS_WKT"}],
        "missing_counts": missing_counts(rows, fields),
        "sample_rows": rows[:5],
        "rows": rows,
        "crs_wkt": crs_wkt,
        "geometry_type": reader.shapeTypeName,
        "bbox": bbox,
    }


def inspect_xlsx(path: Path) -> dict[str, Any] | None:
    try:
        from openpyxl import load_workbook
    except ImportError as exc:
        raise RuntimeError("openpyxl is required to inspect PAAD workbooks") from exc
    workbook = load_workbook(path, read_only=True, data_only=True)
    candidates: list[dict[str, Any]] = []
    for sheet in workbook.worksheets:
        values = sheet.iter_rows(values_only=True)
        header = next(values, None)
        if not header:
            continue
        fields = [str(value).strip() if value is not None else f"column_{index+1}" for index, value in enumerate(header)]
        rows = []
        for values_row in values:
            if not values_row or not any(value is not None for value in values_row):
                continue
            rows.append({field: values_row[index] if index < len(values_row) else None for index, field in enumerate(fields)})
        if rows:
            candidates.append({
                "source_file": str(path),
                "format": f"xlsx:{sheet.title}",
                "record_count": len(rows),
                "fields": fields,
                "field_metadata": [{"name": field, "type": "spreadsheet-cell", "unit_status": "NOT_DOCUMENTED_IN_SOURCE_SCHEMA"} for field in fields],
                "missing_counts": missing_counts(rows, fields),
                "sample_rows": rows[:5],
                "rows": rows,
                "crs_wkt": None,
                "geometry_type": None,
                "bbox": None,
            })
    workbook.close()
    return max(candidates, key=lambda item: (item["record_count"], len(item["fields"]))) if candidates else None


def inspect_tables(root: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for path in sorted(path for path in root.rglob("*") if path.is_file()):
        suffix = path.suffix.lower()
        candidate = None
        if suffix in {".csv", ".tsv", ".tab"}:
            candidate = inspect_csv(path)
        elif suffix in {".geojson", ".json"}:
            candidate = inspect_geojson(path)
        elif suffix == ".shp":
            candidate = inspect_shapefile(path)
        elif suffix == ".xlsx":
            candidate = inspect_xlsx(path)
        if candidate is not None:
            candidate["source_file"] = str(path.relative_to(root))
            candidates.append(candidate)
    return candidates


def write_normalized_csv(path: Path, candidate: dict[str, Any]) -> None:
    rows = candidate["rows"]
    fields = list(candidate["fields"])
    if "source_file" not in fields:
        fields.append("source_file")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            record = dict(row)
            record["source_file"] = candidate["source_file"]
            writer.writerow(record)


def build_receipt(out_dir: Path, *, max_bytes: int, expected_sites: int) -> dict[str, Any]:
    item_payload, _ = fetch_bytes(ITEM_URL, max_bytes=5 * 1024 * 1024)
    item = json.loads(item_payload)
    validate_item(item)
    file_info = collect_file_info(item)
    if not file_info:
        raise RuntimeError("ScienceBase item JSON contains no attached files in files or facets")
    known_sizes = [int(entry["size"]) for entry in file_info if entry.get("size") is not None]
    declared_total = sum(known_sizes)
    if declared_total and declared_total > max_bytes:
        raise ValueError(f"declared ScienceBase files total {declared_total} bytes, above safety limit {max_bytes}")

    archive_payload, archive_headers = fetch_bytes(DOWNLOAD_URL, max_bytes=max_bytes)
    if not zipfile.is_zipfile(io.BytesIO(archive_payload)):
        preview = archive_payload[:160].decode("utf-8", "replace")
        raise ValueError(f"ScienceBase file/get response is not a ZIP archive: {preview!r}")

    raw_dir = out_dir / "raw"
    if raw_dir.exists():
        shutil.rmtree(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    extracted = safe_extract_zip(archive_payload, raw_dir)
    extract_nested_zips(raw_dir)
    candidates = inspect_tables(raw_dir)
    if not candidates:
        raise RuntimeError("downloaded PAAD files contain no parseable CSV, GeoJSON, shapefile or XLSX table")

    primary = max(
        candidates,
        key=lambda item: (
            item["record_count"] == expected_sites,
            item["record_count"],
            len(item["fields"]),
            item["format"] == "shapefile",
        ),
    )
    normalized_path = out_dir / "paad_sites.csv"
    write_normalized_csv(normalized_path, primary)

    extracted_manifest = []
    for path in sorted(path for path in raw_dir.rglob("*") if path.is_file()):
        if path.name == ".extracted":
            continue
        payload = path.read_bytes()
        extracted_manifest.append({
            "path": str(path.relative_to(raw_dir)),
            "size_bytes": len(payload),
            "sha256": sha256(payload),
        })

    summary = {
        "title": item.get("title"),
        "summary": item.get("summary"),
        "citation": item.get("citation"),
        "provenance": item.get("provenance"),
        "rights": item.get("rights"),
        "contacts": item.get("contacts"),
        "dates": item.get("dates"),
    }
    return {
        "schema_version": "paad-sciencebase-ingestion-v1",
        "status": "INGESTED",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {
            "provider": "U.S. Geological Survey",
            "title": item.get("title"),
            "item_id": ITEM_ID,
            "item_url": ITEM_URL,
            "download_endpoint": DOWNLOAD_URL,
            "data_release_page": SOURCE_PAGE,
            "doi": DOI,
            "license": "CC0 1.0 Universal",
            "license_verification_source": SOURCE_PAGE,
            "release_description": "USGS describes PAAD v1 as 45 global dune-field analog sites with core bedform, climate, sand-source, sand-composition, latitude, longitude, average-elevation and approximate-areal-coverage attributes.",
        },
        "source_item_json_sha256": sha256(item_payload),
        "download_archive_sha256": sha256(archive_payload),
        "download_archive_size_bytes": len(archive_payload),
        "download_content_type": archive_headers.get("content-type"),
        "declared_file_info": file_info,
        "declared_file_total_bytes": declared_total,
        "extracted_files": extracted_manifest,
        "source_metadata_summary": summary,
        "expected_site_count_from_release_page": expected_sites,
        "primary_table": {
            "source_file": primary["source_file"],
            "format": primary["format"],
            "record_count": primary["record_count"],
            "count_matches_release_description": primary["record_count"] == expected_sites,
            "fields": primary["fields"],
            "field_metadata": primary["field_metadata"],
            "missing_counts": primary["missing_counts"],
            "geometry_type": primary["geometry_type"],
            "bbox": primary["bbox"],
            "crs_wkt": primary["crs_wkt"],
            "units_status": "Units are not inferred. Each field remains NOT_DOCUMENTED_IN_SOURCE_SCHEMA unless the source file itself documents them.",
            "sample_rows": primary["sample_rows"],
            "normalized_csv": "paad_sites.csv",
        },
        "all_table_candidates": [
            {key: value for key, value in candidate.items() if key not in {"rows", "sample_rows"}}
            for candidate in candidates
        ],
        "warnings": [] if primary["record_count"] == expected_sites else [
            f"Primary table has {primary['record_count']} rows; USGS release page describes {expected_sites} sites. Do not silently force equality."
        ],
        "raw_data_policy": "Raw downloads remain in the workflow workspace; the artifact contains the normalized CC0 site table, metadata receipt and file hashes. No fabricated field observations are added.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Acquire and inspect the public USGS Planetary Aeolian Analog Database (PAAD).")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--max-bytes", type=int, default=MAX_DOWNLOAD_BYTES)
    parser.add_argument("--expected-sites", type=int, default=45)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    receipt_path = args.out / "paad_ingestion_receipt.json"
    try:
        receipt = build_receipt(args.out, max_bytes=args.max_bytes, expected_sites=args.expected_sites)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
        print(json.dumps({
            "status": receipt["status"],
            "item_id": ITEM_ID,
            "archive_sha256": receipt["download_archive_sha256"],
            "primary_format": receipt["primary_table"]["format"],
            "record_count": receipt["primary_table"]["record_count"],
            "count_matches_release_description": receipt["primary_table"]["count_matches_release_description"],
            "fields": receipt["primary_table"]["fields"],
            "missing_counts": receipt["primary_table"]["missing_counts"],
            "crs_wkt_present": bool(receipt["primary_table"]["crs_wkt"]),
            "normalized_csv": "paad_sites.csv",
        }, indent=2, sort_keys=True))
        return 0
    except Exception as exc:
        failure = {
            "schema_version": "paad-sciencebase-ingestion-v1",
            "status": "FAILED",
            "retrieved_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "source": {"item_id": ITEM_ID, "item_url": ITEM_URL, "doi": DOI, "data_release_page": SOURCE_PAGE},
            "error_type": type(exc).__name__,
            "error": str(exc),
            "claim_boundary": "No data ingestion is claimed when the source fetch or parsing fails.",
        }
        receipt_path.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(failure, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
