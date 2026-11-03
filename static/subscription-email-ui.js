/* CA FirmHub — email subscription gate | Designed & Built by Harsh Pala */
(function () {
  if (window.__cafhSubEmail) return;
  window.__cafhSubEmail = true;

  function enhanceGate() {
    var input = document.getElementById('sub-id');
    if (!input) return;
    if (input.getAttribute('data-cafh-email') === '1') return;
    input.setAttribute('data-cafh-email', '1');
    input.type = 'email';
    input.placeholder = 'Firm subscription email (e.g. you@firm.com)';
    input.autocomplete = 'email';
    input.setAttribute('inputmode', 'email');
    var label = input.previousElementSibling;
    if (label && label.tagName === 'LABEL') label.textContent = 'Subscription email';
    var tag = document.querySelector('.sub-tagline, #sub-screen .sub-tagline, p.sub-tagline');
    if (tag) {
      tag.innerHTML =
        'Enter the <strong>email registered with your firm subscription</strong>.<br>' +
        'This is a one-time step on this browser — you will not be asked again until cleared.';
    }
    if (!document.getElementById('cafh-sub-hint')) {
      var hint = document.createElement('p');
      hint.id = 'cafh-sub-hint';
      hint.style.cssText = 'font-size:11px;color:#718096;margin:6px 0 0';
      hint.textContent = 'You can still paste a Subscription ID (SUB-…) if your admin shared one.';
      input.parentNode.insertBefore(hint, input.nextSibling);
    }
  }

  window.doSubscriptionVerify = async function () {
    var input = document.getElementById('sub-id');
    var errEl = document.getElementById('sub-err') || document.querySelector('#sub-screen .login-err, #sub-err');
    var btn = document.getElementById('sub-btn');
    var raw = (input && input.value || '').trim();
    if (errEl) { errEl.style.display = 'none'; errEl.textContent = ''; }
    if (!raw) {
      if (errEl) {
        errEl.textContent = 'Please enter your subscription email (or Subscription ID).';
        errEl.style.display = 'block';
      }
      return;
    }
    if (btn) { btn.disabled = true; btn.textContent = 'Verifying…'; }
    var body = {};
    if (raw.indexOf('@') >= 0) body.email = raw.toLowerCase();
    else body.subscription_id = raw;
    try {
      var r = await fetch('/api/subscription/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      var d = await r.json().catch(function () { return {}; });
      if (!r.ok) throw new Error(d.detail || 'Verification failed');
      var tok = d.subscription_token;
      if (!tok) throw new Error('No token returned');
      try {
        localStorage.setItem('cafirmhub_sub_token', tok);
        var SUB_TOKEN_KEY = window.SUB_TOKEN_KEY || 'cafirmhub_sub_token';
        localStorage.setItem(SUB_TOKEN_KEY, tok);
      } catch (e) {}
      if (typeof showLoginScreen === 'function') showLoginScreen();
      else {
        var sub = document.getElementById('sub-screen');
        var login = document.getElementById('login-screen');
        if (sub) sub.style.display = 'none';
        if (login) login.style.display = 'flex';
      }
      var fb = document.getElementById('login-firm-badge');
      if (fb && d.firm_name) {
        fb.style.display = 'block';
        fb.textContent = d.firm_name + (d.owner_email ? ' · ' + d.owner_email : '');
      }
    } catch (e) {
      if (errEl) {
        errEl.textContent = e.message || 'Verification failed';
        errEl.style.display = 'block';
      }
    } finally {
      if (btn) { btn.disabled = false; btn.textContent = 'Continue →'; }
    }
  };

  function enhanceSuperAdmin() {
    var mo = document.getElementById('firm-mo');
    if (!mo || document.getElementById('firm-owner-email')) return;
    var body = mo.querySelector('.mb, .modal-body, form') || mo;
    var exp = mo.querySelector('#firm-expires, input[type="date"]');
    var fg = document.createElement('div');
    fg.className = 'fg';
    fg.innerHTML =
      '<label>Subscription email *</label>' +
      '<input type="email" id="firm-owner-email" placeholder="admin@yourfirm.com" style="width:100%">' +
      '<p style="font-size:11px;color:#718096;margin-top:4px">Users enter this email on the subscription gate to reach your firm login. Must be unique across firms.</p>';
    if (exp && exp.parentNode && exp.parentNode.parentNode) {
      exp.parentNode.parentNode.insertBefore(fg, exp.parentNode.nextSibling);
    } else {
      body.appendChild(fg);
    }
  }

  var _fetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    try {
      var url = typeof input === 'string' ? input : (input && input.url) || '';
      init = init || {};
      if (url.indexOf('/api/superadmin/firms') !== -1 && init.method && /POST|PUT/i.test(init.method)) {
        var body = init.body;
        if (typeof body === 'string') {
          try {
            var j = JSON.parse(body);
            var em = (document.getElementById('firm-owner-email') || {}).value || '';
            if (em) {
              j.owner_email = em.trim().toLowerCase();
              init = Object.assign({}, init, { body: JSON.stringify(j) });
            }
          } catch (e) {}
        }
      }
    } catch (e) {}
    return _fetch(input, init);
  };

  var obs = new MutationObserver(function () {
    enhanceGate();
    enhanceSuperAdmin();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  setTimeout(enhanceGate, 50);
  setTimeout(enhanceGate, 400);
  setTimeout(enhanceSuperAdmin, 200);
})();
