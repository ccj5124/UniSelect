"""How much of undergraduate admission actually runs through the ATAR?

The first pass reported an unweighted median of the "ATAR only" bucket, which
understates the ATAR's role twice over. This pass fixes both problems:

  1. ATAR is used in TWO buckets, not one:
       numAdmittedAtar      admitted on the basis of ATAR alone
       numAdmittedAtarplus  ATAR considered alongside additional criteria
     Only numAdmittedSec (recent secondary, other criteria) excludes it.

  2. A median across course records weights a 15-student course the same as a
     2,000-student one, and 2,065 records carry aggregationFlag=true, meaning the
     same profile is repeated across several course rows. Both are corrected by
     deduplicating profiles and weighting by student counts.

Suppressed cells ('<5') are counted at 2.5; 'N/A' and 'N/P' are dropped.
"""

import json
import statistics
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
courses = json.loads((ROOT / "data" / "raw" / "courses.json").read_text(encoding="utf-8"))

BUCKETS = ["numAdmittedAtar", "numAdmittedAtarplus", "numAdmittedSec",
           "numAdmittedHe", "numAdmittedVet", "numAdmittedOther"]
LABELS = {
    "numAdmittedAtar": "Recent secondary, ATAR alone",
    "numAdmittedAtarplus": "Recent secondary, ATAR + other criteria",
    "numAdmittedSec": "Recent secondary, no ATAR used",
    "numAdmittedHe": "Prior higher education (transfers)",
    "numAdmittedVet": "VET / TAFE study",
    "numAdmittedOther": "Work and life experience (mature age)",
}


def rule(t):
    print(f"\n{'=' * 74}\n{t}\n{'=' * 74}")


def num(v):
    """Return a usable count, or None if the cell carries no number."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    v = v.strip()
    if v == "<5":
        return 2.5           # midpoint of the suppressed range
    try:
        return float(v)
    except ValueError:
        return None          # 'N/A', 'N/P'


BACH = [c for c in courses if "Bachelor" in (c.get("levelOfQualificationDesc") or "")]
ACTIVE = [c for c in BACH if c.get("hasActiveOffering") == "T"]

# ---------------------------------------------------------------- deduplicate
# An aggregated profile is repeated verbatim across course rows. Key on the
# institution plus the profile payload so each distinct profile counts once.
seen, profiles = set(), []
for c in ACTIVE:
    sp = c.get("studentProfile") or {}
    if not any(num(sp.get(b)) is not None for b in BUCKETS):
        continue
    key = (c["institution"], sp.get("collectionYear"), sp.get("intakePeriod"),
           tuple(str(sp.get(b)) for b in BUCKETS), str(sp.get("totalStudents")))
    if key in seen:
        continue
    seen.add(key)
    profiles.append((c, sp))

rule("SCOPE")
print(f"  active bachelor course records            {len(ACTIVE):6}")
print(f"  distinct admission profiles behind them   {len(profiles):6}")
print(f"  (aggregated/duplicate rows removed:       {len(ACTIVE) - len(profiles):6})")
yrs = Counter(sp.get("collectionYear") for _, sp in profiles)
print(f"  collection years: {dict(sorted(yrs.items(), key=lambda t: str(t[0])))}")

# ------------------------------------------------------------ student-weighted
rule("A. STUDENT-WEIGHTED: share of admitted students by pathway")
tot = Counter()
for _, sp in profiles:
    for b in BUCKETS:
        v = num(sp.get(b))
        if v is not None:
            tot[b] += v
grand = sum(tot.values())
print(f"  total admitted students across profiles: {grand:,.0f}\n")
for b in BUCKETS:
    print(f"  {LABELS[b]:42} {tot[b]:9,.0f}  {tot[b] / grand:6.1%}")

atar_used = tot["numAdmittedAtar"] + tot["numAdmittedAtarplus"]
recent_sec = atar_used + tot["numAdmittedSec"]
print(f"\n  ATAR played a part (alone or with other criteria)   {atar_used / grand:6.1%}")
print(f"  came from recent secondary school at all            {recent_sec / grand:6.1%}")
print(f"  of those recent school leavers, ATAR was used in    {atar_used / recent_sec:6.1%}")

# --------------------------------------------------------------- per-course
rule("B. PER-COURSE: how much each course leans on the ATAR")
shares = []
for _, sp in profiles:
    vals = {b: num(sp.get(b)) for b in BUCKETS}
    t = sum(v for v in vals.values() if v is not None)
    if t < 20:                       # tiny cohorts make percentages meaningless
        continue
    a = (vals["numAdmittedAtar"] or 0) + (vals["numAdmittedAtarplus"] or 0)
    shares.append(a / t)

shares.sort()
print(f"  profiles with a cohort of 20+ : {len(shares)}\n")
q = statistics.quantiles(shares, n=10)
print(f"  ATAR-based share of intake:  p10 {q[0]:5.1%}   median {statistics.median(shares):5.1%}   p90 {q[-1]:5.1%}")
for thresh in (0.25, 0.50, 0.75):
    n = sum(1 for s in shares if s < thresh)
    print(f"  courses where under {thresh:.0%} of the intake came via ATAR: {n:5} ({n / len(shares):5.1%})")

rule("C. THE SAME QUESTION, BY INSTITUTION")
by_inst = {}
for c, sp in profiles:
    vals = {b: num(sp.get(b)) for b in BUCKETS}
    t = sum(v for v in vals.values() if v is not None)
    if t < 20:
        continue
    a = (vals["numAdmittedAtar"] or 0) + (vals["numAdmittedAtarplus"] or 0)
    d = by_inst.setdefault(c["institutionName"], [0.0, 0.0])
    d[0] += a
    d[1] += t

ranked = sorted(((n, a / t, t) for n, (a, t) in by_inst.items() if t >= 500),
                key=lambda x: -x[1])
print(f"  institutions with 500+ admitted students in scope: {len(ranked)}\n")
print(f"  {'institution':44} {'ATAR-based':>11} {'students':>9}")
for n, s, t in ranked[:10]:
    print(f"  {n[:44]:44} {s:11.1%} {t:9,.0f}")
print("   ...")
for n, s, t in ranked[-10:]:
    print(f"  {n[:44]:44} {s:11.1%} {t:9,.0f}")
