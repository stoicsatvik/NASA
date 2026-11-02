import unittest
import numpy as np
from research.e502_mola_pds4 import parse_label, decode, summarize


def label(dtype='SignedMSB2', shape=(2, 3), special='-32768', order='Last Index Fastest'):
    return f'''<Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1">
<File_Area_Observational><File><file_name>test.img</file_name></File>
<Array_2D_Image><offset unit="byte">0</offset><axis_index_order>{order}</axis_index_order>
<Element_Array><data_type>{dtype}</data_type><scaling_factor>2</scaling_factor><value_offset>3</value_offset></Element_Array>
<Axis_Array><axis_name>Line</axis_name><elements>{shape[0]}</elements><sequence_number>1</sequence_number></Axis_Array>
<Axis_Array><axis_name>Sample</axis_name><elements>{shape[1]}</elements><sequence_number>2</sequence_number></Axis_Array>
<Special_Constants><missing_constant>{special}</missing_constant></Special_Constants>
</Array_2D_Image></File_Area_Observational></Product_Observational>'''.encode()


class E502PDS4(unittest.TestCase):
    def test_big_endian_and_missing(self):
        info = parse_label(label(), 'test.img', (2, 3))
        raw = np.array([1, 2, -32768, -2, 0, 7], dtype='>i2').tobytes()
        a, missing = decode(raw, info)
        self.assertEqual(float(a[0, 0]), 5.0)
        self.assertEqual(float(a[1, 0]), -1.0)
        self.assertTrue(np.isnan(a[0, 2]))
        self.assertEqual(int(missing.sum()), 1)
    def test_wrong_filename(self):
        with self.assertRaises(ValueError): parse_label(label(), 'other.img', (2, 3))
    def test_wrong_dimensions(self):
        with self.assertRaises(ValueError): parse_label(label(), 'test.img')
    def test_unsupported_type(self):
        with self.assertRaises(ValueError): parse_label(label(dtype='IEEE754MSBSingle'), 'test.img', (2, 3))
    def test_short_image_rejected(self):
        info = parse_label(label(), 'test.img', (2, 3))
        with self.assertRaises(ValueError): decode(b'\x00'*10, info)
    def test_ambiguous_axis_rejected(self):
        with self.assertRaises(ValueError): parse_label(label(order='Middle Index Fastest'), 'test.img', (2, 3))
    def test_no_observed_cells(self):
        with self.assertRaises(ValueError): summarize(np.zeros((720,1440)), np.zeros((720,1440)))
    def test_count_gate_and_zero_count(self):
        t=np.ones((720,1440),dtype=float)
        c=np.zeros_like(t)
        c[90,720]=3
        r=summarize(t,c)
        self.assertEqual(r['counts_positive_cells'],1)
        self.assertEqual(r['finite_topography_with_zero_count'],720*1440-1)
        self.assertEqual(r['joint_observed_topography_cells'],1)
    def test_negative_counts_rejected(self):
        t=np.ones((720,1440),dtype=float)
        c=np.ones_like(t)
        c[0,0]=-1
        with self.assertRaises(ValueError): summarize(t,c)

if __name__=='__main__': unittest.main()
