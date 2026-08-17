"""Fetch a full snapshot of the Course Seeker public search index.

Course Seeker (courseseeker.edu.au) is a joint initiative of the Australian
Government and the Tertiary Admission Centres. Its front end reads from an
unauthenticated Elasticsearch endpoint; this script pages through that endpoint
once and writes a local snapshot for offline analysis.

Deliberately polite: one request at a time, a delay between requests, and
partitioned by institution so no single query is large.

Output:
    data/raw/institutions.json  - 154 institutions with campuses
    data/raw/courses.json       - all course records
"""

import json
import time
import urllib.request
from pathlib import Path

BASE = "https://www.courseseeker.edu.au/search-engine"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DELAY = 0.4
PAGE = 500


def post(path, body):
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def fetch_institutions():
    d = post("/institutions/institution/_search", {"size": 500, "query": {"match_all": {}}})
    return [h["_source"] for h in d["hits"]["hits"]]


def fetch_courses_for(inst_code):
    out = []
    frm = 0
    while True:
        d = post(
            "/courses/course/_search",
            {
                "size": PAGE,
                "from": frm,
                "query": {"term": {"institution": inst_code}},
                "sort": ["_doc"],
            },
        )
        hits = d["hits"]["hits"]
        out.extend(h["_source"] for h in hits)
        total = d["hits"]["total"]
        total = total if isinstance(total, int) else total["value"]
        frm += PAGE
        if frm >= total or not hits:
            return out, total
        time.sleep(DELAY)


def main():
    RAW.mkdir(parents=True, exist_ok=True)

    insts = fetch_institutions()
    (RAW / "institutions.json").write_text(json.dumps(insts, indent=1), encoding="utf-8")
    print(f"institutions: {len(insts)}")

    # only _search is proxied (_count returns 405), so size:0 gives the total
    expected = post("/courses/course/_search", {"size": 0, "query": {"match_all": {}}})
    expected = expected["hits"]["total"]
    expected = expected if isinstance(expected, int) else expected["value"]
    print(f"expected courses: {expected}")

    courses = []
    for i, inst in enumerate(insts, 1):
        code = inst["institution"]
        try:
            rows, total = fetch_courses_for(code)
        except Exception as e:  # keep going; report gaps at the end
            print(f"  !! {code} {inst['institutionName']}: {e}")
            continue
        courses.extend(rows)
        print(f"[{i:3}/{len(insts)}] {code} {inst['institutionName'][:45]:45} {len(rows):5} / {total}")
        time.sleep(DELAY)

    (RAW / "courses.json").write_text(json.dumps(courses, indent=1), encoding="utf-8")
    print(f"\ncourses fetched: {len(courses)} (endpoint reports {expected})")


if __name__ == "__main__":
    main()
