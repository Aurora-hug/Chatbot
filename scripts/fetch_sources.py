#!/usr/bin/env python3
"""Fetch the candidate public CMRFU corpus with robots and rate-limit checks.

Requires PyMuPDF for PDF text: python -m pip install PyMuPDF
This script never submits forms, authenticates, or circumvents HTTP blocks.
"""
import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.robotparser import RobotFileParser

ROOT = Path(__file__).resolve().parents[1]
AGENT = "CMRFUResearchPrototype/0.1 (+public-source-evaluation)"
ALLOWED = {"www.cmrfu.co.nz", "d26phqdbpt0w91.cloudfront.net", "www.navigationhomesstadium.co.nz"}
MAX_BYTES = 8 * 1024 * 1024


class PageText(HTMLParser):
    SKIP = {"script", "style", "svg", "nav", "footer", "header", "noscript"}
    BREAKS = {"p", "h1", "h2", "h3", "h4", "li", "tr", "td", "th", "br", "section"}
    VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
            "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self):
        super().__init__()
        self.skip_depth = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if self.skip_depth or tag in self.SKIP:
            if tag not in self.VOID:
                self.skip_depth += 1
        elif tag in self.BREAKS:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if self.skip_depth:
            self.skip_depth -= 1
        elif tag in self.BREAKS:
            self.parts.append("\n")

    def handle_data(self, data):
        if not self.skip_depth:
            self.parts.append(data)

    def text(self):
        return "\n".join(
            line for part in "".join(self.parts).splitlines()
            if (line := re.sub(r"\s+", " ", part).strip())
        )


def robots_policy(url):
    parts = urlparse(url)
    if parts.scheme != "https" or parts.hostname not in ALLOWED:
        raise ValueError(f"Unapproved host: {url}")
    parser = RobotFileParser()
    parser.set_url(f"{parts.scheme}://{parts.netloc}/robots.txt")
    parser.read()
    return parser.can_fetch(AGENT, url)


def fetch(url):
    req = Request(url, headers={"User-Agent": AGENT, "Accept": "text/html,application/pdf"})
    with urlopen(req, timeout=20) as resp:
        final_url = resp.geturl()
        if urlparse(final_url).hostname not in ALLOWED:
            raise ValueError(f"Redirected outside allowed hosts: {final_url}")
        blob = resp.read(MAX_BYTES + 1)
        if len(blob) > MAX_BYTES:
            raise ValueError("Source exceeds 8 MiB safety limit")
        return blob, resp.headers.get_content_type(), final_url


def extract(blob, kind):
    if kind == "pdf":
        import fitz
        with fitz.open(stream=blob, filetype="pdf") as doc:
            return "\n\n".join(
                f"[PDF page {i + 1}]\n{page.get_text()}" for i, page in enumerate(doc)
            )
    parser = PageText()
    parser.feed(blob.decode("utf-8", errors="replace"))
    return parser.text()


def main():
    argp = argparse.ArgumentParser(description=__doc__)
    argp.add_argument("--out", type=Path, default=ROOT / "corpus")
    args = argp.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    candidates = json.loads((ROOT / "data/sources.json").read_text())["sources"]
    records = []
    for source in candidates:
        url = source["url"]
        record = {"id": source["id"], "url": url, "client_approval_status": "pending_confirmation"}
        try:
            if not robots_policy(url):
                raise PermissionError("robots.txt disallows this URL or is inaccessible")
            blob, content_type, final_url = fetch(url)
            expected_type = "application/pdf" if source["kind"] == "pdf" else "text/html"
            if content_type != expected_type:
                raise ValueError(f"Unexpected Content-Type: {content_type}")
            content = extract(blob, source["kind"])
            if not content.strip():
                raise ValueError("No readable text extracted")
            (args.out / f"{source['id']}.txt").write_text(content, encoding="utf-8")
            record.update(status="ok", fetched_url=final_url,
                          sha256=hashlib.sha256(blob).hexdigest(),
                          bytes=len(blob), text_characters=len(content))
        except (HTTPError, URLError, PermissionError, ValueError, ImportError) as exc:
            record.update(status="skipped", reason=str(exc))
        records.append(record)
        print(f"{record['id']}: {record['status']}")
        time.sleep(1.5)
    (args.out / "fetch_report.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
