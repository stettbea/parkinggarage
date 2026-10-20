"""
Collect one snapshot of the Zurich parking guidance system (PLS) feed
and append it to a monthly CSV file in data/raw/.

Run every 15 minutes (GitHub Actions, cron, or Windows Task Scheduler).
Uses only the Python standard library, so it runs anywhere without setup.

Feed: https://www.pls-zh.ch/plsFeed/rss  (license: CC-0)
Each <item> contains:
    title        "Parkhaus Urania / Uraniastrasse 3"   -> name / address
    description  "open /  116"  or  "???? / ???"       -> status / free spaces
    guid         ".../urania.jsp?pid=urania"           -> stable parking_id
    dc:date      "2026-10-20T09:25:21Z"                -> when the garage last reported
"""

import csv
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

FEED_URL = "https://www.pls-zh.ch/plsFeed/rss"  # http:// redirects (301) to https://
NS = {"dc": "http://purl.org/dc/elements/1.1/"}
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"

COLUMNS = [
    "fetched_at_utc",         # when WE downloaded the feed
    "source_updated_at_utc",  # when the garage last reported (can be days old!)
    "parking_id",
    "parking_name",
    "address",
    "status",                 # open / closed / unknown
    "free_spaces",            # empty if not reported
]


def fetch_feed(retries=3, wait_seconds=10):
    """Download the feed, retrying a few times on network errors."""
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(FEED_URL, headers={"User-Agent": "ZHAW-student-project/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read()
        except Exception as exc:
            print(f"Attempt {attempt} failed: {exc}", file=sys.stderr)
            if attempt < retries:
                time.sleep(wait_seconds)
    raise RuntimeError("Could not download feed")


def parse_item(item, fetched_at):
    title = item.findtext("title", "").strip()
    name, _, address = title.partition(" / ")

    # description looks like "open /  116" or "???? / ???"
    status_raw, _, free_raw = item.findtext("description", "").partition("/")
    status = status_raw.strip().lower()
    if status not in ("open", "closed"):
        status = "unknown"
    free_raw = free_raw.strip()
    free_spaces = int(free_raw) if free_raw.isdigit() else ""

    guid = item.findtext("guid", "")
    parking_id = parse_qs(urlparse(guid).query).get("pid", [guid])[0]

    return {
        "fetched_at_utc": fetched_at,
        "source_updated_at_utc": item.findtext("dc:date", "", NS).strip(),
        "parking_id": parking_id,
        "parking_name": name.strip(),
        "address": address.strip(),
        "status": status,
        "free_spaces": free_spaces,
    }


def main():
    fetched_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    root = ET.fromstring(fetch_feed())
    rows = [parse_item(item, fetched_at) for item in root.iter("item")]

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out_file = RAW_DIR / f"parking_{fetched_at[:7]}.csv"  # one file per month
    is_new = not out_file.exists()
    with open(out_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if is_new:
            writer.writeheader()
        writer.writerows(rows)

    print(f"{fetched_at}: saved {len(rows)} garages to {out_file.name}")


if __name__ == "__main__":
    main()
