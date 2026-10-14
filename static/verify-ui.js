/* CA FirmHub — Data Verify UI (Designed & Built by Harsh Pala)
   Inward docs vs Client vs Engagement + Excel export
*/
(function () {
  if (window.__cafhVerifyUI) return;
  window.__cafhVerifyUI = true;

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
    wrap.innerHTML = '<div style="background:#fff;border-radius:12px;max-width:900px;width:100%;max-height:90vh;overflow:auto;box-shadow:0 20px 50px rgba(0,0,0,.25)">' +
      '<div style="padding:16px 18px;border-bottom:1px solid #E4EAF2;font-weight:700;color:#003366">' + title + '</div>' +
      '<div style="padding:16px 18px">' + bodyHtml + '</div>' +
      '<div style="padding:12px 18px;border-top:1px solid #E4EAF2;display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap">' + (footerHtml || '') + '</div></div>';
    wrap.onclick = function (e) { if (e.target === wrap) wrap.remove(); };
    document.body.appendChild(wrap);
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
    });
  }
  function statusBadge(st) {
    var colors = {
      'Received': '#276749',
      'Partial': '#975A16',
      'Pending': '#C53030',
      'No data': '#718096',
      'Other': '#4A5568'
    };
    var bg = {
      'Received': '#C6F6D5',
      'Partial': '#FEFCBF',
      'Pending': '#FED7D7',
      'No data': '#E2E8F0',
      'Other': '#EDF2F7'
    };
    return '<span style="display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;color:' +
      (colors[st] || '#4A5568') + ';background:' + (bg[st] || '#EDF2F7') + '">' + esc(st) + '</span>';
  }
  function currentFY() {
    try {
      if (typeof FY !== 'undefined' && FY) return FY;
    } catch (e) {}
    var el = document.getElementById('fy-select') || document.querySelector('[data-fy]');
    if (el && el.value) return el.value;
    return '';
  }

  window.cafhShowDataVerify = async function () {
    var fy = currentFY();
    var q = fy ? ('?fy=' + encodeURIComponent(fy)) : '';
    var data;
    try {
      data = await api('/api/ops/verify/summary' + q);
    } catch (e) {
      toast(e.message || 'Could not load verification', 'err');
      return;
    }
    var t = data.totals || {};
    var rows = data.rows || [];
    var summary =
      '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:14px">' +
      '<div style="background:#EBF4FF;padding:8px 12px;border-radius:8px;font-size:12px"><strong>' + (t.engagements || 0) + '</strong> engagements</div>' +
      '<div style="background:#C6F6D5;padding:8px 12px;border-radius:8px;font-size:12px"><strong>' + (t.status_received || 0) + '</strong> received</div>' +
      '<div style="background:#FEFCBF;padding:8px 12px;border-radius:8px;font-size:12px"><strong>' + (t.status_partial || 0) + '</strong> partial</div>' +
      '<div style="background:#FED7D7;padding:8px 12px;border-radius:8px;font-size:12px"><strong>' + (t.status_pending || 0) + '</strong> pending</div>' +
      '<div style="background:#E2E8F0;padding:8px 12px;border-radius:8px;font-size:12px"><strong>' + (t.status_none || 0) + '</strong> no data</div>' +
      '<div style="background:#F7FAFC;padding:8px 12px;border-radius:8px;font-size:12px">Inward docs: <strong>' + (t.inward_total || 0) + '</strong></div>' +
      '</div>';

    var table;
    if (!rows.length) {
      table = '<p style="color:#718096;text-align:center;padding:24px">No engagements found for this FY. Create engagements under Engagements, and log Inward docs in Doc Register.</p>';
    } else {
      table = '<div style="overflow:auto;max-height:50vh"><table class="dt" style="width:100%;font-size:12px">' +
        '<thead><tr>' +
        '<th>Client</th><th>Engagement</th><th>Type</th><th>Inward</th><th>Received</th><th>Pending</th><th>Last date</th><th>Status</th>' +
        '</tr></thead><tbody>' +
        rows.map(function (r) {
          return '<tr>' +
            '<td><strong>' + esc(r.client_name) + '</strong></td>' +
            '<td>' + esc(r.engagement_title) + '</td>' +
            '<td>' + esc(r.engagement_type) + '</td>' +
            '<td style="text-align:center">' + (r.inward_count || 0) + '</td>' +
            '<td style="text-align:center">' + (r.received_count || 0) + '</td>' +
            '<td style="text-align:center">' + (r.pending_count || 0) + '</td>' +
            '<td>' + esc(r.last_inward_date || '—') + '</td>' +
            '<td>' + statusBadge(r.verify_status) + '</td>' +
            '</tr>';
        }).join('') +
        '</tbody></table></div>';
    }

    openModal(
      'Data Verify — Inward vs Client vs Engagement' + (data.fy ? (' (FY ' + esc(data.fy) + ')') : ''),
      '<p style="font-size:12px;color:#4A5568;margin-bottom:10px">Checks <strong>Doc Register (Inward)</strong> against each client engagement. Export Excel to analyse received vs pending.</p>' +
      summary + table +
      '<p style="font-size:10px;color:#A0AEC0;margin-top:10px">Module: Data Verify · Designed &amp; Built by Harsh Pala</p>',
      '<button class="btn btn-o" onclick="(window.cM?cM():document.getElementById(\'cafh-modal\')?.remove())">Close</button>' +
      '<button class="btn btn-p" onclick="cafhExportDataVerify()">📥 Export Excel</button>'
    );
  };

  window.cafhExportDataVerify = function () {
    var fy = currentFY();
    var q = fy ? ('?fy=' + encodeURIComponent(fy)) : '';
    var token = (typeof T !== 'undefined' && T) ? T : (localStorage.getItem('at') || '');
    fetch('/api/ops/verify/export' + q, {
      headers: { 'Authorization': 'Bearer ' + token }
    }).then(function (r) {
      if (!r.ok) return r.json().then(function (d) { throw new Error(d.detail || 'Export failed'); });
      return r.blob();
    }).then(function (blob) {
      var a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'CA_FirmHub_Data_Verify_' + (fy || 'all') + '.xlsx';
      document.body.appendChild(a);
      a.click();
      a.remove();
      toast('Excel downloaded', 'ok');
    }).catch(function (e) {
      toast(e.message || 'Export failed', 'err');
    });
  };

  function injectVerifyBtn() {
    var pa = document.getElementById('pa');
    var pt = document.getElementById('pt');
    if (!pa || !pt) return;
    if (!(pt.textContent || '').match(/Dashboard/i)) return;
    if (document.getElementById('cafh-verify-btn')) return;
    var s = document.createElement('span');
    s.id = 'cafh-verify-btn';
    s.style.marginLeft = '6px';
    s.innerHTML = '<button class="btn btn-o btn-xs" onclick="cafhShowDataVerify()">✅ Data Verify</button>';
    pa.appendChild(s);

    ['cafh-msg-btns', 'cafh-notify-btns'].forEach(function (id) {
      var el = document.getElementById(id);
      if (el) el.style.display = 'none';
    });
    pa.querySelectorAll('button').forEach(function (b) {
      var t = (b.textContent || '').toLowerCase();
      if (t.indexOf('email digest') >= 0 || t.indexOf('whatsapp') >= 0 ||
          t.indexOf('my contact') >= 0 || t.indexOf('message clients') >= 0) {
        b.style.display = 'none';
      }
    });
  }

  var obs = new MutationObserver(injectVerifyBtn);
  obs.observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState !== 'loading') injectVerifyBtn();
  else document.addEventListener('DOMContentLoaded', injectVerifyBtn);
})();
