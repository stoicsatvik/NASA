"""Independent official USGS 2018 MGD3 database ZIP access, read-only."""
from __future__ import annotations
import argparse
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
from research.e318_mars_dune_source import profile_table, MAX_DOWNLOAD

PAGES = (
    "https://pubs.usgs.gov/of/2018/1164/",
    "https://pubs.usgs.gov/publication/ofr20181164",
)

class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            href = dict(attrs).get("href")
            if href:
                self.hrefs.append(href)


def safe_zip(url: str) -> bool:
    p = urlsplit(url)
    return (p.scheme == "https" and p.hostname == "pubs.usgs.gov"
            and p.path.lower().endswith(".zip") and not p.username and not p.password)


def discover(page: str, html: str) -> list[str]:
    if urlsplit(page).hostname != "pubs.usgs.gov":
        raise ValueError("untrusted discovery page")
    parser = Links()
    parser.feed(html)
    return sorted(set(url for href in parser.hrefs
                      if safe_zip(url := urljoin(page, href))))


def read(url: str, limit: int) -> bytes:
    with urlopen(Request(url, headers={"User-Agent": "NASA-MGD3-E318/1.0"}), timeout=40) as resp:
        p = urlsplit(resp.geturl())
        if p.scheme != "https" or p.hostname != "pubs.usgs.gov":
            raise ValueError("redirect outside official USGS publications host")
        raw = resp.read(limit + 1)
    if len(raw) > limit:
        raise ValueError("official publication resource exceeds bound")
    return raw


def audit(reader=read) -> dict:
    pages = []
    links = set()
    for page in PAGES:
        try:
            html = reader(page, 1_000_000).decode("utf-8", errors="replace")
            found = discover(page, html)
            pages.append({"url": page, "status": "READ", "zip_links": found})
            links.update(found)
        except (OSError, ValueError) as exc:
            pages.append({"url": page, "status": "ACCESS_FAILED", "error_type": type(exc).__name__})
    files = []
    for url in sorted(links)[:5]:
        try:
            data = reader(url, MAX_DOWNLOAD)
            files.append({"url": url, "status": "DOWNLOADED", "bytes": len(data),
                          "sha256": hashlib.sha256(data).hexdigest(),
                          "tables": profile_table(data, urlsplit(url).path.rsplit("/", 1)[-1])})
        except (OSError, ValueError, ImportError) as exc:
            files.append({"url": url, "status": "ACCESS_OR_PARSE_FAILED", "error_type": type(exc).__name__})
    tables = [t for f in files for t in f.get("tables", []) if "rows" in t]
    return {"pages": pages, "file_receipts": files, "tables_profiled": len(tables),
            "status": "REAL_MARS_TABLES_PROFILED" if tables else "NO_MARS_TABLES_PROFILED",
            "source": "USGS OFR 2018-1164, DOI 10.3133/ofr20181164",
            "e001_known_site_recovery": "NOT YET MEASURED",
            "cross_body_similarity": "NOT YET PROVEN"}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = audit()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": result["status"], "tables_profiled": result["tables_profiled"],
                      "pages": result["pages"],
                      "files": [{"url": f["url"], "status": f["status"]} for f in result["file_receipts"]]}, sort_keys=True))

if __name__ == "__main__":
    main()
