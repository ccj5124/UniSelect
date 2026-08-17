# UniSelect

Australian university entry ranks matched to published graduate outcomes and, more
importantly, to how students actually got admitted.

The premise: a family optimises around the ATAR, but the ATAR is the basis for only
about a third of undergraduate admissions, and entry rank barely predicts graduate
employment. Both of those are measurable from public government data.

## Running it

```bash
python -m http.server 8787 --directory app
```

The app is static: `app/index.html`, `app/styles.css`, `app/app.js`, `app/data.json`.
No build step, no dependencies, no backend. It deploys to any static host.

## Rebuilding the data

```bash
python scripts/fetch_courseseeker.py
python scripts/fetch_compared.py
python scripts/build_dataset.py
```

The first two write snapshots to `data/raw/`; the third compacts them into
`app/data.json`. Both fetchers are rate limited and partitioned so no single request
is large. Expect to rerun this once a year, after the QILT results and the new
admissions cycle are published.

## Sources

| Data | Source | Access |
|---|---|---|
| Courses, entry ranks, admission pathway profiles | Course Seeker (Australian Government + Tertiary Admission Centres) | unauthenticated Elasticsearch at `/search-engine/...` |
| Graduate outcomes, student experience, salary | ComparED / QILT (Australian Government + Social Research Centre) | public JSON at `api.compared.edu.au` |

Neither source is published under a Creative Commons licence. Both copyright pages
claim rights in site design and images and direct reuse requests to a contact
address. Australian law does not protect facts as such, and compilations assembled
without human authorial effort attract weak protection at best, so the individual
figures are most likely not themselves copyright. That is not the same as clearance.
**Written permission should be sought before this goes public**:
CourseSeeker@education.gov.au and qilt@srcentre.com.au.

## Research rankings

Shipped and populated, from the **CWTS Leiden Ranking Open Edition 2025**. Chosen
because it is the only credible international ranking that costs nothing to use:
results are on Zenodo under **CC0** (public domain, DOI 10.5281/zenodo.17473224) and
are computed from OpenAlex, itself CC0. QS, THE and ARWU are all proprietary.

`scripts/fetch_leiden.py` pulls 39 Australian universities across Leiden's six field
views, giving both a national rank (of 39) and a global rank (of 2,831). All 39 match
our institution list once Leiden's abbreviations are expanded.

Two honesty constraints are built into how it is displayed:

- It measures **research output and citation impact**, nothing else. It says nothing
  about teaching or graduate outcomes. The detail page states this in a caution box
  rather than in fine print, and the rank sits in its own column on the card so it
  cannot be read as another outcome statistic.
- Leiden has five broad fields against our 21 study areas, so `AREA_TO_LEIDEN` is a
  deliberate approximation, labelled as such in the UI. Science and Mathematics spans
  three Leiden fields and falls back to All sciences.

The mapping is worth knowing when reading results: James Cook physiotherapy sits at
#22 in Australia and #694 globally on research, with 99.0% full time employment. That
gap is the product's whole argument, visible on a single card.

## QS rankings

Wired up but deliberately unpopulated. `data/qs_ranks.json` holds one entry per
institution in the dataset; fill in the ranks and rerun `build_dataset.py`. Null
entries are simply omitted, and the whole feature (card tag, sort option, detail
card) hides itself when no ranks are present.

Two reasons it ships empty:

**Accuracy.** Secondary sites contradict each other and mix editions. Three sources
gave Melbourne as 19, 14 and 13, and UNSW as 20, 19 and 19, all labelled 2026. Get
the numbers from QS's own published table, and record which edition in `_edition`.

**Licensing.** This is the one data source here that is genuinely proprietary. Course
Seeker and QILT publish government facts, which attract little or no copyright
protection in Australia. A ranking is an editorially weighted compilation, which is
exactly the kind of work that does attract protection, and QS licenses it
commercially. Embedding and redistributing it is a materially higher risk than
anything else in this project. Either license it, or link out to QS instead of
storing the numbers.

The detail page deliberately presents QS against the outcome data rather than beside
it: where an institution ranks outside the global top 100 but beats the national
employment average in that field, it says so. That framing is the honest one given
what the correlation analysis shows, and it is also the more useful one for a parent.

## Analysis scripts

`profile_snapshot.py`, `profile_deep.py`, `join_and_test.py` and `atar_share.py` are
the validation passes that produced the findings below. They are kept so every number
in the UI can be traced back and rechecked.

## What the data supports, and what it does not

**Resolution.** QILT outcomes are published per institution per study area, not per
course. 2,589 courses sit on top of only 846 institution-by-field cells. Every course
at one institution in one field shares the same employment and salary figures. The UI
says so on each detail page. This rules out course-level admission probability
modelling of the kind Chinese gaokao tools offer; the data does not exist here.

**Freshness.** Use `atarProfile.collectionYear`, never `hasActiveOffering`. That flag
is `F` on all 2,355 VTAC records with offering dates frozen at 2021, even where the
entry data was collected in 2025; filtering on it silently deletes Victoria. The
build keeps records collected from 2024 onward, which excludes Tasmania entirely
(the newest UTAS data is 2022). The UI discloses this.

**Entry field semantics, the easiest thing here to get wrong.** `lowestAtarAdjusted`
is not "the bar after bonus points brought it down". It is the lowest *selection
rank*, meaning ATAR plus adjustment factors, which is what offers are ranked on. It
runs **above** `lowestAtarUnadjusted` in 91% of records, by a median of 6.7 points and
up to 38. Compare a student's raw ATAR against `lowestAtarUnadjusted`; that is also
the number every public course listing headlines. In the 2% of records where the
adjusted figure sits lower, adjustments genuinely pulled the bar down, and the UI
flags those separately. An earlier build used the adjusted field as the reach
threshold and silently hid reachable courses.

**Campuses are not duplicates.** Deduplication keys on the entry profile as well as
the name, because the same degree at the same institution can differ sharply by
campus: La Trobe physiotherapy has a lowest offer of 94.75 at Melbourne and 80.5 at
Bendigo. Merging them down to the easiest campus understated the Melbourne bar and
hid the Bendigo pathway, which is the more useful of the two.

**Composition effects.** Ranking by outcome premium systematically surfaces regional
and online focused universities: Flinders, Charles Sturt, UNE, Charles Darwin, USQ,
CQU, James Cook. Their students are older and more often already working, which
inflates employment rates independently of teaching quality. The detail page pairs
every outcome with the admission pathway breakdown, and carries an explicit caution,
rather than presenting the ranking as a quality judgement.

**Correlation between entry rank and employment**, computed on the shipped dataset:
negative in 8 of 18 study areas with enough courses to measure (psychology -0.18,
social work -0.27, architecture -0.16, nursing -0.10, agriculture -0.22). The
strongest positive relationship is law at 0.41, which still explains under a fifth of
the variation. Note this weakened once Victoria was included: an earlier pass that
had accidentally excluded VTAC put teacher education at -0.25, and it is +0.03 with
the full data. Do not quote the earlier figures.

**Admission pathways.** Student weighted across 1,745 distinct published admission
profiles: 31.5% of admitted students entered on an ATAR alone, 3.9% on an ATAR plus
other criteria, 27.5% from recent school without an ATAR, 20.9% transferred from other
higher education, 7.7% via VET, 8.5% on work and life experience. So the ATAR played
a part for about 35%. This converges with the published national picture reached a
different way (roughly half of commencers are not recent school leavers, and about
70% of those who are have an ATAR considered). Quote it as "about a third". The
component breakdown is less reliable than the total, because Course Seeker only
carries courses with published admission profiles and misses enabling and bridging
pathways.

Institution level variation is the sharpest finding: UNSW admits 82.8% via ATAR
related pathways, Macquarie 11.0%, UNE 6.1%. Early offer schemes based on Year 11
results are classified as "recent school, no ATAR used", which is what drives the
low numbers at Macquarie, Newcastle and Wollongong.

## Known gaps

- No Tasmania, for the freshness reason above.
- No fee or HECS data. Course Seeker's `fees` field is `{"type":"CSP","amount":0}` on
  7,189 of 8,132 bachelor records, so ROI cannot be computed yet. The Job-ready
  Graduates contribution bands would have to come from the Department of Education,
  at field level rather than course level.
- No adjustment factor detail. Each institution publishes its own bonus point scheme
  and there is no central source. The dataset carries `lowestAtarAdjusted`, which
  reflects adjustments in aggregate but does not tell a user which ones they qualify
  for. This is the largest remaining manual data task and probably the strongest moat.
- 231 of 2,589 courses have no QILT cell (for example ECU Medicine, ANU Tourism,
  where sample sizes are too small to publish). They are kept and flagged rather than
  hidden, but they sort last and are excluded by the default filter.
