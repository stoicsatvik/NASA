"""Synthetic MOLA MEG004 reader regressions. No real NASA raster validation.

Run: python -m unittest discover -s tests -p 'test_*.py'
"""
from __future__ import annotations

import hashlib
import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))
from mola_megdr_quality_gate import analyze, metadata, read_grid  # noqa: E402

ROWS, COLS = 720, 1440
N = ROWS * COLS


def label_text(product: str, **overrides: str) -> str:
    fields = {
        "PRODUCT_ID": f'"{product}"',
        "PRODUCT_VERSION_ID": '"2.0"',
        "PRODUCT_CREATION_TIME": "2003-04-03T01:00:00",
        "SAMPLE_TYPE": "MSB_INTEGER",
        "SAMPLE_BITS": "16",
        "MAP_PROJECTION_TYPE": '"SIMPLE CYLINDRICAL"',
        "COORDINATE_SYSTEM_NAME": "PLANETOCENTRIC",
        "POSITIVE_LONGITUDE_DIRECTION": "EAST",
        "MAP_RESOLUTION": "4 <PIX/DEG>",
        "CENTER_LATITUDE": "0.0 <DEGREE>",
        "CENTER_LONGITUDE": "180.0 <DEGREE>",
        "WESTERNMOST_LONGITUDE": "0.0 <DEGREE>",
        "EASTERNMOST_LONGITUDE": "360.0 <DEGREE>",
        "MAXIMUM_LATITUDE": "90.0 <DEGREE>",
        "MINIMUM_LATITUDE": "-90.0 <DEGREE>",
        "LINE_PROJECTION_OFFSET": "360.5",
        "SAMPLE_PROJECTION_OFFSET": "720.5",
        "MAP_PROJECTION_ROTATION": "0.0",
        "LINES": str(ROWS),
        "LINE_SAMPLES": str(COLS),
        "RECORD_BYTES": str(COLS * 2),
    }
    fields.update(overrides)
    return "PDS_VERSION_ID = PDS3\n" + "\n".join(
        f"  {key}   =   {value}" for key, value in fields.items()
    ) + "\nEND\n"


class MolaMegdrContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.top = self.root / "megt90n000cb.img"
        self.counts = self.root / "megc90n000cb.img"
        self.top_lbl = self.root / "top.lbl"
        self.count_lbl = self.root / "counts.lbl"
        self.top_lbl.write_text(label_text("MEGT90N000CB.IMG"), encoding="ascii")
        self.count_lbl.write_text(label_text("MEGC90N000CB.IMG"), encoding="ascii")

    def grids(self, top_cells=None, count_cells=None) -> tuple[bytes, bytes]:
        top = bytearray(b"\x00\x00" * N)
        counts = bytearray(b"\x00\x00" * N)
        for index, value in (top_cells or {}).items():
            struct.pack_into(">h", top, index * 2, value)
        for index, value in (count_cells or {}).items():
            struct.pack_into(">h", counts, index * 2, value)
        self.top.write_bytes(top)
        self.counts.write_bytes(counts)
        return bytes(top), bytes(counts)

    def test_indented_pds3_fields_are_parsed(self) -> None:
        self.assertEqual(metadata(self.top_lbl, "MEGT90N000CB.IMG"),
                         {"lines": ROWS, "samples": COLS})

    def test_wrong_product_and_version_are_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "wrong product label"):
            metadata(self.top_lbl, "MEGC90N000CB.IMG")
        self.top_lbl.write_text(label_text("MEGT90N000CB.IMG",
                                           PRODUCT_VERSION_ID='"1.0"'), encoding="ascii")
        with self.assertRaisesRegex(ValueError, "not final MEGDR version"):
            metadata(self.top_lbl, "MEGT90N000CB.IMG")

    def test_final_product_creation_date_boundary(self) -> None:
        self.top_lbl.write_text(label_text("MEGT90N000CB.IMG",
                                           PRODUCT_CREATION_TIME="2003-03-21T00:00:00"), encoding="ascii")
        self.assertEqual(metadata(self.top_lbl, "MEGT90N000CB.IMG"),
                         {"lines": ROWS, "samples": COLS})
        self.top_lbl.write_text(label_text("MEGT90N000CB.IMG",
                                           PRODUCT_CREATION_TIME="2003-03-20T23:59:59"), encoding="ascii")
        with self.assertRaisesRegex(ValueError, "pre-final MEGDR"):
            metadata(self.top_lbl, "MEGT90N000CB.IMG")

    def test_invalid_or_missing_creation_date_rejected(self) -> None:
        for value in ("not-a-date", "2003-02-30", "2003-04-03T00:00:00junk", "2003-04-03T25:00:00", "2003-04-03T01:61:00", "2003-04-03T01:00:61"):
            with self.subTest(value=value):
                self.top_lbl.write_text(label_text("MEGT90N000CB.IMG",
                                                   PRODUCT_CREATION_TIME=value), encoding="ascii")
                with self.assertRaisesRegex(ValueError, "invalid MEGDR creation time"):
                    metadata(self.top_lbl, "MEGT90N000CB.IMG")
        self.top_lbl.write_text(label_text("MEGT90N000CB.IMG").replace(
            "  PRODUCT_CREATION_TIME   =   2003-04-03T01:00:00\n", ""), encoding="ascii")
        with self.assertRaisesRegex(ValueError, "missing PRODUCT_CREATION_TIME"):
            metadata(self.top_lbl, "MEGT90N000CB.IMG")

    def test_wrong_row_bytes_are_rejected(self) -> None:
        self.top_lbl.write_text(label_text("MEGT90N000CB.IMG",
                                           RECORD_BYTES="1234"), encoding="ascii")
        with self.assertRaisesRegex(ValueError, "row-byte mismatch"):
            metadata(self.top_lbl, "MEGT90N000CB.IMG")

    def test_mismatched_geospatial_origin_rejected(self) -> None:
        self.count_lbl.write_text(label_text("MEGC90N000CB.IMG",
                                             CENTER_LONGITUDE="90.0 <DEGREE>"), encoding="ascii")
        self.grids(top_cells={0: 1200}, count_cells={0: 1})
        with self.assertRaisesRegex(ValueError, "unexpected MEG004 projection: CENTER_LONGITUDE"):
            analyze(self.top, self.counts, self.top_lbl, self.count_lbl)

    def test_missing_projection_offset_rejected(self) -> None:
        text = label_text("MEGT90N000CB.IMG")
        text = text.replace("  LINE_PROJECTION_OFFSET   =   360.5\n", "")
        self.top_lbl.write_text(text, encoding="ascii")
        with self.assertRaisesRegex(ValueError, "missing LINE_PROJECTION_OFFSET"):
            metadata(self.top_lbl, "MEGT90N000CB.IMG")

    def test_truncated_grid_is_rejected(self) -> None:
        self.top.write_bytes(b"\x00\x00" * (N - 1))
        with self.assertRaisesRegex(ValueError, "expected .* bytes"):
            read_grid(self.top, (ROWS, COLS))

    def test_full_grid_masks_interpolated_and_checks_hashes(self) -> None:
        raw_top, raw_counts = self.grids(
            top_cells={0: 30000, 1: -2000, N - 1: 1200},
            count_cells={1: 1, N - 1: 2},
        )
        result = analyze(self.top, self.counts, self.top_lbl, self.count_lbl, min_count=2)
        self.assertEqual(result["shape"], [ROWS, COLS])
        self.assertEqual(result["total_cells"], N)
        self.assertEqual(result["observed_cells"], 2)
        self.assertEqual(result["interpolated_cells"], N - 2)
        self.assertEqual(result["retained_cells"], 1)
        self.assertEqual(result["retained_topography_min_m"], 1200)
        self.assertEqual(result["retained_topography_max_m"], 1200)
        self.assertAlmostEqual(result["retained_fraction"], 1 / N)
        self.assertEqual(result["topography_sha256"], hashlib.sha256(raw_top).hexdigest())
        self.assertEqual(result["counts_sha256"], hashlib.sha256(raw_counts).hexdigest())
        self.assertIn("NOT YET PROVEN", result["claim_state"])

    def test_swapped_binary_paths_are_rejected(self) -> None:
        self.grids(top_cells={0: 1200}, count_cells={0: 1})
        with self.assertRaisesRegex(ValueError, "binary filename"):
            analyze(self.counts, self.top, self.top_lbl, self.count_lbl)

    def test_negative_counts_and_invalid_threshold_are_rejected(self) -> None:
        self.grids(count_cells={0: -1})
        with self.assertRaisesRegex(ValueError, "negative counts"):
            analyze(self.top, self.counts, self.top_lbl, self.count_lbl)
        with self.assertRaisesRegex(ValueError, "min_count"):
            analyze(self.top, self.counts, self.top_lbl, self.count_lbl, min_count=0)


if __name__ == "__main__":
    unittest.main()
