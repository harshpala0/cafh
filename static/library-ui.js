/* CA FirmHub — Study Material / Library UI
   Designed & Built by Harsh Pala
   Available to all firm staff; hidden from Client users.
   Admin can add/edit/delete firm links (paste URL hosted elsewhere).
*/
(function () {
  if (window.__cafhLibraryUI) return;
  window.__cafhLibraryUI = true;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&', '<': '<', '>': '>', '"': '"', "'": '&#39;' })[c];
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
    var firmCats = data.firm_categories || [];
    var searchId = 'cafh-lib-q';
    var canManage = !!data.can_manage_firm_library;
    window.__cafhLibCanManage = canManage;
    window.__cafhLibFirmItems = [];
    firmCats.forEach(function (c) {
      (c.items || []).forEach(function (it) { if (it.id) window.__cafhLibFirmItems.push(it); });
    });

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
    html += '<button type="button" class="btn btn-o btn-xs cafh-lib-chip" data-cat="firm">📎 Firm materials</button>';
    cats.forEach(function (c) {
      html += '<button type="button" class="btn btn-o btn-xs cafh-lib-chip" data-cat="' + esc(c.id) + '">' +
        esc((c.icon || '') + ' ' + c.title) + '</button>';
    });
    html += '</div>';

    html += '<div id="cafh-lib-body">';

    html += '<div style="margin-bottom:10px;padding:10px 12px;background:#EBF4FF;border-radius:8px;font-size:12px;color:#1A365D;display:flex;flex-wrap:wrap;gap:10px;align-items:center;justify-content:space-between">';
    html += '<div><strong>Your firm materials</strong> (' + (data.firm_item_count || 0) + ') — only this firm. Host PDF/Word on Drive/OneDrive and paste the link.</div>';
    if (canManage) {
      html += '<button type="button" class="btn btn-p btn-xs" onclick="cafhLibAddLink()">+ Add link (Admin)</button>';
    }
    html += '</div>';

    if (firmCats.length) {
      firmCats.forEach(function (c) {
        html += '<div class="card cafh-lib-cat" data-cat="firm" style="margin-bottom:14px;border:1px solid #93C5FD">';
        html += '<div class="card-b" style="padding:16px 18px">';
        html += '<div style="font-weight:700;color:#003366;font-size:15px;margin-bottom:6px">📎 ' + esc(c.title) +
          ' <span style="font-size:11px;background:#BEE3F8;padding:2px 6px;border-radius:4px">Firm only</span></div>';
        html += '<div style="display:grid;gap:8px">';
        (c.items || []).forEach(function (it) {
          html += '<div class="cafh-lib-item" data-text="' + esc((it.title + ' firm').toLowerCase()) + '" ';
          html += 'style="display:flex;justify-content:space-between;gap:12px;padding:10px 12px;border:1px solid #E4EAF2;border-radius:8px;background:#FAFBFC;align-items:center">';
          html += '<div style="min-width:0;flex:1"><div style="font-size:13px;font-weight:600;color:#1A365D">' + esc(it.title) + '</div>';
          html += '<div style="font-size:11px;color:#718096">' + esc(it.source || '') + (it.description ? (' · ' + esc(it.description)) : '') + '</div></div>';
          html += '<div style="display:flex;gap:6px;flex-shrink:0;align-items:center">';
          html += '<a href="' + esc(it.url) + '" target="_blank" rel="noopener noreferrer" class="btn btn-xs btn-o" style="text-decoration:none">Open ↗</a>';
          if (canManage && it.id) {
            html += '<button type="button" class="btn btn-xs btn-o" onclick="cafhLibEditLink(' + it.id + ')">Edit</button>';
            html += '<button type="button" class="btn btn-xs btn-err" onclick="cafhLibDeleteLink(' + it.id + ')">Delete</button>';
          }
          html += '</div></div>';
        });
        html += '</div></div></div>';
      });
    } else if (canManage) {
      html += '<div class="card" style="margin-bottom:14px;border:1px dashed #93C5FD"><div class="card-b" style="padding:20px;text-align:center;color:#718096;font-size:13px">';
      html += 'No firm links yet. Host SOP/PDF/Word on Drive or OneDrive, then click <strong>+ Add link</strong>.</div></div>';
    }

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
        html += 'data-text="' + esc((it.title + ' ' + (it.source || '') + ' ' + c.title).toLowerCase()) + '" ';
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

  window.cafhLibEnsureModal = function () {
    if (document.getElementById('cafh-lib-mo')) return;
    var mo = document.createElement('div');
    mo.id = 'cafh-lib-mo';
    mo.style.cssText = 'display:none;position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:9999;align-items:center;justify-content:center';
    mo.innerHTML =
      '<div style="background:#fff;border-radius:12px;max-width:480px;width:92%;padding:20px;box-shadow:0 12px 40px rgba(0,0,0,.2)">' +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px">' +
      '<h3 id="cafh-lib-mo-title" style="margin:0;font-size:16px;color:#003366">Add firm link</h3>' +
      '<button type="button" onclick="cafhLibCloseMo()" style="border:0;background:transparent;font-size:22px;cursor:pointer;line-height:1">×</button></div>' +
      '<input type="hidden" id="cafh-lib-id">' +
      '<label style="font-size:11px;font-weight:600;color:#4A5568">Title *</label>' +
      '<input id="cafh-lib-title" style="width:100%;margin:4px 0 10px;padding:8px 10px;border:1.5px solid #D1DAEA;border-radius:6px;font:inherit">' +
      '<label style="font-size:11px;font-weight:600;color:#4A5568">URL * (Drive / OneDrive / website)</label>' +
      '<input id="cafh-lib-url" placeholder="https://..." style="width:100%;margin:4px 0 10px;padding:8px 10px;border:1.5px solid #D1DAEA;border-radius:6px;font:inherit">' +
      '<label style="font-size:11px;font-weight:600;color:#4A5568">Category</label>' +
      '<input id="cafh-lib-cat" value="SOP" style="width:100%;margin:4px 0 10px;padding:8px 10px;border:1.5px solid #D1DAEA;border-radius:6px;font:inherit">' +
      '<label style="font-size:11px;font-weight:600;color:#4A5568">Description (optional)</label>' +
      '<input id="cafh-lib-desc" style="width:100%;margin:4px 0 14px;padding:8px 10px;border:1.5px solid #D1DAEA;border-radius:6px;font:inherit">' +
      '<div style="display:flex;gap:8px;justify-content:flex-end">' +
      '<button type="button" class="btn btn-o" onclick="cafhLibCloseMo()">Cancel</button>' +
      '<button type="button" class="btn btn-p" onclick="cafhLibSaveLink()">Save</button></div>' +
      '<p style="font-size:11px;color:#A0AEC0;margin:12px 0 0">Tip: share PDF/Word from Google Drive or OneDrive → copy link → paste here. Admin only.</p></div>';
    document.body.appendChild(mo);
    mo.addEventListener('click', function (e) { if (e.target === mo) cafhLibCloseMo(); });
  };

  window.cafhLibCloseMo = function () {
    var mo = document.getElementById('cafh-lib-mo');
    if (mo) mo.style.display = 'none';
  };

  window.cafhLibAddLink = function () {
    if (!window.__cafhLibCanManage) return;
    cafhLibEnsureModal();
    document.getElementById('cafh-lib-mo-title').textContent = 'Add firm link';
    document.getElementById('cafh-lib-id').value = '';
    document.getElementById('cafh-lib-title').value = '';
    document.getElementById('cafh-lib-url').value = '';
    document.getElementById('cafh-lib-cat').value = 'SOP';
    document.getElementById('cafh-lib-desc').value = '';
    document.getElementById('cafh-lib-mo').style.display = 'flex';
  };

  window.cafhLibEditLink = function (id) {
    if (!window.__cafhLibCanManage) return;
    var it = (window.__cafhLibFirmItems || []).find(function (x) { return x.id === id; });
    if (!it) { toast('Item not found', 'err'); return; }
    cafhLibEnsureModal();
    document.getElementById('cafh-lib-mo-title').textContent = 'Edit firm link';
    document.getElementById('cafh-lib-id').value = String(it.id);
    document.getElementById('cafh-lib-title').value = it.title || '';
    document.getElementById('cafh-lib-url').value = it.url || '';
    document.getElementById('cafh-lib-cat').value = it.category || 'Firm material';
    document.getElementById('cafh-lib-desc').value = it.description || '';
    document.getElementById('cafh-lib-mo').style.display = 'flex';
  };

  window.cafhLibSaveLink = async function () {
    var id = document.getElementById('cafh-lib-id').value;
    var body = {
      title: (document.getElementById('cafh-lib-title').value || '').trim(),
      url: (document.getElementById('cafh-lib-url').value || '').trim(),
      category: (document.getElementById('cafh-lib-cat').value || '').trim() || 'Firm material',
      description: (document.getElementById('cafh-lib-desc').value || '').trim(),
      type: 'Link'
    };
    if (!body.title || !body.url) { toast('Title and URL required', 'err'); return; }
    try {
      if (id) {
        await api('/api/library/firm-items/' + id, { method: 'PUT', body: JSON.stringify(body) });
        toast('Link updated', 'ok');
      } else {
        await api('/api/library/firm-items', { method: 'POST', body: JSON.stringify(body) });
        toast('Link added', 'ok');
      }
      cafhLibCloseMo();
      cafhShowLibrary();
    } catch (e) {
      toast(e.message || 'Save failed', 'err');
    }
  };

  window.cafhLibDeleteLink = async function (id) {
    if (!window.__cafhLibCanManage) return;
    if (!confirm('Delete this firm link?')) return;
    try {
      await api('/api/library/firm-items/' + id, { method: 'DELETE' });
      toast('Deleted', 'ok');
      cafhShowLibrary();
    } catch (e) {
      toast(e.message || 'Delete failed', 'err');
    }
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
