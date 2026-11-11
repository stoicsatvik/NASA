from io import BytesIO
import re
import unittest
import numpy as np
import tifffile
from experiments.e548_hirise_pixel_window import (
    LABEL_PATH,LABEL_URL,MAX_TIFF_TRANSFER_BYTES,TIFF_PATH,TIFF_URL,
    ProbeError,RangeReader,parse_geokeys,parse_pds3_label,read_float_window,validate_url
)

class Raw:
    def __init__(self,body): self.body=body; self.read_bytes=0
    def read(self,amount=-1,decode_content=False):
        data=self.body if amount<0 else self.body[:amount]; self.read_bytes+=len(data); return data
class Response:
    def __init__(self,status,headers=None,body=b""):
        self.status_code=status; self.headers=headers or {}; self.raw=Raw(body); self.closed=False
    def close(self): self.closed=True
class Session:
    def __init__(self,payload,ignore_range=False,wrong_range=False):
        self.payload=payload; self.ignore_range=ignore_range; self.wrong_range=wrong_range
        self.responses=[]; self.calls=[]
    def get(self,url,**kwargs):
        self.calls.append((url,kwargs))
        if self.ignore_range: response=Response(200,{"Content-Length":str(len(self.payload))},self.payload)
        else:
            m=re.fullmatch(r"bytes=(\d+)-(\d+)",kwargs["headers"]["Range"])
            start,end=int(m.group(1)),int(m.group(2)); actual=start+1 if self.wrong_range else start
            body=self.payload[actual:end+1]
            response=Response(206,{"Content-Range":f"bytes {actual}-{end}/{len(self.payload)}",
                "Content-Length":str(len(body)),"Content-Encoding":"identity"},body)
        self.responses.append(response); return response

def fixture():
    buf=BytesIO(); values=np.arange(80*80,dtype=np.float32).reshape(80,80); values[13,12]=-9999.
    keys=(1,1,0,2,1024,0,1,1,1025,0,1,1)
    tifffile.imwrite(buf,values,rowsperstrip=1,metadata=None,extratags=[
        (33550,"d",3,(1.,1.,0.),False),(33922,"d",6,(0.,0.,0.,1000.,2000.,0.),False),
        (34735,"H",len(keys),keys,False)])
    return buf.getvalue(),values

class E548Tests(unittest.TestCase):
    def test_exact_urls_are_pinned(self):
        validate_url(TIFF_URL,TIFF_PATH); validate_url(LABEL_URL,LABEL_PATH)
    def test_allowlist_rejects_host_path_query_and_scheme(self):
        for url in (TIFF_URL.replace("https://","http://"),
            TIFF_URL.replace("asc-pds-services.s3.us-west-2.amazonaws.com","example.com"),
            TIFF_URL+"?download=1",TIFF_URL.replace("_blend40.tif","_other.tif")):
            with self.subTest(url=url),self.assertRaises(ValueError): validate_url(url,TIFF_PATH)
    def test_pds3_label_parser_extracts_nodata_and_units(self):
        f=parse_pds3_label("SAMPLE_TYPE = IEEE_REAL\nSAMPLE_BITS = 32\nMISSING_CONSTANT = -3.4028E+38\nUNIT = METERS\n")
        self.assertEqual(f["SAMPLE_TYPE"],"IEEE_REAL"); self.assertEqual(f["SAMPLE_BITS"],"32")
        self.assertEqual(f["MISSING_CONSTANT"],"-3.4028E+38"); self.assertEqual(f["UNIT"],"METERS")
    def test_geokey_directory_is_decoded(self):
        payload,_=fixture()
        with tifffile.TiffFile(BytesIO(payload)) as tif: keys=parse_geokeys(tif.pages[0])
        self.assertEqual(keys[1024],1); self.assertEqual(keys[1025],1)
    def test_reads_only_requested_float32_rows_and_masks_nodata(self):
        payload,values=fixture(); session=Session(payload); reader=RangeReader(session,TIFF_URL,len(payload),MAX_TIFF_TRANSFER_BYTES)
        with tifffile.TiffFile(BytesIO(payload)) as tif:
            result=read_float_window(reader,tif.pages[0],{"col_off":8,"row_off":8,"width":16,"height":16},-9999.)
        self.assertEqual(result["pixels_requested"],256); self.assertEqual(result["masked_nodata_pixels"],1)
        self.assertEqual(result["usable_pixels"],255); self.assertEqual(result["statistics_raw_sample_values"]["min"],float(values[8,8]))
        self.assertEqual(len(session.calls),16); self.assertTrue(all(x[1]["headers"]["Range"].startswith("bytes=") for x in session.calls))
        self.assertTrue(all(x.closed for x in session.responses)); self.assertFalse(result["raw_pixels_retained"])
    def test_rejects_window_outside_raster(self):
        payload,_=fixture()
        with tifffile.TiffFile(BytesIO(payload)) as tif:
            with self.assertRaisesRegex(ValueError,"exceeds TIFF"):
                read_float_window(RangeReader(Session(payload),TIFF_URL,len(payload)),tif.pages[0],
                    {"col_off":79,"row_off":79,"width":2,"height":2},None)
    def test_range_ignored_without_consuming_body(self):
        payload,_=fixture(); session=Session(payload,ignore_range=True); reader=RangeReader(session,TIFF_URL,len(payload))
        with self.assertRaisesRegex(ProbeError,"ignored Range"): reader.read(16)
        self.assertEqual(session.responses[-1].raw.read_bytes,0); self.assertTrue(session.responses[-1].closed)
    def test_mismatched_content_range_rejected(self):
        payload,_=fixture(); session=Session(payload,wrong_range=True); reader=RangeReader(session,TIFF_URL,len(payload))
        with self.assertRaisesRegex(ProbeError,"Content-Range"): reader.read(16)
        self.assertEqual(session.responses[-1].raw.read_bytes,0)
    def test_transfer_cap_checked_before_request(self):
        payload,_=fixture(); session=Session(payload); reader=RangeReader(session,TIFF_URL,len(payload),max_bytes=8)
        with self.assertRaisesRegex(ProbeError,"1 MB cap"): reader.read(16)
        self.assertEqual(session.calls,[])

if __name__=="__main__": unittest.main()
