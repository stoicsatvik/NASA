"""E555: metadata-only inventory of FOM/provenance assets for the 2020 TRN HiRISE DTM.

The probe reads one public directory index and the product's two small metadata
files. It never requests raster bytes, credentials, signed URLs, or raw pixels.
Only asset names, hashes, bounded keyword counts, and transfer metadata persist.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

import requests

HOST = "asc-pds-services.s3.us-west-2.amazonaws.com"
BASE = "https://asc-pds-services.s3.us-west-2.amazonaws.com/mosaic/mars2020_trn/HiRISE/"
INDEX_URL = BASE + "index.html"
DTM_STEM = "JEZ_hirise_soc_006_DTM_MOLAtopography_DeltaGeoid_1m_Eqc_latTs0_lon0_blend40"
LABEL_URL = BASE + DTM_STEM + "_pds3.lbl"
XML_URL = BASE + DTM_STEM + ".xml"
EXPECTED_ASSETS = {DTM_STEM + ".tif", DTM_STEM + "_pds3.lbl", DTM_STEM + ".xml"}
MAX_INDEX_BYTES = 128_000
MAX_LABEL_BYTES = 256_000
MAX_XML_BYTES = 512_000
USER_AGENT = "Unified-Parallel-Foundry-E555/1.0"

FOM_PATTERNS = (
    re.compile(r"(?<![A-Z0-9])FOM(?![A-Z0-9])", re.IGNORECASE),
    re.compile(r"FIGURE[\s_-]+OF[\s_-]+MERIT", re.IGNORECASE),
)
METADATA_PATTERNS = {
    "confidence": re.compile(r"\bCONFIDENCE\b", re.IGNORECASE),
    "provenance": re.compile(r"\bPROVENANCE\b", re.IGNORECASE),
    "quality": re.compile(r"\bQUALITY\b", re.IGNORECASE),
    "mask": re.compile(r"\bMASK\b", re.IGNORECASE),
    "nodata": re.compile(r"\b(?:NO_DATA|NODATA|MISSING_CONSTANT)\b", re.IGNORECASE),
}


class E555Error(RuntimeError):
    def __init__(self, outcome: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.outcome = outcome
        self.details = details or {}


class _AnchorParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def _validate_pinned_url(url: str, expected_path: str) -> None:
    parsed = urlsplit(url)
    try:
        port = parsed.port
    except ValueError as error:
        raise E555Error("URL_PORT_INVALID", "Pinned metadata URL has an invalid port") from error
    if (
        parsed.scheme != "https"
        or parsed.hostname != HOST
        or port not in (None, 443)
        or parsed.username
        or parsed.password
        or parsed.path != expected_path
        or parsed.query
        or parsed.fragment
    ):
        raise E555Error("URL_OUTSIDE_ALLOWLIST", "Metadata URL is outside the exact public USGS allowlist")


def _read_bounded(session: requests.Session, url: str, expected_path: str, cap: int) -> tuple[bytes, dict]:
    _validate_pinned_url(url, expected_path)
    response = session.get(
        url,
        headers={"User-Agent": USER_AGENT, "Accept-Encoding": "identity"},
        timeout=(15, 45),
        allow_redirects=False,
        stream=True,
    )
    try:
        status = int(response.status_code)
        if status in (301, 302, 303, 307, 308):
            raise E555Error("METADATA_REDIRECT", "Pinned metadata request redirected")
        if status != 200:
            raise E555Error(f"METADATA_HTTP_{status}", "Pinned metadata request did not return HTTP 200")
        if response.url != url:
            raise E555Error("METADATA_FINAL_URL_CHANGED", "Metadata response URL differs from the pinned URL")
        encoding = response.headers.get("Content-Encoding", "identity").lower()
        if encoding not in ("", "identity"):
            raise E555Error("METADATA_CONTENT_ENCODED", "Unexpected content encoding")
        declared = response.headers.get("Content-Length")
        if declared:
            if not declared.isdigit() or int(declared) > cap:
                raise E555Error("METADATA_TOO_LARGE", "Declared metadata size exceeds the cap")
        body = response.raw.read(cap + 1, decode_content=False)
        if len(body) > cap:
            raise E555Error("METADATA_TOO_LARGE", "Bounded metadata read exceeded the cap")
        if declared and len(body) != int(declared):
            raise E555Error("METADATA_LENGTH_MISMATCH", "Metadata byte count differs from Content-Length")
        return body, {
            "url": url,
            "http_status": status,
            "content_type": response.headers.get("Content-Type"),
            "bytes": len(body),
            "sha256": hashlib.sha256(body).hexdigest(),
            "cap_bytes": cap,
        }
    finally:
        response.close()


def _asset_name_from_href(href: str) -> str | None:
    if "\\" in href or "../" in href or href.startswith("../"):
        raise E555Error("INDEX_PATH_TRAVERSAL", "Directory index contains a path-traversal link")
    parsed = urlsplit(href)
    if parsed.query or parsed.fragment:
        raise E555Error("INDEX_QUERY_LINK", "Directory index contains an unexpected query or fragment")
    if parsed.scheme or parsed.netloc:
        if parsed.scheme != "https" or parsed.hostname != HOST:
            raise E555Error("INDEX_EXTERNAL_LINK", "Directory index contains an unexpected external host")
        path = parsed.path
    elif href.startswith("/"):
        path = href
    elif href.startswith("mosaic/"):
        path = "/" + href
    else:
        path = BASE.split(HOST, 1)[1] + href
    if not path.startswith("/mosaic/mars2020_trn/HiRISE/"):
        return None
    if path.endswith("/") or path.endswith("index.html"):
        return None
    name = path.rsplit("/", 1)[-1]
    if not name or name in (".", ".."):
        raise E555Error("INDEX_INVALID_ASSET_NAME", "Directory index contains an invalid asset name")
    return name


def parse_asset_index(payload: bytes) -> list[str]:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise E555Error("INDEX_INVALID_UTF8", "Directory index is not valid UTF-8") from error
    parser = _AnchorParser()
    parser.feed(text)
    names = [_asset_name_from_href(href) for href in parser.hrefs]
    assets = sorted({name for name in names if name})
    if not assets:
        raise E555Error("INDEX_NO_ASSETS", "Pinned directory index contains no assets")
    missing = EXPECTED_ASSETS - set(assets)
    if missing:
        raise E555Error(
            "INDEX_EXPECTED_ASSET_MISSING",
            "Pinned directory index does not contain the expected DTM/metadata files",
            {"missing": sorted(missing)},
        )
    return assets


def classify_asset_names(assets: list[str]) -> dict:
    fom_tokens = ("fom", "figure_of_merit", "figure-of-merit", "figureofmerit")
    provenance_tokens = fom_tokens + ("provenance", "confidence", "quality", "hillshade", "mask")
    fom_assets = sorted(name for name in assets if any(token in name.lower() for token in fom_tokens))
    provenance_assets = sorted(name for name in assets if any(token in name.lower() for token in provenance_tokens))
    return {
        "fom_assets": fom_assets,
        "fom_asset_count": len(fom_assets),
        "provenance_or_quality_assets": provenance_assets,
        "provenance_or_quality_asset_count": len(provenance_assets),
        "raster_asset_count": sum(name.lower().endswith((".tif", ".tiff")) for name in assets),
        "metadata_asset_count": sum(name.lower().endswith((".lbl", ".xml", ".vrt", ".history.isiscube")) for name in assets),
    }


def scan_metadata(payload: bytes) -> dict:
    text = payload.decode("utf-8", errors="replace")
    lines = text.splitlines()
    fom_lines = []
    other_hits = {name: [] for name in METADATA_PATTERNS}
    for number, line in enumerate(lines, start=1):
        if any(pattern.search(line) for pattern in FOM_PATTERNS):
            fom_lines.append(number)
        for name, pattern in METADATA_PATTERNS.items():
            if pattern.search(line):
                other_hits[name].append(number)
    return {
        "line_count": len(lines),
        "fom_reference_line_numbers": fom_lines,
        "fom_reference_line_count": len(fom_lines),
        "keyword_line_numbers": other_hits,
        "raw_metadata_retained": False,
    }


def classify_fom_availability(asset_summary: dict, label_scan: dict, xml_scan: dict) -> str:
    if asset_summary["fom_asset_count"] or label_scan["fom_reference_line_count"] or xml_scan["fom_reference_line_count"]:
        return "FOM_ASSET_OR_REFERENCE_FOUND"
    return "FOM_NOT_LISTED_OR_REFERENCED_IN_PINNED_RELEASE_METADATA"


def run() -> dict:
    session = requests.Session()
    index_bytes, index_receipt = _read_bounded(
        session, INDEX_URL, "/mosaic/mars2020_trn/HiRISE/index.html", MAX_INDEX_BYTES
    )
    assets = parse_asset_index(index_bytes)
    asset_summary = classify_asset_names(assets)

    label_bytes, label_receipt = _read_bounded(
        session, LABEL_URL, urlsplit(LABEL_URL).path, MAX_LABEL_BYTES
    )
    xml_bytes, xml_receipt = _read_bounded(
        session, XML_URL, urlsplit(XML_URL).path, MAX_XML_BYTES
    )
    label_scan = scan_metadata(label_bytes)
    xml_scan = scan_metadata(xml_bytes)
    outcome = classify_fom_availability(asset_summary, label_scan, xml_scan)

    return {
        "experiment": "E555 metadata-only FOM/provenance asset inventory",
        "outcome": outcome,
        "source": {
            "publisher": "USGS Astrogeology Science Center",
            "doi": "10.5066/P9REJ9JN",
            "product": "Mars 2020 TRN HiRISE DTM mosaic (2020)",
            "directory_index": index_receipt,
            "pds3_label": label_receipt,
            "product_xml": xml_receipt,
        },
        "inventory": {
            "public_directory_asset_count": len(assets),
            "asset_names": assets,
            **asset_summary,
            "pds3_label_scan": label_scan,
            "product_xml_scan": xml_scan,
        },
        "design": {
            "metadata_only": True,
            "raster_requests": 0,
            "raw_pixels_requested": False,
            "raw_metadata_retained": False,
            "credentials_used": False,
            "redirects_followed": False,
            "index_cap_bytes": MAX_INDEX_BYTES,
            "label_cap_bytes": MAX_LABEL_BYTES,
            "xml_cap_bytes": MAX_XML_BYTES,
        },
        "interpretation": {
            "fom_available_in_pinned_2020_trn_directory": (
                "LISTED" if asset_summary["fom_asset_count"] else "NOT LISTED"
            ),
            "fom_referenced_by_pinned_product_metadata": (
                "REFERENCED" if label_scan["fom_reference_line_count"] or xml_scan["fom_reference_line_count"] else "NOT REFERENCED"
            ),
            "physical_cause_of_E550_E554_nodata": "NOT DETERMINED",
            "cross_body_similarity": "NOT YET PROVEN",
            "known_site_recovery": "NOT YET MEASURED",
            "novel_analogue_discovery": "NOT YET PROVEN",
            "route_safety": "NOT CLAIMED",
        },
        "limitations": [
            "Absence from this public directory and its two pinned metadata files does not prove that no separate FOM or quality product exists elsewhere.",
            "Generic HiRISE DTM documentation describes FOM assets for standard PDS DTMs; that documentation is not assumed to apply automatically to this 2020 TRN flight mosaic.",
            "No raster, FOM pixels, raw metadata body, or private source was downloaded or retained.",
            "The inventory cannot determine why the three E550/E554 windows are nodata.",
        ],
        "next_action": "If no FOM asset or metadata reference is found, ask the designated PDS/USGS support contact whether this specific flight mosaic has a separate provenance/coverage product; otherwise preserve the unsupported windows.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    try:
        result = run()
    except E555Error as error:
        result = {
            "experiment": "E555 metadata-only FOM/provenance asset inventory",
            "outcome": error.outcome,
            "message": str(error),
            "details": error.details,
            "raster_requests": 0,
            "raw_pixels_requested": False,
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "experiment": result["experiment"],
        "outcome": result["outcome"],
        "public_directory_asset_count": result.get("inventory", {}).get("public_directory_asset_count"),
        "fom_asset_count": result.get("inventory", {}).get("fom_asset_count"),
        "fom_label_reference_lines": result.get("inventory", {}).get("pds3_label_scan", {}).get("fom_reference_line_count"),
        "fom_xml_reference_lines": result.get("inventory", {}).get("product_xml_scan", {}).get("fom_reference_line_count"),
        "raster_requests": result.get("design", {}).get("raster_requests", 0),
    }, sort_keys=True))
    return 0 if result["outcome"] in {
        "FOM_ASSET_OR_REFERENCE_FOUND",
        "FOM_NOT_LISTED_OR_REFERENCED_IN_PINNED_RELEASE_METADATA",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
