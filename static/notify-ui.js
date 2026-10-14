/* CA FirmHub — portal file download helpers only (email/WhatsApp removed) */
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
})();
