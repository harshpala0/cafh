/* CA FirmHub — MRL Maker auth + TaxGuru letter | Designed & Built by Harsh Pala */
(function () {
  function jwt() {
    return localStorage.getItem('at')
      || sessionStorage.getItem('at')
      || localStorage.getItem('token')
      || sessionStorage.getItem('token')
      || '';
  }

  var _fetch = window.fetch.bind(window);
  window.fetch = function (input, init) {
    init = init || {};
    var url = typeof input === 'string' ? input : (input && input.url) || '';
    if (url.indexOf('/api/clients') !== -1) {
      var headers = new Headers(init.headers || (input && input.headers) || {});
      var t = jwt();
      if (t) headers.set('Authorization', 'Bearer ' + t);
      if (!headers.get('Accept')) headers.set('Accept', 'application/json');
      init = Object.assign({}, init, { headers: headers });
    }
    return _fetch(input, init);
  };

  function val(id) {
    var el = document.getElementById(id);
    return el ? (el.value || '').trim() : '';
  }
  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&', '<': '<', '>': '>', '"': '"', "'": '&#39;' })[c];
    });
  }

  function taxGuruLetter() {
    var cn = val('f-client') || ((window.__clients || []).find(function () { return false; }) && '') ||
      (document.getElementById('f-client') && document.getElementById('f-client').value) || '________';
    // Prefer STATE if exposed
    var S = window.__MRL_STATE || window.STATE || {};
    if (S.client && S.client.name) cn = S.client.name;
    var m = S.meta || {};
    var auditor = m.auditorName || val('f-auditor') || 'M/s ________';
    var auditorAddr = m.auditorAddress || val('f-auditor-addr') || '';
    var letterDate = m.letterDate || val('f-date') || '________';
    var ye = m.yearEnd || val('f-ye') || '________';
    var ay = m.assessmentYear || val('f-ay') || '________';
    var sign = m.signatoryName || val('f-sign') || '________';
    var desig = m.signatoryDesignation || val('f-desig') || 'Director / Partner / Proprietor';
    var din = m.signatoryDin || val('f-din') || '';
    var place = m.place || val('f-place') || '________';
    var addr = (S.client && S.client.address) || val('f-addr') || '';
    var gstin = (S.client && S.client.gstin) || val('f-gstin') || '';
    var A = S.answers || {};

    function lineStatus(id, text) {
      var a = A[id];
      if (!a || !a.status || a.status === 'yes') return text;
      if (a.status === 'na') return text + ' [N/A for this engagement]';
      if (a.notes) return text + ' Exception: ' + a.notes;
      return text + ' [Exception — see working papers]';
    }
    var L = [];
    function t(n, text) { L.push(lineStatus('T' + n, text)); }

    L.push('[ON THE LETTER HEAD OF AUDITEE]');
    L.push('');
    L.push('Date: ' + letterDate);
    L.push('');
    L.push('To,');
    L.push(auditor);
    L.push('Chartered Accountants');
    if (auditorAddr) L.push(auditorAddr);
    L.push('');
    L.push('Sub: Management Representation in course of Tax Audit for A.Y. ' + ay);
    L.push('');
    L.push('Sir,');
    L.push('');
    L.push('Please find enclosed a copy of Form 3CD along with all relevant details for the purpose of conducting the Tax Audit of ' + cn + ', for the year ended ' + ye + '. In this connection, we further confirm that:');
    L.push('');
    t('1', '1. The address that we have reported in Clause 2 of the Form 3CD is same as we have informed to the Income Tax Department; there is no change in the same' + (addr ? ' (' + addr + ')' : '') + '.');
    t('2', '2. That the registration or identification number, if any, under indirect tax laws including excise duty, goods & service tax, sales tax, customs duty, etc. as informed to you and reported in Clause 4 of Form 3CD are correct and there is no other number other than what is reported in said clause' + (gstin ? ' [GSTIN: ' + gstin + ']' : '') + '.');
    t('3', '3. We certify, there has been no change in the partners or members or in their profit sharing ratio since the last date of the preceding year during the year under report as stated in clause 9(b) of Form 3CD.');
    t('4', '4. We certify, there has been no change in the nature of business during the year under report as stated in clause 10(a) of Form 3CD.');
    t('5', '5. That the List of books of account as prescribed u/s 44AA have been maintained and the address at which the books of accounts are kept as reported in Clause 11 has been informed by us and there are no other books and no other location at which books are kept.');
    t('6', '6. We confirm that the profit and loss account does not include any profits and gains assessable on presumptive basis under relevant sections 44AD, 44AE, 44AF, 44B, 44BB, 44BBA, 44BBB or any other relevant section as stated in clause 12 of Form 3CD.');
    t('7', '7. The assessee has followed the mercantile system of accounting & there is no change in the method of accounting employed in the immediately preceding previous year, for the preparation of final accounts for the year ended ' + ye + ' as stated in clause 13 of Form 3CD.');
    t('8', '8. We certify that the valuation of closing stock is on the same basis & there is no deviation from the method of valuation prescribed under section 145A as stated in clause 14 of Form 3CD.');
    t('9', '9. We certify that there are no capital assets which are converted into stock in trade as stated in clause 15 of Form 3CD.');
    t('10', '10. We certify there is no capital receipt which is credited to Profit & Loss Account as stated in clause 16 of Form 3CD.');
    t('11', '11. We certify that the items falling within the scope of section 28 have been correctly stated in clause 16.');
    t('12', '12. That there is no land or building or both which is transferred during the previous year for a consideration less than value adopted or assessed or assessable by any authority of a State Government referred to in section 43CA or 50C, other than what is informed by us and has been reported in Clause 17 of Form 3CD.');
    t('13', '13. We follow a policy of capitalizing an asset only after the asset has been purchased and has been put to use. The date on which the asset is put to use is as certified by us in Clause 18 of Form 3CD.');
    t('14', '14. We certify that particulars of depreciation allowable as per the Income-tax Act, 1961 in respect of each asset or block of assets, as the case may be, are correct.');
    t('15', '15. We certify that there is no sum paid to an employee as bonus or commission for service rendered, where such sum was otherwise payable to him as profit or dividend as stated in clause 20 of Form 3CD.');
    t('16', "16. The employee's and employer's share contributed towards provident fund, pension fund and ESI, date of deposit and amount of deposit is correctly stated in clause 20(b) of Form 3CD.");
    t('17', '17. No Capital Expenses have been debited to any Revenue Accounts as stated in clause 21(a) of Form 3CD.');
    t('18', '18. All the expenses incurred during the Year by us are for the purpose of business only.');
    t('19', '19. No personal expenses, except those under contractual obligations or by generally accepted business practice, have been charged to the profit & loss account.');
    t('20', '20. We certify that there is no expenditure on advertisement in any souvenir, brochure, tract, pamphlet etc. published by a political party. Further we confirm that we have not made any expenditure at clubs.');
    t('21', '21. There have been no amounts in the nature of penalties or fines levied on us other than what has been disclosed in Clause 21(a).');
    t('22', '22. We have not made any payments otherwise than Account payee cheque, above Rs. 10,000/- (Rs. 35,000 in case of Transporters) covered u/s 40A(3) or Section 40A(3A) during the year except those which have been disclosed in Clause 21(d).');
    t('23', '23. No sums have been paid by the company as an employer which is not allowable u/s 40A(7) of the Income Tax Act, 1961 as stated in Clause 21(e).');
    t('24', '24. We have not incurred any liability of a contingent nature as stated in Clause 21(g).');
    t('25', '25. No amount of interest inadmissible under section 23 of the Micro, Small and Medium Enterprises Development Act, 2006 other than stated in Clause 22.');
    t('26', '26. All transactions with any related party within the meaning of section 40A(2)(b) of the Act, have been disclosed in Clause 23.');
    t('27', '27. No amounts deemed to be profits and gains under section 32AC or 32AD or 33AB or 33ABA or 33AC other than stated in Clause 24.');
    t('28', '28. There is no amount of profit chargeable to tax u/s 41 as disclosed under clause 25 of Form 3CD.');
    t('29', '29. All the statutory dues have been deposited on time as disclosed under clause 26.');
    t('30', '30. That during the previous year we have not received any property, being share of a company not being a company in which the public are substantially interested, without consideration or for inadequate consideration as referred to in section 56(2)(viia) under clause 28 of Form 3CD.');
    t('31', '31. That during the previous year we have not received any consideration for issue of shares which exceeds the fair market value of the shares as referred to in section 56(2)(viib) under clause 29 of Form 3CD.');
    t('32', '32. That we have not accepted or repaid any amount borrowed on hundi or any amount due thereon in contravention to Section 269SS and 269T of the Act (including interest on the amount borrowed), otherwise than through an account payee cheque, bank draft, Online payments as stated in clause 30 & 31 of Form 3CD.');
    t('33', '33. That we have not incurred any loss referred to in section 73A of the Act in respect of any specified business during the previous year as stated in clause 32 of Form 3CD.');
    t('34', '34. That the company is not deemed to be carrying on a speculation business as referred in explanation to section 73 as stated in clause 32 of Form 3CD.');
    t('35', '35. There are no deductions under Chapter VI-A other than those stated in Clause 33.');
    t('36', '36. The taxes deducted at source by us under the provisions of the Income-tax Act during the year have been paid to the Central Government except those which have been disclosed in Clause 34(a).');
    t('37', '37. The statement of tax deducted or collected contains information about all transactions which are required to be reported under Clause 34(b) of the Form 3CD.');
    t('38', '38. Interest payable u/s 201(1A) and 206C(7) of the Act have been paid which have been disclosed in Clause 34(c).');
    t('39', '39. We certify that stock quantities furnished in Clause 35 of Form 3CD has been valued & certified by us.');
    t('40', '40. No Cost Audit was carried out during the relevant Assessment year as reported in the clause 37.');
    t('41', '41. No audit under Central Excise Act was carried out during the relevant Assessment year as reported in the clause 38.');
    t('42', '42. No audit was conducted under section 72A of the Finance Act, 1994 in relation to valuation of taxable services during the relevant Assessment year as reported in clause 39.');
    t('43', '43. The basis of calculation of ratios as specified in clause 40 of Form 3CD is correct.');
    t('44', '44. That there is no demand raised or refund issued during the previous year under any tax laws other than Income Tax Act, 1961 and Wealth tax Act, 1957 as required in Clause 41.');
    t('45', '45. We also certify information furnished in Clause 1 to 44 & Annexures of Form 3CD are true and correct.');
    L.push('');
    L.push('By order of the Board / For ' + cn);
    L.push('');
    L.push('Sd/-');
    L.push(sign);
    L.push(desig);
    if (din) L.push('DIN- ' + din);
    L.push('');
    L.push('Place:- ' + place);
    L.push('Date:- ' + letterDate);
    L.push('');
    L.push('— CA FirmHub MRL Maker · Designed & Built by Harsh Pala —');
    L.push('(Format adapted from TaxGuru draft MRL on Tax Audit)');
    return L.join('\n');
  }

  window.buildTaxLetter = taxGuruLetter;

  function installBuildLetter() {
    var orig = window.buildLetter;
    if (!orig || orig.__taxguru) return;
    function wrapped() {
      var mode = (window.__MRL_STATE && window.__MRL_STATE.mode) || (window.STATE && window.STATE.mode) || 'tax';
      // Detect tax from UI if needed
      var taxBtn = document.querySelector('.status-row button.on-yes');
      if (taxBtn && /Tax Audit/i.test(taxBtn.textContent)) mode = 'tax';
      if (mode === 'tax') {
        var text = taxGuruLetter();
        window.__letterText = text;
        var content = document.getElementById('content');
        if (content) {
          content.innerHTML = '<div class="card"><h3>Management Representation Letter</h3>' +
            '<p class="muted">TaxGuru draft format (45 points). Print for Times New Roman PDF.</p>' +
            '<div style="margin:12px 0;display:flex;gap:8px;flex-wrap:wrap">' +
            '<button class="btn btn-g" type="button" onclick="printLetter()">Print / Save as PDF</button>' +
            '<button class="btn" type="button" onclick="downloadHtml()">Download HTML</button>' +
            '<button class="btn" type="button" onclick="copyLetter()">Copy text</button></div>' +
            '<div id="letter-preview">' + esc(text) + '</div></div>';
        }
        var pt = document.getElementById('page-title');
        if (pt) pt.textContent = 'Full letter';
        return;
      }
      return orig.apply(this, arguments);
    }
    wrapped.__taxguru = true;
    window.buildLetter = wrapped;
  }

  function retryClients() {
    var sel = document.getElementById('client-sel');
    if (!sel) return;
    var tok = jwt();
    if (!tok) {
      sel.innerHTML = '<option value="">Not logged in — open main CA FirmHub, log in, then refresh this page</option>';
      return;
    }
    // Always force reload so JWT is applied
    sel.innerHTML = '<option value="">Loading clients…</option>';
    fetch('/api/clients/', { headers: { Authorization: 'Bearer ' + tok, Accept: 'application/json' } })
      .then(function (r) {
        if (!r.ok) throw new Error(r.status === 401 ? 'Session expired — log in again on main app' : 'HTTP ' + r.status);
        return r.json();
      })
      .then(function (list) {
        window.__clients = Array.isArray(list) ? list : (list.clients || list.data || []);
        if (!window.__clients.length) {
          sel.innerHTML = '<option value="">No clients in register</option>';
          return;
        }
        sel.innerHTML = '<option value="">— Select client —</option>' +
          window.__clients.map(function (c) {
            return '<option value="' + c.id + '">' + (c.name || '') +
              (c.pan ? ' (' + c.pan + ')' : '') + '</option>';
          }).join('');
      })
      .catch(function (e) {
        sel.innerHTML = '<option value="">' + (e.message || 'Failed to load') + '</option>';
      });
  }

  setTimeout(installBuildLetter, 200);
  setTimeout(installBuildLetter, 800);
  setTimeout(retryClients, 300);
  setTimeout(retryClients, 1200);
  var obs = new MutationObserver(function () {
    installBuildLetter();
    var sel = document.getElementById('client-sel');
    if (sel && sel.options.length <= 1 && /Loading|Not logged|Failed|Select client|No clients/i.test(sel.options[0] && sel.options[0].text || '')) {
      // only auto-retry when empty/error
    }
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
})();
