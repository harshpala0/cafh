/* CA FirmHub — mobile drawer + PWA registration */
(function () {
  function ensureOverlay() {
    if (document.getElementById('side-overlay')) return;
    var lay = document.querySelector('.lay');
    if (!lay) return;
    var o = document.createElement('div');
    o.className = 'side-overlay';
    o.id = 'side-overlay';
    o.onclick = closeSide;
    lay.insertBefore(o, lay.firstChild);
  }

  function ensureMenuBtn() {
    if (document.getElementById('menu-btn')) return;
    var left = document.querySelector('.ph-left');
    if (!left) return;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'menu-btn';
    btn.id = 'menu-btn';
    btn.setAttribute('aria-label', 'Open menu');
    btn.onclick = toggleSide;
    btn.innerHTML = '<svg viewBox="0 0 24 24"><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="18" x2="21" y2="18"/></svg>';
    left.insertBefore(btn, left.firstChild);
  }

  window.toggleSide = function () {
    ensureOverlay();
    var s = document.querySelector('.side');
    var o = document.getElementById('side-overlay');
    if (!s) return;
    var open = s.classList.toggle('open');
    if (o) o.classList.toggle('show', open);
    document.body.classList.toggle('side-open', open);
  };

  window.closeSide = function () {
    var s = document.querySelector('.side');
    var o = document.getElementById('side-overlay');
    if (s) s.classList.remove('open');
    if (o) o.classList.remove('show');
    document.body.classList.remove('side-open');
  };

  document.addEventListener('click', function (e) {
    var ni = e.target.closest && e.target.closest('.ni');
    if (ni && window.innerWidth <= 900) closeSide();
  }, true);

  function boot() {
    ensureOverlay();
    ensureMenuBtn();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }

  var obs = new MutationObserver(function () {
    if (document.getElementById('app') && document.getElementById('app').style.display !== 'none') {
      boot();
    }
  });
  obs.observe(document.documentElement, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'class'] });

  if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
      navigator.serviceWorker.register('/static/sw.js').catch(function () {});
    });
  }
})();
