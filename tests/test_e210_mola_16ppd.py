"""E210 synthetic endian and metadata controls; no Mars measurements."""
import unittest
from research.e210_mola_16ppd import decode_msb16, validate_label


class Mola16Tests(unittest.TestCase):
    def test_big_endian_signed_values(self):
        self.assertEqual(
            list(decode_msb16(b"\x00\x01\xff\xfe\x7f\xff\x80\x00", 4)),
            [1, -2, 32767, -32768],
        )

    def test_reject_short_binary(self):
        with self.assertRaisesRegex(ValueError, "expected"):
            decode_msb16(b"\x00\x01", 2)

    def test_label_requires_real_resolution(self):
        fields = {
            "PRODUCT_ID": "MEGT90N000EB.IMG", "PRODUCT_VERSION_ID": "2.0",
            "SAMPLE_TYPE": "MSB_INTEGER", "SAMPLE_BITS": "16",
            "LINES": "2880", "LINE_SAMPLES": "5760", "RECORD_BYTES": "11520",
            "MAP_PROJECTION_TYPE": "SIMPLE CYLINDRICAL",
            "COORDINATE_SYSTEM_NAME": "PLANETOCENTRIC",
            "POSITIVE_LONGITUDE_DIRECTION": "EAST", "MAP_RESOLUTION": "16.0",
            "LINE_PROJECTION_OFFSET": "1440.5", "SAMPLE_PROJECTION_OFFSET": "2880.5",
            "UNIT": "METER",
        }
        label = "\n".join(f"{k} = {v}" for k, v in fields.items())
        validate_label(label, "MEGT90N000EB.IMG", True)
        with self.assertRaisesRegex(ValueError, "MAP_RESOLUTION"):
            validate_label(label.replace("MAP_RESOLUTION = 16.0", "MAP_RESOLUTION = 4.0"),
                           "MEGT90N000EB.IMG", True)


if __name__ == "__main__":
    unittest.main()
