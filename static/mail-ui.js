/* CA FirmHub — Client Mail UI | Designed & Built by Harsh Pala */
(function () {
  if (window.__cafhMailUI) return;
  window.__cafhMailUI = true;

  function api(path, opts) {
    opts = opts || {};
    var headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
    var t = (typeof T !== 'undefined' && T) || localStorage.getItem('at') || '';
    if (t) headers['Authorization'] = 'Bearer ' + t;
    return fetch(path, Object.assign({}, opts, {
      headers: headers,
      body: opts.body && typeof opts.body === 'object' ? JSON.stringify(opts.body) : opts.body
    })).then(function (r) {
      return r.json().then(function (d) {
        if (!r.ok) throw new Error(d.detail || d.message || ('HTTP ' + r.status));
        return d;
      });
    });
  }

  function toast(msg, kind) {
    if (typeof window.toast === 'function') return window.toast(msg, kind);
    alert(msg);
  }

  function injectNav() {
    var nav = document.querySelector('.side-nav');
    if (!nav || document.querySelector('[data-p="mail"]')) return;
    var anchor = nav.querySelector('[data-p="invoices"], [data-p="docregister"], [data-p="reports"]');
    var el = document.createElement('div');
    el.className = 'ni';
    el.setAttribute('data-p', 'mail');
    el.onclick = function () {
      if (typeof window.nav === 'function') window.nav('mail');
      else showMail();
    };
    el.innerHTML = '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg> Mail';
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(el, anchor);
    else nav.appendChild(el);
  }

  var _nav = window.nav;
  if (typeof _nav === 'function' && !window.__cafhMailNav) {
    window.__cafhMailNav = true;
    window.nav = function (p) {
      if (p === 'mail') {
        document.querySelectorAll('.ni').forEach(function (n) {
          n.classList.toggle('on', n.dataset.p === 'mail');
        });
        showMail();
        return;
      }
      return _nav.apply(this, arguments);
    };
  }

  function esc(s) {
    return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
  }

  async function showMail() {
    var pa = document.getElementById('pa');
    var pt = document.getElementById('pt');
    if (pt) pt.textContent = 'Mail';
    if (!pa) return;
    pa.innerHTML = '<div style="padding:24px;color:var(--text2)">Loading clients…</div>';
    var data;
    try {
      data = await api('/api/mail/recipients');
    } catch (e) {
      pa.innerHTML = '<div style="padding:24px;color:var(--err)">' + (e.message || 'Failed to load') + '</div>';
      return;
    }
    var settings = data.settings || {};
    var clients = data.clients || [];
    var smtpOk = settings.smtp_configured;

    pa.innerHTML =
      '<div style="padding:16px 20px;max-width:960px">' +
      '<div class="card" style="margin-bottom:16px">' +
      '<div class="card-h">Firm mail identity (Admin)</div>' +
      '<div class="card-b">' +
      (smtpOk
        ? '<p style="font-size:12.5px;color:var(--ok);margin-bottom:10px">✓ SMTP is configured on the server.</p>'
        : '<p style="font-size:12.5px;color:var(--warn);margin-bottom:10px">⚠ SMTP not configured. Set SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM on Render (or host) env.</p>') +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">' +
      '<div class="fg"><label>From name</label><input id="mail-from-name" value="' + esc(settings.from_name) + '" placeholder="Your CA Firm"></div>' +
      '<div class="fg"><label>Your email (Reply-To)</label><input id="mail-from-email" type="email" value="' + esc(settings.from_email) + '" placeholder="you@firm.com"></div>' +
      '</div>' +
      '<div class="fg" style="margin-top:10px"><label>Signature (appended to every mail)</label>' +
      '<textarea id="mail-sig" rows="3" style="width:100%;padding:10px;border-radius:8px;border:1.5px solid var(--border);font:inherit">' + esc(settings.signature) + '</textarea></div>' +
      '<button class="btn btn-o btn-s" style="margin-top:10px" onclick="window.__saveMailSettings()">Save mail identity</button>' +
      '<p style="font-size:11.5px;color:var(--text3);margin-top:8px">Select clients below — only their contact_email from client master is used.</p>' +
      '</div></div>' +
      '<div class="card">' +
      '<div class="card-h">Compose to clients</div>' +
      '<div class="card-b">' +
      '<div class="fg"><label>Subject</label><input id="mail-subj" placeholder="e.g. Documents required for tax audit FY 2025-26" style="width:100%"></div>' +
      '<div class="fg" style="margin-top:10px"><label>Message</label>' +
      '<textarea id="mail-body" rows="8" style="width:100%;padding:12px;border-radius:8px;border:1.5px solid var(--border);font:inherit" ' +
      'placeholder="Dear Sir/Madam,\n\nPlease share the pending documents…\n\nUse {{client_name}} for the client name."></textarea></div>' +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin:14px 0 8px">' +
      '<div style="font-size:13px;font-weight:600;color:var(--icai-navy)">Select clients (' + data.with_email + ' with email / ' + data.without_email + ' without)</div>' +
      '<div style="display:flex;gap:8px">' +
      '<button class="btn btn-o btn-xs" onclick="window.__mailSelect(true)">Select all with email</button>' +
      '<button class="btn btn-o btn-xs" onclick="window.__mailSelect(false)">Clear</button>' +
      '</div></div>' +
      '<div id="mail-client-list" style="max-height:280px;overflow:auto;border:1px solid var(--border-l);border-radius:10px">' +
      clients.map(function (c) {
        var dis = c.has_email ? '' : 'disabled';
        var muted = c.has_email ? '' : 'opacity:.55';
        return '<label style="display:flex;gap:10px;align-items:center;padding:10px 12px;border-bottom:1px solid var(--border-l);cursor:pointer;' + muted + '">' +
          '<input type="checkbox" class="mail-cid" value="' + c.id + '" ' + dis + '>' +
          '<div style="flex:1"><strong>' + esc(c.name) + '</strong>' +
          '<div style="font-size:12px;color:var(--text3)">' +
          (c.has_email ? esc(c.contact_email) : '<span style="color:var(--warn)">No contact email on file</span>') +
          (c.contact_person ? ' · ' + esc(c.contact_person) : '') +
          '</div></div></label>';
      }).join('') +
      '</div>' +
      '<button class="btn btn-p" style="margin-top:14px" onclick="window.__sendMail()">Send mail →</button>' +
      '<div id="mail-result" style="margin-top:12px;font-size:13px"></div>' +
      '</div></div></div>';
  }

  window.__saveMailSettings = async function () {
    try {
      await api('/api/mail/settings', {
        method: 'PUT',
        body: {
          from_name: (document.getElementById('mail-from-name') || {}).value || '',
          from_email: (document.getElementById('mail-from-email') || {}).value || '',
          reply_to: (document.getElementById('mail-from-email') || {}).value || '',
          signature: (document.getElementById('mail-sig') || {}).value || ''
        }
      });
      toast('Mail identity saved');
    } catch (e) {
      toast(e.message || 'Save failed', 'err');
    }
  };

  window.__mailSelect = function (on) {
    document.querySelectorAll('.mail-cid:not([disabled])').forEach(function (cb) {
      cb.checked = !!on;
    });
  };

  window.__sendMail = async function () {
    var ids = Array.from(document.querySelectorAll('.mail-cid:checked')).map(function (c) {
      return parseInt(c.value, 10);
    });
    var subject = (document.getElementById('mail-subj') || {}).value || '';
    var body = (document.getElementById('mail-body') || {}).value || '';
    var resEl = document.getElementById('mail-result');
    if (!ids.length) { toast('Select at least one client with email', 'err'); return; }
    if (!subject.trim()) { toast('Enter subject', 'err'); return; }
    if (!body.trim()) { toast('Enter message', 'err'); return; }
    if (resEl) resEl.textContent = 'Sending…';
    try {
      var r = await fetch('/api/mail/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + ((typeof T !== 'undefined' && T) || localStorage.getItem('at') || '')
        },
        body: JSON.stringify({ client_ids: ids, subject: subject, body: body })
      });
      var d = await r.json().catch(function () { return {}; });
      if (resEl) {
        resEl.innerHTML =
          '<div style="padding:10px 12px;border-radius:8px;background:' +
          (d.sent_count ? 'var(--ok-bg)' : 'var(--err-bg)') + '">' +
          (d.detail || '') +
          (d.errors && d.errors.length
            ? '<div style="margin-top:6px;font-size:12px">' + d.errors.map(function (e) {
                return esc(e.name) + ': ' + esc(e.error);
              }).join('<br>') + '</div>'
            : '') +
          '</div>';
      }
      if (d.sent_count) toast('Sent to ' + d.sent_count + ' client(s)');
      else toast((d.detail || (d.errors && d.errors[0] && d.errors[0].error) || 'Send failed'), 'err');
    } catch (e) {
      toast(e.message || 'Send failed', 'err');
      if (resEl) resEl.textContent = e.message || 'Failed';
    }
  };

  window.showMail = showMail;

  var obs = new MutationObserver(function () { injectNav(); });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  setTimeout(injectNav, 200);
  setTimeout(injectNav, 1000);
})();
