"""Fetch QILT graduate outcome and student experience data from the ComparED API.

ComparED (compared.edu.au) is the Australian Government / Social Research Centre
site that publishes the QILT survey results. Its Angular front end reads a public
JSON API at api.compared.edu.au; one request per study area returns every
institution's full indicator set, so the whole national matrix is ~21 requests.

Output:
    data/raw/compared_study_areas.json  - raw payload per study area
    data/raw/qilt_matrix.json           - flat institution x study area rows
"""

import json
import time
import urllib.request
from pathlib import Path

API = "https://api.compared.edu.au"
ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
DELAY = 0.5


def get(path):
    req = urllib.request.Request(API + path, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as r:
        return json.load(r)


def flatten(inst, area_title, level):
    """One row per institution x study area x study level."""
    block = inst.get(level) or {}
    row = {
        "institution": inst.get("title"),
        "institutionAlias": inst.get("alias"),
        "instType": inst.get("type"),
        "states": inst.get("location"),
        "studyArea": area_title,
        "studyLevel": level,
        "seResponses": block.get("studentExperienceCount"),
        "geResponses": block.get("graduateEmploymentCount"),
    }
    for h in block.get("highlights") or []:
        # -2.0 is ComparED's "not published / too few responses" sentinel
        score = h.get("score")
        key = h.get("alias") or h.get("title")
        row[key] = None if score in (-2.0, -1.0) else score
        row[f"{key}__natAvg"] = h.get("nationalAverageScore")
        row[f"{key}__aboveNat"] = h.get("aboveNationalAverage")
    sal = (block.get("salary") or {}).get("overview") or {}
    nat = (block.get("salary") or {}).get("nationalAverage") or {}
    row["salary1yr"] = sal.get("oneYear")
    row["salary5yr"] = sal.get("fiveYear")
    row["salary9yr"] = sal.get("nineYear")
    row["salary1yr__natAvg"] = nat.get("oneYear")
    row["salary5yr__natAvg"] = nat.get("fiveYear")
    row["salary9yr__natAvg"] = nat.get("nineYear")
    return row


def main():
    RAW.mkdir(parents=True, exist_ok=True)

    areas = get("/study-areas")
    print(f"study areas: {len(areas)}")

    payloads, rows = {}, []
    for i, a in enumerate(areas, 1):
        alias = a["alias"]
        d = get(f"/study-area/{alias}")
        payloads[alias] = d
        insts = d.get("institutions") or []
        for inst in insts:
            for level in ("undergraduate", "postgraduate"):
                rows.append(flatten(inst, d.get("title"), level))
        print(f"[{i:2}/{len(areas)}] {d.get('title')[:44]:46} {len(insts):3} institutions")
        time.sleep(DELAY)

    (RAW / "compared_study_areas.json").write_text(json.dumps(payloads, indent=1), encoding="utf-8")
    (RAW / "qilt_matrix.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    ug = [r for r in rows if r["studyLevel"] == "undergraduate"]
    print(f"\nrows: {len(rows)} ({len(ug)} undergraduate)")


if __name__ == "__main__":
    main()
