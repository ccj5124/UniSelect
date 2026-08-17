"""Profile the Course Seeker snapshot: what is actually usable for a
"score in, undervalued courses out" product.

Answers, in order:
  1. what fields exist at all
  2. how many records are bachelor-level undergraduate
  3. how many of those carry a usable ATAR / selection rank profile
  4. which collection years the profiles come from
  5. whether courses can be joined to QILT study areas
  6. whether there is real spread to exploit (the "value gap" premise)
"""

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
courses = json.loads((ROOT / "data" / "raw" / "courses.json").read_text(encoding="utf-8"))
insts = json.loads((ROOT / "data" / "raw" / "institutions.json").read_text(encoding="utf-8"))

inst_type = {i["institution"]: i.get("hepType") for i in insts}


def rule(t):
    print(f"\n{'=' * 68}\n{t}\n{'=' * 68}")


rule("1. FIELD COVERAGE (top level)")
fields = Counter()
for c in courses:
    for k, v in c.items():
        fields[k] += 1 if v not in (None, "", [], {}) else 0
print(f"{len(courses)} course records, {len(insts)} institutions\n")
for k, n in fields.most_common():
    print(f"  {k:32} {n:6} ({n / len(courses):5.1%})")

rule("2. QUALIFICATION LEVELS")
for k, n in Counter(c.get("levelOfQualificationDesc") for c in courses).most_common(15):
    print(f"  {str(k)[:50]:52} {n:6}")

BACH = [c for c in courses if "Bachelor" in (c.get("levelOfQualificationDesc") or "")]
print(f"\n  -> Bachelor-level records: {len(BACH)}")

rule("3. ATAR / SELECTION RANK COVERAGE (Bachelor records only)")


def prof(c):
    return c.get("atarProfile") or {}


def has(c, key):
    return prof(c).get(key) is not None


metrics = [
    "medianAtarUnadjusted", "lowestAtarUnadjusted", "highestAtarUnadjusted",
    "medianAtarAdjusted", "lowestAtarAdjusted", "highestAtarAdjusted",
]
for m in metrics:
    n = sum(1 for c in BACH if has(c, m))
    print(f"  atarProfile.{m:26} {n:6} ({n / len(BACH):5.1%} of bachelors)")

for m in ["lowestRankUnadjusted", "lowestRankAdjusted"]:
    n = sum(1 for c in BACH if c.get(m) is not None)
    print(f"  {m:38} {n:6} ({n / len(BACH):5.1%} of bachelors)")

USABLE = [c for c in BACH if has(c, "medianAtarUnadjusted") or has(c, "lowestAtarUnadjusted")]
print(f"\n  -> Bachelor records with ANY usable ATAR figure: {len(USABLE)} ({len(USABLE) / len(BACH):.1%})")

print("\n  Reasons given when no profile is available:")
for k, n in Counter(prof(c).get("message") for c in BACH if not has(c, "medianAtarUnadjusted")).most_common(8):
    print(f"    {n:6}  {str(k)[:88]}")

rule("4. DATA VINTAGE (collectionYear on bachelor profiles)")
for k, n in sorted(Counter(prof(c).get("collectionYear") for c in BACH).items(), key=lambda x: str(x[0])):
    print(f"  {str(k):10} {n:6}")

rule("5. JOIN KEYS TO QILT STUDY AREAS")
print("  Fields that could carry a field-of-education code:")
cand = [k for k in fields if any(s in k.lower() for s in ("foe", "field", "categ", "area", "disc"))]
print(f"    {cand or 'NONE FOUND ON COURSE RECORDS'}")
print("\n  courseCategory values present:")
for k, n in Counter(c.get("courseCategory") for c in courses).most_common(10):
    print(f"    {str(k)[:60]:62} {n:6}")

rule("6. VALUE-GAP PREMISE: ATAR spread by institution (bachelors with data)")
by_inst = defaultdict(list)
for c in USABLE:
    v = prof(c).get("medianAtarUnadjusted") or prof(c).get("lowestAtarUnadjusted")
    try:
        by_inst[c["institutionName"]].append(float(v))
    except (TypeError, ValueError):
        pass

ranked = sorted(((n, statistics.median(v), len(v)) for n, v in by_inst.items() if len(v) >= 10),
                key=lambda x: -x[1])
print(f"  {len(ranked)} institutions with 10+ priced bachelor courses\n")
print(f"  {'institution':46} {'median':>7} {'n':>5}")
for n, m, c in ranked[:12]:
    print(f"  {n[:46]:46} {m:7.1f} {c:5}")
print("   ...")
for n, m, c in ranked[-8:]:
    print(f"  {n[:46]:46} {m:7.1f} {c:5}")

allv = [v for vs in by_inst.values() for v in vs]
if allv:
    q = statistics.quantiles(allv, n=10)
    print(f"\n  All priced bachelor courses: n={len(allv)}  min={min(allv):.1f}  "
          f"p10={q[0]:.1f}  median={statistics.median(allv):.1f}  p90={q[-1]:.1f}  max={max(allv):.1f}")

rule("7. TAC / STATE SPLIT (bachelors with usable ATAR)")
for k, n in Counter(c.get("admissionCentre") for c in USABLE).most_common():
    tot = sum(1 for c in BACH if c.get("admissionCentre") == k)
    print(f"  {str(k):8} {n:6} of {tot:6} bachelors  ({n / tot:5.1%} priced)")
