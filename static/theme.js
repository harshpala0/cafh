/**
 * CA FirmHub — Day / Night theme (module-wide)
 * Designed & Built by Harsh Pala
 */
(function () {
  var KEY = 'cfh-theme';
  // Inject stylesheet once
  if (!document.getElementById('cfh-theme-css')) {
    var link = document.createElement('link');
    link.id = 'cfh-theme-css';
    link.rel = 'stylesheet';
    link.href = '/static/theme.css';
    document.head.appendChild(link);
  }

  function get() {
    try {
      var t = localStorage.getItem(KEY);
      if (t === 'dark' || t === 'light') return t;
    } catch (e) {}
    try {
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) return 'dark';
    } catch (e) {}
    return 'light';
  }

  function set(theme) {
    theme = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem(KEY, theme); } catch (e) {}
    paintButtons(theme);
    try {
      document.dispatchEvent(new CustomEvent('cfh-theme-change', { detail: { theme: theme } }));
    } catch (e) {}
  }

  function sunSvg() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>';
  }
  function moonSvg() {
    return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M21 14.5A8.5 8.5 0 1111.5 3 7 7 0 0021 14.5z"/></svg>';
  }

  function paintButtons(theme) {
    document.querySelectorAll('#cfh-theme-btn, .cfh-theme-btn, #cfh-theme-float').forEach(function (btn) {
      var dark = theme === 'dark';
      btn.innerHTML = dark ? sunSvg() : moonSvg();
      btn.title = dark ? 'Switch to Day mode' : 'Switch to Night mode';
      btn.setAttribute('aria-label', btn.title);
    });
  }

  function toggle() {
    set(get() === 'dark' ? 'light' : 'dark');
  }

  function ensureHeaderBtn() {
    var host = document.querySelector('.ph-right');
    if (!host) return;
    if (document.getElementById('cfh-theme-btn')) {
      paintButtons(get());
      return;
    }
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'cfh-theme-btn';
    btn.className = 'cfh-theme-btn';
    btn.addEventListener('click', toggle);
    var pa = document.getElementById('pa');
    if (pa && pa.parentNode === host) host.insertBefore(btn, pa);
    else host.insertBefore(btn, host.firstChild);
    paintButtons(get());
  }

  function ensureLoginBtn() {
    if (document.getElementById('cfh-theme-float')) return;
    var sub = document.getElementById('sub-screen');
    var login = document.getElementById('login-screen') || document.getElementById('lg-screen');
    if (!sub && !login) return;
    var btn = document.createElement('button');
    btn.type = 'button';
    btn.id = 'cfh-theme-float';
    btn.className = 'cfh-theme-btn';
    btn.style.cssText = 'position:fixed;top:16px;right:16px;z-index:9999;width:40px;height:40px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;background:var(--surface);border:1px solid var(--border);color:var(--icai-navy);cursor:pointer;box-shadow:var(--sh-md)';
    btn.addEventListener('click', toggle);
    document.body.appendChild(btn);
    paintButtons(get());
  }

  set(get());
  function boot() {
    ensureHeaderBtn();
    ensureLoginBtn();
    var btn = document.getElementById('cfh-theme-btn');
    if (btn && !btn._cfhBound) {
      btn.addEventListener('click', toggle);
      btn._cfhBound = true;
    }
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', boot);
  else boot();

  var obs = new MutationObserver(function () {
    if (!document.getElementById('cfh-theme-btn')) ensureHeaderBtn();
  });
  try { obs.observe(document.body, { childList: true, subtree: true }); } catch (e) {}

  window.cfhTheme = { get: get, set: set, toggle: toggle };
})();
