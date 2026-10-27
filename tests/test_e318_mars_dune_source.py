"""Synthetic structural controls; no geological measurements are fabricated."""
import io
from zipfile import ZipFile

import pytest
from research.e318_mars_dune_source import (
    ITEM_ID, allowed_file_url, select_files, profile_table, audit, MAX_EXPANDED,
)


def item(files=()):
    return {"id": ITEM_ID, "title": "Mars Dune Digital Database - Merged", "files": list(files)}


def test_item_identity_must_match():
    with pytest.raises(ValueError):
        select_files({"id": "wrong", "title": "Mars dune", "files": []})


def test_no_cross_host_or_insecure_urls():
    assert allowed_file_url("https://www.sciencebase.gov/catalog/file/get/abc")
    assert not allowed_file_url("https://evil.example/catalog/file/get/abc")
    assert not allowed_file_url("http://www.sciencebase.gov/catalog/file/get/abc")
    assert not allowed_file_url("https://www.sciencebase.gov@evil.example/catalog/file/get/abc")


def test_csv_raw_morphology_not_inferred():
    t = profile_table(b"Dune_Type,Site,Other\nB,A,1\nL,B,2\nB,C,\n", "dunes.csv")[0]
    assert t["rows"] == 3
    assert t["dune_type_raw_codes"] == {"Dune_Type": {"B": 2, "L": 1}}
    assert t["codebook_interpretation"].startswith("UNVERIFIED")


def test_zip_dbf_and_csv_profiles_only_data_members():
    f = io.BytesIO()
    with ZipFile(f, "w") as z:
        z.writestr("data/field.csv", "DuneType,ID\nB,1\nP,2\n")
        z.writestr("data/image.jpg", b"not a table")
    p = profile_table(f.getvalue(), "dunes.zip")
    assert len(p) == 1 and p[0]["rows"] == 2


def test_expanded_bound_enforced():
    with pytest.raises(ValueError):
        profile_table(b"a" * (MAX_EXPANDED + 1), "dunes.csv")


def test_audit_never_promotes_to_e001():
    url = "https://www.sciencebase.gov/catalog/file/get/abc"
    data = item([{"name": "dunes.csv", "size": 50, "downloadUri": url}])
    result = audit(data, downloader=lambda _, __: b"Dune_Type,ID\nB,1\n")
    assert result["status"] == "REAL_MARS_TABLES_PROFILED"
    assert result["total_table_rows_not_unique_sites"] == 1
    assert result["e001_known_site_recovery"] == "NOT YET MEASURED"
    assert result["cross_body_similarity"] == "NOT YET PROVEN"
    assert "uri" not in result["file_receipts"][0]


def test_unknown_and_oversize_files_never_downloaded():
    data = item([{"name": "dunes.csv", "size": 50, "downloadUri": "https://evil.example/a"},
                 {"name": "big.zip", "size": 100_000_000,
                  "downloadUri": "https://www.sciencebase.gov/catalog/file/get/abc"}])
    result = audit(data, downloader=lambda *_: pytest.fail("unexpected download"))
    assert result["status"] == "NO_MARS_TABLES_PROFILED"
    assert [r["status"] for r in result["file_receipts"]] == ["NOT_ELIGIBLE", "NOT_ELIGIBLE"]
