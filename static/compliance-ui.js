/* CA FirmHub — compliance board + bifurcated calendar + import packs
   Designed & Built by Harsh Pala
*/
(function () {
  if (window.__cafhComplianceUI) return;
  window.__cafhComplianceUI = true;

  function getSelectedFY() {
    try {
      if (typeof FY === 'string' && FY) return FY;
      if (window.FY) return window.FY;
    } catch (e) {}
    try {
      var el = document.getElementById('fy-label') || document.querySelector('[data-fy], .fy-label');
      if (el && el.textContent) {
        var m = el.textContent.match(/(\d{4}\s*[-–]\s*\d{2,4})/);
        if (m) return m[1].replace(/\s/g, '').replace('–', '-');
      }
    } catch (e) {}
    var d = new Date();
    var y = d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1;
    return y + '-' + String(y + 1).slice(-2);
  }

  function injectImportPacksUI() {
    try {
      var fileInput = document.querySelector('input[type="file"]');
      if (!fileInput || document.getElementById('cafh-imp-packs')) return;
      var box = document.createElement('div');
      box.id = 'cafh-imp-packs';
      box.style.cssText = 'margin:12px 0;padding:12px;border:1px solid #e2e8f0;border-radius:8px;background:#f8fafc';
      box.innerHTML =
        '<div style="font-size:12px;font-weight:700;color:#003366;margin-bottom:6px">Default Compliance Packs (optional)</div>' +
        '<div style="font-size:11px;color:#718096;margin-bottom:8px">Applied when Excel <strong>Compliance Packs</strong> cell is blank. Excel values always win per row. Use <strong>Tax Audit Applicable</strong> column (Y/N) on the template for ITR vs tax-audit due dates.</div>' +
        '<div style="display:flex;flex-wrap:wrap;gap:10px">' +
        ['GST_MONTHLY|GST Monthly','GST_QRMP|GST QRMP','TDS|TDS','ITR|ITR non-audit (31 Jul)','TAX_AUDIT|Tax audit + ITR audit (Sep/Oct)','ROC|ROC','PF_ESI|PF / ESI'].map(function (x) {
          var p = x.split('|');
          return '<label style="font-size:12px;display:flex;align-items:center;gap:4px"><input type="checkbox" class="cafh-imp-pack" value="' + p[0] + '"> ' + p[1] + '</label>';
        }).join('') +
        '</div>';
      fileInput.parentNode.insertBefore(box, fileInput.nextSibling);
    } catch (e) {}
  }

  function patchRunImport() {
    if (window.__cafhImpPatched) return;
    window.__cafhImpPatched = true;
    var orig = window.runImport;
    if (typeof orig !== 'function') return;
    window.runImport = async function () {
      var fileInput = document.querySelector('#impFile, input[type="file"]');
      var file = fileInput && fileInput.files && fileInput.files[0];
      if (!file) { toast('Choose a file', 'err'); return; }
      var fd = new FormData();
      fd.append('file', file);
      fd.append('fy', getSelectedFY());
      var packs = [];
      document.querySelectorAll('.cafh-imp-pack:checked').forEach(function (c) { packs.push(c.value); });
      if (packs.length) fd.append('default_packs', packs.join(','));
      try {
        var r = await fetch('/api/clients/import-excel', {
          method: 'POST',
          headers: { Authorization: 'Bearer ' + (typeof T !== 'undefined' ? T : localStorage.getItem('at') || '') },
          body: fd
        });
        var res = await r.json().catch(function () { return {}; });
        if (!r.ok) throw new Error(res.detail || res.message || 'Import failed');
        var lines = [];
        if ('packs_applied' in res || 'calendar_items_added' in res) {
          lines.push('<p><strong>' + (res.packs_applied || 0) + '</strong> client(s) got compliance packs; <strong>' + (res.calendar_items_added || 0) + '</strong> calendar item(s) added.</p>');
        }
        toast('Import complete', 'ok');
        try { cM(); } catch (e) {}
        try { if (typeof lClients === 'function') lClients(); } catch (e) {}
      } catch (e) {
        toast(e.message || 'Import failed', 'err');
      }
    };
  }

  var obs = new MutationObserver(function () {
    injectImportPacksUI();
    patchRunImport();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  setTimeout(injectImportPacksUI, 50);
  setTimeout(injectImportPacksUI, 250);
  setTimeout(patchRunImport, 100);
})();
