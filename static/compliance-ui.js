/* CA FirmHub — compliance board + bifurcated statutory calendar
   Designed & Built by Harsh Pala
   Additive: does not remove core calendar features.
*/
(function () {
  if (window.__cafhComplianceUI) return;
  window.__cafhComplianceUI = true;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&', '<': '<', '>': '>', '"': '"', "'": '&#39;' })[c];
    });
  }

  window.cafhSeedEnhanced = async function () {
    var fy = window.FY || (typeof getCurFY === 'function' ? getCurFY() : '') || '';
    fy = prompt('Financial year to seed (firm-level deadlines)', fy || '2026-27');
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

  function rowHtml(i) {
    var today = new Date().toISOString().split('T')[0];
    var colors = (typeof CAL_COLORS !== 'undefined' && CAL_COLORS) ? CAL_COLORS : {};
    var col = colors[i.category] || '#6B7280';
    var days = Math.round((new Date(i.due_date) - new Date(today)) / 86400000);
    var daysStr = i.status === 'Completed' ? 'Done'
      : days < 0 ? '<span style="color:var(--err)">' + Math.abs(days) + 'd overdue</span>'
      : days === 0 ? '<span style="color:var(--warn)">Today</span>'
      : '<span style="color:' + (days <= 7 ? 'var(--warn)' : 'var(--navy)') + '">' + days + 'd</span>';
    return '<tr data-bucket="' + esc(i.bucket || '') + '">' +
      '<td><span style="background:' + col + '22;color:' + col + ';padding:2px 8px;border-radius:12px;font-size:12px;font-weight:600">' +
      esc(i.category || '') + '</span></td>' +
      '<td><strong>' + esc(i.title) + '</strong>' +
      (i.is_recurring ? ' <span style="font-size:10px;color:var(--text2)">↻</span>' : '') + '</td>' +
      '<td>' + esc(i.due_date) + '</td>' +
      '<td style="color:var(--text2);font-size:12px">' + esc(i.financial_year || '-') + '</td>' +
      '<td>' + daysStr + '</td>' +
      '<td><select style="font-size:12px;padding:2px 6px;border:1px solid var(--border);border-radius:4px" ' +
      'onchange="updCalStatus(' + i.id + ',this.value)">' +
      '<option ' + (i.status === 'Upcoming' ? 'selected' : '') + '>Upcoming</option>' +
      '<option ' + (i.status === 'Completed' ? 'selected' : '') + '>Completed</option>' +
      '<option ' + (i.status === 'Missed' ? 'selected' : '') + '>Missed</option></select></td>' +
      '<td style="white-space:nowrap">' +
      '<button class="btn btn-xs btn-o" onclick="calFm(' + i.id + ')">Edit</button> ' +
      '<button class="btn btn-xs btn-err" onclick="dlCal(' + i.id + ')">Del</button></td></tr>';
  }

  function sectionTable(title, subtitle, items, accent) {
    var body = items.length
      ? items.map(rowHtml).join('')
      : '<tr><td colspan="7" style="text-align:center;padding:18px;color:var(--text2)">No items in this section.</td></tr>';
    return '<div class="card" style="margin-bottom:16px;border-top:3px solid ' + accent + '">' +
      '<div class="card-h" style="display:flex;flex-wrap:wrap;gap:8px;align-items:baseline;justify-content:space-between">' +
      '<div><span style="color:' + accent + '">' + esc(title) + '</span>' +
      '<div style="font-size:12px;font-weight:400;color:var(--text2);margin-top:2px">' + esc(subtitle) + '</div></div>' +
      '<span style="font-size:12px;color:var(--text2)">' + items.length + ' item(s)</span></div>' +
      '<div class="card-b" style="overflow-x:auto;padding:0">' +
      '<table class="dt"><thead><tr>' +
      '<th>Category</th><th>Title</th><th>Due Date</th><th>FY Tag</th><th>Countdown</th><th>Status</th><th></th>' +
      '</tr></thead><tbody>' + body + '</tbody></table></div></div>';
  }

  window.cafhRenderBifurcatedCalendar = async function () {
    var fy = window.FY || (typeof getCurFY === 'function' ? getCurFY() : '') || '';
    if (!fy) return;
    var pb = document.getElementById('pb');
    if (!pb) return;
    try {
      var d = await api('/api/compliance-calendar/bifurcated?fy=' + encodeURIComponent(fy));
      window.__cafhBifurcated = d;
      var prior = d.prior_fy_due_in_window || [];
      var current = d.current_fy || [];
      var other = d.other_in_window || [];
      if (typeof S !== 'undefined') {
        S.compliance = prior.concat(current).concat(other);
      }
      var banner =
        '<div style="margin-bottom:14px;padding:12px 14px;background:#EBF4FF;border-radius:8px;font-size:13px;color:#1A365D">' +
        '<strong>Bifurcated view for FY ' + esc(d.selected_fy) + '</strong>' +
        ' <span style="color:#4A5568">(window ' + esc(d.window_start) + ' → ' + esc(d.window_end) + ')</span>' +
        '<div style="font-size:12px;margin-top:4px;color:#4A5568">' +
        'Section 1: obligations of <strong>FY ' + esc(d.prior_fy) + '</strong> whose due dates fall in this FY. ' +
        'Section 2: obligations of <strong>FY ' + esc(d.selected_fy) + '</strong> due in this FY. ' +
        'Next year the same pattern continues automatically.</div></div>';
      var html = banner;
      html += sectionTable(
        (d.labels && d.labels.prior) || ('FY ' + d.prior_fy + ' due in FY ' + d.selected_fy),
        'Carry-forward / prior-year filings due during ' + d.selected_fy,
        prior, '#C05621'
      );
      html += sectionTable(
        (d.labels && d.labels.current) || ('FY ' + d.selected_fy + ' due in FY ' + d.selected_fy),
        'Current-year compliance due during ' + d.selected_fy,
        current, '#003366'
      );
      if (other.length) {
        html += sectionTable('Other items due in this window',
          'Tagged with a different FY but due in this window', other, '#718096');
      }
      var host = document.getElementById('cafh-bifurcated-host');
      if (!host) {
        host = document.createElement('div');
        host.id = 'cafh-bifurcated-host';
        var tables = pb.querySelectorAll('.card');
        var replaced = false;
        tables.forEach(function (card) {
          if (replaced) return;
          if (card.querySelector('#cal-tbody, table.dt tbody')) {
            card.style.display = 'none';
            card.parentNode.insertBefore(host, card.nextSibling);
            replaced = true;
          }
        });
        if (!replaced) pb.appendChild(host);
      }
      host.innerHTML = html;
      host.style.display = '';
    } catch (e) {
      console.warn('[compliance-ui] bifurcated', e);
    }
  };

  function patchLCalendar() {
    if (window.__cafhCalPatched) return;
    if (typeof window.lCalendar !== 'function') return;
    window.__cafhCalPatched = true;
    var _lCalendar = window.lCalendar;
    window.lCalendar = async function () {
      await _lCalendar.apply(this, arguments);
      await cafhRenderBifurcatedCalendar();
    };
  }

  function patchFilterCal() {
    if (window.__cafhFilterPatched) return;
    if (typeof window.filterCal !== 'function') return;
    window.__cafhFilterPatched = true;
    var _filterCal = window.filterCal;
    window.filterCal = function () {
      _filterCal.apply(this, arguments);
      var d = window.__cafhBifurcated;
      if (!d) return;
      var cat = (document.getElementById('cal-cat-f') || {}).value || '';
      var st = (document.getElementById('cal-status-f') || {}).value || '';
      function match(i) {
        if (cat && i.category !== cat) return false;
        if (st && i.status !== st) return false;
        return true;
      }
      var prior = (d.prior_fy_due_in_window || []).filter(match);
      var current = (d.current_fy || []).filter(match);
      var other = (d.other_in_window || []).filter(match);
      var host = document.getElementById('cafh-bifurcated-host');
      if (!host) return;
      var html = '<div style="margin-bottom:14px;padding:12px 14px;background:#EBF4FF;border-radius:8px;font-size:13px;color:#1A365D">' +
        '<strong>Bifurcated view for FY ' + esc(d.selected_fy) + '</strong></div>';
      html += sectionTable((d.labels && d.labels.prior) || 'Prior FY due in window', 'Filtered', prior, '#C05621');
      html += sectionTable((d.labels && d.labels.current) || 'Current FY due in window', 'Filtered', current, '#003366');
      if (other.length) html += sectionTable('Other', '', other, '#718096');
      host.innerHTML = html;
    };
  }

  var obs = new MutationObserver(function () {
    patchLCalendar();
    patchFilterCal();
    var pa = document.getElementById('pa');
    if (!pa || pa.dataset.cafhComp) return;
    var pt = document.getElementById('pt');
    if (!pt || !(pt.textContent || '').includes('Compliance Calendar')) return;
    pa.dataset.cafhComp = '1';
    var extra = document.createElement('span');
    extra.style.marginLeft = '8px';
    extra.innerHTML =
      '<button class="btn btn-o btn-xs" onclick="cafhSeedEnhanced()">⚡ Enhanced Seed</button> ' +
      '<button class="btn btn-o btn-xs" onclick="cafhComplianceBoard()">📋 Board</button> ' +
      '<button class="btn btn-o btn-xs" onclick="cafhRenderBifurcatedCalendar()">⇅ Bifurcate</button>';
    pa.appendChild(extra);
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  patchLCalendar();
  patchFilterCal();
})();
