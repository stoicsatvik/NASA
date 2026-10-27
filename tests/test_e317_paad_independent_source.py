"""E317 deterministic controls; fixtures are synthetic, not geological observations."""
import csv
import io
import json
from zipfile import ZipFile

import pytest

from research.e317_paad_independent_source import (
    ITEM_ID, _csv_profile, _safe_url, audit, metadata_summary, profile,
)


def item(files=()):
    return {"id": ITEM_ID, "title": "PAAD: The Planetary Aeolian Analog Database",
            "files": list(files)}


def test_reject_wrong_item():
    with pytest.raises(ValueError):
        metadata_summary({"id": "wrong", "title": "Planetary Aeolian Analog Database"})


def test_only_allow_public_sciencebase_file_urls():
    assert _safe_url("https://www.sciencebase.gov/catalog/file/get/abc?name=table.csv")
    assert not _safe_url("https://evil.example/catalog/file/get/abc")
    assert not _safe_url("http://www.sciencebase.gov/catalog/file/get/abc")
    assert not _safe_url("https://www.sciencebase.gov@evil.example/catalog/file/get/abc")


def test_csv_bounded_header_and_count():
    p = _csv_profile(b"name,latitude,longitude\nA,10,20\nB,30,40\n", "sites.csv")
    assert p["rows"] == 2
    assert p["columns"] == ["name", "latitude", "longitude"]


def test_zip_table_is_profiled_without_invented_site_labels():
    b = io.BytesIO()
    with ZipFile(b, "w") as z:
        z.writestr("data/sites.csv", "site,latitude,longitude\nA,1,2\nB,3,4\n")
    tables = profile(b.getvalue(), "dataset.zip")
    assert len(tables) == 1
    assert tables[0]["rows"] == 2


def test_audit_only_reports_observed_rows():
    url = "https://www.sciencebase.gov/catalog/file/get/abc"
    metadata = item([{"name": "sites.csv", "size": 100, "downloadUri": url}])
    result = audit(metadata, downloader=lambda _: b"site,latitude\nA,10\nB,20\n")
    assert result["site_rows_observed"] == 2
    assert result["e001_known_site_recovery"] == "NOT YET MEASURED"
    assert result["cross_body_similarity"] == "NOT YET PROVEN"
    assert all("_uri" not in record for record in result["files"])


def test_untrusted_uri_is_not_downloaded():
    metadata = item([{"name": "sites.csv", "size": 100,
                      "downloadUri": "https://evil.example/sites.csv"}])
    result = audit(metadata, downloader=lambda _: pytest.fail("unexpected download"))
    assert result["site_rows_observed"] == 0
    assert result["status"] == "NO_TABULAR_SOURCE_PROFILED"


def test_real_schema_coordinate_completeness_controls():
    raw = ("\\n".join([
        "Field_Site,Center_Latitude,Center_Longitude,Dune_Type,References",
        "Alpha,19.5,76.1,barchan,doi:1",
        "Beta,not-a-lat,71.0,linear,",
        "Gamma,90.1,50.0,barchan,doi:3",
        "Delta,20.0,75.0,,",
    ]) + "\\n").encode()
    result = _csv_profile(raw, "sites.csv")
    assert result["rows"] == 4
    assert result["valid_numeric_coordinate_pairs"] == 2
    assert result["invalid_or_missing_coordinate_pairs"] == 2
    assert result["distinct_nonempty_site_names"] == 4
    assert result["dune_type_categories"] == {"barchan": 2, "linear": 1}
    assert result["nonempty_by_field"]["References"] == 2
