"""Synthetic georeference controls; real-data claim requires workflow artifact."""
import io
import unittest
from unittest.mock import patch

import numpy as np
import tifffile
from research import e505_etopo_earth_ingest as m


def fixture(origin=(75., 30.), resolution=1/240, size=3600):
    a = np.zeros((size, size), dtype=np.int16)
    if size > 2400:
        a[2400, 360] = 123
    buf = io.BytesIO()
    tifffile.imwrite(buf, a, photometric='minisblack', metadata=None,
                     extratags=[(33550, 'd', 3, (resolution, resolution, 0), False),
                                (33922, 'd', 6, (0, 0, 0, origin[0], origin[1], 0), False)])
    return buf.getvalue()


class TestE505(unittest.TestCase):
    def test_registered_patch_and_units(self):
        out = m.extract(fixture())
        self.assertEqual(out['shape'], [3600, 3600])
        self.assertEqual(out['finite_cells'], 3600**2)
        self.assertEqual(len(out['sites']['Lonar_candidate']['elevation_m']), 5)
        self.assertLess(abs(out['sites']['Lonar_candidate']['center_lat_lon_deg'][0] - 19.976), 1/240)

    def test_wrong_resolution_rejected(self):
        with self.assertRaisesRegex(ValueError, 'resolution'):
            m.extract(fixture(resolution=1/120))

    def test_wrong_origin_rejected(self):
        with self.assertRaisesRegex(ValueError, 'origin'):
            m.extract(fixture(origin=(76., 30.)))

    def test_wrong_dimensions_rejected(self):
        with self.assertRaisesRegex(ValueError, 'dimensions'):
            m.extract(fixture(size=120))

    def test_download_is_not_needed_for_synthetic_tests(self):
        with patch.object(m, 'bounded_download', side_effect=AssertionError('network called')):
            self.assertEqual(m.extract(fixture())['dtype'], 'int16')


if __name__ == '__main__':
    unittest.main()
