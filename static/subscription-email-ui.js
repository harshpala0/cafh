/* CA FirmHub — email subscription gate + multi-firm pick + firm-scoped login | Designed & Built by Harsh Pala */
(function () {
  if (window.__cafhSubEmail) return;
  window.__cafhSubEmail = true;

  var _pendingSelection = null;

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
        'If several firms share this email, you will choose your firm next.';
    }
    if (!document.getElementById('cafh-sub-hint')) {
      var hint = document.createElement('p');
      hint.id = 'cafh-sub-hint';
      hint.style.cssText = 'font-size:11px;color:#718096;margin:6px 0 0';
      hint.textContent = 'You can still paste a Subscription ID (SUB-…) if your admin shared one.';
      input.parentNode.insertBefore(hint, input.nextSibling);
    }
  }

  function ensureFirmPickScreen() {
    var el = document.getElementById('cafh-firm-pick-screen');
    if (el) return el;
    el = document.createElement('div');
    el.id = 'cafh-firm-pick-screen';
    el.style.cssText =
      'display:none;position:fixed;inset:0;z-index:9999;background:rgba(11,31,58,.92);' +
      'align-items:center;justify-content:center;padding:20px;';
    el.innerHTML =
      '<div style="background:#fff;border-radius:16px;max-width:420px;width:100%;padding:28px 24px;' +
      'box-shadow:0 20px 50px rgba(0,0,0,.35);font-family:system-ui,sans-serif">' +
      '<div style="font-size:13px;font-weight:600;color:#0B1F3A;margin-bottom:4px">CA FirmHub</div>' +
      '<h2 style="margin:0 0 8px;font-size:20px;color:#0B1F3A">Select your firm</h2>' +
      '<p id="cafh-firm-pick-email" style="font-size:13px;color:#64748b;margin:0 0 16px"></p>' +
      '<div id="cafh-firm-pick-list" style="display:flex;flex-direction:column;gap:8px;margin-bottom:16px"></div>' +
      '<p id="cafh-firm-pick-err" style="display:none;color:#b91c1c;font-size:13px;margin:0 0 10px"></p>' +
      '<button type="button" id="cafh-firm-pick-back" style="background:transparent;border:none;' +
      'color:#64748b;font-size:13px;cursor:pointer;padding:8px 0">← Use a different email</button>' +
      '</div>';
    document.body.appendChild(el);
    var back = document.getElementById('cafh-firm-pick-back');
    if (back) {
      back.onclick = function () {
        _pendingSelection = null;
        el.style.display = 'none';
        var sub = document.getElementById('sub-screen');
        if (sub) sub.style.display = '';
      };
    }
    return el;
  }

  function showFirmPicker(data) {
    var el = ensureFirmPickScreen();
    _pendingSelection = {
      token: data.selection_token || '',
      email: data.owner_email || '',
      firms: data.firms || []
    };
    var emailEl = document.getElementById('cafh-firm-pick-email');
    if (emailEl) {
      emailEl.textContent =
        (data.owner_email || '') +
        ' is linked to ' +
        _pendingSelection.firms.length +
        ' firm(s). Choose the firm you work with — data stays separate.';
    }
    var list = document.getElementById('cafh-firm-pick-list');
    var errEl = document.getElementById('cafh-firm-pick-err');
    if (errEl) {
      errEl.style.display = 'none';
      errEl.textContent = '';
    }
    if (list) {
      list.innerHTML = '';
      (_pendingSelection.firms || []).forEach(function (f) {
        var btn = document.createElement('button');
        btn.type = 'button';
        btn.style.cssText =
          'text-align:left;padding:14px 16px;border-radius:12px;border:1.5px solid #e2e8f0;' +
          'background:#f8fafc;cursor:pointer;font:inherit;width:100%';
        btn.innerHTML =
          '<div style="font-weight:600;color:#0B1F3A">' +
          esc(f.name || 'Firm #' + f.id) +
          '</div>' +
          '<div style="font-size:12px;color:#64748b;margin-top:4px">' +
          (f.reg_no ? esc(f.reg_no) + ' · ' : '') +
          (f.expires_at ? 'Expires ' + esc(f.expires_at) : 'Active') +
          '</div>';
        btn.onmouseenter = function () {
          btn.style.borderColor = '#2563eb';
          btn.style.background = '#eff6ff';
        };
        btn.onmouseleave = function () {
          btn.style.borderColor = '#e2e8f0';
          btn.style.background = '#f8fafc';
        };
        btn.onclick = function () {
          selectFirm(f.id, btn);
        };
        list.appendChild(btn);
      });
    }
    var sub = document.getElementById('sub-screen');
    if (sub) sub.style.display = 'none';
    el.style.display = 'flex';
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  async function selectFirm(firmId, btn) {
    var errEl = document.getElementById('cafh-firm-pick-err');
    if (!_pendingSelection) return;
    if (btn) {
      btn.disabled = true;
      btn.style.opacity = '0.7';
    }
    try {
      var r = await fetch('/api/subscription/select-firm', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          firm_id: firmId,
          selection_token: _pendingSelection.token,
          email: _pendingSelection.email
        })
      });
      var d = await r.json().catch(function () {
        return {};
      });
      if (!r.ok) throw new Error(d.detail || 'Could not select firm');
      finishVerify(d);
      var pick = document.getElementById('cafh-firm-pick-screen');
      if (pick) pick.style.display = 'none';
      _pendingSelection = null;
    } catch (e) {
      if (errEl) {
        errEl.textContent = e.message || 'Selection failed';
        errEl.style.display = 'block';
      }
      if (btn) {
        btn.disabled = false;
        btn.style.opacity = '1';
      }
    }
  }

  function finishVerify(d) {
    var tok = d.subscription_token;
    if (!tok) throw new Error('No token returned');
    try {
      localStorage.setItem('sub_tk', tok);
      localStorage.setItem('cafirmhub_sub_token', tok);
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
  }

  window.doSubscriptionVerify = async function () {
    var input = document.getElementById('sub-id');
    var errEl =
      document.getElementById('sub-err') ||
      document.querySelector('#sub-screen .login-err, #sub-err');
    var btn = document.getElementById('sub-btn');
    var raw = ((input && input.value) || '').trim();
    if (errEl) {
      errEl.style.display = 'none';
      errEl.textContent = '';
    }
    if (!raw) {
      if (errEl) {
        errEl.textContent = 'Please enter your subscription email (or Subscription ID).';
        errEl.style.display = 'block';
      }
      return;
    }
    if (btn) {
      btn.disabled = true;
      btn.textContent = 'Verifying…';
    }
    var body = {};
    if (raw.indexOf('@') >= 0) body.email = raw.toLowerCase();
    else body.subscription_id = raw;
    try {
      var r = await fetch('/api/subscription/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      var d = await r.json().catch(function () {
        return {};
      });
      if (!r.ok) throw new Error(d.detail || 'Verification failed');
      if (d.multiple && d.firms && d.firms.length > 1) {
        showFirmPicker(d);
        return;
      }
      finishVerify(d);
    } catch (e) {
      if (errEl) {
        errEl.textContent = e.message || 'Verification failed';
        errEl.style.display = 'block';
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.textContent = 'Continue →';
      }
    }
  };

  var _fetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    try {
      var url = typeof input === 'string' ? input : (input && input.url) || '';
      init = init || {};
      if (
        url.indexOf('/api/auth/login') !== -1 &&
        init.method &&
        String(init.method).toUpperCase() === 'POST'
      ) {
        var body = init.body;
        if (typeof body === 'string') {
          try {
            var j = JSON.parse(body);
            if (!j.subscription_token) {
              var tok = '';
              try {
                tok =
                  localStorage.getItem('sub_tk') ||
                  localStorage.getItem('cafirmhub_sub_token') ||
                  '';
              } catch (e) {}
              if (tok) {
                j.subscription_token = tok;
                init = Object.assign({}, init, { body: JSON.stringify(j) });
              }
            }
          } catch (e) {}
        }
      }
      if (
        (url === '/api/superadmin/firms' || /\/api\/superadmin\/firms\/\d+$/.test(url)) &&
        init.method &&
        /POST|PUT/i.test(String(init.method))
      ) {
        var body2 = init.body;
        if (typeof body2 === 'string') {
          try {
            var j2 = JSON.parse(body2);
            var em = (document.getElementById('firm-owner-email') || {}).value || '';
            if (em) {
              j2.owner_email = em.trim().toLowerCase();
              init = Object.assign({}, init, { body: JSON.stringify(j2) });
            }
          } catch (e) {}
        }
      }
    } catch (e) {}
    return _fetch(input, init);
  };

  function enhanceSuperAdmin() {
    var mo = document.getElementById('firm-mo');
    if (!mo || document.getElementById('firm-owner-email')) return;
    var body = mo.querySelector('.md-b, .mb, .modal-body, form') || mo;
    var fg = document.createElement('div');
    fg.className = 'fg';
    fg.style.marginTop = '12px';
    fg.innerHTML =
      '<label>Subscription email *</label>' +
      '<input type="email" id="firm-owner-email" placeholder="admin@yourfirm.com" style="width:100%">' +
      '<p style="font-size:11px;color:#718096;margin-top:4px">' +
      'Users enter this email on the gate. Same email may be used on more than one firm; ' +
      'at login they will choose which firm, then use that firm’s user ID and password. ' +
      'Firm data stays fully separate.</p>';
    body.appendChild(fg);
  }

  function patchSaveFirm() {
    if (window.__cafhSaveFirmPatched) return;
    if (typeof window.saveFirm !== 'function') return;
    window.__cafhSaveFirmPatched = true;
    var origSave = window.saveFirm;
    window.saveFirm = async function () {
      var emailEl = document.getElementById('firm-owner-email');
      var email = emailEl ? emailEl.value.trim().toLowerCase() : '';
      if (!window.EDIT_FIRM_ID && !email) {
        if (typeof toast === 'function') toast('Subscription email is required', 'err');
        return;
      }
      return origSave.apply(this, arguments);
    };
  }

  var obs = new MutationObserver(function () {
    enhanceGate();
    enhanceSuperAdmin();
    patchSaveFirm();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  setTimeout(enhanceGate, 50);
  setTimeout(enhanceGate, 400);
  setTimeout(enhanceSuperAdmin, 200);
  setTimeout(patchSaveFirm, 300);
})();
