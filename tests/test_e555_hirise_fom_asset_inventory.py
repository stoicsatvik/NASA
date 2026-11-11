"""Deterministic tests for E555 metadata inventory; no network or raster access."""
import pytest

from experiments.e555_hirise_fom_asset_inventory import (
    classify_asset_names,
    classify_fom_availability,
    parse_asset_index,
    scan_metadata,
    E555Error,
    DTM_STEM,
)


def test_directory_index_finds_pinned_product_and_metadata_files():
    html = f"""
    <html><body>
      <a href="/mosaic/mars2020_trn/HiRISE/{DTM_STEM}.tif">DTM</a>
      <a href="/mosaic/mars2020_trn/HiRISE/{DTM_STEM}.xml">XML</a>
      <a href="/mosaic/mars2020_trn/HiRISE/{DTM_STEM}_pds3.lbl">Label</a>
      <a href="/mosaic/mars2020_trn/HiRISE/ortho.tif">Ortho</a>
    </body></html>
    """.encode()
    assets = parse_asset_index(html)
    assert len(assets) == 4
    assert DTM_STEM + ".tif" in assets


def test_fom_asset_names_are_distinguished_from_ordinary_rasters():
    summary = classify_asset_names([
        "surface.tif",
        "surface_FOM.tif",
        "surface_provenance.xml",
        "hillshade.tif",
    ])
    assert summary["fom_assets"] == ["surface_FOM.tif"]
    assert summary["fom_asset_count"] == 1
    assert summary["provenance_or_quality_asset_count"] == 3


def test_metadata_scan_records_line_numbers_without_retaining_raw_text():
    scan = scan_metadata(b"PRODUCT_ID = TEST\nFOM_IMAGE = NONE\nMISSING_CONSTANT = -9999\n")
    assert scan["fom_reference_line_numbers"] == [2]
    assert scan["keyword_line_numbers"]["nodata"] == [3]
    assert scan["raw_metadata_retained"] is False


def test_no_fom_asset_or_reference_is_an_explicit_inventory_result():
    assets = classify_asset_names(["surface.tif", "surface.xml"])
    empty_scan = scan_metadata(b"PRODUCT_ID = TEST\nMISSING_CONSTANT = -9999\n")
    assert classify_fom_availability(assets, empty_scan, empty_scan) == (
        "FOM_NOT_LISTED_OR_REFERENCED_IN_PINNED_RELEASE_METADATA"
    )


def test_fom_metadata_reference_is_detected_even_without_a_separate_asset():
    assets = classify_asset_names(["surface.tif", "surface.xml"])
    scan = scan_metadata(b"FIGURE OF MERIT IMAGE = surface_fom.tif\n")
    assert classify_fom_availability(assets, scan, scan) == "FOM_ASSET_OR_REFERENCE_FOUND"


@pytest.mark.parametrize("href", [
    "https://evil.example/fom.tif",
    "/mosaic/mars2020_trn/HiRISE/../private/fom.tif",
    "/mosaic/mars2020_trn/HiRISE/fom.tif?token=secret",
])
def test_unexpected_or_unsafe_directory_links_fail_closed(href):
    html = f'<a href="{href}">bad</a>'.encode()
    with pytest.raises(E555Error):
        parse_asset_index(html)
