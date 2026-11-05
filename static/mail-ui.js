/* CA FirmHub — Client Mail UI | Designed & Built by Harsh Pala */
(function () {
  if (window.__cafhMailUI) return;
  window.__cafhMailUI = true;

  function token() {
    try {
      if (typeof T !== 'undefined' && T) return T;
    } catch (e) {}
    try {
      return localStorage.getItem('at') || localStorage.getItem('token') || '';
    } catch (e) {
      return '';
    }
  }

  function api(path, opts) {
    opts = opts || {};
    var headers = Object.assign({}, opts.headers || {});
    if (!headers['Content-Type'] && opts.body) headers['Content-Type'] = 'application/json';
    var t = token();
    if (t) headers['Authorization'] = 'Bearer ' + t;
    var body = opts.body;
    if (body && typeof body === 'object') body = JSON.stringify(body);
    return fetch(path, {
      method: opts.method || 'GET',
      headers: headers,
      body: body
    }).then(function (r) {
      return r.text().then(function (text) {
        var d = {};
        if (text) {
          try {
            d = JSON.parse(text);
          } catch (e) {
            if (!r.ok) {
              throw new Error('Server error (' + r.status + '). Is the Mail module deployed?');
            }
            throw new Error('Invalid server response (not JSON)');
          }
        }
        if (!r.ok) throw new Error(d.detail || d.message || ('HTTP ' + r.status));
        return d;
      });
    });
  }

  function toast(msg, kind) {
    if (typeof window.toast === 'function') return window.toast(msg, kind);
    console.log(msg);
  }

  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&')
      .replace(/</g, '<')
      .replace(/>/g, '>')
      .replace(/"/g, '"');
  }

  function injectNav() {
    var sideNav = document.querySelector('.side-nav');
    if (!sideNav || document.querySelector('.ni[data-p="mail"]')) return;
    var el = document.createElement('div');
    el.className = 'ni';
    el.setAttribute('data-p', 'mail');
    el.innerHTML =
      '<svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2">' +
      '<path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>' +
      '<polyline points="22,6 12,13 2,6"/></svg> Mail';
    el.addEventListener('click', function (e) {
      e.preventDefault();
      e.stopPropagation();
      openMailPage();
    });
    var anchor =
      sideNav.querySelector('[data-p="invoices"]') ||
      sideNav.querySelector('[data-p="docregister"]') ||
      sideNav.querySelector('[data-p="reports"]');
    if (anchor && anchor.parentNode) anchor.parentNode.insertBefore(el, anchor);
    else sideNav.appendChild(el);
  }

  function openMailPage() {
    document.querySelectorAll('.ni').forEach(function (n) {
      n.classList.toggle('on', n.getAttribute('data-p') === 'mail');
    });
    var pt = document.getElementById('pt');
    var pa = document.getElementById('pa');
    var pb = document.getElementById('pb');
    if (pt) pt.textContent = 'Mail';
    if (pa) pa.innerHTML = '';
    if (pb) pb.innerHTML = '<div style="padding:24px;color:var(--text2)">Loading mail…</div>';
    showMail().catch(function (e) {
      var target = document.getElementById('pb') || document.getElementById('pa');
      if (target) {
        target.innerHTML =
          '<div style="padding:24px">' +
          '<div style="color:var(--err);font-weight:600;margin-bottom:8px">Could not open Mail</div>' +
          '<div style="color:var(--text2);font-size:13px">' + esc(e.message || String(e)) + '</div>' +
          '<p style="margin-top:12px;font-size:12.5px;color:var(--text3)">If this persists, hard-refresh after deploy.</p>' +
          '</div>';
      }
      toast(e.message || 'Mail failed', 'err');
    });
  }

  function patchNav() {
    if (window.__cafhMailNav) return;
    if (typeof window.nav !== 'function') return;
    window.__cafhMailNav = true;
    var orig = window.nav;
    window.nav = function (p) {
      if (p === 'mail') {
        openMailPage();
        return;
      }
      return orig.apply(this, arguments);
    };
  }

  async function showMail() {
    var pb = document.getElementById('pb');
    if (!pb) throw new Error('Content panel (#pb) not found');

    var data = await api('/api/mail/recipients');
    var settings = data.settings || {};
    var clients = data.clients || [];
    var smtpOk = !!settings.smtp_configured;

    pb.innerHTML =
      '<div style="padding:16px 20px;max-width:960px">' +
      '<div class="card" style="margin-bottom:16px">' +
      '<div class="card-h">Firm mail identity (Admin)</div>' +
      '<div class="card-b">' +
      (smtpOk
        ? '<p style="font-size:12.5px;color:var(--ok);margin-bottom:10px">✓ SMTP is configured on the server.</p>'
        : '<p style="font-size:12.5px;color:var(--warn);margin-bottom:10px">⚠ SMTP not configured yet. Add SMTP_* env vars on Render (see setup guide).</p>') +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">' +
      '<div class="fg"><label>From name</label>' +
      '<input id="mail-from-name" value="' + esc(settings.from_name) + '" placeholder="Your CA Firm"></div>' +
      '<div class="fg"><label>Your email (Reply-To)</label>' +
      '<input id="mail-from-email" type="email" value="' + esc(settings.from_email) + '" placeholder="you@firm.com"></div>' +
      '</div>' +
      '<div class="fg" style="margin-top:10px"><label>Signature (appended to every mail)</label>' +
      '<textarea id="mail-sig" rows="3" style="width:100%;padding:10px;border-radius:8px;border:1.5px solid var(--border);font:inherit">' +
      esc(settings.signature) +
      '</textarea></div>' +
      '<button type="button" class="btn btn-o btn-s" style="margin-top:10px" id="mail-save-btn">Save mail identity</button>' +
      '<p style="font-size:11.5px;color:var(--text3);margin-top:8px">Mails go only to contact_email stored on each client.</p>' +
      '</div></div>' +
      '<div class="card">' +
      '<div class="card-h">Compose to clients</div>' +
      '<div class="card-b">' +
      '<div class="fg"><label>Subject</label>' +
      '<input id="mail-subj" placeholder="e.g. Documents required for tax audit" style="width:100%"></div>' +
      '<div class="fg" style="margin-top:10px"><label>Message</label>' +
      '<textarea id="mail-body" rows="8" style="width:100%;padding:12px;border-radius:8px;border:1.5px solid var(--border);font:inherit" ' +
      'placeholder="Dear Sir/Madam,\n\nPlease share the pending documents…\n\nUse {{client_name}} for the client name."></textarea></div>' +
      '<div style="display:flex;justify-content:space-between;align-items:center;margin:14px 0 8px;flex-wrap:wrap;gap:8px">' +
      '<div style="font-size:13px;font-weight:600;color:var(--icai-navy)">Select clients (' +
      (data.with_email || 0) +
      ' with email / ' +
      (data.without_email || 0) +
      ' without)</div>' +
      '<div style="display:flex;gap:8px">' +
      '<button type="button" class="btn btn-o btn-xs" id="mail-sel-all">Select all with email</button>' +
      '<button type="button" class="btn btn-o btn-xs" id="mail-sel-none">Clear</button>' +
      '</div></div>' +
      '<div id="mail-client-list" style="max-height:280px;overflow:auto;border:1px solid var(--border-l);border-radius:10px">' +
      (clients.length
        ? clients
            .map(function (c) {
              var dis = c.has_email ? '' : ' disabled';
              var muted = c.has_email ? '' : 'opacity:.55';
              return (
                '<label style="display:flex;gap:10px;align-items:center;padding:10px 12px;border-bottom:1px solid var(--border-l);cursor:pointer;' +
                muted +
                '">' +
                '<input type="checkbox" class="mail-cid" value="' +
                c.id +
                '"' +
                dis +
                '>' +
                '<div style="flex:1"><strong>' +
                esc(c.name) +
                '</strong>' +
                '<div style="font-size:12px;color:var(--text3)">' +
                (c.has_email
                  ? esc(c.contact_email)
                  : '<span style="color:var(--warn)">No contact email on file</span>') +
                (c.contact_person ? ' · ' + esc(c.contact_person) : '') +
                '</div></div></label>'
              );
            })
            .join('')
        : '<div style="padding:16px;color:var(--text3)">No clients found. Add clients first.</div>') +
      '</div>' +
      '<button type="button" class="btn btn-p" style="margin-top:14px" id="mail-send-btn">Send mail →</button>' +
      '<div id="mail-result" style="margin-top:12px;font-size:13px"></div>' +
      '</div></div></div>';

    var saveBtn = document.getElementById('mail-save-btn');
    if (saveBtn) saveBtn.onclick = saveMailSettings;
    var selAll = document.getElementById('mail-sel-all');
    if (selAll)
      selAll.onclick = function () {
        document.querySelectorAll('.mail-cid:not([disabled])').forEach(function (cb) {
          cb.checked = true;
        });
      };
    var selNone = document.getElementById('mail-sel-none');
    if (selNone)
      selNone.onclick = function () {
        document.querySelectorAll('.mail-cid').forEach(function (cb) {
          cb.checked = false;
        });
      };
    var sendBtn = document.getElementById('mail-send-btn');
    if (sendBtn) sendBtn.onclick = sendMail;
  }

  async function saveMailSettings() {
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
  }

  async function sendMail() {
    var ids = Array.from(document.querySelectorAll('.mail-cid:checked')).map(function (c) {
      return parseInt(c.value, 10);
    });
    var subject = ((document.getElementById('mail-subj') || {}).value || '').trim();
    var body = ((document.getElementById('mail-body') || {}).value || '').trim();
    var resEl = document.getElementById('mail-result');
    if (!ids.length) {
      toast('Select at least one client with email', 'err');
      return;
    }
    if (!subject) {
      toast('Enter subject', 'err');
      return;
    }
    if (!body) {
      toast('Enter message', 'err');
      return;
    }
    if (resEl) resEl.textContent = 'Sending…';
    try {
      var r = await fetch('/api/mail/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: 'Bearer ' + token()
        },
        body: JSON.stringify({ client_ids: ids, subject: subject, body: body })
      });
      var text = await r.text();
      var d = {};
      try {
        d = text ? JSON.parse(text) : {};
      } catch (e) {
        throw new Error('Server error (' + r.status + ')');
      }
      if (resEl) {
        resEl.innerHTML =
          '<div style="padding:10px 12px;border-radius:8px;background:' +
          (d.sent_count ? 'var(--ok-bg)' : 'var(--err-bg)') +
          '">' +
          esc(d.detail || '') +
          (d.errors && d.errors.length
            ? '<div style="margin-top:6px;font-size:12px">' +
              d.errors
                .map(function (e) {
                  return esc(e.name) + ': ' + esc(e.error);
                })
                .join('<br>') +
              '</div>'
            : '') +
          '</div>';
      }
      if (d.sent_count) toast('Sent to ' + d.sent_count + ' client(s)');
      else toast(d.detail || (d.errors && d.errors[0] && d.errors[0].error) || 'Send failed', 'err');
    } catch (e) {
      toast(e.message || 'Send failed', 'err');
      if (resEl) resEl.textContent = e.message || 'Failed';
    }
  }

  window.showMail = function () {
    openMailPage();
  };

  var obs = new MutationObserver(function () {
    injectNav();
    patchNav();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  setTimeout(function () {
    injectNav();
    patchNav();
  }, 100);
  setTimeout(function () {
    injectNav();
    patchNav();
  }, 800);
  setTimeout(patchNav, 2000);
})();
