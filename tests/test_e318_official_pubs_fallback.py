"""Synthetic URL discovery controls, not planetary observations."""
from research.e318_official_pubs_fallback import discover, safe_zip, audit


def test_allow_only_official_zip():
    assert safe_zip("https://pubs.usgs.gov/of/2018/1164/dunes.zip")
    assert not safe_zip("https://evil.example/dunes.zip")
    assert not safe_zip("http://pubs.usgs.gov/of/2018/1164/dunes.zip")


def test_relative_official_links_discovered():
    page = "https://pubs.usgs.gov/of/2018/1164/"
    html = '<a href="dunes.zip">Data</a><a href="https://evil.example/dunes.zip">Bad</a>'
    assert discover(page, html) == [page + "dunes.zip"]


def test_untrusted_page_rejected():
    import pytest
    with pytest.raises(ValueError):
        discover("https://evil.example", '<a href="https://pubs.usgs.gov/dunes.zip">x</a>')


def test_no_link_is_honest_negative_result():
    result = audit(reader=lambda url, limit: b"<html>No ZIP here</html>")
    assert result["status"] == "NO_MARS_TABLES_PROFILED"
    assert result["e001_known_site_recovery"] == "NOT YET MEASURED"
