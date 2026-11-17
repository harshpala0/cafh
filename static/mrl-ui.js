/* CA FirmHub — MRL Maker launcher (Company / LLP statutory + CARO)
   Designed & Built by Harsh Pala
*/
(function () {
  if (window.__cafhMrlUI) return;
  window.__cafhMrlUI = true;

  window.lMrlMaker = function () {
    document.getElementById('pt').textContent = 'MRL Maker — Management Representation Letter';
    document.getElementById('pa').innerHTML =
      '<a href="/tools/mrl" target="_blank" class="btn btn-g" style="text-decoration:none">↗ Open MRL tools</a>';
    document.getElementById('pb').innerHTML =
      '<div class="card"><div class="card-b" style="padding:28px">' +
      '<div style="font-family:Poppins,sans-serif;font-size:18px;font-weight:700;color:var(--navy);margin-bottom:8px;text-align:center">Statutory Audit MRL</div>' +
      '<p style="color:var(--text2);font-size:13.5px;max-width:520px;margin:0 auto 18px;line-height:1.5;text-align:center">' +
      'Full drafter with live preview, clause toggles, Excel import and Word export. ' +
      'Pick <strong>Company</strong> (Statutory + CARO 2020) or <strong>LLP</strong> (LLP Act / ICAI levels).</p>' +
      '<div style="display:grid;gap:10px;max-width:480px;margin:0 auto">' +
      '<a href="/tools/mrl/company" target="_blank" class="btn btn-p" style="text-decoration:none;text-align:center">' +
      'Company — Statutory Audit &amp; CARO 2020</a>' +
      '<a href="/tools/mrl/llp" target="_blank" class="btn btn-g" style="text-decoration:none;text-align:center">' +
      'LLP — Statutory Audit</a>' +
      '<a href="/tools/mrl" target="_blank" style="text-align:center;font-size:12px;color:var(--text2)">Or open chooser page</a>' +
      '</div>' +
      '<p style="margin-top:16px;font-size:11px;color:var(--text2);text-align:center">Designed & Built by Harsh Pala</p>' +
      '</div></div>';
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
      el.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg><span>MRL Maker</span>';
      if (wp && wp.parentNode) wp.parentNode.insertBefore(el, wp.nextSibling);
      else nav.appendChild(el);
    } catch (e) {}
  }

  var _nav = window.nav;
  if (typeof _nav === 'function') {
    window.nav = function (p) {
      if (p === 'mrlmaker') {
        try {
          document.querySelectorAll('.ni').forEach(function (n) {
            n.classList.toggle('on', n.getAttribute('data-p') === 'mrlmaker');
          });
        } catch (e) {}
        lMrlMaker();
        return;
      }
      return _nav.apply(this, arguments);
    };
  }

  injectNav();
  setTimeout(injectNav, 400);
  setTimeout(injectNav, 1200);
})();
