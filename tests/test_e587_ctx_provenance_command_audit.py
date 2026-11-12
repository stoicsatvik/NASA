import unittest

from experiments.e587_ctx_provenance_command_audit import (
    analyze_features,
    is_control_asset,
    is_provenance_asset,
    parse_command_line,
    parse_commands,
    select_exact_features,
)

COLLECTION = "mro_ctx_controlled_usgs_dtms"


def receipt(ids):
    return {
        "experiment": "E583",
        "credentials_used": False,
        "items": [{"id": item_id} for item_id in ids],
    }


def features(ids, asset_key="provenance"):
    rows = []
    for item_id in ids:
        rows.append({
            "type": "Feature",
            "id": item_id,
            "collection": COLLECTION,
            "assets": {
                asset_key: {
                    "href": "https://astrogeo-ard.s3.amazonaws.com/provenance.txt?X-Amz-Signature=SECRET",
                    "title": "Processing provenance commands",
                    "type": "text/plain",
                    "roles": ["metadata"],
                },
                "mola_control": {
                    "href": "https://astrogeo-ard.s3.amazonaws.com/mola.csv",
                    "title": "MOLA control points",
                    "type": "text/csv",
                    "roles": ["metadata"],
                },
                "qa_metrics": {
                    "href": "https://astrogeo-ard.s3.amazonaws.com/qa_metrics.txt",
                    "title": "ASP Generated Quality Assurance Metrics",
                    "type": "text/plain",
                    "roles": ["metadata"],
                },
            },
        })
    return rows


class E587Tests(unittest.TestCase):
    def test_geodiff_default_is_first_minus_second_and_maps_ctx_mola(self):
        result = parse_command_line(
            "geodiff /work/CTX_DTM.tif /work/MOLA_control.csv -o /tmp/qa "
            "--csv-format '1:lon 2:lat 3:height_above_datum'"
        )
        self.assertEqual(result["difference_semantics"], "first_minus_second")
        self.assertEqual(result["interpreted_role_difference"], "CTX_MINUS_MOLA")
        self.assertEqual(result["input_files"], ["CTX_DTM.tif", "MOLA_control.csv"])
        self.assertNotIn("/work", str(result))
        self.assertNotIn("/tmp", str(result))

    def test_geodiff_reverse_and_absolute_remove_or_flip_sign(self):
        reversed_result = parse_command_line(
            "geodiff --reverse /work/CTX_DTM.tif /work/MOLA_control.csv -o qa"
        )
        absolute_result = parse_command_line(
            "geodiff --absolute /work/CTX_DTM.tif /work/MOLA_control.csv -o qa"
        )
        self.assertEqual(reversed_result["interpreted_role_difference"], "MOLA_MINUS_CTX")
        self.assertEqual(absolute_result["interpreted_role_difference"], "ABSOLUTE_DIFFERENCE_SIGN_UNAVAILABLE")

    def test_pc_align_first_is_reference_second_is_source(self):
        result = parse_command_line(
            "pc_align --max-displacement 100 /work/CTX_PC.tif /work/MOLA_points.csv -o /tmp/align"
        )
        self.assertEqual(result["reference_fixed_input"], "CTX_PC.tif")
        self.assertEqual(result["source_movable_input"], "MOLA_points.csv")
        self.assertEqual(result["identified_alignment_direction"], "MOLA_SOURCE_MOVED_TO_CTX_REFERENCE")
        self.assertEqual(result["forward_transform_direction"], "second_source_to_first_reference")
        self.assertNotIn("/work", str(result))

    def test_pc_align_mola_reference_and_ctx_source_are_not_reversed(self):
        result = parse_command_line(
            "pc_align /data/MOLA_reference.csv /data/CTX_stereo_points.tif -o run"
        )
        self.assertEqual(result["identified_alignment_direction"], "CTX_SOURCE_MOVED_TO_MOLA_REFERENCE")

    def test_unknown_operand_roles_are_not_overclaimed(self):
        result = parse_command_line("geodiff a.tif b.csv -o qa")
        self.assertEqual(result["difference_semantics"], "first_minus_second")
        self.assertEqual(result["interpreted_role_difference"], "ORDER_KNOWN_ROLES_UNKNOWN")

    def test_provenance_and_control_asset_selection_is_narrow(self):
        self.assertTrue(is_provenance_asset("provenance", {"title": "Commands"}))
        self.assertTrue(is_provenance_asset("history", {"title": "Processing pipeline"}))
        self.assertFalse(is_provenance_asset("qa_metrics", {"title": "ASP Generated Quality Assurance Metrics"}))
        self.assertTrue(is_control_asset("mola_control", {"title": "MOLA points"}))
        self.assertFalse(is_control_asset("qa_metrics", {"title": "QA metrics"}))

    def test_command_parser_handles_multiline_and_deduplicates(self):
        text = (
            "pc_align --max-displacement 100 \\\n"
            "  /work/CTX_PC.tif /work/MOLA.csv -o run\n"
            "geodiff /work/CTX_DTM.tif /work/MOLA.csv -o qa\n"
        )
        commands = parse_commands(text)
        self.assertEqual({row["tool"] for row in commands}, {"pc_align", "geodiff"})
        self.assertEqual(len(commands), 2)

    def test_exact_item_set_mismatch_fails_closed(self):
        ids = [f"item-{index}" for index in range(9)]
        rows = features(ids)
        rows.pop()
        selected, mismatch = select_exact_features(rows, receipt(ids))
        self.assertEqual(selected, [])
        self.assertEqual(mismatch["decision"], "ITEM_SET_MISMATCH")
        self.assertEqual(mismatch["missing_item_ids"], [ids[-1]])

    def test_asset_inventory_redacts_signed_query_values_and_raw_text(self):
        ids = [f"item-{index}" for index in range(9)]
        payload = "geodiff /work/CTX_DTM.tif /work/MOLA.csv -o qa".encode("utf-8")

        def fake_fetcher(url, *, max_bytes):
            self.assertLessEqual(len(payload), max_bytes)
            return {
                "status": 200,
                "headers": {"Content-Type": "text/plain"},
                "payload": payload,
                "bytes_read": len(payload),
                "declared_bytes": len(payload),
                "final_url": url,
                "too_large": False,
            }

        result = analyze_features(features(ids), receipt(ids), fetcher=fake_fetcher)
        self.assertEqual(result["decision"], "PROVENANCE_COMMANDS_FOUND")
        self.assertEqual(result["item_count"], 9)
        self.assertEqual(result["provenance_asset_download_count"], 9)
        self.assertEqual(result["relevant_command_count"], 9)
        rendered = str(result)
        self.assertNotIn("SECRET", rendered)
        self.assertNotIn("/work", rendered)
        self.assertNotIn("geodiff /work", rendered)
        self.assertFalse(result["raw_provenance_text_stored"])

    def test_item_set_mismatch_performs_no_asset_fetch(self):
        ids = [f"item-{index}" for index in range(9)]
        rows = features(ids)[:-1]
        calls = []

        def fake_fetcher(url, *, max_bytes):
            calls.append(url)
            raise AssertionError("fetch must not run on an item-set mismatch")

        result = analyze_features(rows, receipt(ids), fetcher=fake_fetcher)
        self.assertEqual(result["decision"], "ITEM_SET_MISMATCH")
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
