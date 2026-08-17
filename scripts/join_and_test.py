"""Join Course Seeker courses to QILT outcomes and test the core product premise:
are there courses with a low entry bar but genuinely good graduate outcomes?

Join keys:
  study area   Course Seeker qiltStudyAreaName  ->  ComparED study area title
  institution  Course Seeker institutionName    ->  ComparED institution title

Universe: bachelor courses that are actively offered and carry a clean median ATAR.
"""

import json
import re
import statistics
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"

courses = json.loads((RAW / "courses.json").read_text(encoding="utf-8"))
qilt = json.loads((RAW / "qilt_matrix.json").read_text(encoding="utf-8"))
QILT_UG = [r for r in qilt if r["studyLevel"] == "undergraduate"]


def rule(t):
    print(f"\n{'=' * 76}\n{t}\n{'=' * 76}")


def norm_area(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower().replace(" and ", " & "))


def norm_inst(s):
    s = (s or "").lower()
    s = re.sub(r"\b(the|of|australia|australian)\b", " ", s)
    s = s.replace("univ.", "university").replace("&", "and")
    return re.sub(r"[^a-z0-9]", "", s)


# ---------------------------------------------------------------- build lookup
qilt_by = {}
qilt_inst_names = set()
for r in QILT_UG:
    qilt_by[(norm_inst(r["institution"]), norm_area(r["studyArea"]))] = r
    qilt_inst_names.add(r["institution"])


def median_atar(c):
    v = (c.get("atarProfile") or {}).get("medianAtarUnadjusted")
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if 20 <= v <= 100 else None


UNIVERSE = [
    c for c in courses
    if "Bachelor" in (c.get("levelOfQualificationDesc") or "")
    and c.get("hasActiveOffering") == "T"
    and median_atar(c) is not None
]

rule("1. JOIN RATE")
print(f"  universe (active bachelor + clean median ATAR): {len(UNIVERSE)}")

joined, misses = [], defaultdict(int)
for c in UNIVERSE:
    k = (norm_inst(c["institutionName"]), norm_area(c.get("qiltStudyAreaName")))
    r = qilt_by.get(k)
    if r:
        joined.append((c, r))
    else:
        misses[c["institutionName"]] += 1

print(f"  joined to QILT outcomes: {len(joined)} ({len(joined) / len(UNIVERSE):.1%})")
print(f"\n  top unmatched institutions ({sum(misses.values())} course records):")
for name, n in sorted(misses.items(), key=lambda x: -x[1])[:12]:
    print(f"    {n:4}  {name}")

rule("2. OUTCOME DATA COMPLETENESS ON JOINED COURSES")
for field, label in [("full-time-employment", "full time employment %"),
                     ("employment", "overall employment %"),
                     ("educational-experience", "positive experience %"),
                     ("salary1yr", "median salary, 1 yr out"),
                     ("salary5yr", "median salary, 5 yr out")]:
    n = sum(1 for _, r in joined if r.get(field) is not None)
    print(f"  {label:28} {n:5} / {len(joined)} ({n / len(joined):5.1%})")

# ------------------------------------------------------- the actual premise test
rule("3. VALUE GAP: low entry bar, high graduate outcome")
FTE = "full-time-employment"
rows = [(c, r) for c, r in joined if r.get(FTE) is not None and median_atar(c) is not None]
print(f"  courses with both an ATAR and an employment figure: {len(rows)}")

by_area = defaultdict(list)
for c, r in rows:
    by_area[c["qiltStudyAreaName"]].append((median_atar(c), r[FTE], c, r))

print(f"\n  {'study area':42} {'n':>4} {'ATAR~emp corr':>14} {'gap courses':>12}")
gap_all = []
for area, vals in sorted(by_area.items()):
    if len(vals) < 15:
        continue
    atars = [v[0] for v in vals]
    emps = [v[1] for v in vals]
    try:
        corr = statistics.correlation(atars, emps)
    except statistics.StatisticsError:
        corr = float("nan")
    a_med = statistics.median(atars)
    e_med = statistics.median(emps)
    gap = [v for v in vals if v[0] <= a_med and v[1] >= e_med]
    gap_all.extend((area, *v) for v in gap)
    print(f"  {area[:42]:42} {len(vals):4} {corr:14.2f} {len(gap):12}")

print(f"\n  -> total 'value gap' courses (entry bar at or below the study area median,")
print(f"     employment at or above it): {len(gap_all)} of {len(rows)} ({len(gap_all) / len(rows):.1%})")

rule("4. THE STRONGEST EXAMPLES (biggest outcome premium per ATAR point below median)")
scored = []
for area, atar, emp, c, r in gap_all:
    vals = by_area[area]
    a_med = statistics.median([v[0] for v in vals])
    e_med = statistics.median([v[1] for v in vals])
    scored.append((((emp - e_med) + (a_med - atar)), area, atar, a_med, emp, e_med, c, r))

print(f"  {'course':46} {'inst':30} {'ATAR':>5} {'med':>5} {'emp%':>5} {'med':>5} {'sal1yr':>8}")
for s, area, atar, a_med, emp, e_med, c, r in sorted(scored, key=lambda x: -x[0])[:20]:
    sal = r.get("salary1yr")
    print(f"  {c['name'][:46]:46} {c['institutionName'][:30]:30} "
          f"{atar:5.1f} {a_med:5.1f} {emp:5.1f} {e_med:5.1f} "
          f"{('$' + format(sal, ',')) if sal else 'n/a':>8}")

rule("5. WORKED EXAMPLE: ATAR 75, what the tool would surface")
target = 75.0
picks = [(area, atar, emp, c, r) for area, atar, emp, c, r in gap_all if atar <= target]
print(f"  courses within reach at ATAR {target:g} that beat their study area on employment: {len(picks)}\n")
by_a = defaultdict(list)
for p in picks:
    by_a[p[0]].append(p)
for area in ["Nursing", "Engineering", "Computing and Information Systems", "Teacher Education"]:
    ps = sorted(by_a.get(area, []), key=lambda x: -x[2])[:5]
    if not ps:
        continue
    print(f"  {area}")
    for area_, atar, emp, c, r in ps:
        sal = r.get("salary1yr")
        sal5 = r.get("salary5yr")
        print(f"    ATAR {atar:5.1f}  emp {emp:5.1f}%  "
              f"1yr {('$' + format(sal, ',')) if sal else 'n/a':>8}  "
              f"5yr {('$' + format(sal5, ',')) if sal5 else 'n/a':>8}  "
              f"{c['institutionName'][:28]:28} {c['name'][:40]}")
    print()
