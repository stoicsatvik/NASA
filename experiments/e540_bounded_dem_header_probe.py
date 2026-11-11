"""Probe only the first 32 bytes of one metadata-named public ScienceBase DEM."""
from __future__ import annotations
import argparse, hashlib, json, re, urllib.error, urllib.parse, urllib.request
from pathlib import Path
from experiments.e539_public_cloud_url_metadata_audit import _fetch_metadata

ITEM_ID = "662bccfad34ea70bd5f11f88"
ITEM_URL = f"https://www.sciencebase.gov/catalog/item/{ITEM_ID}?format=json"
TARGET = "GFDF_Ripples_2023_04_18_DEM.tif"
LIMIT = 32
SB_HOSTS = {"www.sciencebase.gov", "sciencebase.gov", "sciencebase.usgs.gov"}
S3_HOSTS = {"prod-is-usgs-sb-prod-content.s3.amazonaws.com"}
SIGNED_KEYS = {"awsaccesskeyid", "expires", "signature", "x-amz-algorithm", "x-amz-credential", "x-amz-date", "x-amz-expires", "x-amz-security-token", "x-amz-signedheaders", "x-amz-signature"}
TOKEN_KEYS = {"token", "access_token", "auth", "authorization", "key", "api_key", "signature", "sig", "awsaccesskeyid", "x-amz-signature", "x-amz-credential", "x-amz-security-token", "expires", "se", "sp", "sv"}
MAGIC = {b"II*\x00": "TIFF_CLASSIC_LE", b"MM\x00*": "TIFF_CLASSIC_BE", b"II+\x00": "BIGTIFF_LE", b"MM\x00+": "BIGTIFF_BE"}

class UnsafeRedirect(RuntimeError): pass

def _keys(parsed):
    return {k.lower() for k, _ in urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)}

def _allowed(url, redirect=False):
    try:
        p = urllib.parse.urlsplit(url)
        if p.scheme != "https" or not p.hostname or p.username or p.password or p.fragment:
            return False
        host, keys = p.hostname.lower(), _keys(p)
        if host in SB_HOSTS:
            return p.path.startswith(("/manager/download/", "/catalog/file/get/")) and not (keys & TOKEN_KEYS)
        if host in S3_HOSTS:
            return not (keys & TOKEN_KEYS) if not redirect else (not keys or keys <= SIGNED_KEYS)
        return False
    except ValueError:
        return False

def _summary(url):
    p = urllib.parse.urlsplit(url)
    return {"scheme": p.scheme, "host": (p.hostname or "").lower(), "path": p.path or "/", "query_key_names": sorted(_keys(p))}

def _find_file(files):
    if not isinstance(files, list): raise ValueError("missing file list")
    matches = [x for x in files if isinstance(x, dict) and x.get("name") == TARGET]
    if len(matches) != 1: raise ValueError(f"expected one exact DEM record, found {len(matches)}")
    rec = matches[0]
    if not isinstance(rec.get("downloadUri"), str) or not _allowed(rec["downloadUri"]):
        raise ValueError("exact DEM record has no admissible anonymous downloadUri")
    return rec

def _magic(data): return MAGIC.get(data[:4]) if len(data) >= 4 else None

def _request(url):
    if not _allowed(url): raise ValueError("source URL outside allowlist")
    return urllib.request.Request(url, headers={"User-Agent": "UnifiedParallelFoundry-E540/1.0", "Accept": "image/tiff, application/octet-stream", "Range": f"bytes=0-{LIMIT-1}"}, method="GET")

class _Redirects(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not _allowed(newurl, redirect=True): raise UnsafeRedirect("redirect outside pinned ScienceBase/USGS hosts")
        return super().redirect_request(req, fp, code, msg, headers, newurl)

def _classify(status, headers, data, expected_size):
    cr = headers.get("Content-Range") if headers else None
    m = re.fullmatch(r"bytes\s+0-31/(\d+)", cr.strip(), re.I) if cr else None
    total = int(m.group(1)) if m else None
    magic = _magic(data)
    if status == 206:
        if len(data) != LIMIT: decision = "SHORT_OR_OVERSIZED_RANGE_BODY"
        elif total is None: decision = "INVALID_CONTENT_RANGE"
        elif magic is None: decision = "NON_TIFF_HEADER"
        elif expected_size is not None and total != expected_size: decision = "METADATA_SIZE_MISMATCH"
        else: decision = "BOUNDED_TIFF_HEADER_ACQUIRED"
    elif status == 200: decision = "SERVER_IGNORED_RANGE_LIMIT"
    elif status in {403, 404}: decision = "ANONYMOUS_ACCESS_DENIED_OR_MISSING"
    else: decision = f"HTTP_{status}"
    length = headers.get("Content-Length") if headers else None
    return {"http_status": status, "bytes_read": len(data), "range_requested": f"bytes=0-{LIMIT-1}", "content_range": cr, "content_range_total_bytes": total, "content_length_bytes": int(length) if length and length.isdigit() else None, "content_type": headers.get("Content-Type") if headers else None, "tiff_magic": magic, "header_sha256": hashlib.sha256(data).hexdigest() if data else None, "decision": decision, "raster_bytes_stored": False, "raw_url_stored": False, "query_values_stored": False}

def _probe(url, expected_size):
    opener = urllib.request.build_opener(_Redirects())
    try:
        with opener.open(_request(url), timeout=30) as r:
            data = r.read(LIMIT + 1)
            result = _classify(r.status, r.headers, data, expected_size)
            result["final_url"] = _summary(r.geturl())
            return result
    except urllib.error.HTTPError as e:
        data = e.read(LIMIT + 1)
        result = _classify(e.code, e.headers, data, expected_size)
        result["final_url"] = _summary(e.geturl())
        return result
    except UnsafeRedirect:
        return {"decision": "REDIRECT_REJECTED_OUTSIDE_ALLOWLIST", "bytes_read": 0, "raster_bytes_stored": False, "raw_url_stored": False, "query_values_stored": False}
    except Exception as e:
        return {"decision": "REQUEST_ERROR", "error_type": type(e).__name__, "bytes_read": 0, "raster_bytes_stored": False, "raw_url_stored": False, "query_values_stored": False}

def audit():
    status, raw, _ = _fetch_metadata(ITEM_URL)
    out = {"experiment": "E540", "item_id": ITEM_ID, "target_file": TARGET, "metadata_http_status": status, "range_limit_bytes": LIMIT, "credentials_sent": False, "full_file_download_attempted": False, "raster_bytes_stored": False, "raw_url_stored": False, "query_values_stored": False}
    if status != 200:
        out["decision"] = f"METADATA_HTTP_{status}"; return out
    try:
        rec = _find_file(json.loads(raw.decode("utf-8")).get("files"))
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as e:
        out["decision"] = "EXACT_FILE_RECORD_NOT_ADMISSIBLE"; out["error_type"] = type(e).__name__; return out
    size = rec.get("size")
    size = size if isinstance(size, int) and not isinstance(size, bool) and size >= 0 else None
    out["metadata_file_size_bytes"] = size
    out["source_url"] = _summary(rec["downloadUri"])
    out["probe"] = _probe(rec["downloadUri"], size)
    out["decision"] = out["probe"]["decision"]
    out["interpretation"] = "A positive result proves only a 32-byte TIFF-family header response. It does not establish CRS, vertical datum, pixel scale, nodata, elevation units, uncertainty, or Earth/Mars comparability."
    return out

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path(".artifacts/e540/bounded-dem-header.json"))
    args = parser.parse_args(); result = audit()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({k: result.get(k) for k in ("experiment", "decision", "range_limit_bytes", "credentials_sent", "full_file_download_attempted", "raster_bytes_stored")}, sort_keys=True))

if __name__ == "__main__": main()
