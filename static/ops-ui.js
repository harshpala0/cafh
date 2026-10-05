/* CA FirmHub — Ops UI: reminders, receivables, portal inbox (additive) */
(function () {
  if (window.__cafhOpsUI) return;
  window.__cafhOpsUI = true;

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
    wrap.innerHTML = '<div style="background:#fff;border-radius:12px;max-width:640px;width:100%;max-height:90vh;overflow:auto;box-shadow:0 20px 50px rgba(0,0,0,.25)">' +
      '<div style="padding:16px 18px;border-bottom:1px solid #E4EAF2;font-weight:700;color:#003366">' + title + '</div>' +
      '<div style="padding:16px 18px">' + bodyHtml + '</div>' +
      '<div style="padding:12px 18px;border-top:1px solid #E4EAF2;display:flex;gap:8px;justify-content:flex-end">' + (footerHtml || '') + '</div></div>';
    wrap.onclick = function (e) { if (e.target === wrap) wrap.remove(); };
    document.body.appendChild(wrap);
  }
  function closeModal() {
    if (typeof cM === 'function') try { cM(); } catch (e) {}
    var m = document.getElementById('cafh-modal');
    if (m) m.remove();
  }
  function money(n) {
    return '₹' + Number(n || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 });
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
    });
  }

  window.cafhShowReminders = async function () {
    try {
      var d = await api('/api/ops/reminders');
      var items = d.items || [];
      var html = '<p style="font-size:12px;color:#4A5568;margin-bottom:12px">Compliance due, open doc requests, and unpaid fees.</p>';
      if (!items.length) {
        html += '<div style="text-align:center;padding:24px;color:#718096">All clear — nothing urgent.</div>';
      } else {
        html += items.map(function (it) {
          var color = it.severity === 'high' ? '#C53030' : it.severity === 'warn' ? '#C05621' : it.severity === 'ok' ? '#1E7E44' : '#1A5699';
          return '<div style="padding:10px 0;border-bottom:1px solid #EEF2F7;display:flex;gap:10px;align-items:flex-start">' +
            '<span style="font-size:10px;font-weight:700;color:' + color + ';text-transform:uppercase;min-width:72px">' + esc(it.type) + '</span>' +
            '<div style="flex:1"><div style="font-weight:600;font-size:13px">' + esc(it.title) + '</div>' +
            '<div style="font-size:12px;color:#718096">' + esc(it.meta || '') + (it.due_date ? (' · ' + esc(it.due_date)) : '') + '</div></div></div>';
        }).join('');
      }
      openModal(
        'Reminders (' + (d.counts && d.counts.total || 0) + ')',
        html,
        '<button class="btn btn-o" onclick="(window.cM?cM():document.getElementById(\'cafh-modal\')?.remove())">Close</button>'
      );
    } catch (e) { toast(e.message, 'err'); }
  };

  window.cafhShowReceivables = async function () {
    try {
      var d = await api('/api/ops/receivables');
      var labels = [
        ['current', 'Not due / today'],
        ['d1_30', '1–30 days'],
        ['d31_60', '31–60 days'],
        ['d61_90', '61–90 days'],
        ['d90_plus', '90+ days']
      ];
      var summary = '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(100px,1fr));gap:8px;margin-bottom:14px">' +
        '<div style="background:#EBF4FF;padding:10px;border-radius:8px;text-align:center"><div style="font-size:16px;font-weight:700;color:#003366">' + money(d.total_outstanding) + '</div><div style="font-size:10px;color:#4A5568">TOTAL OS</div></div>' +
        labels.map(function (L) {
          return '<div style="background:#F7F9FC;padding:10px;border-radius:8px;text-align:center"><div style="font-size:14px;font-weight:700">' + money(d.amounts[L[0]]) + '</div><div style="font-size:10px;color:#718096">' + L[1] + '</div></div>';
        }).join('') + '</div>';

      var rows = (d.all || []).slice(0, 40).map(function (r) {
        return '<div style="padding:8px 0;border-bottom:1px solid #EEF2F7;font-size:13px;display:flex;justify-content:space-between;gap:8px">' +
          '<div><strong>' + esc(r.client_name) + '</strong> · ' + esc(r.invoice_no) +
          '<div style="font-size:11px;color:#718096">' + esc(r.invoice_date) + ' · ' + (r.age_days || 0) + 'd · ' + esc(r.payment_status) + '</div></div>' +
          '<div style="font-weight:700;white-space:nowrap">' + money(r.total_amount) + '</div></div>';
      }).join('') || '<div style="text-align:center;padding:20px;color:#718096">No outstanding invoices.</div>';

      openModal('Receivables', summary + rows,
        '<button class="btn btn-o" onclick="(window.cM?cM():document.getElementById(\'cafh-modal\')?.remove())">Close</button>');
    } catch (e) { toast(e.message, 'err'); }
  };

  window.cafhShowPortalInbox = async function () {
    try {
      var rows = await api('/api/ops/portal-inbox');
      if (!rows.length) {
        openModal('Portal inbox', '<div style="text-align:center;padding:24px;color:#718096">No document requests yet.<br>Use <strong>Request docs</strong> on a client.</div>',
          '<button class="btn btn-o" onclick="(window.cM?cM():document.getElementById(\'cafh-modal\')?.remove())">Close</button>');
        return;
      }
      var html = rows.map(function (r) {
        var badge = r.status === 'Submitted' ? '#1E7E44' : r.status === 'Open' ? '#C05621' : '#718096';
        return '<div style="padding:10px 0;border-bottom:1px solid #EEF2F7">' +
          '<div style="display:flex;justify-content:space-between;gap:8px;align-items:center">' +
          '<div style="font-weight:600">' + esc(r.title) + '</div>' +
          '<span style="font-size:11px;font-weight:700;color:' + badge + '">' + esc(r.status) + '</span></div>' +
          '<div style="font-size:12px;color:#718096">' + esc(r.client_name) +
          (r.due_date ? (' · Due ' + esc(r.due_date)) : '') +
          ' · ' + (r.file_count || 0) + ' file(s)</div>' +
          '<div style="margin-top:6px">' +
          '<button class="btn btn-xs btn-o" onclick="cafhViewPortalFiles(' + r.id + ')">View files</button> ' +
          (r.status !== 'Closed' ? '<button class="btn btn-xs btn-o" onclick="cafhClosePortalReq(' + r.id + ')">Close</button>' : '') +
          '</div></div>';
      }).join('');
      openModal('Portal inbox', html,
        '<button class="btn btn-o" onclick="(window.cM?cM():document.getElementById(\'cafh-modal\')?.remove())">Close</button>');
    } catch (e) { toast(e.message, 'err'); }
  };

  window.cafhViewPortalFiles = async function (rid) {
    try {
      var d = await api('/api/ops/portal-inbox/' + rid + '/files');
      var files = d.files || [];
      var html = files.length ? files.map(function (f) {
        var link = f.download_url
          ? ('<a href="' + esc(f.download_url) + '" target="_blank" style="color:#004080;font-weight:600">Download</a>')
          : '<span style="color:#718096;font-size:12px">Stored on cloud — open from storage</span>';
        return '<div style="padding:8px 0;border-bottom:1px solid #EEF2F7;font-size:13px">' +
          '<strong>' + esc(f.original_filename) + '</strong>' +
          '<div style="font-size:11px;color:#718096">' + esc(f.uploaded_at) +
          (f.note ? (' · ' + esc(f.note)) : '') + '</div>' + link + '</div>';
      }).join('') : '<div style="padding:16px;color:#718096;text-align:center">No files uploaded yet.</div>';
      openModal('Files — request #' + rid, html,
        '<button class="btn btn-o" onclick="cafhShowPortalInbox()">Back</button>');
    } catch (e) { toast(e.message, 'err'); }
  };

  window.cafhClosePortalReq = async function (rid) {
    if (!confirm('Mark this document request as Closed?')) return;
    try {
      await api('/api/ops/portal-inbox/' + rid + '/close', { method: 'POST', body: '{}' });
      toast('Closed', 'ok');
      cafhShowPortalInbox();
    } catch (e) { toast(e.message, 'err'); }
  };

  function injectOpsButtons() {
    var pa = document.getElementById('pa');
    var pt = document.getElementById('pt');
    if (!pa || !pt) return;
    var title = pt.textContent || '';
    if (title.match(/Dashboard/i) && !pa.dataset.cafhOps) {
      pa.dataset.cafhOps = '1';
      var span = document.createElement('span');
      span.style.marginLeft = '6px';
      span.innerHTML =
        '<button class="btn btn-o btn-xs" onclick="cafhShowReminders()">🔔 Reminders</button> ' +
        '<button class="btn btn-o btn-xs" onclick="cafhShowReceivables()">💰 Receivables</button> ' +
        '<button class="btn btn-o btn-xs" onclick="cafhShowPortalInbox()">📥 Portal inbox</button>';
      pa.appendChild(span);
    }
  }

  var obs = new MutationObserver(injectOpsButtons);
  obs.observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState !== 'loading') injectOpsButtons();
  else document.addEventListener('DOMContentLoaded', injectOpsButtons);
})();
