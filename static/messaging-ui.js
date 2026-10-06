/* CA FirmHub — Client messaging UI (Designed & Built by Harsh Pala) */
(function () {
  if (window.__cafhMessagingUI) return;
  window.__cafhMessagingUI = true;

  function openModal(title, bodyHtml, footerHtml) {
    if (typeof oM === 'function') {
      oM(title, bodyHtml, footerHtml || '');
      return;
    }
    var old = document.getElementById('cafh-modal');
    if (old) old.remove();
    var wrap = document.createElement('div');
    wrap.id = 'cafh-modal';
    wrap.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:9999;display:flex;align-items:center;justify-content:center;padding:16px';
    wrap.innerHTML = '<div style="background:#fff;border-radius:12px;max-width:560px;width:100%;max-height:90vh;overflow:auto;box-shadow:0 20px 50px rgba(0,0,0,.25)">' +
      '<div style="padding:16px 18px;border-bottom:1px solid #E4EAF2;font-weight:700;color:#003366">' + title + '</div>' +
      '<div style="padding:16px 18px">' + bodyHtml + '</div>' +
      '<div style="padding:12px 18px;border-top:1px solid #E4EAF2;display:flex;gap:8px;justify-content:flex-end;flex-wrap:wrap">' + (footerHtml || '') + '</div></div>';
    wrap.onclick = function (e) { if (e.target === wrap) wrap.remove(); };
    document.body.appendChild(wrap);
  }
  function closeModal() {
    if (typeof cM === 'function') try { cM(); } catch (e) {}
    var m = document.getElementById('cafh-modal');
    if (m) m.remove();
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
    });
  }

  window.cafhMsgSettings = async function () {
    var s = { notify_email: '', notify_phone: '', notify_from_name: '', smtp_ready: false, whatsapp_ready: false };
    try {
      s = await api('/api/ops/messaging/settings');
    } catch (e) {
      toast((e && e.message) ? e.message : 'Could not load settings', 'err');
      return;
    }
    openModal(
      'My contact details (for client messages)',
      '<p style="font-size:12px;color:#4A5568;margin-bottom:12px">Save <strong>your</strong> email &amp; phone once. Messages go to each client&rsquo;s contact details from Client Ledger.</p>' +
      '<div class="fg"><label style="font-size:11px;font-weight:600">Your / firm display name</label>' +
      '<input id="cafh-msg-name" value="' + esc(s.notify_from_name || '') + '" placeholder="e.g. Harsh Pala &amp; Associates" style="width:100%;padding:8px;margin-top:4px;border:1.5px solid #D1DAEA;border-radius:6px"></div>' +
      '<div class="fg" style="margin-top:10px"><label style="font-size:11px;font-weight:600">Your email</label>' +
      '<input id="cafh-msg-email" type="email" value="' + esc(s.notify_email || '') + '" placeholder="you@firm.com" style="width:100%;padding:8px;margin-top:4px;border:1.5px solid #D1DAEA;border-radius:6px"></div>' +
      '<div class="fg" style="margin-top:10px"><label style="font-size:11px;font-weight:600">Your phone (WhatsApp)</label>' +
      '<input id="cafh-msg-phone" value="' + esc(s.notify_phone || '') + '" placeholder="9198xxxxxxxx" style="width:100%;padding:8px;margin-top:4px;border:1.5px solid #D1DAEA;border-radius:6px"></div>' +
      '<p style="font-size:11px;margin-top:12px;padding:10px;border-radius:8px;background:' + (s.smtp_ready ? '#E6F4EA' : '#FEF3C7') + ';color:#1A202C">' +
      (s.smtp_ready
        ? '✓ Email server (SMTP) is configured — you can send mail to clients.'
        : '⚠ Email will not send until you add SMTP settings on Render:<br>SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_FROM') +
      '<br>' +
      (s.whatsapp_ready
        ? '✓ WhatsApp webhook is configured.'
        : '⚠ WhatsApp needs WHATSAPP_WEBHOOK_URL on Render (optional).') +
      '</p>',
      '<button class="btn btn-o" onclick="(window.cM?cM():document.getElementById(\'cafh-modal\')?.remove())">Cancel</button>' +
      '<button class="btn btn-p" onclick="cafhMsgSaveSettings()">Save</button>'
    );
  };

  window.cafhMsgSaveSettings = async function () {
    var body = {
      notify_from_name: (document.getElementById('cafh-msg-name') || {}).value || '',
      notify_email: (document.getElementById('cafh-msg-email') || {}).value || '',
      notify_phone: (document.getElementById('cafh-msg-phone') || {}).value || ''
    };
    try {
      await api('/api/ops/messaging/settings', { method: 'PUT', body: JSON.stringify(body) });
      toast('Your contact details saved', 'ok');
      closeModal();
    } catch (e) {
      toast(e.message || 'Save failed', 'err');
    }
  };

  window.cafhMsgCompose = async function () {
    var clients = [];
    try {
      clients = await api('/api/ops/messaging/clients');
    } catch (e) {
      toast(e.message || 'Could not load clients', 'err');
      return;
    }
    if (!clients.length) {
      toast('No active clients. Add clients with email/phone in Client Ledger.', 'err');
      return;
    }
    var list = clients.map(function (c) {
      var meta = [];
      if (c.contact_email) meta.push(c.contact_email);
      if (c.contact_phone) meta.push(c.contact_phone);
      if (!meta.length) meta.push('No email/phone — will skip');
      return '<label style="display:flex;align-items:flex-start;gap:8px;padding:8px 0;border-bottom:1px solid #EEF2F7;font-size:13px;cursor:pointer">' +
        '<input type="checkbox" class="cafh-msg-cl" value="' + c.id + '" style="margin-top:3px" ' +
        ((c.can_email || c.can_whatsapp) ? '' : 'disabled') + '>' +
        '<span><strong>' + esc(c.name) + '</strong>' +
        '<div style="font-size:11px;color:#718096">' + esc(meta.join(' · ')) + '</div></span></label>';
    }).join('');

    openModal(
      'Message clients',
      '<p style="font-size:12px;color:#4A5568;margin-bottom:8px">Select clients. Mail goes to <strong>their</strong> contact email from Client Ledger. Requires SMTP on Render.</p>' +
      '<div style="max-height:180px;overflow:auto;margin-bottom:12px;border:1px solid #E4EAF2;border-radius:8px;padding:4px 10px">' + list + '</div>' +
      '<div class="fg"><label style="font-size:11px;font-weight:600">Channel</label>' +
      '<select id="cafh-msg-channel" style="width:100%;padding:8px;margin-top:4px;border:1.5px solid #D1DAEA;border-radius:6px">' +
      '<option value="email">Email only</option>' +
      '<option value="whatsapp">WhatsApp only</option>' +
      '<option value="both">Email + WhatsApp</option></select></div>' +
      '<div class="fg" style="margin-top:10px"><label style="font-size:11px;font-weight:600">Subject (email)</label>' +
      '<input id="cafh-msg-subject" value="Message from CA FirmHub" style="width:100%;padding:8px;margin-top:4px;border:1.5px solid #D1DAEA;border-radius:6px"></div>' +
      '<div class="fg" style="margin-top:10px"><label style="font-size:11px;font-weight:600">Message *</label>' +
      '<textarea id="cafh-msg-body" rows="4" placeholder="Write your message…" style="width:100%;padding:8px;margin-top:4px;border:1.5px solid #D1DAEA;border-radius:6px"></textarea></div>',
      '<button class="btn btn-o" onclick="(window.cM?cM():document.getElementById(\'cafh-modal\')?.remove())">Cancel</button>' +
      '<button class="btn btn-p" onclick="cafhMsgDoSend()">Send</button>'
    );
  };

  window.cafhMsgDoSend = async function () {
    var boxes = document.querySelectorAll('.cafh-msg-cl:checked');
    var ids = Array.prototype.map.call(boxes, function (b) { return parseInt(b.value, 10); });
    if (!ids.length) {
      toast('Select at least one client', 'err');
      return;
    }
    var message = ((document.getElementById('cafh-msg-body') || {}).value || '').trim();
    if (!message) {
      toast('Message is required', 'err');
      return;
    }
    var body = {
      client_ids: ids,
      channel: (document.getElementById('cafh-msg-channel') || {}).value || 'email',
      subject: (document.getElementById('cafh-msg-subject') || {}).value || '',
      message: message
    };
    try {
      var r = await api('/api/ops/messaging/send', { method: 'POST', body: JSON.stringify(body) });
      var reason = '';
      if (r.results && r.results.length) {
        var parts = [];
        r.results.forEach(function (row) {
          if (row.email && !row.email.ok) parts.push((row.client_name || '') + ' email: ' + (row.email.detail || 'failed'));
          if (row.whatsapp && !row.whatsapp.ok) parts.push((row.client_name || '') + ' WhatsApp: ' + (row.whatsapp.detail || 'failed'));
        });
        if (parts.length) reason = ' — ' + parts.slice(0, 2).join('; ');
      }
      if (r.sent_ok) {
        toast('Sent to ' + r.sent_ok + ' of ' + r.total + ' clients', 'ok');
      } else {
        toast('Sent to 0 of ' + (r.total || 0) + ' clients' + reason, 'err');
      }
      closeModal();
    } catch (e) {
      toast(e.message || 'Send failed — set SMTP_* on Render', 'err');
    }
  };

  window.cafhSendEmailDigest = function () { cafhMsgCompose(); };
  window.cafhSendWhatsAppDigest = function () { cafhMsgCompose(); };

  function injectMsgButtons() {
    var pa = document.getElementById('pa');
    var pt = document.getElementById('pt');
    if (!pa || !pt) return;
    if (!(pt.textContent || '').match(/Dashboard/i)) return;
    if (document.getElementById('cafh-msg-btns')) return;
    var s = document.createElement('span');
    s.id = 'cafh-msg-btns';
    s.style.marginLeft = '6px';
    s.innerHTML =
      '<button class="btn btn-o btn-xs" onclick="cafhMsgSettings()">👤 My contact</button> ' +
      '<button class="btn btn-o btn-xs" onclick="cafhMsgCompose()">✉️ Message clients</button>';
    pa.appendChild(s);
  }

  var obs = new MutationObserver(injectMsgButtons);
  obs.observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState !== 'loading') injectMsgButtons();
  else document.addEventListener('DOMContentLoaded', injectMsgButtons);
})();
