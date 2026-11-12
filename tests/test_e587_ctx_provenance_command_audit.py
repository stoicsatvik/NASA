import unittest

from experiments.e587_ctx_provenance_command_audit import (
    analyze_features,
    is_control_asset,
    is_provenance_asset,
    parse_command_line,
    parse_commands,
    select_exact_features,
    build_s3_list_url,
    parse_s3_listing_xml,
    audit_s3_prefixes,
    build_s3_object_url,
    summarize_sidecar_json,
    audit_sidecar_json,
)

COLLECTION = "mro_ctx_controlled_usgs_dtms"


def receipt(ids):
    return {
        "experiment": "E583",
        "credentials_used": False,
        "items": [{"id": item_id} for item_id in ids],
    }


def features(ids, asset_key="provenance", include_provenance_asset=True, provenance_link=False):
    rows = []
    for item_id in ids:
        assets = {
            "dtm": {
                "href": f"https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/{item_id}/{item_id}_dtm.tif",
                "title": "Digital Terrain Model",
                "type": "image/tiff",
                "roles": ["data"],
            },
            "mola_control": {
                "href": f"https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/{item_id}/{item_id}_mola.csv",
                "title": "MOLA control points",
                "type": "text/csv",
                "roles": ["metadata"],
            },
            "qa_metrics": {
                "href": f"https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/{item_id}/qa_metrics.txt",
                "title": "ASP Generated Quality Assurance Metrics",
                "type": "text/plain",
                "roles": ["metadata"],
            },
        }
        if include_provenance_asset:
            assets[asset_key] = {
                "href": f"https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/{item_id}/provenance.txt?X-Amz-Signature=SECRET",
                "title": "Processing provenance commands",
                "type": "text/plain",
                "roles": ["metadata"],
            }
        links = [{"rel": "self", "href": "https://stac.astrogeology.usgs.gov/item.json", "type": "application/geo+json"}]
        if provenance_link:
            links.append({
                "rel": "provenance",
                "href": f"https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/{item_id}/processing.txt?X-Amz-Signature=SECRET",
                "title": "Processing commands",
                "type": "text/plain",
            })
        rows.append({
            "type": "Feature",
            "id": item_id,
            "collection": COLLECTION,
            "assets": assets,
            "links": links,
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


    def test_s3_prefix_is_derived_from_exact_dtm_asset_path(self):
        url = build_s3_list_url(
            "https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/mro/ctx/item-1/item-1_dtm.tif"
        )
        from urllib.parse import parse_qs, urlsplit
        parsed = urlsplit(url)
        query = parse_qs(parsed.query)
        self.assertEqual(parsed.netloc, "astrogeo-ard.s3-us-west-2.amazonaws.com")
        self.assertEqual(query["prefix"], ["mars/mro/ctx/item-1/"])
        self.assertEqual(query["max-keys"], ["100"])
        self.assertEqual(parsed.path, "/")

    def test_s3_listing_parser_detects_unadvertised_provenance_sidecar(self):
        xml = b'''<?xml version="1.0" encoding="UTF-8"?>
        <ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
          <IsTruncated>false</IsTruncated>
          <Contents><Key>mars/item-1/item-1_dtm.tif</Key><Size>100</Size><ETag>"abc"</ETag><LastModified>2026-11-01T00:00:00.000Z</LastModified></Contents>
          <Contents><Key>mars/item-1/provenance_commands.txt</Key><Size>250</Size><ETag>"def"</ETag><LastModified>2026-11-01T00:00:00.000Z</LastModified></Contents>
          <Contents><Key>mars/item-1/item-1_mola_shots.csv</Key><Size>500</Size><ETag>"ghi"</ETag><LastModified>2026-11-01T00:00:00.000Z</LastModified></Contents>
        </ListBucketResult>'''
        result = parse_s3_listing_xml(xml)
        self.assertEqual(result["decision"], "LISTED")
        self.assertFalse(result["is_truncated"])
        self.assertEqual(len(result["objects"]), 3)
        self.assertTrue(result["objects"][1]["is_provenance_candidate"])
        self.assertTrue(result["objects"][2]["is_control_candidate"])
        self.assertNotIn("mars/item-1", str(result))
        self.assertFalse(result["objects"][0]["full_key_stored"])

    def test_s3_listing_parser_preserves_truncation(self):
        xml = b'''<ListBucketResult xmlns="http://s3.amazonaws.com/doc/2006-03-01/"><IsTruncated>true</IsTruncated></ListBucketResult>'''
        result = parse_s3_listing_xml(xml)
        self.assertTrue(result["is_truncated"])

    def test_s3_prefix_access_denied_is_preserved_without_retrying_other_items(self):
        ids = [f"item-{index}" for index in range(9)]
        rows = features(ids, include_provenance_asset=False, provenance_link=False)
        for row in rows:
            row["assets"]["dtm"] = {
                "href": "https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/item/item_dtm.tif",
                "type": "image/tiff",
            }
        calls = []

        def fake_fetcher(url, *, max_bytes):
            calls.append(url)
            return {
                "status": 403,
                "headers": {"Content-Type": "application/xml"},
                "payload": b"<Error><Code>AccessDenied</Code></Error>",
                "bytes_read": 45,
                "declared_bytes": 45,
                "final_url": url,
                "too_large": False,
            }

        result = audit_s3_prefixes(rows, fetcher=fake_fetcher)
        self.assertEqual(result["decision"], "S3_LISTING_ACCESS_DENIED")
        self.assertEqual(result["item_prefixes_listed"], 0)
        self.assertEqual(len(calls), 1)


    def test_sidecar_object_url_uses_exact_listed_basename(self):
        url = build_s3_object_url(
            "https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/item/item_dtm.tif",
            "item.json",
        )
        self.assertEqual(
            url,
            "https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/item/item.json",
        )
        with self.assertRaises(Exception):
            build_s3_object_url(
                "https://astrogeo-ard.s3-us-west-2.amazonaws.com/mars/item/item_dtm.tif",
                "../other.json",
            )

    def test_sidecar_summary_extracts_commands_without_raw_values(self):
        payload = {
            "processing": {
                "commands": [
                    "pc_align --max-displacement 100 /work/CTX_PC.tif /work/MOLA.csv -o run",
                    "geodiff /work/CTX_DTM.tif /work/MOLA.csv -o qa",
                ],
                "notes": "internal /private/work/path",
            },
            "unrelated": {"version": "1.0"},
        }
        import json
        result = summarize_sidecar_json(json.dumps(payload).encode("utf-8"))
        self.assertEqual(result["command_count"], 2)
        self.assertEqual(result["top_level_keys"], ["processing", "unrelated"])
        self.assertIn("processing.commands", result["relevant_key_paths"])
        self.assertNotIn("/work", str(result))
        self.assertNotIn("/private", str(result))
        self.assertFalse(result["raw_json_stored"])

    def test_sidecar_inventory_downloads_only_exact_listed_json_sidecars(self):
        ids = [f"item-{index}" for index in range(9)]
        rows = features(ids, include_provenance_asset=False, provenance_link=False)
        prefix_items = []
        for item_id in ids:
            prefix_items.append({
                "id": item_id,
                "objects": [{
                    "basename": f"{item_id}.json",
                    "size_bytes": 100,
                }],
            })
        prefix_inventory = {"items": prefix_items}
        payload = b'{"processing":{"commands":["geodiff /work/CTX.tif /work/MOLA.csv -o qa"]}}'
        calls = []

        def fake_fetcher(url, *, max_bytes):
            calls.append((url, max_bytes))
            return {
                "status": 200,
                "headers": {"Content-Type": "application/json"},
                "payload": payload,
                "bytes_read": len(payload),
                "declared_bytes": len(payload),
                "final_url": url,
                "too_large": False,
            }

        result = audit_sidecar_json(rows, prefix_inventory, fetcher=fake_fetcher)
        self.assertEqual(result["decision"], "SIDECAR_COMMANDS_FOUND")
        self.assertEqual(result["sidecar_download_count"], 9)
        self.assertEqual(result["relevant_command_count"], 9)
        self.assertEqual(len(calls), 9)
        self.assertTrue(all(limit <= 64_000 for _, limit in calls))
        self.assertNotIn("/work", str(result))


    def test_prose_mention_of_pc_align_is_not_a_command(self):
        self.assertIsNone(
            parse_command_line("MOLA Spot Observations Used for initial pc_align")
        )


if __name__ == "__main__":
    unittest.main()
