/* CA FirmHub — MRL Maker launcher (full tool at /tools/mrl)
   Designed & Built by Harsh Pala
*/
(function () {
  if (window.__cafhMrlUI) return;
  window.__cafhMrlUI = true;

  window.lMrlMaker = function () {
    document.getElementById('pt').textContent = 'MRL Maker — Management Representation Letter';
    document.getElementById('pa').innerHTML =
      '<a href="/tools/mrl" target="_blank" class="btn btn-g" style="text-decoration:none">↗ Open Full MRL Maker</a>';
    document.getElementById('pb').innerHTML =
      '<div class="card"><div class="card-b" style="padding:28px;text-align:center">' +
      '<div style="font-family:Poppins,sans-serif;font-size:18px;font-weight:700;color:var(--navy);margin-bottom:8px">MRL Maker</div>' +
      '<p style="color:var(--text2);font-size:13.5px;max-width:480px;margin:0 auto 18px;line-height:1.5">' +
      'Step-by-step Management Representation Letter for <strong>Tax Audit (u/s 44AB)</strong> and ' +
      '<strong>Statutory Audit (SA 580 / CARO / Rule 11)</strong> — same style as Audit Working Papers. ' +
      'Loads clients from your register, confirms every clause, then prints a formal letter.</p>' +
      '<a href="/tools/mrl" target="_blank" class="btn btn-p" style="text-decoration:none">↗ Open MRL Maker Tool</a>' +
      '<p style="margin-top:14px;font-size:11px;color:var(--text2)">Designed & Built by Harsh Pala</p>' +
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
      el.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>MRL Maker';
      if (wp && wp.parentNode) wp.parentNode.insertBefore(el, wp.nextSibling);
      else nav.appendChild(el);
    } catch (e) {}
  }

  function patchNav() {
    if (window.__cafhMrlNavPatched || typeof window.nav !== 'function') return;
    window.__cafhMrlNavPatched = true;
    var _nav = window.nav;
    window.nav = function (p) {
      if (p === 'mrlmaker') {
        try {
          document.querySelectorAll('.ni').forEach(function (n) {
            n.classList.toggle('on', n.getAttribute('data-p') === p);
          });
        } catch (e) {}
        if (typeof window.lMrlMaker === 'function') window.lMrlMaker();
        return;
      }
      return _nav.apply(this, arguments);
    };
  }

  var obs = new MutationObserver(function () { injectNav(); patchNav(); });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  injectNav();
  patchNav();
})();
