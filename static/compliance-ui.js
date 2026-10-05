/* CA FirmHub — compliance board helpers (additive, non-breaking) */
(function () {
  if (window.__cafhComplianceUI) return;
  window.__cafhComplianceUI = true;

  window.cafhSeedEnhanced = async function () {
    var fy = (window.FY || (typeof getCurFY === 'function' ? getCurFY() : '')) || '';
    fy = prompt('Financial year to seed (YYYY-YY)', fy);
    if (!fy) return;
    try {
      var r = await api('/api/compliance-calendar/seed-fy-enhanced', {
        method: 'POST',
        body: JSON.stringify({ financial_year: fy })
      });
      toast(r.message || 'Seeded', 'ok');
      if (typeof lCalendar === 'function') lCalendar();
    } catch (e) { toast(e.message, 'err'); }
  };

  window.cafhComplianceBoard = async function () {
    try {
      var d = await api('/api/compliance-calendar/board');
      var lines = [];
      lines.push('OVERDUE (' + (d.overdue || []).length + ')');
      (d.overdue || []).slice(0, 8).forEach(function (x) {
        lines.push('  • ' + x.due_date + ' — ' + x.title);
      });
      lines.push('');
      lines.push('THIS WEEK (' + (d.this_week || []).length + ')');
      (d.this_week || []).slice(0, 8).forEach(function (x) {
        lines.push('  • ' + x.due_date + ' — ' + x.title);
      });
      alert(lines.join('\n'));
    } catch (e) { toast(e.message, 'err'); }
  };

  window.cafhSetClientPacks = async function (clientId) {
    if (!clientId) return;
    var packs = prompt(
      'Comma-separated packs:\nGST_MONTHLY, GST_QRMP, TDS, ITR, ROC, PF_ESI',
      'GST_MONTHLY,TDS,ITR'
    );
    if (packs === null) return;
    var list = packs.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    try {
      await api('/api/compliance-calendar/client-packs/' + clientId, {
        method: 'PUT',
        body: JSON.stringify({ packs: list })
      });
      var fy = window.FY || (typeof getCurFY === 'function' ? getCurFY() : '');
      var r = await api('/api/compliance-calendar/generate-for-client', {
        method: 'POST',
        body: JSON.stringify({ client_id: clientId, financial_year: fy })
      });
      toast(r.message || 'Packs saved & calendar generated', 'ok');
    } catch (e) { toast(e.message, 'err'); }
  };

  // Add extra buttons on calendar page when it loads
  var obs = new MutationObserver(function () {
    var pa = document.getElementById('pa');
    if (!pa || pa.dataset.cafhComp) return;
    if (!(document.getElementById('pt') || {}).textContent) return;
    if (!(document.getElementById('pt').textContent || '').includes('Compliance Calendar')) return;
    pa.dataset.cafhComp = '1';
    var extra = document.createElement('span');
    extra.style.marginLeft = '8px';
    extra.innerHTML =
      '<button class="btn btn-o btn-xs" onclick="cafhSeedEnhanced()">⚡ Enhanced Seed</button> ' +
      '<button class="btn btn-o btn-xs" onclick="cafhComplianceBoard()">📋 Board</button>';
    pa.appendChild(extra);
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
})();
