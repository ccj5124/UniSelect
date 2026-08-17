"""Compact the two raw snapshots into a single dataset the front end can ship.

Inputs   data/raw/courses.json        Course Seeker course records
         data/raw/qilt_matrix.json    ComparED institution x study area outcomes
Output   data.json                    everything the app needs, ~1 file

The app is served from the repository root because GitHub Pages is configured to
deploy from a branch, and that mode can only publish the root or /docs.

Scope: bachelor courses that are actively offered and carry a clean entry rank.
Courses whose institution x study area cell has no published QILT result are kept
and flagged, not dropped, so the app can say "not published" rather than hide them.
"""

import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT

AREA_ZH = {
    "Agriculture and Environmental Studies": "农业与环境",
    "Architecture and Building": "建筑与营造",
    "Business and Management": "商科与管理",
    "Communications": "传播",
    "Computing and Information Systems": "计算机与信息系统",
    "Creative Arts": "创意艺术",
    "Dentistry": "牙医",
    "Engineering": "工程",
    "Health Services and Support": "健康服务",
    "Humanities, Culture and Social Sciences": "人文与社会科学",
    "Law and Paralegal Studies": "法律",
    "Medicine": "医学",
    "Nursing": "护理",
    "Pharmacy": "药学",
    "Psychology": "心理学",
    "Rehabilitation": "康复治疗",
    "Science and Mathematics": "理科与数学",
    "Social Work": "社会工作",
    "Teacher Education": "教育",
    "Tourism, Hospitality, Personal Services, Sport and Recreation": "旅游酒店与体育",
    "Veterinary Science": "兽医",
}

# ComparED indicator alias -> short key we ship
IND = {
    "full-time-employment": "fte",
    "employment": "emp",
    "educational-experience": "exp",
    "teaching-quality": "teach",
    "student-support": "sup",
    "skills-development": "skills",
    "overall-satisfaction": "sat",
    "learning-resources": "res",
}

# QILT study area -> Leiden main field. Leiden publishes five broad fields, so
# this is a coarse approximation and the UI labels it as one. "Science and
# Mathematics" spans three Leiden fields, so it falls back to All sciences.
AREA_TO_LEIDEN = {
    "Agriculture and Environmental Studies": "Life and earth sciences",
    "Veterinary Science": "Life and earth sciences",
    "Architecture and Building": "Physical sciences and engineering",
    "Engineering": "Physical sciences and engineering",
    "Computing and Information Systems": "Mathematics and computer science",
    "Dentistry": "Biomedical and health sciences",
    "Health Services and Support": "Biomedical and health sciences",
    "Medicine": "Biomedical and health sciences",
    "Nursing": "Biomedical and health sciences",
    "Pharmacy": "Biomedical and health sciences",
    "Rehabilitation": "Biomedical and health sciences",
    "Business and Management": "Social sciences and humanities",
    "Communications": "Social sciences and humanities",
    "Creative Arts": "Social sciences and humanities",
    "Humanities, Culture and Social Sciences": "Social sciences and humanities",
    "Law and Paralegal Studies": "Social sciences and humanities",
    "Psychology": "Social sciences and humanities",
    "Social Work": "Social sciences and humanities",
    "Teacher Education": "Social sciences and humanities",
    "Tourism, Hospitality, Personal Services, Sport and Recreation": "Social sciences and humanities",
    "Science and Mathematics": "All sciences",
}

# Leiden abbreviates university names; these are the ones normalisation misses.
LEIDEN_ALIASES = {
    "Univ New S Wales": "University of New South Wales",
    "Univ West Australia": "The University of Western Australia",
    "Univ Technol - Sydney": "University of Technology Sydney",
    "Australian Natl Univ": "The Australian National University",
    "West Sydney Univ": "Western Sydney University",
    "Univ S Australia": "University of South Australia",
    "Univ South Queensland": "University of Southern Queensland",
    "Cent Queensland Univ": "CQUniversity",
    "Univ New England - Australia": "The University of New England",
    "Victoria Univ - Melbourne": "Victoria University",
    "South Cross Univ": "Southern Cross University",
    "Federat Univ Australia": "Federation University Australia",
    "Univ Notre Dame Australia": "The University of Notre Dame Australia",
    "Australian Cath Univ": "Australian Catholic University",
    "Univ Sunshine Coast": "University of the Sunshine Coast",
    "Swinburne Univ Technol": "Swinburne University of Technology",
    "Queensland Univ Technol": "Queensland University of Technology",
}

PATH_KEYS = [
    ("numAdmittedAtar", "atar"),
    ("numAdmittedAtarplus", "atarPlus"),
    ("numAdmittedSec", "secOther"),
    ("numAdmittedHe", "transfer"),
    ("numAdmittedVet", "vet"),
    ("numAdmittedOther", "mature"),
]


def norm_area(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower().replace(" and ", " & "))


def norm_inst(s):
    s = (s or "").lower()
    s = re.sub(r"\b(the|of|australia|australian)\b", " ", s)
    return re.sub(r"[^a-z0-9]", "", s.replace("&", "and"))


def adm_criteria(c):
    """Selection criteria headings from the admission criteria blob.

    The markup is regular: <h4> is the applicant category, <h5> each criterion
    ("ATAR", "Interview", "Regional Adjustment", "Supplementary form"). Used to
    explain why two listings of the same degree carry different entry ranks.
    """
    for f in (c.get("features") or []):
        if f.get("code") == "ADM-CRITERIA":
            v = f.get("value") or ""
            return {re.sub(r"\s+", " ", t).strip()
                    for t in re.findall(r"<h5[^>]*>(.*?)</h5>", v, re.S | re.I)}
    return set()


def expand_leiden(s):
    """Leiden abbreviates: 'Univ Melbourne', 'Queensland Univ Technol'."""
    s = re.sub(r"\bUniv\b", "University", s)
    return re.sub(r"\bTechnol\b", "Technology", s)


def fnum(v, lo=20, hi=100):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if lo <= v <= hi else None


def count(v):
    """Admission counts: '<5' is a suppressed cell, 'N/A' and 'N/P' are absent."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    v = v.strip()
    if v == "<5":
        return 2.5
    try:
        return float(v)
    except ValueError:
        return None


def main():
    courses = json.loads((RAW / "courses.json").read_text(encoding="utf-8"))
    qrows = [r for r in json.loads((RAW / "qilt_matrix.json").read_text(encoding="utf-8"))
             if r["studyLevel"] == "undergraduate"]

    # ------------------------------------------------------------- study areas
    area_names = sorted({c.get("qiltStudyAreaName") for c in courses if c.get("qiltStudyAreaName")})
    area_idx = {n: i for i, n in enumerate(area_names)}
    areas = [{"en": n, "zh": AREA_ZH.get(n, n)} for n in area_names]

    # national averages are per indicator per study area, so they live on the area
    qa_by_norm = defaultdict(list)
    for r in qrows:
        qa_by_norm[norm_area(r["studyArea"])].append(r)
    for n, a in zip(area_names, areas):
        rs = qa_by_norm.get(norm_area(n), [])
        nat = {}
        for r in rs:
            for alias, short in IND.items():
                v = r.get(f"{alias}__natAvg")
                if v is not None and v > 0:
                    nat[short] = v
            for k in ("salary1yr", "salary5yr", "salary9yr"):
                v = r.get(f"{k}__natAvg")
                if v:
                    nat[k.replace("salary", "s").replace("yr", "")] = v
        a["nat"] = nat

    # ------------------------------------------------------------ institutions
    inst_names = sorted({c["institutionName"] for c in courses})
    inst_idx = {n: i for i, n in enumerate(inst_names)}
    inst_meta = {norm_inst(r["institution"]): r for r in qrows}

    # Optional and manually maintained: QS is proprietary, so nothing is fetched.
    # Missing or null ranks simply mean the app shows no QS figure.
    qs_file = ROOT / "data" / "qs_ranks.json"
    qs_ranks, qs_edition = {}, None
    if qs_file.exists():
        qs_doc = json.loads(qs_file.read_text(encoding="utf-8"))
        qs_ranks = {k: v for k, v in (qs_doc.get("ranks") or {}).items() if v}
        qs_edition = qs_doc.get("_edition")

    # Leiden research rankings, CC0. Keyed by our institution name after
    # normalising Leiden's abbreviations.
    leiden_file = RAW / "leiden_au.json"
    leiden, leiden_meta = {}, {}
    if leiden_file.exists():
        ld = json.loads(leiden_file.read_text(encoding="utf-8"))
        leiden_meta = {k: v for k, v in ld.items() if k.startswith("_")}
        by_norm = {norm_inst(n): n for n in inst_names}
        for field, block in ld["fields"].items():
            for r in block["rows"]:
                canonical = LEIDEN_ALIASES.get(r["u"], r["u"])
                target = by_norm.get(norm_inst(expand_leiden(canonical)))
                if not target:
                    continue
                leiden.setdefault(target, {})[field] = {
                    "au": r["auRank"], "world": r["globalRank"],
                    "worldSize": block["worldSize"], "pp": r["PPtop10"],
                }

    insts = []
    for n in inst_names:
        m = inst_meta.get(norm_inst(n)) or {}
        rec = {"n": n, "t": m.get("instType") or ""}
        if qs_ranks.get(n):
            rec["qs"] = qs_ranks[n]
        if leiden.get(n):
            rec["lr"] = leiden[n]
        insts.append(rec)

    unmatched = set()
    if leiden_file.exists():
        matched_norm = {norm_inst(k) for k in leiden}
        for r in json.loads(leiden_file.read_text(encoding="utf-8"))["fields"]["All sciences"]["rows"]:
            c = expand_leiden(LEIDEN_ALIASES.get(r["u"], r["u"]))
            if norm_inst(c) not in matched_norm:
                unmatched.add(r["u"])

    # ------------------------------------------------ outcomes lookup by cell
    qilt = {}
    for r in qrows:
        ii = inst_idx.get(next((n for n in inst_names if norm_inst(n) == norm_inst(r["institution"])), None))
        ai = area_idx.get(next((n for n in area_names if norm_area(n) == norm_area(r["studyArea"])), None))
        if ii is None or ai is None:
            continue
        cell = {}
        for alias, short in IND.items():
            v = r.get(alias)
            if v is not None and v > 0:
                cell[short] = round(v, 1)
        for k, short in (("salary1yr", "s1"), ("salary5yr", "s5"), ("salary9yr", "s9")):
            if r.get(k):
                cell[short] = r[k]
        cell["nSE"] = r.get("seResponses")
        cell["nGE"] = r.get("geResponses")
        qilt[f"{ii}-{ai}"] = cell

    # ----------------------------------------------------------------- courses
    # Freshness comes from the ATAR profile's collection year, NOT hasActiveOffering.
    # That flag is unreliable: every VTAC record carries 'F' with offering dates
    # frozen at 2021, even where the entry data was collected in 2025. Filtering on
    # it silently removes all of Victoria. The collection year is per record and is
    # surfaced in the UI so the user can judge each figure's age.
    MIN_YEAR = 2024
    universe = [
        c for c in courses
        if "Bachelor" in (c.get("levelOfQualificationDesc") or "")
        and ((c.get("atarProfile") or {}).get("collectionYear") or 0) >= MIN_YEAR
        and fnum((c.get("atarProfile") or {}).get("medianAtarUnadjusted")) is not None
    ]

    # Collapse only true duplicates: the same offering listed under several TAC
    # codes with an identical entry profile. Campuses of the same course can differ
    # sharply in selectivity (La Trobe physiotherapy is 85.6 at one campus and 94.8
    # at another), so the entry figures are part of the key and those stay as
    # separate rows rather than being merged down to the easiest campus.
    grouped = defaultdict(list)
    for c in universe:
        ap = c.get("atarProfile") or {}
        key = (c["institutionName"], re.sub(r"\s+", " ", c["name"]).strip().lower(),
               c.get("qiltStudyAreaName"),
               str(ap.get("medianAtarUnadjusted")), str(ap.get("lowestAtarUnadjusted")))
        grouped[key].append(c)

    out_courses = []
    for (iname, _, aname, _, _), rows in grouped.items():
        if aname not in area_idx:
            continue
        meds = [fnum((r.get("atarProfile") or {}).get("medianAtarUnadjusted")) for r in rows]
        meds = [m for m in meds if m]
        rep = min(rows, key=lambda r: fnum((r.get("atarProfile") or {}).get("medianAtarUnadjusted")) or 999)
        ap = rep.get("atarProfile") or {}
        sp = rep.get("studentProfile") or {}

        pw = {}
        for src, dst in PATH_KEYS:
            v = count(sp.get(src))
            if v is not None:
                pw[dst] = v
        pw_total = sum(pw.values()) if pw else 0

        states = sorted({s for r in rows for s in (r.get("states") or []) if s})
        campuses = sorted({cp["campusName"] for r in rows for cp in (r.get("campuses") or [])
                           if cp.get("campusName")})

        ii, ai = inst_idx[iname], area_idx[aname]
        out_courses.append({
            "n": rep["name"],
            "i": ii,
            "a": ai,
            "st": states,
            # 2dp, as ATARs are quoted. Rounding to 1dp turns a 99.95 median into
            # 100.0, which is above the maximum ATAR and reads as a plain error.
            "med": round(min(meds), 2),
            "medHi": round(max(meds), 2) if max(meds) != min(meds) else None,
            "low": fnum(ap.get("lowestAtarUnadjusted")),
            "lowAdj": fnum(ap.get("lowestAtarAdjusted")),
            # Median on the selection rank scale, so the card can show a lowest
            # and a median that belong to the same measure. Pairing a selection
            # rank floor with a raw ATAR median made the "lowest" read higher
            # than the "median" on 14% of records.
            "medAdj": fnum(ap.get("medianAtarAdjusted")),
            "yr": ap.get("collectionYear"),
            "pw": pw if pw_total >= 20 else None,
            "pwYr": sp.get("collectionYear") if pw_total >= 20 else None,
            "cmp": campuses[:6],
            "code": rep.get("courseCodeTac"),
            "tac": rep.get("admissionCentre"),
            "url": rep.get("tacLink"),
            "_crit": adm_criteria(rep),
            "q": f"{ii}-{ai}" if f"{ii}-{ai}" in qilt else None,
        })

    # ------------------------------- per-area medians, used for the "beats the
    # area" comparison the app makes. Computed on the shipped course set so the
    # figure the user sees is the figure the ranking used.
    # A tertiary admissions centre often lists one degree under several codes,
    # one per applicant category or selection route, each with its own entry
    # rank. Three La Trobe "Bachelor of Oral Health Science" listings at Bendigo
    # range from 60.65 to 80.15 for exactly this reason. Where that happens,
    # record what actually differs so the cards can say why, instead of looking
    # like the same course repeated with contradictory numbers.
    sibling = defaultdict(list)
    for c in out_courses:
        sibling[(c["i"], re.sub(r"\s+", " ", c["n"]).strip().lower(), c["a"])].append(c)

    for group in sibling.values():
        if len(group) > 1:
            shared = set.intersection(*(c["_crit"] for c in group)) if all(c["_crit"] for c in group) else set()
            for c in group:
                only = sorted(c["_crit"] - shared)
                if only:
                    c["dif"] = only[:3]
    for c in out_courses:
        c.pop("_crit", None)

    for ai, a in enumerate(areas):
        a["lf"] = AREA_TO_LEIDEN.get(a["en"], "All sciences")
        cs = [c for c in out_courses if c["a"] == ai]
        atars = [c["med"] for c in cs]
        emps = [qilt[c["q"]]["fte"] for c in cs if c["q"] and "fte" in qilt[c["q"]]]
        a["n"] = len(cs)
        a["medAtar"] = round(statistics.median(atars), 1) if atars else None
        a["medFte"] = round(statistics.median(emps), 1) if emps else None

    used_i = sorted({c["i"] for c in out_courses})
    data = {
        "meta": {
            "courses": len(out_courses),
            "institutions": len(used_i),
            "areas": len(areas),
            "qiltCells": len(qilt),
            "sources": {
                "entry": "Course Seeker (Australian Government and Tertiary Admission Centres)",
                "outcomes": "ComparED / QILT (Australian Government and the Social Research Centre)",
            },
            "qsEdition": qs_edition,
            "qsCount": sum(1 for i in insts if i.get("qs")),
            "leiden": leiden_meta,
            "leidenCount": sum(1 for i in insts if i.get("lr")),
        },
        "areas": areas,
        "insts": insts,
        "qilt": qilt,
        "courses": sorted(out_courses, key=lambda c: (c["a"], c["med"])),
    }

    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "data.json").write_text(json.dumps(data, separators=(",", ":"), ensure_ascii=False),
                                   encoding="utf-8")

    size = (OUT / "data.json").stat().st_size
    with_q = sum(1 for c in out_courses if c["q"])
    with_pw = sum(1 for c in out_courses if c["pw"])
    print(f"courses          {len(out_courses)}  (from {len(universe)} raw rows)")
    print(f"  with outcomes  {with_q} ({with_q / len(out_courses):.1%})")
    print(f"  with pathways  {with_pw} ({with_pw / len(out_courses):.1%})")
    print(f"institutions     {len(used_i)}")
    print(f"qilt cells       {len(qilt)}")
    print(f"leiden ranked    {sum(1 for i in insts if i.get('lr'))} institutions")
    if unmatched:
        print(f"  unmatched Leiden names: {sorted(unmatched)}")
    print(f"data.json        {size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
