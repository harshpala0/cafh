/* CA FirmHub — staff helpers: client packs + portal doc requests (additive)
   Designed & Built by Harsh Pala
*/
(function () {
  if (window.__cafhStaffUI) return;
  window.__cafhStaffUI = true;

  var PACKS = [
    { id: 'GST_MONTHLY', label: 'GST Monthly (GSTR-1/3B)' },
    { id: 'GST_QRMP', label: 'GST QRMP' },
    { id: 'TDS', label: 'TDS returns' },
    { id: 'ITR', label: 'ITR non-audit (31 Jul)' },
    { id: 'TAX_AUDIT', label: 'Tax audit report + ITR (Sep/Oct)' },
    { id: 'ROC', label: 'ROC (AOC-4 / MGT-7)' },
    { id: 'PF_ESI', label: 'PF / ESI' }
  ];

  function clientName(id) {
    try {
      var c = (window.S && S.clients || []).find(function (x) { return x.id == id; });
      return c ? c.name : ('Client #' + id);
    } catch (e) { return 'Client #' + id; }
  }

  function yearNow() {
    try {
      if (typeof FY === 'string' && FY) return FY;
      if (window.FY) return window.FY;
    } catch (e) {}
    var d = new Date();
    var y = d.getMonth() >= 3 ? d.getFullYear() : d.getFullYear() - 1;
    return y + '-' + String(y + 1).slice(-2);
  }

  window.cafhOpenPacks = async function (clientId) {
    var current = [];
    try {
      var d = await api('/api/compliance-calendar/client-packs/' + clientId);
      current = d.packs || [];
    } catch (e) {}
    var html = '<div style="font-size:12px;color:var(--text2);margin-bottom:10px">'
      + 'Select services for this client. <strong>ITR</strong> = non-audit return (31 Jul). '
      + '<strong>TAX_AUDIT</strong> = tax audit report (30 Sep) + audited ITR (31 Oct).'
      + '</div><div style="display:grid;gap:8px">';
    PACKS.forEach(function (p) {
      var on = current.indexOf(p.id) >= 0;
      html += '<label style="display:flex;align-items:center;gap:8px;font-size:13px">'
        + '<input type="checkbox" class="cafh-pack-cb" value="' + p.id + '" ' + (on ? 'checked' : '') + '>'
        + p.label + '</label>';
    });
    html += '</div><div style="margin-top:14px;display:flex;gap:8px;flex-wrap:wrap">'
      + '<button class="btn btn-p" onclick="cafhSavePacks(' + clientId + ')">Save & generate</button>'
      + '<button class="btn btn-o" onclick="cM()">Close</button></div>';
    try {
      openModal('Compliance packs — ' + clientName(clientId), html);
    } catch (e) {
      document.getElementById('pb').innerHTML = '<div class="card"><div class="card-b">' + html + '</div></div>';
    }
  };

  window.cafhSavePacks = async function (clientId) {
    var list = [];
    document.querySelectorAll('.cafh-pack-cb:checked').forEach(function (c) { list.push(c.value); });
    try {
      await api('/api/compliance-calendar/client-packs/' + clientId, {
        method: 'PUT',
        body: JSON.stringify({ packs: list })
      });
      if (list.length) {
        var year = yearNow();
        await api('/api/compliance-calendar/generate-for-client', {
          method: 'POST',
          body: JSON.stringify({ client_id: clientId, financial_year: year, packs: list })
        });
        toast('Packs saved & calendar generated for ' + year, 'ok');
      } else {
        toast('Packs cleared (no services selected)', 'ok');
      }
      try { cM(); } catch (e) {}
    } catch (e) {
      toast(e.message || 'Failed', 'err');
    }
  };

  function injectPackButtons() {
    try {
      if (!document.querySelector('[data-p="clients"].on') && !(location.hash || '').match(/clients/i)) {
        // still try on clients table when present
      }
      document.querySelectorAll('table.dt tbody tr').forEach(function (tr) {
        var btn = tr.querySelector('button[onclick*="cfm("]');
        if (!btn) return;
        var m = (btn.getAttribute('onclick') || '').match(/cfm\((\d+)\)/);
        if (!m) return;
        var id = m[1];
        if (tr.querySelector('[data-cafh-packs]')) return;
        var td = btn.parentElement;
        if (!td) return;
        var span = document.createElement('span');
        span.setAttribute('data-cafh-packs', '1');
        span.innerHTML = ' <button class="btn btn-xs btn-o" title="Compliance packs" onclick="cafhOpenPacks(' + id + ')">📦 Packs</button>';
        td.appendChild(span);
      });
    } catch (e) {}
  }

  var obs = new MutationObserver(function () { injectPackButtons(); });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  setTimeout(injectPackButtons, 500);
})();
