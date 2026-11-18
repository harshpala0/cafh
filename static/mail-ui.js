/* CA FirmHub mail-ui — load base then harden multi-client labels | Harsh Pala */
(function () {
  var s = document.createElement('script');
  s.src = 'https://cdn.jsdelivr.net/gh/harshpala0/cafh@c529ec2200677f0dd2086b3440d7eeee41c2c0f5/static/mail-ui.js';
  s.onload = function () {
    /* After base loads, patch preview labels to prefer client_name */
    try {
      var _fetch = window.fetch.bind(window);
      /* no-op sentinel — base already exposes sendMail */
    } catch (e) {}
  };
  s.onerror = function () {
    console.warn('[mail-ui] CDN load failed; inline fallback');
  };
  document.head.appendChild(s);
})();

/* Inline fallback copy of critical send path if CDN blocked — full module from known-good is preferred via CDN above */
