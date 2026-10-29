/* CA FirmHub — MRL Maker UI (Tax Audit + Statutory Audit)
   Designed & Built by Harsh Pala
   Letter bodies: /static/mrl-letters.js
*/
(function () {
  if (window.__cafhMrlUI) return;
  window.__cafhMrlUI = true;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&', '<': '<', '>': '>', '"': '"', "'": '&#39;' })[c];
    });
  }

  function val(id, def) {
    var el = document.getElementById(id);
    var v = el ? String(el.value || '').trim() : '';
    return v || (def || '____________');
  }

  function todayISO() {
    return new Date().toISOString().slice(0, 10);
  }

  function fyEndFromLabel(fy) {
    try {
      var p = String(fy).split('-');
      var sy = parseInt(p[0], 10);
      if (!sy) return '31st March, 20XX';
      return '31st March, ' + (sy + 1);
    } catch (e) {
      return '31st March, 20XX';
    }
  }

  function getFY() {
    try {
      var lb = document.getElementById('fy-label');
      if (lb) {
        var m = (lb.textContent || '').match(/(\d{4}-\d{2})/);
        if (m) return m[1];
      }
    } catch (e) {}
    if (window.FY) return String(window.FY);
    return '2025-26';
  }

  function taxAuditLetter(d) {
    if (typeof window.cafhTaxAuditLetter === 'function') return window.cafhTaxAuditLetter(d);
    return 'Full Tax Audit MRL templates failed to load. Hard-refresh the page (Ctrl+Shift+R).';
  }

  function statutoryLetter(d) {
    if (typeof window.cafhStatutoryLetter === 'function') return window.cafhStatutoryLetter(d);
    return 'Full Statutory MRL templates failed to load. Hard-refresh the page (Ctrl+Shift+R).';
  }

  function collect() {
    var fy = getFY();
    return {
      type: (document.getElementById('mrl-type') || {}).value || 'tax',
      clientName: val('mrl-client', 'M/s ________________'),
      panName: val('mrl-pan-name', val('mrl-client', '________________')),
      pan: val('mrl-pan', '____________'),
      gstin: val('mrl-gstin', 'Not applicable / ________'),
      businessAddress: val('mrl-addr', ''),
      auditorName: val('mrl-auditor', '________________, Chartered Accountants'),
      auditorAddress: val('mrl-auditor-addr', ''),
      letterDate: val('mrl-date', todayISO()),
      yearEnd: val('mrl-year-end', fyEndFromLabel(fy)),
      engagementDate: val('mrl-eng-date', '____________'),
      accountingMethod: (document.getElementById('mrl-acct') || {}).value || 'mercantile',
      changeInAccounting: (document.getElementById('mrl-change-acct') || {}).value || 'No',
      indirectTax: (document.getElementById('mrl-idt') || {}).value || 'Yes',
      opted115: (document.getElementById('mrl-115') || {}).value || 'No',
      natureOfBusiness: val('mrl-nob', 'as disclosed in Form 3CD'),
      booksList: val('mrl-books', 'Cash Book, Bank Book, Ledger, Journal'),
      partners: val('mrl-partners', 'Not applicable / as per deed'),
      hasBranches: (document.getElementById('mrl-branches') || {}).value || 'No',
      cashBalance: val('mrl-cash', ''),
      includeIFC: (document.getElementById('mrl-ifc') || {}).value || 'No',
      signatoryName: val('mrl-sign-name', '________________'),
      signatoryDesignation: val('mrl-sign-desig', 'Director / Partner / Proprietor')
    };
  }

  function generate() {
    var d = collect();
    var text = d.type === 'statutory' ? statutoryLetter(d) : taxAuditLetter(d);
    var pre = document.getElementById('mrl-preview');
    if (pre) pre.value = text;
    return text;
  }

  function downloadTxt() {
    var text = generate();
    var blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'MRL_' + (collect().type === 'statutory' ? 'Statutory' : 'TaxAudit') + '_' + (collect().clientName || 'Client').replace(/[^\w]+/g, '_').slice(0, 40) + '.txt';
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    if (typeof toast === 'function') toast('Downloaded', 'ok');
  }

  function copyText() {
    var text = generate();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        if (typeof toast === 'function') toast('Copied to clipboard', 'ok');
      }).catch(function () { fallbackCopy(text); });
    } else fallbackCopy(text);
  }

  function fallbackCopy(text) {
    var pre = document.getElementById('mrl-preview');
    if (pre) { pre.select(); document.execCommand('copy'); }
    if (typeof toast === 'function') toast('Copied', 'ok');
  }

  function printLetter() {
    generate();
    var text = (document.getElementById('mrl-preview') || {}).value || '';
    var w = window.open('', '_blank');
    if (!w) { if (typeof toast === 'function') toast('Allow pop-ups to print', 'err'); return; }
    w.document.write('<pre style="font-family:Georgia,serif;font-size:12pt;line-height:1.45;white-space:pre-wrap;padding:24px">' +
      esc(text).replace(/\n/g, '<br>') + '</pre>');
    w.document.close();
    w.focus();
    w.print();
  }

  window.cafhMrlGenerate = generate;
  window.cafhMrlDownload = downloadTxt;
  window.cafhMrlCopy = copyText;
  window.cafhMrlPrint = printLetter;

  window.lMrlMaker = function () {
    var fy = getFY();
    document.getElementById('pt').textContent = 'MRL Maker — Management Representation Letter (Full)';
    document.getElementById('pa').innerHTML = '';
    var clients = [];
    try { clients = (window.S && S.clients) || []; } catch (e) {}
    var clientOpts = '<option value="">— Select client (optional) —</option>' +
      clients.map(function (c) {
        return '<option value="' + esc(c.name) + '" data-pan="' + esc(c.pan || '') + '" data-gstin="' + esc(c.gstin || '') + '" data-addr="' + esc(c.address || '') + '">' + esc(c.name) + '</option>';
      }).join('');

    document.getElementById('pb').innerHTML =
      '<div style="display:grid;grid-template-columns:minmax(280px,380px) 1fr;gap:16px;align-items:start">' +
      '<div class="card"><div class="card-h">Letter particulars</div><div class="card-b" style="font-size:13px">' +
      '<div class="fg"><label>Type of MRL</label><select id="mrl-type" onchange="cafhMrlToggleType()">' +
      '<option value="tax">Tax Audit (u/s 44AB) — Full 55 clauses</option>' +
      '<option value="statutory">Statutory Audit — Full SA 580 / CARO / IFC / Rule 11</option></select></div>' +
      '<div class="fg"><label>Client (from register)</label><select id="mrl-client-sel" onchange="cafhMrlFillClient()">' + clientOpts + '</select></div>' +
      '<div class="fg"><label>Client / Assessee name *</label><input id="mrl-client" placeholder="M/s ABC Pvt Ltd"></div>' +
      '<div class="fg"><label>Name as per PAN</label><input id="mrl-pan-name" placeholder="Same as client if blank"></div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' +
      '<div class="fg"><label>PAN</label><input id="mrl-pan" placeholder="ABCDE1234F"></div>' +
      '<div class="fg"><label>GSTIN</label><input id="mrl-gstin" placeholder="Optional"></div></div>' +
      '<div class="fg"><label>Business address</label><input id="mrl-addr" placeholder="As communicated to ITD / registered office"></div>' +
      '<div class="fg"><label>Auditor firm name *</label><input id="mrl-auditor" placeholder="XYZ & Co., Chartered Accountants"></div>' +
      '<div class="fg"><label>Auditor address</label><input id="mrl-auditor-addr" placeholder="Optional"></div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' +
      '<div class="fg"><label>Letter date</label><input type="date" id="mrl-date" value="' + todayISO() + '"></div>' +
      '<div class="fg"><label>Year ended</label><input id="mrl-year-end" value="' + fyEndFromLabel(fy) + '"></div></div>' +
      '<div class="fg mrl-stat"><label>Audit engagement date</label><input id="mrl-eng-date" placeholder="DD/MM/YYYY"></div>' +
      '<div class="fg mrl-tax"><label>Accounting method</label><select id="mrl-acct"><option>mercantile</option><option>cash</option></select></div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px" class="mrl-tax">' +
      '<div class="fg"><label>Change in method?</label><select id="mrl-change-acct"><option>No</option><option>Yes</option></select></div>' +
      '<div class="fg"><label>Liable to indirect tax?</label><select id="mrl-idt"><option>Yes</option><option>No</option></select></div></div>' +
      '<div class="fg mrl-tax"><label>Opted 115BA/BAA/etc.?</label><select id="mrl-115"><option>No</option><option>Yes</option></select></div>' +
      '<div class="fg mrl-tax"><label>Nature of business</label><input id="mrl-nob" placeholder="Trading / Manufacturing / …"></div>' +
      '<div class="fg mrl-tax"><label>Books maintained</label><input id="mrl-books" value="Cash Book, Bank Book, Ledger, Journal"></div>' +
      '<div class="fg mrl-tax"><label>Partners / members (if any)</label><input id="mrl-partners" placeholder="Not applicable"></div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px" class="mrl-stat">' +
      '<div class="fg"><label>Has branches?</label><select id="mrl-branches"><option>No</option><option>Yes</option></select></div>' +
      '<div class="fg"><label>Include IFC para?</label><select id="mrl-ifc"><option>No</option><option>Yes</option></select></div></div>' +
      '<div class="fg mrl-stat"><label>Cash balance (optional)</label><input id="mrl-cash" placeholder="Rs."></div>' +
      '<div class="fg"><label>Signatory name *</label><input id="mrl-sign-name" placeholder="Full name"></div>' +
      '<div class="fg"><label>Designation</label><input id="mrl-sign-desig" value="Director / Partner / Proprietor"></div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px">' +
      '<button class="btn btn-p" type="button" onclick="cafhMrlGenerate()">Generate full letter</button>' +
      '<button class="btn btn-o" type="button" onclick="cafhMrlCopy()">Copy</button>' +
      '<button class="btn btn-o" type="button" onclick="cafhMrlDownload()">Download .txt</button>' +
      '<button class="btn btn-o" type="button" onclick="cafhMrlPrint()">Print</button>' +
      '</div>' +
      '<p style="font-size:11px;color:var(--text2);margin-top:10px;line-height:1.4"><strong>Full templates:</strong> Tax Audit = complete 55-clause Form 3CD MRL. Statutory = SA 580 + PPE/Inventory/RPT + full CARO 2020 clauses + IFC + Rule 11 + fraud. Delete inapplicable paras and fill blanks. Designed & Built by Harsh Pala.</p>' +
      '</div></div>' +
      '<div class="card"><div class="card-h">Full letter preview</div><div class="card-b" style="padding:0">' +
      '<textarea id="mrl-preview" readonly style="width:100%;min-height:70vh;border:0;padding:16px;font-family:Georgia,serif;font-size:13px;line-height:1.5;resize:vertical;box-sizing:border-box" placeholder="Click Generate full letter…"></textarea>' +
      '</div></div></div>';

    window.cafhMrlToggleType = function () {
      var t = (document.getElementById('mrl-type') || {}).value;
      document.querySelectorAll('.mrl-tax').forEach(function (el) { el.style.display = t === 'tax' ? '' : 'none'; });
      document.querySelectorAll('.mrl-stat').forEach(function (el) { el.style.display = t === 'statutory' ? '' : 'none'; });
    };
    window.cafhMrlFillClient = function () {
      var sel = document.getElementById('mrl-client-sel');
      if (!sel || !sel.value) return;
      var opt = sel.options[sel.selectedIndex];
      document.getElementById('mrl-client').value = sel.value;
      document.getElementById('mrl-pan-name').value = sel.value;
      if (opt) {
        if (opt.getAttribute('data-pan')) document.getElementById('mrl-pan').value = opt.getAttribute('data-pan');
        if (opt.getAttribute('data-gstin')) document.getElementById('mrl-gstin').value = opt.getAttribute('data-gstin');
        if (opt.getAttribute('data-addr')) document.getElementById('mrl-addr').value = opt.getAttribute('data-addr');
      }
    };
    cafhMrlToggleType();
  };

  function injectNav() {
    try {
      var nav = document.querySelector('.side-nav');
      if (!nav || document.querySelector('[data-p="mrlmaker"]')) return;
      var wp = document.querySelector('[data-p="workpapers"]');
      var el = document.createElement('div');
      el.className = 'ni';
      el.setAttribute('data-p', 'mrlmaker');
      el.setAttribute('onclick', "nav('mrlmaker')");
      el.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>MRL Maker';
      if (wp && wp.parentNode) wp.parentNode.insertBefore(el, wp.nextSibling);
      else nav.appendChild(el);
    } catch (e) { console.warn('[mrl]', e); }
  }

  function patchNav() {
    if (window.__cafhMrlNavPatched) return;
    if (typeof window.nav !== 'function') return;
    window.__cafhMrlNavPatched = true;
    var _nav = window.nav;
    window.nav = function (p) {
      if (p === 'mrlmaker') {
        try {
          document.querySelectorAll('.ni').forEach(function (n) { n.classList.toggle('on', n.getAttribute('data-p') === p); });
        } catch (e) {}
        if (typeof window.lMrlMaker === 'function') window.lMrlMaker();
        return;
      }
      return _nav.apply(this, arguments);
    };
  }

  var obs = new MutationObserver(function () {
    injectNav();
    patchNav();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  injectNav();
  patchNav();
})();
