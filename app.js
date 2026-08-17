/* UniSelect - entry ranks matched to published outcomes and real admission pathways.
   No dependencies, no build step. Data ships as one JSON file. */

'use strict';

/* ------------------------------------------------------------------ i18n */

const STR = {
  zh: {
    heroTitle: '你的分数，能去的比你以为的多',
    heroSub: '用官方录取数据和毕业生就业结果，找出门槛在你射程内、但结果高于同领域平均的课程。顺便告诉你，这些学校到底有多少人是靠 ATAR 进去的。',
    fATAR: '你的 ATAR / Selection Rank',
    fATARHint: '还没出分？填一个预估值即可。加分（adjustment factors）会在结果里单独标注。',
    fKeyword: '课程或学校关键词',
    fKeywordHint: '按名字搜比按领域找更准。政府的学科分类不直观，比如物理治疗被归在「康复治疗」下面，还有一部分散在「医学」和「理科」里。',
    fArea: '学科领域',
    fState: '州 / 地区',
    fOnlyGood: '只看就业结果高于该领域中位的课程',
    fSubmit: '查看结果',
    anyArea: '全部领域',
    anyState: '全澳',
    whyTitle: '为什么值得看一眼',
    whyBody: '入学门槛几乎预测不了毕业生就业结果。在心理学、社会工作、建筑、护理这几个领域，两者甚至是负相关：门槛更高的课程，就业结果反而略差。18 个学科领域里有 8 个如此，而关系最强的法律，门槛也只能解释不到五分之一的就业差异。这不是观点，是用政府数据算出来的。',
    statCourses: '门在售课程',
    statInsts: '所院校',
    statCells: '个院校×学科单元',
    resFound: n => `${n} 门课程在你的射程内`,
    resSubBoth: (a, e) => `该领域中位入学门槛 ${a}，中位全职就业率 ${e}%`,
    excluded: (rank, out) => {
      const p = [];
      if (rank) p.push(`${rank} 门门槛高于你的分数`);
      if (out) p.push(`${out} 门就业结果低于领域中位（被筛选条件排除）`);
      return p.length ? '另有 ' + p.join('，') + '。' : '';
    },
    sortValue: '结果溢价',
    sortEmp: '就业率',
    sortSal1: '起薪',
    sortSal5: '五年薪资',
    sortAtar: '门槛由低到高',
    sortQs: 'QS 排名',
    qsTitle: 'QS 世界排名',
    qsRank: r => `全球第 ${r} 位`,
    qsEdition: e => `版本：${e}`,
    qsContrast: (r, e, n) => `该校 QS 排名第 ${r} 位，但这个专业的全职就业率是 ${e}%，高于全国均值 ${n}%。排名衡量的是研究声誉和师生比，不是毕业生去向。`,
    qsNote: 'QS 排名为第三方商业榜单，与本工具其余数据（政府发布）性质不同，权重设计包含大量主观成分。',
    rkAu: '澳洲',
    rkWorld: '全球',
    rkTitle: '研究排名',
    rkOf: n => `／${n} 所`,
    rkField: f => `学科口径：${f}`,
    rkSource: 'CWTS Leiden Ranking Open Edition 2025，基于 OpenAlex 开放数据，统计 2020 至 2023 年发表量。CC0 公共领域授权。',
    rkCaveat: '这是研究产出排名，衡量的是论文数量和被引影响力，不衡量教学质量，也不衡量毕业生去向。本科生的实际体验与就业结果请看上面的 QILT 数据。Leiden 只划分 5 个大学科，与这里的 21 个学科领域是近似对应。',
    fieldsZh: {
      'All sciences': '全学科',
      'Social sciences and humanities': '社科与人文',
      'Biomedical and health sciences': '生物医学与健康',
      'Physical sciences and engineering': '理工与工程',
      'Life and earth sciences': '生命与地球科学',
      'Mathematics and computer science': '数学与计算机',
    },
    noResults: '没有符合条件的课程。试试放宽筛选，或取消勾选「只看就业结果高于中位」。',
    capCourse: '课程',
    capArea: '学科领域',
    capInst: '学校',
    mLowest: '最低录取分',
    mAtar: '中位录取分',
    mEmp: '全职就业',
    mSal: '起薪中位',
    tagReach: '够得着',
    tagStretch: '需冲刺',
    tagAdj: a => `加分后 ${a} 可入`,
    tagAtarShare: p => `仅 ${p}% 靠 ATAR 录取`,
    tagNoOutcome: '官方未发布结果数据',
    dPathTitle: '这门课的学生实际是怎么进来的',
    dPathLead: n => `基于该校该课程 ${n} 名录取学生的官方入学途径分解。`,
    pAtar: '纯 ATAR 录取',
    pAtarPlus: 'ATAR + 其他条件',
    pSecOther: '应届中学，未用 ATAR（含 early offer）',
    pTransfer: '从其他高校转入',
    pVet: 'TAFE / VET 途径',
    pMature: '工作与生活经验',
    dPathPunch: p => `只有 <b>${p}%</b> 的人是靠 ATAR 进来的。`,
    dPathNone: '该课程未公布入学途径分解。',
    dOutTitle: '毕业生结果',
    dOutLead: '来自政府 QILT 调查，口径是该校该学科领域的本科毕业生整体，不是单门课程。',
    oFte: '全职就业率',
    oEmp: '总就业率',
    oExp: '整体就读体验',
    oTeach: '教学质量评价',
    oSup: '学生支持',
    oSat: '毕业生总体满意度',
    dSalTitle: '薪资轨迹',
    dSalLead: '中位收入，来自税务数据关联，口径同为该校该学科领域。',
    s1: '毕业 1 年',
    s5: '毕业 5 年',
    s9: '毕业 9 年',
    natAvg: v => `全国 ${v}`,
    dEntryTitle: '入学门槛',
    eMed: '中位录取分（不含加分）',
    eLow: '最低录取分（不含加分）',
    eLowAdj: '最低 selection rank（含加分）',
    eLowAdjNote: 'selection rank 是 ATAR 加上各类加分后的分数，用于实际排序。它通常高于最低 ATAR：一个 ATAR 较低但拿到加分的学生，最终排序分可能更高。判断自己是否够得着，看上面那行「最低录取分」。',
    eYear: '数据采集年份',
    eCampus: '校区',
    dOfficial: '查看官方课程页面',
    dCautionTitle: '看这些数字时请注意',
    dCaution: '就业结果是「该校该学科领域」的整体数字，不是这一门课的。区域性和在线为主的大学在这些指标上普遍偏高，部分原因是学生结构不同（年龄偏大、在职就读），不完全等于教学质量。请结合左边的入学途径分解一起看。',
    footSources: '入学数据来源：Course Seeker（澳洲政府与各州招生中心）。结果数据来源：ComparED / QILT（澳洲政府与 Social Research Centre）。',
    footDisclaimer: '本工具为独立制作，与上述任何机构无关联、未获其背书。所有数字均为参考性质，采集年份各校不一，每门课程页面均标注。仅收录 2024 年及以后采集的入学数据，因此塔斯马尼亚（UTAS 最新数据为 2022 年）暂未覆盖。做决定前请以院校和招生中心的官方信息为准。',
    loading: '加载中…',
  },
  en: {
    heroTitle: 'Your rank opens more doors than you think',
    heroSub: 'Official entry data matched to published graduate outcomes, to surface courses within your reach that beat their field on results. Plus how many students actually got in on an ATAR.',
    fATAR: 'Your ATAR / selection rank',
    fATARHint: 'No result yet? An estimate works. Adjustment factors are flagged separately in the results.',
    fKeyword: 'Course or institution keyword',
    fKeywordHint: 'Searching by name beats browsing by field. The government taxonomy is not intuitive: physiotherapy sits under "Rehabilitation", with more of it filed under Medicine and Science.',
    fArea: 'Study area',
    fState: 'State or territory',
    fOnlyGood: 'Only show courses beating the field median on employment',
    fSubmit: 'See results',
    anyArea: 'All study areas',
    anyState: 'Anywhere in Australia',
    whyTitle: 'Why this is worth a look',
    whyBody: 'Entry rank barely predicts graduate employment. In psychology, social work, architecture and nursing the relationship is actually negative: the courses with the higher bar produce slightly weaker employment outcomes. That holds in 8 of 18 study areas, and even in law, where the link is strongest, entry rank explains under a fifth of the variation. That is not an opinion, it falls out of the official data.',
    statCourses: 'courses on offer',
    statInsts: 'institutions',
    statCells: 'institution x field cells',
    resFound: n => `${n} courses within your reach`,
    resSubBoth: (a, e) => `Field median entry rank ${a}, median full time employment ${e}%`,
    excluded: (rank, out) => {
      const p = [];
      if (rank) p.push(`${rank} sit above your rank`);
      if (out) p.push(`${out} fall below the field median on employment and are filtered out`);
      return p.length ? 'Also matched: ' + p.join(', ') + '.' : '';
    },
    sortValue: 'Outcome premium',
    sortEmp: 'Employment',
    sortSal1: 'Starting salary',
    sortSal5: 'Salary at 5 years',
    sortAtar: 'Lowest bar first',
    sortQs: 'QS rank',
    qsTitle: 'QS World University Ranking',
    qsRank: r => `#${r} globally`,
    qsEdition: e => `Edition: ${e}`,
    qsContrast: (r, e, n) => `This institution ranks #${r} globally, yet full time employment in this field is ${e}%, above the national ${n}%. The ranking measures research reputation and staff ratios, not where graduates end up.`,
    qsNote: 'QS is a third party commercial ranking, unlike every other figure here, which comes from government sources. Its weightings are substantially subjective.',
    rkAu: 'in Australia',
    rkWorld: 'world',
    rkTitle: 'Research ranking',
    rkOf: n => `of ${n}`,
    rkField: f => `Field basis: ${f}`,
    rkSource: 'CWTS Leiden Ranking Open Edition 2025, computed from OpenAlex on publications from 2020 to 2023. Released under CC0.',
    rkCaveat: 'This ranks research output: how much a university publishes and how often it is cited. It does not measure teaching, and it does not measure where graduates end up. For that, read the QILT figures above. Leiden splits research into five broad fields, so the match to these 21 study areas is approximate.',
    fieldsZh: {},
    noResults: 'Nothing matched. Try widening the filters, or unticking the employment filter.',
    capCourse: 'Course',
    capArea: 'Study area',
    capInst: 'Institution',
    mLowest: 'Lowest offer',
    mAtar: 'Median entry',
    mEmp: 'Full time employment',
    mSal: 'Median starting salary',
    tagReach: 'Within reach',
    tagStretch: 'A stretch',
    tagAdj: a => `${a} with adjustments`,
    tagAtarShare: p => `only ${p}% admitted on ATAR`,
    tagNoOutcome: 'Outcomes not published',
    dPathTitle: 'How students actually got in',
    dPathLead: n => `Official admission pathway breakdown for ${n} admitted students.`,
    pAtar: 'ATAR alone',
    pAtarPlus: 'ATAR plus other criteria',
    pSecOther: 'Recent school, no ATAR used (incl. early offers)',
    pTransfer: 'Transfer from other higher education',
    pVet: 'TAFE / VET pathway',
    pMature: 'Work and life experience',
    dPathPunch: p => `Only <b>${p}%</b> got in on an ATAR.`,
    dPathNone: 'No admission pathway breakdown published for this course.',
    dOutTitle: 'Graduate outcomes',
    dOutLead: 'From the government QILT surveys. Measured across the institution’s undergraduates in this field, not this single course.',
    oFte: 'Full time employment',
    oEmp: 'Overall employment',
    oExp: 'Positive overall experience',
    oTeach: 'Teaching quality',
    oSup: 'Student support',
    oSat: 'Graduate satisfaction',
    dSalTitle: 'Salary trajectory',
    dSalLead: 'Median earnings from linked tax data, same institution and field basis.',
    s1: '1 year out',
    s5: '5 years out',
    s9: '9 years out',
    natAvg: v => `national ${v}`,
    dEntryTitle: 'Entry requirements',
    eMed: 'Median ATAR (before adjustments)',
    eLow: 'Lowest ATAR to receive an offer',
    eLowAdj: 'Lowest selection rank (with adjustments)',
    eLowAdjNote: 'A selection rank is an ATAR plus any adjustment factors, and it is what offers are actually ranked on. It usually sits above the lowest ATAR: a student with a lower ATAR who earned adjustments can end up ranked higher. To judge whether a course is within reach, use the lowest ATAR above.',
    eYear: 'Data collected',
    eCampus: 'Campuses',
    dOfficial: 'View the official course page',
    dCautionTitle: 'Read these numbers carefully',
    dCaution: 'Outcomes describe the institution’s graduates in this whole field, not this one course. Regional and online focused universities tend to score higher on these measures partly because their student mix differs (older, already working), which is not the same as better teaching. Read them alongside the pathway breakdown.',
    footSources: 'Entry data: Course Seeker (Australian Government and the Tertiary Admission Centres). Outcomes: ComparED / QILT (Australian Government and the Social Research Centre).',
    footDisclaimer: 'Independently built, not affiliated with or endorsed by any of the above. All figures are indicative and collection years vary by institution, and are shown on every course page. Only entry data collected from 2024 onwards is included, so Tasmania is not yet covered (the most recent UTAS data is from 2022). Check the official institution and admissions centre sources before deciding anything.',
    loading: 'Loading…',
  },
};

const PATHS = [
  ['atar', 'pAtar', '#1d5fd0'],
  ['atarPlus', 'pAtarPlus', '#5b8ae8'],
  ['secOther', 'pSecOther', '#e0a355'],
  ['transfer', 'pTransfer', '#0f7a52'],
  ['vet', 'pVet', '#4ecfa0'],
  ['mature', 'pMature', '#9aa5b4'],
];

/* ----------------------------------------------------------------- state */

let DATA = null;
let lang = localStorage.getItem('lang')
  || ((navigator.language || '').toLowerCase().startsWith('zh') ? 'zh' : 'en');
if (!['zh', 'en'].includes(lang)) lang = 'zh';
let query = null;
let sortKey = 'value';

const $ = s => document.querySelector(s);
const t = (k, ...a) => {
  const v = STR[lang][k];
  return typeof v === 'function' ? v(...a) : (v ?? k);
};
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const money = n => n ? '$' + Math.round(n / 100) / 10 + 'k' : '—';
const pct = n => n == null ? '—' : n.toFixed(1) + '%';

/* --------------------------------------------------------------- helpers */

// Compare a raw ATAR against the lowest ATAR that received an offer, which is
// what every public source headlines. Do NOT use lowAdj here: despite the name,
// `lowestAtarAdjusted` is the lowest SELECTION RANK (ATAR plus adjustment
// factors), and it runs higher than the raw floor in 91% of records, by a median
// of 6.7 points and up to 38. Using it as the threshold hides courses the student
// can actually reach.
const entryFloor = c => c.low ?? c.lowAdj ?? c.med;

// The 2% of records where the adjusted figure sits below the raw floor are the
// ones where adjustment factors demonstrably pulled the bar down.
const adjHelps = c => c.lowAdj != null && c.low != null && c.lowAdj < c.low;

const outcomes = c => (c.q && DATA.qilt[c.q]) || null;

function atarShare(c) {
  if (!c.pw) return null;
  const total = Object.values(c.pw).reduce((a, b) => a + b, 0);
  if (total < 20) return null;
  return ((c.pw.atar || 0) + (c.pw.atarPlus || 0)) / total * 100;
}

function premium(c) {
  const o = outcomes(c), area = DATA.areas[c.a];
  if (!o || o.fte == null || area.medFte == null) return null;
  return o.fte - area.medFte;
}

/* ---------------------------------------------------------------- render */

function applyStatic() {
  document.documentElement.lang = lang;
  $('#lang').textContent = lang === 'zh' ? 'EN' : '中文';
  document.querySelectorAll('[data-i]').forEach(el => { el.textContent = t(el.dataset.i); });
}

function fillSelects() {
  const area = $('#area'), state = $('#state');
  const areaVal = area.value, stateVal = state.value;
  area.innerHTML = `<option value="">${esc(t('anyArea'))}</option>` +
    DATA.areas.map((a, i) => `<option value="${i}">${esc(lang === 'zh' ? a.zh : a.en)}</option>`).join('');
  const states = [...new Set(DATA.courses.flatMap(c => c.st))].sort();
  state.innerHTML = `<option value="">${esc(t('anyState'))}</option>` +
    states.map(s => `<option value="${esc(s)}">${esc(s)}</option>`).join('');
  area.value = areaVal; state.value = stateVal;
}

function homeStats() {
  const m = DATA.meta;
  $('#homeStats').innerHTML = [
    [m.courses, 'statCourses'], [m.institutions, 'statInsts'], [m.qiltCells, 'statCells'],
  ].map(([v, k]) => `<div class="stat"><b>${v}</b><span>${esc(t(k))}</span></div>`).join('');
}

function search() {
  const { atar, area, state, keyword, onlyGood } = query;
  const kw = keyword.trim().toLowerCase();

  // Match on the user's terms first, then count what each filter removes, so the
  // results page can explain an empty or short list instead of going silent.
  const matched = DATA.courses.filter(c => {
    if (area !== '' && c.a !== +area) return false;
    if (state && !c.st.includes(state)) return false;
    if (kw && !(c.n.toLowerCase().includes(kw) || DATA.insts[c.i].n.toLowerCase().includes(kw))) return false;
    return true;
  });

  const inReach = matched.filter(c => entryFloor(c) <= atar);
  let rows = inReach;
  let cutByOutcome = 0;
  if (onlyGood) {
    rows = inReach.filter(c => { const p = premium(c); return p != null && p >= 0; });
    cutByOutcome = inReach.length - rows.length;
  }
  search.stats = { aboveRank: matched.length - inReach.length, cutByOutcome };

  const sorters = {
    value: (a, b) => (premium(b) ?? -99) - (premium(a) ?? -99),
    emp: (a, b) => ((outcomes(b)?.fte) ?? -1) - ((outcomes(a)?.fte) ?? -1),
    sal1: (a, b) => ((outcomes(b)?.s1) ?? -1) - ((outcomes(a)?.s1) ?? -1),
    sal5: (a, b) => ((outcomes(b)?.s5) ?? -1) - ((outcomes(a)?.s5) ?? -1),
    atar: (a, b) => a.med - b.med,
    qs: (a, b) => (DATA.insts[a.i].qs ?? 1e6) - (DATA.insts[b.i].qs ?? 1e6),
  };
  rows.sort(sorters[sortKey]);
  return rows;
}

function renderResults() {
  const rows = search();
  const area = query.area !== '' ? DATA.areas[+query.area] : null;

  const s = search.stats || { aboveRank: 0, cutByOutcome: 0 };
  $('#resTitle').textContent = t('resFound', rows.length);
  $('#resSub').textContent = [
    area && area.medAtar != null && area.medFte != null ? t('resSubBoth', area.medAtar, area.medFte) : '',
    t('excluded', s.aboveRank, s.cutByOutcome),
  ].filter(Boolean).join(' ');

  $('#sortbar').innerHTML = [
    ['value', 'sortValue'], ['emp', 'sortEmp'], ['sal1', 'sortSal1'],
    ['sal5', 'sortSal5'], ['atar', 'sortAtar'],
    ...(DATA.meta.qsCount ? [['qs', 'sortQs']] : []),
  ].map(([k, s]) =>
    `<button data-sort="${k}" aria-pressed="${k === sortKey}">${esc(t(s))}</button>`).join('');

  $('#resEmpty').hidden = rows.length > 0;
  $('#resList').innerHTML = rows.slice(0, 200).map(card).join('');
}

function card(c) {
  const o = outcomes(c), inst = DATA.insts[c.i], share = atarShare(c);
  const idx = DATA.courses.indexOf(c);

  const tags = [
    `<span class="tag good">${esc(t('tagReach'))}</span>`,
    inst.qs ? `<span class="tag">QS ${inst.qs}</span>` : '',
    adjHelps(c) ? `<span class="tag">${esc(t('tagAdj', c.lowAdj))}</span>` : '',
    share != null && share < 40 ? `<span class="tag warn">${esc(t('tagAtarShare', Math.round(share)))}</span>` : '',
    !o ? `<span class="tag">${esc(t('tagNoOutcome'))}</span>` : '',
    ...c.st.map(s => `<span class="tag">${esc(s)}</span>`),
  ].join('');

  const area = DATA.areas[c.a];
  const campus = (c.cmp && c.cmp.length)
    ? c.cmp.slice(0, 2).join(' / ') + (c.cmp.length > 2 ? ` +${c.cmp.length - 2}` : '')
    : '';

  const lr = inst.lr && inst.lr[area.lf];
  const fieldLabel = lang === 'zh' ? (STR.zh.fieldsZh[area.lf] || area.lf) : area.lf;

  // The three sections are the three levels the data actually exists at: entry
  // ranks are per course, outcomes are per institution x study area, and the
  // research rank is per institution. Splitting them visually stops a reader
  // taking the employment rate as a fact about this one course.
  return `<button class="item" data-idx="${idx}">
    <div class="secs">

      <div class="sec sec-course">
        <div class="cap">${esc(t('capCourse'))}</div>
        <div class="inst">${esc(inst.n)}${campus ? ' · ' + esc(campus) : ''}</div>
        <div class="name">${esc(c.n)}</div>
        <div class="metrics">
          <div class="metric"><b>${entryFloor(c)}</b><span>${esc(t('mLowest'))}</span></div>
          <div class="metric"><b>${c.med}</b><span>${esc(t('mAtar'))}</span></div>
        </div>
        <div class="tags">${tags}</div>
      </div>

      <div class="sec sec-area">
        <div class="cap">${esc(t('capArea'))}</div>
        ${o && o.fte != null
          ? `<div class="metric"><b>${pct(o.fte)}</b><span>${esc(t('mEmp'))}</span></div>` : ''}
        ${o && o.s1
          ? `<div class="metric"><b>${money(o.s1)}</b><span>${esc(t('mSal'))}</span></div>` : ''}
        <div class="rkf">${esc(lang === 'zh' ? area.zh : area.en)}</div>
      </div>

      <div class="sec sec-inst">
        <div class="cap">${esc(t('capInst'))}</div>
        ${lr ? `<div class="rk"><b>#${lr.au}</b><span>${esc(t('rkAu'))}</span></div>
                <div class="rk"><b>#${lr.world}</b><span>${esc(t('rkWorld'))}</span></div>` : ''}
        ${inst.qs ? `<div class="rk"><b>#${inst.qs}</b><span>QS</span></div>` : ''}
        ${lr ? `<div class="rkf">${esc(fieldLabel)}</div>` : ''}
      </div>

    </div>
  </button>`;
}

function renderDetail(c) {
  const o = outcomes(c), inst = DATA.insts[c.i], area = DATA.areas[c.a];
  const areaName = lang === 'zh' ? area.zh : area.en;
  const share = atarShare(c);
  let h = '';

  h += `<div class="dh">
    <div class="inst">${esc(inst.n)} · ${esc(areaName)}</div>
    <h1>${esc(c.n)}</h1>
  </div>`;

  /* ---- pathways: the part nobody else shows */
  h += `<div class="card"><h2>${esc(t('dPathTitle'))}</h2>`;
  if (c.pw) {
    const total = Object.values(c.pw).reduce((a, b) => a + b, 0);
    h += `<p class="sub">${esc(t('dPathLead', Math.round(total)))}</p>`;
    if (share != null) h += `<div class="callout">${t('dPathPunch', Math.round(share))}</div>`;
    h += `<div class="bar">` + PATHS.map(([k, , col]) => {
      const v = c.pw[k] || 0;
      return v ? `<div style="width:${v / total * 100}%;background:${col}"></div>` : '';
    }).join('') + `</div>`;
    h += `<div class="legend">` + PATHS.filter(([k]) => c.pw[k]).map(([k, lbl, col]) =>
      `<div class="row"><span class="sw" style="background:${col}"></span>
       <span class="lbl">${esc(t(lbl))}</span>
       <span class="pct">${(c.pw[k] / total * 100).toFixed(1)}%</span></div>`).join('') + `</div>`;
    if (c.pwYr) h += `<p class="fine" style="margin-top:10px">${esc(t('eYear'))}: ${c.pwYr}</p>`;
  } else {
    h += `<p class="sub">${esc(t('dPathNone'))}</p>`;
  }
  h += `</div>`;

  /* ---- entry */
  h += `<div class="card"><h2>${esc(t('dEntryTitle'))}</h2><table class="kv">`;
  if (c.low != null) h += row(t('eLow'), c.low);
  h += row(t('eMed'), c.med + (c.medHi ? '–' + c.medHi : ''));
  if (c.lowAdj != null) h += row(t('eLowAdj'), c.lowAdj);
  if (c.yr) h += row(t('eYear'), c.yr);
  if (c.cmp && c.cmp.length) h += row(t('eCampus'), c.cmp.join(', '));
  h += `</table>`;
  if (c.lowAdj != null) h += `<p class="fine" style="margin:10px 0 0">${esc(t('eLowAdjNote'))}</p>`;
  if (c.url) h += `<p style="margin:12px 0 0"><a class="ext" href="${esc(c.url)}" target="_blank" rel="noopener">${esc(t('dOfficial'))} ↗</a></p>`;
  h += `</div>`;

  /* ---- outcomes */
  if (o) {
    h += `<div class="card"><h2>${esc(t('dOutTitle'))}</h2>
      <p class="sub">${esc(t('dOutLead'))}</p><table class="kv">`;
    [['fte', 'oFte'], ['emp', 'oEmp'], ['exp', 'oExp'], ['teach', 'oTeach'], ['sup', 'oSup'], ['sat', 'oSat']]
      .forEach(([k, lbl]) => {
        if (o[k] == null) return;
        const nat = area.nat[k];
        h += row(t(lbl), pct(o[k]), nat ? t('natAvg', pct(nat)) : null, nat && o[k] > nat);
      });
    h += `</table></div>`;

    if (o.s1 || o.s5 || o.s9) {
      h += `<div class="card"><h2>${esc(t('dSalTitle'))}</h2>
        <p class="sub">${esc(t('dSalLead'))}</p><table class="kv">`;
      [['s1', 's1'], ['s5', 's5'], ['s9', 's9']].forEach(([k, lbl]) => {
        if (!o[k]) return;
        const nat = area.nat[k];
        h += row(t(lbl), money(o[k]), nat ? t('natAvg', money(nat)) : null, nat && o[k] > nat);
      });
      h += `</table></div>`;
    }
  }

  /* ---- research ranking, kept clearly apart from the outcome data */
  const lr = inst.lr && inst.lr[area.lf];
  if (lr) {
    const fieldLabel = lang === 'zh' ? (STR.zh.fieldsZh[area.lf] || area.lf) : area.lf;
    h += `<div class="card"><h2>${esc(t('rkTitle'))}</h2>
      <p class="sub">${esc(t('rkField', fieldLabel))}</p><table class="kv">`;
    h += row(t('rkAu'), `#${lr.au}`, t('rkOf', 39));
    h += row(t('rkWorld'), `#${lr.world}`, t('rkOf', lr.worldSize));
    h += row('PP(top 10%)', lr.pp);
    h += `</table>
      <div class="callout caution" style="margin:12px 0 0">${esc(t('rkCaveat'))}</div>
      <p class="fine" style="margin:10px 0 0">${esc(t('rkSource'))}</p></div>`;
  }

  /* ---- QS, shown against the outcomes rather than on its own */
  if (inst.qs) {
    h += `<div class="card"><h2>${esc(t('qsTitle'))}</h2><table class="kv">`;
    h += row(inst.n, t('qsRank', inst.qs));
    h += `</table>`;
    const natFte = area.nat.fte;
    if (o && o.fte != null && natFte && o.fte > natFte && inst.qs > 100) {
      h += `<div class="callout" style="margin:12px 0 0">${esc(t('qsContrast', inst.qs, o.fte.toFixed(1), natFte.toFixed(1)))}</div>`;
    }
    h += `<p class="fine" style="margin:10px 0 0">${esc(t('qsNote'))}${DATA.meta.qsEdition ? ' ' + esc(t('qsEdition', DATA.meta.qsEdition)) : ''}</p></div>`;
  }

  h += `<div class="callout caution"><b>${esc(t('dCautionTitle'))}</b><br>${esc(t('dCaution'))}</div>`;
  $('#detail').innerHTML = h;
}

function row(label, value, sub, above) {
  return `<tr><th>${esc(label)}</th><td class="${above ? 'above' : ''}">${esc(value)}
    ${sub ? `<span class="vs">${esc(sub)}</span>` : ''}</td></tr>`;
}

/* ---------------------------------------------------------------- routing */

function show(view) {
  ['home', 'results', 'detail'].forEach(v => { $('#view-' + v).hidden = v !== view; });
  $('#back').hidden = view === 'home';
  window.scrollTo(0, 0);
}

function route() {
  const h = location.hash.slice(2);
  if (h.startsWith('c/')) {
    const c = DATA.courses[+h.slice(2)];
    if (c) { renderDetail(c); show('detail'); return; }
  }
  if (h === 'r' && query) { renderResults(); show('results'); return; }
  show('home');
}

/* ------------------------------------------------------------------ init */

async function init() {
  applyStatic();
  // revalidate rather than trust the browser cache: the dataset is replaced
  // wholesale on each annual rebuild, and a stale copy fails silently
  DATA = await (await fetch('data.json', { cache: 'no-cache' })).json();
  fillSelects();
  homeStats();

  $('#form').addEventListener('submit', e => {
    e.preventDefault();
    const atar = parseFloat($('#atar').value);
    if (!(atar >= 30 && atar <= 100)) { $('#atar').focus(); return; }
    query = {
      atar, area: $('#area').value, state: $('#state').value,
      keyword: $('#keyword').value, onlyGood: $('#onlyGood').checked,
    };
    location.hash = '#/r';
  });

  $('#sortbar').addEventListener('click', e => {
    const b = e.target.closest('[data-sort]');
    if (!b) return;
    sortKey = b.dataset.sort;
    renderResults();
  });

  $('#resList').addEventListener('click', e => {
    const b = e.target.closest('[data-idx]');
    if (b) location.hash = '#/c/' + b.dataset.idx;
  });

  $('#back').addEventListener('click', () => history.back());

  $('#lang').addEventListener('click', () => {
    lang = lang === 'zh' ? 'en' : 'zh';
    localStorage.setItem('lang', lang);
    applyStatic(); fillSelects(); homeStats(); route();
  });

  window.addEventListener('hashchange', route);
  route();
}

init();
