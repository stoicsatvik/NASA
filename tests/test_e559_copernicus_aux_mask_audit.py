import xml.etree.ElementTree as ET

import numpy as np
import pytest

from experiments.e559_copernicus_aux_mask_audit import (
    AUXFILES,
    PREVIEW,
    E559Error,
    expected_key,
    object_url,
    parse_listing,
    summarize_kml,
    summarize_mask_window,
    validate_key,
)


def _listing(prefix, keys, truncated="false"):
    ns = "http://s3.amazonaws.com/doc/2006-03-01/"
    root = ET.Element(f"{{{ns}}}ListBucketResult")
    ET.SubElement(root, f"{{{ns}}}Name").text = "copernicus-dem-30m"
    ET.SubElement(root, f"{{{ns}}}Prefix").text = prefix
    ET.SubElement(root, f"{{{ns}}}KeyCount").text = str(len(keys))
    ET.SubElement(root, f"{{{ns}}}IsTruncated").text = truncated
    for key, size in keys:
        item = ET.SubElement(root, f"{{{ns}}}Contents")
        ET.SubElement(item, f"{{{ns}}}Key").text = key
        ET.SubElement(item, f"{{{ns}}}Size").text = str(size)
        ET.SubElement(item, f"{{{ns}}}ETag").text = '"fixture"'
    return ET.tostring(root, encoding="utf-8")


def test_expected_handbook_keys_use_exact_dged_names_and_folders():
    prefix = "Copernicus_DSM_COG_10_N19_00_E076_00_DEM/"
    assert expected_key(prefix, "WBM") == (
        prefix + "AUXFILES/Copernicus_DSM_10_N19_00_E076_00_WBM.tif"
    )
    assert expected_key(prefix, "FLM").endswith("/AUXFILES/Copernicus_DSM_10_N19_00_E076_00_FLM.tif")
    assert expected_key(prefix, "SRC").endswith("/PREVIEW/Copernicus_DSM_10_N19_00_E076_00_SRC.kml")
    assert expected_key(prefix, "ACM").endswith("/AUXFILES/Copernicus_DSM_10_N19_00_E076_00_ACM.kml")
    assert AUXFILES == "AUXFILES" and PREVIEW == "PREVIEW"


def test_object_key_validation_rejects_prefix_escape_and_path_traversal():
    prefix = "tile/AUXFILES/"
    assert validate_key(prefix + "mask_WBM.tif", prefix).endswith("mask_WBM.tif")
    with pytest.raises(E559Error) as caught:
        validate_key("tile/PREVIEW/other.kml", prefix)
    assert caught.value.outcome == "OBJECT_KEY_OUTSIDE_PREFIX"
    with pytest.raises(E559Error):
        validate_key(prefix + "../secret", prefix)


def test_object_url_is_https_and_scoped_to_exact_public_bucket():
    key = "tile/AUXFILES/mask_WBM.tif"
    url = object_url(key, "tile/AUXFILES/")
    assert url == "https://copernicus-dem-30m.s3.eu-central-1.amazonaws.com/tile/AUXFILES/mask_WBM.tif"


def test_parse_listing_records_only_keys_sizes_and_marks_truncation():
    prefix = "tile/AUXFILES/"
    body = _listing(prefix, [(prefix + "mask_WBM.tif", 1234)])
    result = parse_listing(body, prefix)
    assert result["bucket"] == "copernicus-dem-30m"
    assert result["key_count_reported"] == 1
    assert result["is_truncated"] is False
    assert result["objects"][0]["size_bytes"] == 1234
    partial = parse_listing(_listing(prefix, [], truncated="true"), prefix)
    assert partial["is_truncated"] is True


def test_parse_listing_fails_closed_on_wrong_prefix_or_invalid_xml():
    with pytest.raises(E559Error) as caught:
        parse_listing(_listing("tile/PREVIEW/", []), "tile/AUXFILES/")
    assert caught.value.outcome == "LISTING_SCOPE_MISMATCH"
    with pytest.raises(E559Error) as caught:
        parse_listing(b"<not-xml", "tile/AUXFILES/")
    assert caught.value.outcome == "LISTING_XML_INVALID"


def test_wbm_class_counts_preserve_water_classes_and_no_water():
    values = np.asarray([[0, 0, 2], [0, 3, 2], [1, 0, 0]], dtype=np.uint8)
    result = summarize_mask_window(values, "WBM", None)
    assert result["value_counts"] == {"0": 5, "1": 1, "2": 2, "3": 1}
    assert result["class_counts"] == {"no_water": 5, "ocean": 1, "lake": 2, "river": 1}
    assert result["raw_window_retained"] is False


def test_flm_unknown_values_are_not_silently_relabelled():
    values = np.asarray([[2, 3, 9], [101, 255, 1], [0, 0, 2]], dtype=np.uint8)
    result = summarize_mask_window(values, "FLM", None)
    assert result["class_counts"]["ASTER"] == 1
    assert result["class_counts"]["Spain_DSM05"] == 1
    assert result["unknown_values"] == [255]


def test_hem_sentinel_is_excluded_from_height_error_statistics():
    values = np.asarray([[1.0, 2.0, -32767.0], [3.0, 4.0, -32767.0]], dtype=np.float32)
    result = summarize_mask_window(values, "HEM", -32767)
    assert result["valid_samples"] == 4
    assert result["masked_or_sentinel_samples"] == 2
    assert result["height_error_median_m"] == 2.5
    assert result["center_value"] == 3.0


def test_kml_summary_extracts_metadata_without_retaining_raw_xml():
    xml = b"""<kml xmlns="http://www.opengis.net/kml/2.2"><Document>
    <Placemark><name>Scene A</name><ExtendedData>
    <Data name="acquisition_date"><value>2014-02-03</value></Data>
    <Data name="scene_id"><value>ABC123</value></Data>
    </ExtendedData></Placemark></Document></kml>"""
    result = summarize_kml(xml)
    assert result["placemark_count"] == 1
    assert result["field_names"] == ["acquisition_date", "scene_id"]
    assert result["sample_features"][0]["name"] == "Scene A"
    assert result["raw_kml_retained"] is False
