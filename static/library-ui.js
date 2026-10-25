/* CA FirmHub — Study Material / Library UI
   Designed & Built by Harsh Pala
   Available to all firm staff; hidden from Client users.
*/
(function () {
  if (window.__cafhLibraryUI) return;
  window.__cafhLibraryUI = true;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
    });
  }

  function isStaff() {
    try {
      if (typeof U !== 'undefined' && U && U.role) return U.role !== 'Client';
    } catch (e) {}
    return true;
  }

  function injectNavItem() {
    if (!isStaff()) return;
    var side = document.querySelector('.side') || document.querySelector('nav') || document.querySelector('[class*="sidebar"]');
    if (!side) {
      var dash = document.querySelector('.ni[data-p="dashboard"]');
      if (dash) side = dash.parentElement;
    }
    if (!side) return;
    if (document.querySelector('.ni[data-p="library"]')) return;

    var reports = side.querySelector('.ni[data-p="reports"]');
    var node = document.createElement('div');
    node.className = 'ni';
    node.setAttribute('data-p', 'library');
    node.onclick = function () { nav('library'); };
    node.innerHTML =
      '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">' +
      '<path d="M4 19.5A2.5 2.5 0 016.5 17H20"/>' +
      '<path d="M6.5 2H20v20H6.5A2.5 2.5 0 014 19.5v-15A2.5 2.5 0 016.5 2z"/>' +
      '<path d="M8 7h8M8 11h8M8 15h5"/></svg>Study Material';

    if (reports && reports.parentElement === side) {
      reports.parentElement.insertBefore(node, reports.nextSibling);
    } else {
      side.appendChild(node);
    }
  }

  function patchNav() {
    if (window.__cafhLibNavPatched) return;
    if (typeof window.nav !== 'function') return;
    window.__cafhLibNavPatched = true;
    var _nav = window.nav;
    window.nav = function (p) {
      if (p === 'library') {
        document.querySelectorAll('.ni').forEach(function (n) { n.classList.remove('on'); });
        var el = document.querySelector('.ni[data-p="library"]');
        if (el) el.classList.add('on');
        var pt = document.getElementById('pt');
        if (pt) pt.textContent = 'Study Material / Library';
        var pa = document.getElementById('pa');
        if (pa) pa.innerHTML = '';
        return cafhShowLibrary();
      }
      return _nav(p);
    };
  }

  window.cafhShowLibrary = async function () {
    if (!isStaff()) {
      toast('Study Material is not available for Client users', 'err');
      return;
    }
    var pb = document.getElementById('pb');
    if (!pb) return;
    pb.innerHTML = '<div class="card"><div class="card-b" style="padding:40px;text-align:center;color:#718096">Loading library…</div></div>';

    var data;
    try {
      data = await api('/api/library/catalog');
    } catch (e) {
      pb.innerHTML = '<div class="card"><div class="card-b" style="padding:24px;color:#C53030">' +
        esc(e.message || 'Could not load library') + '</div></div>';
      return;
    }

    var cats = data.categories || [];
    var searchId = 'cafh-lib-q';

    var html = '';
    html += '<div style="margin-bottom:16px">';
    html += '<div style="display:flex;flex-wrap:wrap;gap:12px;align-items:center;justify-content:space-between">';
    html += '<div><div style="font-size:18px;font-weight:700;color:#003366">' + esc(data.title || 'Study Material') + '</div>';
    html += '<div style="font-size:12px;color:#718096;margin-top:4px">' + esc(data.subtitle || '') + '</div></div>';
    html += '<input id="' + searchId + '" type="search" placeholder="Search topics, Acts, DTAA, GST…" ';
    html += 'style="min-width:220px;flex:1;max-width:360px;padding:10px 12px;border:1.5px solid #D1DAEA;border-radius:8px;font-size:13px">';
    html += '</div>';
    html += '<p style="font-size:11px;color:#A0AEC0;margin-top:10px">' + esc(data.note || '') +
      ' · ' + esc(data.builder || 'Designed & Built by Harsh Pala') + '</p>';
    html += '</div>';

    html += '<div id="cafh-lib-chips" style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:16px">';
    html += '<button type="button" class="btn btn-o btn-xs cafh-lib-chip on" data-cat="all">All</button>';
    cats.forEach(function (c) {
      html += '<button type="button" class="btn btn-o btn-xs cafh-lib-chip" data-cat="' + esc(c.id) + '">' +
        esc((c.icon || '') + ' ' + c.title) + '</button>';
    });
    html += '</div>';

    html += '<div id="cafh-lib-body">';
    cats.forEach(function (c) {
      html += '<div class="card cafh-lib-cat" data-cat="' + esc(c.id) + '" style="margin-bottom:14px">';
      html += '<div class="card-b" style="padding:16px 18px">';
      html += '<div style="display:flex;align-items:center;gap:10px;margin-bottom:6px">';
      html += '<span style="font-size:22px">' + esc(c.icon || '📘') + '</span>';
      html += '<div><div style="font-weight:700;color:#003366;font-size:15px">' + esc(c.title) + '</div>';
      html += '<div style="font-size:12px;color:#718096">' + esc(c.description || '') + '</div></div></div>';
      html += '<div style="margin-top:12px;display:grid;gap:8px">';
      (c.items || []).forEach(function (it) {
        html += '<a class="cafh-lib-item" href="' + esc(it.url) + '" target="_blank" rel="noopener noreferrer" ';
        html += 'data-text="' + esc((it.title + ' ' + (it.source || '') + ' ' + (it.type || '') + ' ' + c.title).toLowerCase()) + '" ';
        html += 'style="display:flex;align-items:center;justify-content:space-between;gap:12px;padding:10px 12px;';
        html += 'border:1px solid #E4EAF2;border-radius:8px;text-decoration:none;color:inherit;background:#FAFBFC">';
        html += '<div><div style="font-size:13px;font-weight:600;color:#1A365D">' + esc(it.title) + '</div>';
        html += '<div style="font-size:11px;color:#718096;margin-top:2px">' + esc(it.source || '') +
          (it.type ? (' · ' + esc(it.type)) : '') + '</div></div>';
        html += '<span style="font-size:12px;color:#004080;font-weight:600;white-space:nowrap">Open ↗</span>';
        html += '</a>';
      });
      html += '</div></div></div>';
    });
    html += '</div>';

    pb.innerHTML = html;

    var qEl = document.getElementById(searchId);
    function applyFilter() {
      var q = (qEl && qEl.value || '').trim().toLowerCase();
      var activeChip = document.querySelector('.cafh-lib-chip.on');
      var cat = activeChip ? activeChip.getAttribute('data-cat') : 'all';
      document.querySelectorAll('.cafh-lib-cat').forEach(function (block) {
        var cid = block.getAttribute('data-cat');
        var showCat = (cat === 'all' || cat === cid);
        var items = block.querySelectorAll('.cafh-lib-item');
        var any = false;
        items.forEach(function (a) {
          var text = a.getAttribute('data-text') || '';
          var match = !q || text.indexOf(q) >= 0;
          a.style.display = match ? '' : 'none';
          if (match) any = true;
        });
        block.style.display = (showCat && any) ? '' : 'none';
      });
    }
    if (qEl) qEl.addEventListener('input', applyFilter);
    document.querySelectorAll('.cafh-lib-chip').forEach(function (btn) {
      btn.addEventListener('click', function () {
        document.querySelectorAll('.cafh-lib-chip').forEach(function (b) { b.classList.remove('on'); });
        btn.classList.add('on');
        applyFilter();
      });
    });
  };

  function boot() {
    patchNav();
    injectNavItem();
  }

  var obs = new MutationObserver(function () {
    patchNav();
    injectNavItem();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState !== 'loading') boot();
  else document.addEventListener('DOMContentLoaded', boot);
})();
