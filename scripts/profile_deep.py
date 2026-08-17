"""Second pass: inspect the fields the first profile turned up, and test the
core product premise (same study area, very different entry bar).
"""

import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
courses = json.loads((ROOT / "data" / "raw" / "courses.json").read_text(encoding="utf-8"))


def rule(t):
    print(f"\n{'=' * 74}\n{t}\n{'=' * 74}")


BACH = [c for c in courses if "Bachelor" in (c.get("levelOfQualificationDesc") or "")]


def median_atar(c):
    v = (c.get("atarProfile") or {}).get("medianAtarUnadjusted")
    try:
        v = float(v)
    except (TypeError, ValueError):
        return None
    return v if 20 <= v <= 100 else None  # drop obvious junk (0.0 etc)


rule("A. SAMPLE RECORD (a real bachelor course, all fields)")
sample = next(c for c in BACH if median_atar(c) and c.get("fees") and c.get("studentProfile"))
print(json.dumps(sample, indent=1)[:3000])

rule("B. QILT STUDY AREA COVERAGE")
codes = Counter((c.get("qiltCode"), c.get("qiltStudyAreaName")) for c in BACH)
print(f"  distinct QILT study areas on bachelor records: {len(codes)}\n")
for (code, name), n in sorted(codes.items(), key=lambda x: str(x[0][0])):
    print(f"  {str(code):6} {str(name)[:52]:54} {n:5}")

rule("C. FEES FIELD STRUCTURE")
fee_samples = [c["fees"] for c in BACH if c.get("fees")][:3]
for f in fee_samples:
    print(" ", json.dumps(f)[:300])
print(f"\n  bachelors with fees: {sum(1 for c in BACH if c.get('fees'))} / {len(BACH)}")

rule("D. STUDENT PROFILE STRUCTURE (admission pathway mix)")
sp = [c["studentProfile"] for c in BACH if c.get("studentProfile")]
print(" ", json.dumps(sp[0], indent=1)[:1200] if sp else "none")
print(f"\n  bachelors with a student profile: {len(sp)} / {len(BACH)}")

rule("E. CORE PREMISE: entry-bar spread WITHIN a study area")
by_area = defaultdict(list)
for c in BACH:
    m = median_atar(c)
    if m and c.get("qiltStudyAreaName"):
        by_area[c["qiltStudyAreaName"]].append((m, c["institutionName"], c["name"], c.get("states")))

print(f"  {'study area':40} {'n':>4} {'p10':>6} {'med':>6} {'p90':>6} {'spread':>7}")
rows = []
for area, vals in by_area.items():
    if len(vals) < 20:
        continue
    xs = sorted(v[0] for v in vals)
    q = statistics.quantiles(xs, n=10)
    rows.append((area, len(xs), q[0], statistics.median(xs), q[-1], q[-1] - q[0]))
for r in sorted(rows, key=lambda x: -x[5]):
    print(f"  {r[0][:40]:40} {r[1]:4} {r[2]:6.1f} {r[3]:6.1f} {r[4]:6.1f} {r[5]:7.1f}")

rule("F. WORKED EXAMPLE: what a student with ATAR 75 sees in Nursing")
target = 75.0
for area in ["Nursing", "Engineering", "Computing and information systems", "Teacher education"]:
    vals = by_area.get(area)
    if not vals:
        continue
    reach = sorted([v for v in vals if v[0] <= target + 2], key=lambda x: -x[0])
    print(f"\n  {area}: {len(vals)} courses priced, {len(reach)} within reach at ATAR {target:g}")
    for m, inst, name, st in reach[:8]:
        print(f"    {m:5.1f}  {inst[:34]:34} {name[:44]:44} {st}")
