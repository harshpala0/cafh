/* CA FirmHub — notify helpers (email digest / WhatsApp / better downloads) */
(function () {
  if (window.__cafhNotifyUI) return;
  window.__cafhNotifyUI = true;

  var _origView = window.cafhViewPortalFiles;
  window.cafhViewPortalFiles = async function (rid) {
    try {
      var d;
      try {
        d = await api('/api/ops/portal-inbox/' + rid + '/files-v2');
      } catch (e) {
        if (_origView) return _origView(rid);
        throw e;
      }
      var files = d.files || [];
      var html = files.length ? files.map(function (f) {
        var link = f.download_url
          ? ('<a href="' + f.download_url + '" target="_blank" style="color:#004080;font-weight:600">Download</a>')
          : '<span style="color:#718096;font-size:12px">No download</span>';
        return '<div style="padding:8px 0;border-bottom:1px solid #EEF2F7;font-size:13px">' +
          '<strong>' + (f.original_filename || '') + '</strong>' +
          '<div style="font-size:11px;color:#718096">' + (f.uploaded_at || '') +
          (f.note ? (' · ' + f.note) : '') + '</div>' + link + '</div>';
      }).join('') : '<div style="padding:16px;color:#718096;text-align:center">No files uploaded yet.</div>';
      if (typeof oM === 'function') {
        oM('Files — request #' + rid, html,
          '<button class="btn btn-o" onclick="cafhShowPortalInbox()">Back</button>');
      } else {
        alert(files.length + ' file(s)');
      }
    } catch (e) { toast(e.message, 'err'); }
  };

  window.cafhSendEmailDigest = async function () {
    var to = prompt('Send digest to email (comma-separated):', '');
    if (to === null) return;
    try {
      var body = {};
      if (to.trim()) body.to = to.trim();
      var r = await api('/api/ops/notify/email-digest', { method: 'POST', body: JSON.stringify(body) });
      toast('Email sent to ' + (r.to || 'recipient'), 'ok');
    } catch (e) {
      toast(e.message || 'Email failed — set SMTP_HOST on Render', 'err');
    }
  };

  window.cafhSendWhatsAppDigest = async function () {
    var phone = prompt('WhatsApp number (with country code, e.g. 9198xxxxxxxx):', '');
    if (phone === null) return;
    try {
      var body = {};
      if (phone.trim()) body.phone = phone.trim();
      await api('/api/ops/notify/whatsapp', { method: 'POST', body: JSON.stringify(body) });
      toast('WhatsApp webhook called', 'ok');
    } catch (e) {
      toast(e.message || 'WhatsApp failed — set WHATSAPP_WEBHOOK_URL on Render', 'err');
    }
  };

  function injectNotifyBtns() {
    var pa = document.getElementById('pa');
    var pt = document.getElementById('pt');
    if (!pa || !pt) return;
    if (!(pt.textContent || '').match(/Dashboard/i)) return;
    if (document.getElementById('cafh-notify-btns')) return;
    var s = document.createElement('span');
    s.id = 'cafh-notify-btns';
    s.style.marginLeft = '6px';
    s.innerHTML =
      '<button class="btn btn-o btn-xs" onclick="cafhSendEmailDigest()">📧 Email digest</button> ' +
      '<button class="btn btn-o btn-xs" onclick="cafhSendWhatsAppDigest()">💬 WhatsApp</button>';
    pa.appendChild(s);
  }

  var obs = new MutationObserver(injectNotifyBtns);
  obs.observe(document.documentElement, { childList: true, subtree: true });
  if (document.readyState !== 'loading') injectNotifyBtns();
  else document.addEventListener('DOMContentLoaded', injectNotifyBtns);
})();
