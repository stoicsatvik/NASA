from __future__ import annotations

import argparse, csv, hashlib, io, json, re, urllib.parse, urllib.request, zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SOURCE_PAGE = "https://pubs.usgs.gov/publication/ofr20181164"
ARCHIVE_URL = "https://pubs.usgs.gov/of/2018/1164/ofr20181164_dunedatabase.zip"
SOURCE_DOI = "10.3133/ofr20181164"
EXPECTED_E318_SHA256 = "92771c23cfa4a64dfcc38f5ad29de00adfa41b9f321d3665beb2112eefe3485e"
MAX_ARCHIVE_BYTES = 10 * 1024 * 1024
USER_AGENT = "NASA-Analog-Research/0.1 (public USGS MGD3 2018 join)"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_archive_url(url: str) -> bool:
    p = urllib.parse.urlparse(url)
    return p.scheme == "https" and p.hostname == "pubs.usgs.gov" and p.path.startswith("/of/2018/1164/") and p.path.lower().endswith(".zip")


def fetch_archive(url: str = ARCHIVE_URL, limit: int = MAX_ARCHIVE_BYTES) -> tuple[bytes, str]:
    if not safe_archive_url(url):
        raise ValueError(f"non-canonical USGS 2018 MGD3 URL: {url}")
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/zip, */*"})
    with urllib.request.urlopen(req, timeout=120) as response:
        final = response.geturl()
        if not safe_archive_url(final):
            raise ValueError(f"redirect outside official USGS report path: {final}")
        length = response.headers.get("Content-Length")
        if length and int(length) > limit:
            raise ValueError(f"2018 archive exceeds byte limit: {length}")
        chunks, total = [], 0
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > limit:
                raise ValueError(f"2018 archive exceeded byte limit: {total}")
            chunks.append(chunk)
    payload = b"".join(chunks)
    if not payload.startswith(b"PK\x03\x04"):
        raise ValueError("USGS 2018 response is not a ZIP archive")
    return payload, final


def normalize_id(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "na", "n/a"}:
        return None
    if text.endswith(".0") and text[:-2].isdigit():
        text = text[:-2]
    return text


def decode_dune_id(value: Any) -> dict[str, float] | None:
    """Decode the documented MGD3 Dune_ID coordinate code, not a measured position."""
    text = normalize_id(value)
    if text is None:
        return None
    match = re.fullmatch(r"(\d{4})([+-])(\d{3})", text)
    if not match:
        return None
    longitude_tenths = int(match.group(1))
    latitude_tenths = int(match.group(3))
    if longitude_tenths > 3600 or latitude_tenths > 900:
        return None
    latitude = latitude_tenths / 10.0
    if match.group(2) == "-":
        latitude = -latitude
    return {
        "longitude_east_deg": longitude_tenths / 10.0,
        "latitude_aerocentric_deg": latitude,
    }


def summarize_dune_ids(values: set[str] | list[str]) -> dict[str, Any]:
    ordered_values = sorted(str(value) for value in values)
    decoded = [decode_dune_id(value) for value in ordered_values]
    valid = [item for item in decoded if item is not None]
    latitudes = [item["latitude_aerocentric_deg"] for item in valid]
    unparsed = [value for value, item in zip(ordered_values, decoded) if item is None]
    return {
        "encoding": "four longitude digits in 0.1-degree units, followed by signed three-digit latitude in 0.1-degree units",
        "coordinate_semantics": "identifier-derived centroid coordinates; not an independent geometry or positional-accuracy measurement",
        "decoded_id_count": len(valid),
        "unparsed_id_count": len(unparsed),
        "latitude_min_deg": min(latitudes) if latitudes else None,
        "latitude_max_deg": max(latitudes) if latitudes else None,
        "within_2007_65S_65N_count": sum(-65.0 <= value <= 65.0 for value in latitudes),
        "south_of_65S_count": sum(value < -65.0 for value in latitudes),
        "north_of_65N_count": sum(value > 65.0 for value in latitudes),
        "at_65_degree_boundary_count": sum(abs(value) == 65.0 for value in latitudes),
        "unparsed_id_samples": unparsed[:5],
    }


def _dune_id_field(fieldnames: list[str]) -> str | None:
    exact = [
        field for field in fieldnames
        if re.sub(r"[^a-z0-9]", "", field.lower()) in {"duneid", "dunefieldid", "dfid"}
    ]
    if exact:
        return exact[0] if len(exact) == 1 else None
    candidates = [
        field for field in fieldnames
        if "dune" in field.lower()
        and re.search(r"(?:^|[^a-z])id(?:$|[^a-z])", field.lower())
    ]
    return candidates[0] if len(candidates) == 1 else None


def read_spatial_ids(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("2007 spatial CSV has no header")
        id_field = _dune_id_field(reader.fieldnames)
        if not id_field:
            raise ValueError("2007 spatial CSV lacks Dune_ID or has ambiguous Dune_ID fields")
        ids = {value for row in reader if (value := normalize_id(row.get(id_field))) is not None}
    if not ids:
        raise ValueError("2007 spatial CSV has no nonempty dune IDs")
    return ids


def _header_index(rows: list[tuple[Any, ...]]) -> tuple[int, list[str], int] | None:
    for row_index, row in enumerate(rows):
        fields = [str(value).strip() if value is not None else f"column_{i+1}" for i, value in enumerate(row)]
        normalized = [field.lower().replace("_", "").replace(" ", "") for field in fields]
        candidates = [i for i, field in enumerate(normalized) if field in {"duneid", "dunefieldid"}]
        if len(candidates) == 1:
            return row_index, fields, candidates[0]
    return None


def profile_workbook(payload: bytes, source_name: str, spatial_ids: set[str]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from openpyxl import load_workbook
    workbook = load_workbook(io.BytesIO(payload), read_only=True, data_only=True)
    profiles, joined_rows = [], []
    try:
        for sheet in workbook.worksheets:
            first_rows = list(sheet.iter_rows(min_row=1, max_row=min(12, sheet.max_row or 12), values_only=True))
            header = _header_index(first_rows)
            if header is None:
                continue
            header_row, fields, id_index = header
            total_rows, missing_ids, ids, non_data_note_rows, non_data_note_samples = 0, 0, [], 0, []
            for row in sheet.iter_rows(min_row=header_row + 2, values_only=True):
                if not row or not any(value is not None and str(value).strip() for value in row):
                    continue
                total_rows += 1
                value = row[id_index] if id_index < len(row) else None
                dune_id = normalize_id(value)
                if dune_id is None:
                    missing_ids += 1
                    continue
                if decode_dune_id(dune_id) is None and (len(dune_id) > 40 or any(character.isspace() for character in dune_id)):
                    non_data_note_rows += 1
                    if len(non_data_note_samples) < 3:
                        non_data_note_samples.append(dune_id[:160])
                    continue
                ids.append(dune_id)
                record = {fields[i]: (str(row[i]) if i < len(row) and row[i] is not None else None) for i in range(len(fields))}
                joined_rows.append({
                    "workbook": source_name,
                    "sheet": sheet.title,
                    "dune_id": dune_id,
                    "matched_2007_spatial": dune_id in spatial_ids,
                    "row_json": json.dumps(record, sort_keys=True, separators=(",", ":")),
                })
            unique = set(ids)
            matched = unique & spatial_ids
            profiles.append({
                "workbook": source_name,
                "sheet": sheet.title,
                "header_row_1based": header_row + 1,
                "id_field": fields[id_index],
                "worksheet_rows_not_unique_sites": total_rows,
                "nonempty_id_rows": len(ids) + non_data_note_rows,
                "valid_dune_id_rows": len(ids),
                "missing_id_rows": missing_ids,
                "non_data_note_rows": non_data_note_rows,
                "non_data_note_samples": non_data_note_samples,
                "unparsed_encoding_id_rows": sum(decode_dune_id(value) is None for value in ids),
                "unique_ids": len(unique),
                "duplicate_id_rows": len(ids) - len(unique),
                "decoded_id_geography": summarize_dune_ids(unique),
                "matched_2007_spatial_unique_ids": len(matched),
                "unmatched_2018_unique_ids": len(unique - spatial_ids),
                "2007_spatial_ids_absent_from_sheet": len(spatial_ids - unique),
                "sample_matched_ids": sorted(matched)[:10],
                "fields": fields,
            })
    finally:
        workbook.close()
    return profiles, joined_rows


def inspect_archive(payload: bytes, spatial_ids: set[str]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    profiles, joined_rows, files = [], [], []
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        bad = archive.testzip()
        if bad:
            raise ValueError(f"2018 MGD3 archive CRC failure: {bad}")
        for info in archive.infolist():
            name = info.filename.replace("\\", "/")
            if info.is_dir() or name.startswith("__MACOSX/") or "/._" in name or name.startswith("._"):
                continue
            if not name.lower().endswith(".xlsx"):
                continue
            if info.file_size > MAX_ARCHIVE_BYTES:
                files.append({"name": name, "status": "OVERSIZED_WORKBOOK", "bytes": info.file_size})
                continue
            data = archive.read(info)
            try:
                workbook_profiles, rows = profile_workbook(data, name, spatial_ids)
                files.append({"name": name, "status": "PARSED", "bytes": len(data), "worksheets_with_dune_ids": len(workbook_profiles)})
                profiles.extend(workbook_profiles)
                joined_rows.extend(rows)
            except Exception as exc:
                files.append({"name": name, "status": "PARSE_FAILED", "error_type": type(exc).__name__, "error": str(exc)})
    matched_sheets = [profile for profile in profiles if profile["matched_2007_spatial_unique_ids"] > 0]
    return {
        "files": files,
        "worksheet_profiles": profiles,
        "worksheets_with_dune_id": len(profiles),
        "worksheets_with_2007_id_matches": len(matched_sheets),
        "unique_matched_ids_union": len({row["dune_id"] for row in joined_rows if row["matched_2007_spatial"]}),
        "rows_with_ids": len(joined_rows),
        "claim_boundary": "An identifier join establishes cross-release record linkage only. It does not establish shared physical descriptors, analogue labels, or E001 recovery.",
    }, joined_rows


def build_receipt(spatial_csv: Path, out: Path) -> dict[str, Any]:
    spatial_ids = read_spatial_ids(spatial_csv)
    payload, final_url = fetch_archive()
    digest = sha256(payload)
    audit, joined_rows = inspect_archive(payload, spatial_ids)
    csv_path = out / "mgd3_2018_id_join.csv"
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["workbook", "sheet", "dune_id", "matched_2007_spatial", "row_json"])
        writer.writeheader()
        writer.writerows(joined_rows)
    return {
        "schema_version": "mgd3-2018-id-join-v2",
        "experiment": "E528_MGD3_2018_TO_2007_DUNE_ID_JOIN",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": {"report_page": SOURCE_PAGE, "archive_url": ARCHIVE_URL, "final_url": final_url, "doi": SOURCE_DOI, "publisher": "U.S. Geological Survey"},
        "id_encoding_basis": {
            "description": "Dune_ID encodes east longitude first, then signed aerocentric latitude, each to one decimal place",
            "sources": ["USGS Open-File Report 2007-1158 ReadMe_GIS", "USGS Open-File Report 2012-1259 South Polar Dune_Field metadata"],
            "warning": "Decoded values are identifier-derived and are not independent coordinates or positional-accuracy measurements.",
        },
        "archive": {"bytes": len(payload), "sha256": digest, "matches_prior_e318_receipt": digest == EXPECTED_E318_SHA256, "expected_e318_sha256": EXPECTED_E318_SHA256},
        "spatial_2007": {"csv": str(spatial_csv), "unique_dune_ids": len(spatial_ids), "decoded_id_geography": summarize_dune_ids(spatial_ids)},
        **audit,
        "normalized_join_table": {"path": csv_path.name, "rows": len(joined_rows)},
        "status": "JOINED" if audit["unique_matched_ids_union"] > 0 else "NO_MATCHED_IDS",
        "cross_body_similarity": "NOT YET PROVEN",
        "e001_known_site_recovery": "NOT YET MEASURED",
        "novel_analogue_discovery": "NOT YET PROVEN",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Join official USGS 2018 MGD3 workbook records to the 2007 MGD3 spatial Dune_ID index.")
    parser.add_argument("--spatial-csv", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    receipt_path = args.out / "mgd3_2018_id_join_receipt.json"
    try:
        receipt = build_receipt(args.spatial_csv, args.out)
        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps({"status": receipt["status"], "archive_sha256": receipt["archive"]["sha256"], "spatial_ids": receipt["spatial_2007"]["unique_dune_ids"], "worksheets": receipt["worksheets_with_dune_id"], "matched_union": receipt["unique_matched_ids_union"], "join_rows": receipt["normalized_join_table"]["rows"]}, sort_keys=True))
        return 0 if receipt["status"] == "JOINED" else 1
    except Exception as exc:
        failure = {"schema_version": "mgd3-2018-id-join-v2", "experiment": "E528_MGD3_2018_TO_2007_DUNE_ID_JOIN", "retrieved_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "source": {"report_page": SOURCE_PAGE, "archive_url": ARCHIVE_URL, "doi": SOURCE_DOI}, "status": "FAILED", "error_type": type(exc).__name__, "error": str(exc), "claim_boundary": "No cross-release join is claimed when the archive cannot be retrieved or parsed."}
        receipt_path.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(json.dumps(failure, indent=2, sort_keys=True))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
