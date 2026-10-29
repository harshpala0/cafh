/* CA FirmHub MRL Maker — step-by-step | Designed & Built by Harsh Pala */
(function(){
  document.body.innerHTML = `<div id="app">
  <aside id="sidebar">
    <div id="sidebar-header">
      <h1>MRL Maker</h1>
      <p>CA FIRMHUB · HARSH PALA</p>
      <div class="progress"><div id="prog-bar"></div></div>
      <p id="prog-label" style="margin-top:6px;opacity:.8">0% complete</p>
    </div>
    <nav id="nav"></nav>
  </aside>
  <div id="main">
    <div id="topbar">
      <h2 id="page-title">Setup</h2>
      <button class="btn" type="button" onclick="showSetup()">Setup</button>
      <button class="btn btn-p" type="button" onclick="buildLetter()">Generate letter</button>
      <button class="btn btn-g" type="button" onclick="printLetter()">Print / PDF</button>
      <button class="btn" type="button" onclick="downloadHtml()">Download HTML</button>
    </div>
    <div id="content"></div>
  </div>
</div>
<div class="toast" id="toast"></div>`;

const STATE = {
  mode: 'tax',
  client: null,
  meta: {
    auditorName: '', auditorAddress: '', letterDate: new Date().toISOString().slice(0,10),
    yearEnd: '', engagementDate: '', signatoryName: '', signatoryDesignation: 'Director / Partner / Proprietor',
    includeIFC: false
  },
  answers: {}
};

function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.style.display = 'block';
  setTimeout(() => t.style.display = 'none', 2200);
}

function token() {
  return localStorage.getItem('token') || sessionStorage.getItem('token') || '';
}

async function loadClients() {
  const sel = document.getElementById('client-sel');
  if (!sel) return;
  sel.innerHTML = '<option value="">Loading clients…</option>';
  try {
    const r = await fetch('/api/clients/', { headers: { Authorization: 'Bearer ' + token() } });
    if (!r.ok) throw new Error('Open CA FirmHub main app, log in, then open this tool again.');
    const list = await r.json();
    window.__clients = list;
    sel.innerHTML = '<option value="">— Select client —</option>' +
      list.map(c => `<option value="${c.id}">${esc(c.name)}${c.pan ? ' (' + esc(c.pan) + ')' : ''}</option>`).join('');
    if (!list.length) toast('No clients in register yet');
  } catch (e) {
    sel.innerHTML = '<option value="">' + esc(e.message || 'Failed to load') + '</option>';
    toast(e.message || 'Could not load clients');
  }
}

function onClientPick() {
  const id = document.getElementById('client-sel').value;
  const c = (window.__clients || []).find(x => String(x.id) === String(id));
  STATE.client = c || null;
  if (c) {
    document.getElementById('f-client').value = c.name || '';
    document.getElementById('f-pan').value = c.pan || '';
    document.getElementById('f-gstin').value = c.gstin || '';
    document.getElementById('f-addr').value = c.address || '';
  }
}

function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"']/g, c => ({'&':'&','<':'<','>':'>','"':'"',"'":'&#39;'}[c]));
}

function allSteps() {
  if (STATE.mode === 'tax') {
    return TAX_CLAUSES.map(c => ({ id: 'T' + c[0], no: c[0], title: c[1], body: c[2], fields: c[3] || [], chapter: 'Tax Audit clauses' }));
  }
  const steps = [];
  STAT_CHAPTERS.forEach(ch => {
    ch[2].forEach(s => steps.push({ id: s[0], no: s[0], title: s[1], body: s[2], fields: [], chapter: ch[1] }));
  });
  return steps;
}

function progress() {
  const steps = allSteps();
  const done = steps.filter(s => STATE.answers[s.id] && STATE.answers[s.id].status).length;
  const pct = steps.length ? Math.round(100 * done / steps.length) : 0;
  document.getElementById('prog-bar').style.width = pct + '%';
  document.getElementById('prog-label').textContent = done + ' / ' + steps.length + ' · ' + pct + '%';
  return pct;
}

function renderNav() {
  const nav = document.getElementById('nav');
  let html = '';
  html += '<div class="nav-sec">Start</div>';
  html += '<div class="nav-item" data-go="setup" onclick="showSetup()"><span class="dot"></span> Engagement setup</div>';
  if (STATE.mode === 'tax') {
    html += '<div class="nav-sec">Tax Audit MRL</div>';
    TAX_CLAUSES.forEach(c => {
      const id = 'T' + c[0];
      const a = STATE.answers[id];
      const cls = a && a.status === 'yes' ? 'done' : (a && a.status ? 'flag' : '');
      html += `<div class="nav-item ${cls}" data-go="${id}" onclick="showStep('${id}')"><span class="dot"></span>${c[0]}. ${esc(c[1].slice(0,32))}${c[1].length>32?'…':''}</div>`;
    });
  } else {
    STAT_CHAPTERS.forEach(ch => {
      html += `<div class="nav-sec">${esc(ch[1])}</div>`;
      ch[2].forEach(s => {
        const a = STATE.answers[s[0]];
        const cls = a && a.status === 'yes' ? 'done' : (a && a.status ? 'flag' : '');
        html += `<div class="nav-item ${cls}" data-go="${s[0]}" onclick="showStep('${s[0]}')"><span class="dot"></span>${esc(s[0])} ${esc(s[1].slice(0,28))}</div>`;
      });
    });
  }
  html += '<div class="nav-sec">Output</div>';
  html += '<div class="nav-item" onclick="buildLetter()"><span class="dot"></span> Full letter</div>';
  nav.innerHTML = html;
  progress();
}

function showSetup() {
  document.getElementById('page-title').textContent = 'Engagement setup';
  const m = STATE.meta;
  document.getElementById('content').innerHTML = `
    <div class="card">
      <h3>Type of MRL</h3>
      <div class="status-row">
        <button type="button" class="${STATE.mode==='tax'?'on-yes':''}" onclick="setMode('tax')">Tax Audit u/s 44AB — 55 clauses</button>
        <button type="button" class="${STATE.mode==='statutory'?'on-yes':''}" onclick="setMode('statutory')">Statutory Audit — SA 580 / CARO / Rule 11</button>
      </div>
    </div>
    <div class="card">
      <h3>Client</h3>
      <p class="muted">Loaded from your firm client register (same list as Clients module). Stay logged in on the main app.</p>
      <div class="fg"><label>Client from register</label><select id="client-sel" onchange="onClientPick()"></select></div>
      <div class="fg"><label>Client / Assessee name *</label><input id="f-client" value="${esc(STATE.client && STATE.client.name || '')}"></div>
      <div class="row">
        <div class="fg"><label>PAN</label><input id="f-pan" value="${esc(STATE.client && STATE.client.pan || '')}"></div>
        <div class="fg"><label>GSTIN</label><input id="f-gstin" value="${esc(STATE.client && STATE.client.gstin || '')}"></div>
      </div>
      <div class="fg"><label>Address</label><input id="f-addr" value="${esc(STATE.client && STATE.client.address || '')}"></div>
    </div>
    <div class="card">
      <h3>Auditor & dates</h3>
      <div class="fg"><label>Auditor firm name *</label><input id="f-auditor" value="${esc(m.auditorName)}" placeholder="XYZ & Co., Chartered Accountants"></div>
      <div class="fg"><label>Auditor address</label><input id="f-auditor-addr" value="${esc(m.auditorAddress)}"></div>
      <div class="row">
        <div class="fg"><label>Letter date</label><input type="date" id="f-date" value="${esc(m.letterDate)}"></div>
        <div class="fg"><label>Year ended</label><input id="f-ye" value="${esc(m.yearEnd)}" placeholder="31st March, 2026"></div>
      </div>
      <div class="fg"><label>Engagement letter date</label><input id="f-eng" value="${esc(m.engagementDate)}" placeholder="For statutory MRL"></div>
      <div class="row">
        <div class="fg"><label>Signatory name *</label><input id="f-sign" value="${esc(m.signatoryName)}"></div>
        <div class="fg"><label>Designation</label><input id="f-desig" value="${esc(m.signatoryDesignation)}"></div>
      </div>
      <div class="fg" id="ifc-row" style="${STATE.mode==='statutory'?'':'display:none'}"><label><input type="checkbox" id="f-ifc" ${m.includeIFC?'checked':''}> Include IFC (s.143(3)(i)) representations</label></div>
    </div>
    <div class="card">
      <button class="btn btn-p" type="button" onclick="saveSetup()">Save & start clauses →</button>
      <p class="muted" style="margin-top:10px">Work through each clause in the left sidebar. Mark <strong>Confirmed</strong>, <strong>Exception</strong>, or <strong>N/A</strong>. Then generate the formal letter for print/PDF.</p>
    </div>`;
  loadClients();
  renderNav();
}

function setMode(mode) { STATE.mode = mode; showSetup(); }

function saveSetup() {
  STATE.meta.auditorName = document.getElementById('f-auditor').value.trim();
  STATE.meta.auditorAddress = document.getElementById('f-auditor-addr').value.trim();
  STATE.meta.letterDate = document.getElementById('f-date').value;
  STATE.meta.yearEnd = document.getElementById('f-ye').value.trim();
  STATE.meta.engagementDate = document.getElementById('f-eng').value.trim();
  STATE.meta.signatoryName = document.getElementById('f-sign').value.trim();
  STATE.meta.signatoryDesignation = document.getElementById('f-desig').value.trim();
  const ifc = document.getElementById('f-ifc');
  STATE.meta.includeIFC = ifc ? ifc.checked : false;
  const name = document.getElementById('f-client').value.trim();
  if (!STATE.client) STATE.client = {};
  STATE.client.name = name;
  STATE.client.pan = document.getElementById('f-pan').value.trim();
  STATE.client.gstin = document.getElementById('f-gstin').value.trim();
  STATE.client.address = document.getElementById('f-addr').value.trim();
  if (!name || !STATE.meta.auditorName) { toast('Client name and auditor firm are required'); return; }
  toast('Saved');
  renderNav();
  const steps = allSteps();
  if (steps[0]) showStep(steps[0].id);
}

function showStep(id) {
  const steps = allSteps();
  const idx = steps.findIndex(s => s.id === id);
  if (idx < 0) return;
  const s = steps[idx];
  const a = STATE.answers[id] || { status: '', notes: '', fields: {} };
  document.getElementById('page-title').textContent = s.no + ' · ' + s.title;
  let fieldsHtml = '';
  (s.fields || []).forEach(f => {
    const v = (a.fields && a.fields[f.id]) || f.def || '';
    if (f.type === 'select') {
      fieldsHtml += `<div class="fg"><label>${esc(f.label)}</label><select id="fld-${f.id}">${f.opts.map(o=>`<option ${o===v?'selected':''}>${esc(o)}</option>`).join('')}</select></div>`;
    } else {
      fieldsHtml += `<div class="fg"><label>${esc(f.label)}</label><input id="fld-${f.id}" value="${esc(v)}"></div>`;
    }
  });
  document.getElementById('content').innerHTML = `
    <div class="card">
      <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;flex-wrap:wrap">
        <span class="tag">${esc(s.chapter || '')}</span>
        <span class="muted">Step ${idx+1} of ${steps.length}</span>
      </div>
      <h3 style="margin-top:10px">${esc(s.no)}. ${esc(s.title)}</h3>
      <div class="clause-body">${esc(s.body)}</div>
      ${fieldsHtml}
      <p class="muted" style="margin-top:8px">Representation status for this clause</p>
      <div class="status-row">
        <button type="button" id="st-yes" class="${a.status==='yes'?'on-yes':''}" onclick="setStatus('${id}','yes')">Confirmed</button>
        <button type="button" id="st-no" class="${a.status==='no'?'on-no':''}" onclick="setStatus('${id}','no')">Exception / modify</button>
        <button type="button" id="st-na" class="${a.status==='na'?'on-na':''}" onclick="setStatus('${id}','na')">N/A</button>
      </div>
      <div class="fg"><label>Notes / exception wording (included in letter if Exception)</label>
        <textarea id="step-notes" rows="3">${esc(a.notes||'')}</textarea></div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:8px">
        <button class="btn" type="button" onclick="saveStep('${id}',${idx-1})">${idx?'← Previous':'Setup'}</button>
        <button class="btn btn-p" type="button" onclick="saveStep('${id}',${idx+1})">Save & next →</button>
      </div>
    </div>`;
  document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('on', n.getAttribute('data-go')===id));
  progress();
}

function setStatus(id, st) {
  if (!STATE.answers[id]) STATE.answers[id] = { status: '', notes: '', fields: {} };
  STATE.answers[id].status = st;
  ['yes','no','na'].forEach(x => {
    const b = document.getElementById('st-' + x);
    if (b) b.className = st === x ? ('on-' + x) : '';
  });
  progress();
  renderNav();
  document.querySelectorAll('.nav-item').forEach(n => n.classList.toggle('on', n.getAttribute('data-go')===id));
}

function saveStep(id, nextIdx) {
  const steps = allSteps();
  const s = steps.find(x => x.id === id);
  if (!STATE.answers[id]) STATE.answers[id] = { status: '', notes: '', fields: {} };
  STATE.answers[id].notes = (document.getElementById('step-notes') || {}).value || '';
  const fields = {};
  (s.fields || []).forEach(f => {
    const el = document.getElementById('fld-' + f.id);
    if (el) fields[f.id] = el.value;
  });
  STATE.answers[id].fields = fields;
  if (!STATE.answers[id].status) STATE.answers[id].status = 'yes';
  renderNav();
  if (nextIdx < 0) showSetup();
  else if (nextIdx >= steps.length) buildLetter();
  else showStep(steps[nextIdx].id);
}

function field(a, id, def) {
  if (a && a.fields && a.fields[id]) return a.fields[id];
  return def || '________';
}

function lineStatus(id, defaultText) {
  const a = STATE.answers[id];
  if (!a || !a.status || a.status === 'yes') return defaultText;
  if (a.status === 'na') return defaultText + ' [N/A for this engagement]';
  if (a.notes) return defaultText + ' Exception: ' + a.notes;
  return defaultText + ' [Exception — see working papers]';
}

function buildTaxLetter() {
  const c = STATE.client || {};
  const m = STATE.meta;
  const A = STATE.answers;
  const L = [];
  L.push('To');
  L.push(m.auditorName || '________________');
  L.push('Chartered Accountants');
  if (m.auditorAddress) L.push(m.auditorAddress);
  L.push('');
  L.push('Date: ' + (m.letterDate || '________'));
  L.push('');
  L.push('Sub: Representation from Management for the purpose of Tax Audit under section 44AB of the Income Tax Act, 1961 (the "Act") for the year ended on ' + (m.yearEnd || '________') + '.');
  L.push('');
  L.push('Respected Sir / Madam,');
  L.push('');
  L.push('This representation letter is provided in connection with the tax audit u/s 44AB of the Income Tax Act of ' + (c.name || '________') + ' for the year ended ' + (m.yearEnd || '________') + ' for the purpose of expressing an opinion as to whether the Form 3CD along with the annexure thereto gives a true and correct view of the facts mentioned therein. We acknowledge our responsibility to keep and maintain such books of account and other documents as may enable the tax auditor to complete tax audit u/s 44AB, in accordance with the provisions of the Income Tax Act, 1961.');
  L.push('');
  L.push('We confirm the following representations to the best of our knowledge and belief:');
  L.push('');
  const t = (n, text) => L.push(lineStatus('T'+n, text));
  t('1', '1. The name of the assessee as per PAN card is ' + field(A.T1,'pan_name', c.name||'________') + '. PAN: ' + field(A.T1,'pan', c.pan||'________') + '. A copy of PAN Card is available / attached.');
  t('2', '2. The assessee has no other business address than communicated to the Income-tax Department for assessment purposes' + (field(A.T2,'biz_addr', c.address||'') ? ' (principal place: ' + field(A.T2,'biz_addr', c.address) + ')' : '') + '.');
  t('3', '3. The Assessee has employed the ' + field(A.T3,'acct_method','mercantile') + ' system of accounting during the year.');
  t('4', '4. There has been ' + (field(A.T4,'chg_acct','No')==='Yes'?'a change':'no change') + ' in the method of accounting. Effect on profit: Rs. ' + field(A.T4,'chg_effect','Nil') + '.');
  t('5', '5. Indirect tax registrations — GSTIN: ' + field(A.T5,'gstin', c.gstin||'________') + '. Other: ' + field(A.T5,'other_reg','________') + '.');
  t('6', '6. The Assessee has ' + (field(A.T6,'opt115','No')==='Yes'?'opted':'not opted') + ' 115BA/BAA/BAB/BAC/BAD.');
  t('7', '7. P&L does not include presumptive profits under 44AD/AE etc., except as disclosed in Form 3CD.');
  t('8', '8. Business as reported in clause 10(a) of Form 3CD: ' + field(A.T8,'nob','________') + '.');
  t('9', '9. Nature of business disclosed; no undisclosed change from earlier years, except as in Form 3CD.');
  t('10', '10. Books maintained: ' + field(A.T10,'books','Cash Book, Bank Book, Ledger, Journal') + '.');
  t('11', '11. Books kept as per addresses in clause 11(b) of Form 3CD.');
  t('12', '12. Partners / members and PSR: ' + field(A.T12,'partners','Not applicable') + '.');
  t('13', '13. No items of income/capital receipts omitted from P&L except as disclosed in Form 3CD.');
  t('14', '14. No land/building transfer below s.43CA/50C value except as in Form 3CD.');
  t('15', '15. ICDS disclosures under s.145(2) / clause 13(e) are correct.');
  t('16', '16. ICDS adjustments as in Form 3CD. Net effect: Rs. ' + field(A.T16,'icds_net','Nil') + '.');
  t('17', '17. Stock at cost or NRV. Policy change: ' + field(A.T17,'inv_policy','No') + '. Effect: Rs. ' + field(A.T17,'inv_effect','Nil') + '.');
  t('18', '18. Depreciation particulars under clause 18 of Form 3CD are correct.');
  t('19', '19. s.32AC/35 etc. amounts correctly reported in Form 3CD.');
  t('20', '20. No bonus/commission otherwise payable as profits/dividend, except as disclosed.');
  t('21', '21. Employee contributions and payments under clause 20(b) of Form 3CD are correct.');
  t('22', '22. No capital expenditure debited to P&L except as disclosed.');
  t('23', '23. No capital asset converted into stock-in-trade except as disclosed.');
  t('24', '24. No personal expenditure debited to P&L except as disclosed.');
  t('25', '25. No advertisement in any political party publication.');
  t('26', '26. No club entrance/subscription/facilities except as disclosed.');
  t('27', '27. No penalty/fine for law violation or prohibited purpose except TDS/TCS interest in clause 34(c) (Rs. ' + field(A.T27,'penalty_amt','Nil') + ').');
  t('28', '28. No other penalty or fine except as disclosed.');
  t('29', '29. s.40(a) amounts only as in Form 3CD (Rs. ' + field(A.T29,'40a_amt','Nil') + ').');
  t('30', '30. s.40A(3) payments above limit by a/c payee cheque/draft/ECS except as disclosed.');
  t('31', '31. No sums disallowed u/s 40A(9).');
  t('32', '32. No contingent liability debited to P&L.');
  t('33', '33. s.14A deduction Rs. ' + field(A.T33,'14a_amt','Nil') + ' / as disclosed.');
  t('34', '34. No interest inadmissible under proviso to s.36(1)(iii) except as disclosed.');
  t('35', '35. s.40A(2)(b) payments in clause 23 of Form 3CD are correct.');
  t('36', '36. No profit chargeable u/s 41 except as disclosed.');
  t('37', '37. No s.56(2)(viia) receipt except as in clause 28 of Form 3CD.');
  t('38', '38. No s.56(2)(viib)/(ix)/(x) excess share consideration except as in clause 29.');
  t('39', '39. s.43B amounts correctly reported in clause 26 of Form 3CD.');
  t('40', '40. CENVAT/ITC treatment correctly reported in clause 27(a).');
  t('41', '41. Prior-period items only as in clause 27(b).');
  t('42', '42. Loans/deposits above limit by a/c payee cheque/draft/ECS except as disclosed.');
  t('43', '43. Chapter VI-A / 10A/10AA only as in clause 33 of Form 3CD.');
  t('44', '44. Chapter XVII-B/BB complied with; exceptions only as in clause 34(a).');
  t('45', '45. TDS/TCS statements within time except as in clause 34(b).');
  t('46', '46. Interest u/s 201(1A)/206C(7) in clause 34(c) is correct.');
  t('47', '47. Quantitative details only as in clause 35.');
  t('48', '48. No s.2(22)(e) dividend except as in clause 36A.');
  t('49', '49. No Central Excise / s.72A audit except as disclosed.');
  t('50', '50. No adverse cost audit comments except as disclosed.');
  t('51', '51. No other tax-law demand/refund except as in clause 41.');
  t('52', '52. Turnover/GP ratios in clause 40 are correct.');
  t('53', '53. Form 61/61A/61B complied with as applicable.');
  t('54', '54. s.286(2) statement complied with as applicable.');
  t('55', '55. GST expenditure as in clause 44 of Form 3CD.');
  L.push('');
  L.push('For and on behalf of');
  L.push(c.name || '________________');
  L.push('');
  L.push('');
  L.push(m.signatoryName || '________________');
  L.push(m.signatoryDesignation || 'Director / Partner / Proprietor');
  L.push('');
  L.push('— CA FirmHub MRL Maker · Designed & Built by Harsh Pala —');
  return L.join('\n');
}

function buildStatLetter() {
  const c = STATE.client || {};
  const m = STATE.meta;
  const ye = m.yearEnd || '________';
  const cn = c.name || '________';
  const L = [];
  const t = (id, text) => L.push(lineStatus(id, text));
  L.push('ON THE LETTERHEAD OF THE CLIENT');
  L.push('');
  L.push('MANAGEMENT REPRESENTATION LETTER IN CONNECTION WITH THE STATUTORY AUDIT OF');
  L.push(cn.toUpperCase());
  L.push('FOR THE YEAR ENDED ' + ye.toUpperCase());
  L.push('');
  L.push('To');
  L.push(m.auditorName || '________________');
  L.push('Chartered Accountants');
  if (m.auditorAddress) L.push(m.auditorAddress);
  L.push('');
  L.push('Date: ' + (m.letterDate || '________'));
  L.push('');
  t('A1', '1. This representation letter is provided in connection with your audit of the financial statements of ' + cn + ' for the year ended ' + ye + ' for the purpose of expressing an opinion as to whether the financial statements give a true and fair view in accordance with the applicable accounting standards in India.');
  L.push('');
  L.push('Representations concerning the financial statements');
  t('A2', '2. We have fulfilled our responsibilities as set out in the audit engagement dated ' + (m.engagementDate||'________') + ' for preparation of the financial statements.');
  t('A3', '3. We provided access to all relevant information, additional information requested, and unrestricted access to persons within the entity.');
  t('A4', '4. All transactions have been recorded and are reflected in the financial statements.');
  t('A5', '5. Proper books of account have been maintained as required by law.');
  t('A6', '6. BS, P&L, SCE and CFS (as applicable) agree with the books of account.');
  t('A7', '7. Financial statements comply with AS referred to in section 133 of the Companies Act, 2013 (to the extent applicable).');
  t('A8', '8. No branches, OR proper branch returns received and dealt with in the FS.');
  t('A9', '9. None of the directors is disqualified under Section 164(2) as on ' + ye + ' (to the extent applicable).');
  t('A10', '10. Accounting policies are appropriate; FS prepared on accrual basis.');
  L.push('');
  L.push('Balance sheet items');
  t('B1', '11–13. PPE: stated after additions, disposals and depreciation; physically verified (or none).');
  t('B2', '15–16. Intangibles disclosed per AS/Ind AS & Schedule III (or none).');
  t('B3', '17–18. CWIP / IA under development disclosed with ageing where required (or none).');
  t('B4', '19–21. Investments accounted, valued and held in company name (or none).');
  t('B5', '22–25. Loans, advances and other assets good and recoverable except provisions.');
  t('B6', '26–33. Inventories: counted under supervision; owned; valued cost/NRV; provisions adequate.');
  t('B7', '34–36. Trade receivables good except as stated; ageing correct.');
  t('B8', '37–39. Bank accounts as disclosed; cash certified by management.');
  t('B9', '44–52. Share capital and borrowings disclosed; covenants complied with except as disclosed.');
  t('B10', '53–59. All known liabilities recorded; contingencies complete.');
  t('B11', '60–61. Provisions for known material losses and claims made.');
  L.push('');
  L.push('Related parties and other matters');
  t('C1', '62–64. Related parties and RPTs complete per AS 18 / Ind AS 24 and Companies Act.');
  t('C2', '65. Results not affected by unusual/exceptional/prior-period items except as disclosed.');
  t('C3', '66. No personal expenses charged to revenue.');
  t('C4', '68. MSME requirements addressed; no material delayed-payment claims except disclosed.');
  t('C5', '69–70. No struck-off company or crypto transactions except disclosed.');
  t('C6', '71–72. Minutes and registers complete; made available to you.');
  if (m.includeIFC) {
    L.push('');
    L.push('Internal Financial Controls (Section 143(3)(i))');
    t('D1', '74–77. We are responsible for adequate and effective IFC.');
    t('D2', '78–80. IFC was adequate and operating effectively as at ' + ye + ', except deficiencies disclosed to you.');
    t('D3', '81–90. Significant deficiencies and material frauds involving management disclosed.');
  }
  L.push('');
  L.push('CARO 2020 (Section 143(11)) — where applicable');
  t('E1', '101. Clause 3(i): PPE/intangibles — records, verification, title deeds, benami.');
  t('E2', '102. Clause 3(ii): Inventory verification; WC returns agree with books.');
  t('E3', '103–106. Clauses 3(iii)–(vi): Loans/guarantees; s.185/186; deposits; cost records.');
  t('E4', '107–108. Clauses 3(vii)–(viii): Statutory dues; unrecorded income.');
  t('E5', '109–110. Clauses 3(ix)–(x): Borrowings; IPO/preferential issues.');
  t('E6', '111–115. Clauses 3(xi)–(xv): Fraud; Nidhi; RPT; internal audit; s.192.');
  t('E7', '116–121. Clauses 3(xvi)–(xxi): RBI; cash losses; resignation; liquidity; CSR; CFS.');
  L.push('');
  L.push('Fraud, Rule 11, subsequent events');
  t('F1', '122–130. Fraud prevention responsibility; risk assessment disclosed; no material fraud except communicated.');
  t('F2', '131–134. Rule 11(a)/(b)/(c)/(f) as disclosed.');
  t('F3', '135–139. Rule 11(e): no intermediary funding for ultimate beneficiaries except notes.');
  t('F4', '160–171. Subsequent events and NOCLAR disclosed as required.');
  L.push('');
  L.push('For and on behalf of');
  L.push(cn);
  L.push('');
  L.push('');
  L.push(m.signatoryName || '________________');
  L.push(m.signatoryDesignation || 'Director / Partner / Proprietor');
  L.push('');
  L.push('— CA FirmHub MRL Maker · Designed & Built by Harsh Pala —');
  return L.join('\n');
}

function buildLetter() {
  const text = STATE.mode === 'tax' ? buildTaxLetter() : buildStatLetter();
  document.getElementById('page-title').textContent = 'Full letter';
  document.getElementById('content').innerHTML = `
    <div class="card">
      <h3>Management Representation Letter</h3>
      <p class="muted">Formal letter from your clause-by-clause confirmations. Use Print to save as PDF (Times New Roman letter format).</p>
      <div style="margin:12px 0;display:flex;gap:8px;flex-wrap:wrap">
        <button class="btn btn-g" type="button" onclick="printLetter()">Print / Save as PDF</button>
        <button class="btn" type="button" onclick="downloadHtml()">Download HTML</button>
        <button class="btn" type="button" onclick="copyLetter()">Copy text</button>
      </div>
      <div id="letter-preview">${esc(text)}</div>
    </div>`;
  window.__letterText = text;
  progress();
}

function printLetter() {
  if (!window.__letterText) buildLetter();
  const w = window.open('', '_blank');
  if (!w) { toast('Allow pop-ups'); return; }
  const title = (STATE.mode==='tax'?'Tax Audit':'Statutory') + ' MRL — ' + ((STATE.client||{}).name||'');
  w.document.write(`<!DOCTYPE html><html><head><title>${esc(title)}</title>
    <style>@page{margin:22mm 18mm}body{font-family:'Times New Roman',Times,serif;font-size:12pt;line-height:1.5;color:#000}
    pre{white-space:pre-wrap;font-family:inherit;font-size:12pt;margin:0}</style></head>
    <body><pre>${esc(window.__letterText||'')}</pre></body></html>`);
  w.document.close();
  setTimeout(() => { w.focus(); w.print(); }, 300);
}

function downloadHtml() {
  if (!window.__letterText) buildLetter();
  const title = (STATE.mode==='tax'?'Tax_Audit':'Statutory') + '_MRL';
  const blob = new Blob([`<!DOCTYPE html><html><head><meta charset="utf-8"><title>${title}</title>
    <style>body{font-family:'Times New Roman',Times,serif;font-size:12pt;line-height:1.5;max-width:700px;margin:24px auto;padding:0 16px}
    pre{white-space:pre-wrap;font-family:inherit}</style></head>
    <body><pre>${esc(window.__letterText||'')}</pre>
    <p style="margin-top:24px;font-size:10pt;color:#666">CA FirmHub MRL Maker · Designed & Built by Harsh Pala</p>
    </body></html>`], {type:'text/html'});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = title + '_' + ((STATE.client||{}).name||'Client').replace(/[^\w]+/g,'_').slice(0,40) + '.html';
  a.click();
}

function copyLetter() {
  if (!window.__letterText) buildLetter();
  navigator.clipboard.writeText(window.__letterText||'').then(()=>toast('Copied')).catch(()=>toast('Copy failed'));
}

window.showSetup = showSetup;
window.setMode = setMode;
window.saveSetup = saveSetup;
window.showStep = showStep;
window.setStatus = setStatus;
window.saveStep = saveStep;
window.buildLetter = buildLetter;
window.printLetter = printLetter;
window.downloadHtml = downloadHtml;
window.copyLetter = copyLetter;
window.onClientPick = onClientPick;

showSetup();
})();
