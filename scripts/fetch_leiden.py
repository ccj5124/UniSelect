"""Fetch Australian university research rankings from the CWTS Leiden Ranking
Open Edition 2025.

Chosen because it is the one credible international ranking that costs nothing to
use: the results are published on Zenodo under CC0 (public domain, DOI
10.5281/zenodo.17473224) and are computed from OpenAlex, itself CC0. QS, THE and
ARWU are all proprietary and licensed commercially.

The published results file is 589 MB, so this reads the same numbers from the
ranking site's own list endpoint instead: one request per field for Australia,
one for the world, giving both a national and a global rank.

Output: data/raw/leiden_au.json
"""

import json
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

URL = "https://open.leidenranking.com/Ranking2025/Ranking2025ListResult"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

PERIOD_ID = "15"          # 2020-2023, the most recent window
PERIOD_TEXT = "2020–2023"
FIELDS = {
    "0": "All sciences",
    "1": "Social sciences and humanities",
    "2": "Biomedical and health sciences",
    "3": "Physical sciences and engineering",
    "4": "Life and earth sciences",
    "5": "Mathematics and computer science",
}


class Rows(HTMLParser):
    """The endpoint returns a bare run of <tr> fragments."""

    def __init__(self):
        super().__init__()
        self.rows, self._row, self._cell, self._in = [], None, None, False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self._row = []
        elif tag in ("td", "th") and self._row is not None:
            self._cell, self._in = [], True

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self._in:
            self._row.append("".join(self._cell).strip())
            self._in = False
        elif tag == "tr" and self._row is not None:
            self.rows.append(self._row)
            self._row = None

    def handle_data(self, d):
        if self._in:
            self._cell.append(d)


def fetch(field_id, country_code=""):
    body = urllib.parse.urlencode({
        "field_id": field_id,
        "continent_code": "",
        "country_code": country_code,
        "performance_dimension": "0",      # scientific impact
        "ranking_indicator": "3",          # P, P(top 10%), PP(top 10%)
        "fractional_counting": "false",
        "core_pubs_only": "true",
        "number_of_publications": "0",
        "period_id": PERIOD_ID,
        "period_text": PERIOD_TEXT,
        "order_by": "p",                   # publication volume, the site default
    }).encode()
    req = urllib.request.Request(URL, data=body, headers={
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "Referer": "https://open.leidenranking.com/ranking/2025/list",
    })
    with urllib.request.urlopen(req, timeout=180) as r:
        p = Rows()
        p.feed(r.read().decode("utf-8", "replace"))
    return [row for row in p.rows if len(row) > 4 and row[0].isdigit()]


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    out = {
        "_source": "CWTS Leiden Ranking Open Edition 2025",
        "_doi": "10.5281/zenodo.17473224",
        "_licence": "CC0 1.0 Universal (public domain dedication)",
        "_basis": "OpenAlex data, core publications 2020-2023, full counting, "
                  "ranked by publication volume (P)",
        "fields": {},
    }
    for fid, name in FIELDS.items():
        au = fetch(fid, "AU")
        time.sleep(0.5)
        world = fetch(fid)
        time.sleep(0.5)
        gpos = {row[1]: i + 1 for i, row in enumerate(world)}
        out["fields"][name] = {
            "worldSize": len(world),
            "rows": [{
                "u": r[1],
                "auRank": i + 1,
                "globalRank": gpos.get(r[1]),
                "P": int(r[2].replace(",", "")),
                "Ptop10": int(r[3].replace(",", "")),
                "PPtop10": r[4],
            } for i, r in enumerate(au)],
        }
        print(f"  {name:38} AU {len(au):3}   world {len(world)}")

    (RAW / "leiden_au.json").write_text(json.dumps(out, indent=1, ensure_ascii=False),
                                        encoding="utf-8")
    print(f"\nwrote {RAW / 'leiden_au.json'}")


if __name__ == "__main__":
    main()
