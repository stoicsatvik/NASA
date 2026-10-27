"""Synthetic fixtures for E319. No synthetic row is a geological observation."""
import pytest

from research.e319_paad_mars_codebook_overlap import (
    MARS_CODE_ASSIGNMENTS, audit_csv, split_raw_codes,
)


def csv_bytes(rows):
    header = "Field_Site,Dune_Type,References\n"
    return (header + "".join(rows)).encode("utf-8")


def test_mars_2007_table1_exact_codebook():
    assert MARS_CODE_ASSIGNMENTS["Bd"] == 261
    assert MARS_CODE_ASSIGNMENTS["B"] == 144
    assert "TR" not in MARS_CODE_ASSIGNMENTS


def test_preserve_case_and_multi_label_boundary():
    assert split_raw_codes("B, Bd / SS + TR") == ("B", "Bd", "SS", "TR")
    assert split_raw_codes("  ") == ()
    assert split_raw_codes("Bd") != ("B",)


def test_unknown_codes_not_silently_promoted():
    data = csv_bytes([
        'Alpha,"B, TR",ref1\n',
        'Beta,Bd,ref2\n',
        'Gamma,"L / SS",ref3\n',
        'Delta,MG,ref4\n',
    ])
    result = audit_csv(data)
    assert result["earth_rows"] == 4
    assert result["single_token_rows"] == 2
    assert result["multi_token_rows"] == 2
    assert result["rows_with_all_tokens_in_mars_2007_codebook"] == 2
    assert result["rows_with_partial_codebook_overlap"] == 1
    assert result["tokens_not_in_mars_2007_codebook"] == {"MG": 1, "TR": 1}
    assert result["e001_known_site_recovery"] == "NOT YET MEASURED"
    assert result["cross_body_similarity"] == "NOT YET PROVEN"


def test_missing_labels_do_not_become_negative_examples():
    result = audit_csv(csv_bytes(["Alpha,,ref\n", "Beta,B,ref\n"]))
    assert result["nonempty_dune_type_rows"] == 1
    assert result["rows_with_all_tokens_in_mars_2007_codebook"] == 1
    assert result["independent_positive_negative_pairs"] == "ABSENT"


def test_duplicate_site_rejected():
    with pytest.raises(ValueError, match="duplicated"):
        audit_csv(csv_bytes(["Alpha,B,ref\n", "Alpha,L,ref\n"]))


def test_missing_required_column_rejected():
    with pytest.raises(ValueError, match="required"):
        audit_csv(b"Field_Site,Climate\nAlpha,dry\n")


def test_multicharacter_codes_are_not_substring_matches():
    result = audit_csv(csv_bytes(["Alpha,Bd,ref\n", "Beta,Bx,ref\n"]))
    assert result["raw_token_counts"] == {"Bd": 1, "Bx": 1}
    assert result["rows_with_all_tokens_in_mars_2007_codebook"] == 1
    assert result["tokens_not_in_mars_2007_codebook"] == {"Bx": 1}
