/* CA FirmHub — Client mail UI | Designed & Built by Harsh Pala
   Loads known-good mail-ui then shows client names in context preview.
*/
(function () {
  if (window.__cafhMailUILoading) return;
  window.__cafhMailUILoading = true;

  function injectBase(code) {
    try {
      // Soft-patch context preview labels inside the loaded source
      code = code.replace(
        /var c = _ctxByClient\[id\] \|\| \{\};\s*lines\.push\(\s*'<div style="font-size:12px;margin-bottom:4px"><strong>#' \+\s*esc\(id\) \+/,
        "var c = _ctxByClient[id] || _ctxByClient[String(id)] || {}; var nm = c.client_name || ('#' + id); lines.push( '<div style=\"font-size:12px;margin-bottom:4px\"><strong>' + esc(nm) +"
      );
    } catch (e) {}
    var el = document.createElement('script');
    el.textContent = code;
    document.head.appendChild(el);
  }

  var urls = [
    'https://cdn.jsdelivr.net/gh/harshpala0/cafh@c529ec2200677f0dd2086b3440d7eeee41c2c0f5/static/mail-ui.js',
    'https://raw.githubusercontent.com/harshpala0/cafh/c529ec2200677f0dd2086b3440d7eeee41c2c0f5/static/mail-ui.js'
  ];

  function tryLoad(i) {
    if (i >= urls.length) {
      console.error('[mail-ui] Could not load base mail UI');
      return;
    }
    fetch(urls[i], { cache: 'no-store' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.text();
      })
      .then(function (code) {
        if (!code || code.length < 1000) throw new Error('short body');
        injectBase(code);
      })
      .catch(function () {
        tryLoad(i + 1);
      });
  }
  tryLoad(0);
})();
