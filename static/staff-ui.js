/* CA FirmHub — staff helpers: client packs + portal doc requests (additive) */
(function () {
  if (window.__cafhStaffUI) return;
  window.__cafhStaffUI = true;

  var PACKS = [
    { id: 'GST_MONTHLY', label: 'GST Monthly (GSTR-1/3B)' },
    { id: 'GST_QRMP', label: 'GST QRMP (quarterly)' },
    { id: 'TDS', label: 'TDS returns' },
    { id: 'ITR', label: 'Income tax / ITR' },
    { id: 'ROC', label: 'ROC (AOC-4 / MGT-7)' },
    { id: 'PF_ESI', label: 'PF / ESI monthly' }
  ];

  function fy() {
    return (window.FY || (typeof getCurFY === 'function' ? getCurFY() : '')) || '';
  }

  function clientName(id) {
    try {
      var c = (window.S && S.clients || []).find(function (x) { return x.id === id; });
      return c ? c.name : ('#' + id);
    } catch (e) { return '#' + id; }
  }

  function openModal(title, bodyHtml, footerHtml) {
    if (typeof oM === 'function') {
      oM(title, bodyHtml, footerHtml || '');
      return;
    }
    var old = document.getElementById('cafh-modal');
    if (old) old.remove();
    var wrap = document.createElement('div');
    wrap.id = 'cafh-modal';
    wrap.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px';
    wrap.innerHTML =
      '<div style="background:#fff;border-radius:12px;max-width:480px;width:100%;max-height:90vh;overflow:auto;box-shadow:0 20px 50px rgba(0,0,0,.25)">' +
      '<div style="padding:16px 18px;border-bottom:1px solid #E4EAF2;font-weight:700;color:#003366">' + title + '</div>' +
      '<div style="padding:16px 18px">' + bodyHtml + '</div>' +
      '<div style="padding:12px 18px;border-top:1px solid #E4EAF2;display:flex;gap:8px;justify-content:flex-end">' + (footerHtml || '') + '</div></div>';
    wrap.addEventListener('click', function (e) { if (e.target === wrap) wrap.remove(); });
    document.body.appendChild(wrap);
  }

  function closeModal() {
    if (typeof cM === 'function') cM();
    var m = document.getElementById('cafh-modal');
    if (m) m.remove();
  }

  window.cafhOpenPacks = async function (clientId) {
    var current = [];
    try {
      var d = await api('/api/compliance-calendar/client-packs/' + clientId);
      current = d.packs || [];
    } catch (e) { }

    var checks = PACKS.map(function (p) {
      var on = current.indexOf(p.id) >= 0;
      return '<label style="display:flex;align-items:center;gap:8px;margin:8px 0;font-size:13px;cursor:pointer">' +
        '<input type="checkbox" class="cafh-pack" value="' + p.id + '" ' + (on ? 'checked' : '') + '>' +
        p.label + '</label>';
    }).join('');

    openModal(
      'Compliance packs — ' + clientName(clientId),
      '<p style="font-size:12px;color:#4A5568;margin-bottom:10px">Select services for this client, then generate calendar dates for the current FY.</p>' +
      checks +
      '<div class="fg" style="margin-top:12px"><label style="font-size:11px;font-weight:600">Financial year</label>' +
      '<input id="cafh-pack-fy" value="' + fy() + '" placeholder="2025-26" style="width:100%;padding:8px;margin-top:4px;border:1.5px solid #D1DAEA;border-radius:6px"></div>',
      '<button class="btn btn-o" onclick="(window.cM?cM():document.getElementById(\'cafh-modal\')?.remove())">Cancel</button>' +
      '<button class="btn btn-p" onclick="cafhSavePacks(' + clientId + ')">Save &amp; generate</button>'
    );
  };

  window.cafhSavePacks = async function (clientId) {
    var boxes = document.querySelectorAll('.cafh-pack:checked');
    var list = Array.prototype.map.call(boxes, function (b) { return b.value; });
    var year = (document.getElementById('cafh-pack-fy') || {}).value || fy();
    try {
      await api('/api/compliance-calendar/client-packs/' + clientId, {
        method: 'PUT',
        body: JSON.stringify({ packs: list })
      });
      if (list.length && year) {
        var r = await api('/api/compliance-calendar/generate-for-client', {
          method: 'POST',
          body: JSON.stringify({ client_id: clientId, financial_year: year })
        });
        toast(r.message || 'Packs saved', 'ok');
      } else {
        toast('Packs saved (no dates generated)', 'ok');
      }
      closeModal();
    } catch (e) { toast(e.message, 'err'); }
  };

  window.cafhRequestDocs = function (clientId) {
    openModal(
      'Request documents — ' + clientName(clientId),
      '<p style="font-size:12px;color:#4A5568;margin-bottom:10px">Client will see this on their portal and can upload files.</p>' +
      '<div class="fg"><label style="font-size:11px;font-weight:600">Title *</label>' +
      '<input id="cafh-dr-title" placeholder="e.g. Bank statements FY 2025-26" style="width:100%;padding:8px;margin-top:4px;border:1.5px solid #D1DAEA;border-radius:6px"></div>' +
      '<div class="fg" style="margin-top:10px"><label style="font-size:11px;font-weight:600">Description</label>' +
      '<textarea id="cafh-dr-desc" rows="3" placeholder="What to upload and for which period" style="width:100%;padding:8px;margin-top:4px;border:1.5px solid #D1DAEA;border-radius:6px"></textarea></div>' +
      '<div class="fg" style="margin-top:10px"><label style="font-size:11px;font-weight:600">Due date</label>' +
      '<input type="date" id="cafh-dr-due" style="width:100%;padding:8px;margin-top:4px;border:1.5px solid #D1DAEA;border-radius:6px"></div>',
      '<button class="btn btn-o" onclick="(window.cM?cM():document.getElementById(\'cafh-modal\')?.remove())">Cancel</button>' +
      '<button class="btn btn-p" onclick="cafhSendDocRequest(' + clientId + ')">Send request</button>'
    );
  };

  window.cafhSendDocRequest = async function (clientId) {
    var title = (document.getElementById('cafh-dr-title') || {}).value || '';
    title = title.trim();
    if (!title) { toast('Title required', 'err'); return; }
    var body = {
      client_id: clientId,
      title: title,
      description: ((document.getElementById('cafh-dr-desc') || {}).value || '').trim(),
      due_date: (document.getElementById('cafh-dr-due') || {}).value || null
    };
    try {
      await api('/api/portal/admin/doc-requests', { method: 'POST', body: JSON.stringify(body) });
      toast('Document request sent to client portal', 'ok');
      closeModal();
    } catch (e) { toast(e.message, 'err'); }
  };

  function injectClientActions() {
    var pt = document.getElementById('pt');
    if (!pt || !(pt.textContent || '').match(/Client/i)) return;
    var rows = document.querySelectorAll('#pb table.dt tbody tr');
    if (!rows.length) return;
    rows.forEach(function (tr) {
      if (tr.dataset.cafhStaff) return;
      var actions = tr.querySelector('td:last-child');
      if (!actions) return;
      var editBtn = actions.querySelector('button[onclick*="cfm("]');
      if (!editBtn) return;
      var m = (editBtn.getAttribute('onclick') || '').match(/cfm\((\d+)\)/);
      if (!m) return;
      var id = m[1];
      tr.dataset.cafhStaff = '1';
      var span = document.createElement('span');
      span.innerHTML =
        ' <button class="btn btn-xs btn-o" title="Compliance packs" onclick="cafhOpenPacks(' + id + ')">📦 Packs</button>' +
        ' <button class="btn btn-xs btn-o" title="Request documents via portal" onclick="cafhRequestDocs(' + id + ')">📎 Request docs</button>';
      actions.appendChild(span);
    });
  }

  function injectPortalLink() {
    if (document.getElementById('cafh-portal-link')) return;
    var ph = document.querySelector('.ph-right') || document.querySelector('.ph-left');
    if (!ph) return;
    var a = document.createElement('a');
    a.id = 'cafh-portal-link';
    a.href = '/portal';
    a.target = '_blank';
    a.textContent = 'Client Portal';
    a.style.cssText = 'font-size:12px;font-weight:600;color:#003366;margin-right:10px;text-decoration:none;padding:4px 8px;border:1px solid #D1DAEA;border-radius:6px;background:#fff';
    ph.insertBefore(a, ph.firstChild);
  }

  var obs = new MutationObserver(function () {
    injectClientActions();
    injectPortalLink();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      injectClientActions();
      injectPortalLink();
    });
  } else {
    injectClientActions();
    injectPortalLink();
  }
})();
