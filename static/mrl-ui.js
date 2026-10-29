/* CA FirmHub — MRL Maker (Tax Audit + Statutory Audit)
   Designed & Built by Harsh Pala
*/
(function () {
  if (window.__cafhMrlUI) return;
  window.__cafhMrlUI = true;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
      return ({ '&': '&', '<': '<', '>': '>', '"': '"', "'": '&#39;' })[c];
    });
  }

  function val(id, def) {
    var el = document.getElementById(id);
    var v = el ? String(el.value || '').trim() : '';
    return v || (def || '____________');
  }

  function todayISO() {
    return new Date().toISOString().slice(0, 10);
  }

  function fyEndFromLabel(fy) {
    try {
      var p = String(fy).split('-');
      var sy = parseInt(p[0], 10);
      if (!sy) return '31st March, 20XX';
      return '31st March, ' + (sy + 1);
    } catch (e) {
      return '31st March, 20XX';
    }
  }

  function getFY() {
    try {
      var lb = document.getElementById('fy-label');
      if (lb) {
        var m = (lb.textContent || '').match(/(\d{4}-\d{2})/);
        if (m) return m[1];
      }
    } catch (e) {}
    if (window.FY) return String(window.FY);
    return '2025-26';
  }

  function taxAuditLetter(d) {
    var lines = [];
    lines.push('To');
    lines.push(d.auditorName);
    lines.push('Chartered Accountants');
    if (d.auditorAddress) lines.push(d.auditorAddress);
    lines.push('');
    lines.push('Date: ' + d.letterDate);
    lines.push('');
    lines.push('Sub: Representation from Management for the purpose of Tax Audit under section 44AB of the Income Tax Act, 1961 for the year ended on ' + d.yearEnd + '.');
    lines.push('');
    lines.push('Respected Sir / Madam,');
    lines.push('');
    lines.push('This representation letter is provided in connection with the tax audit u/s 44AB of the Income Tax Act of ' + d.clientName + ' for the year ended ' + d.yearEnd + ' for the purpose of expressing an opinion as to whether the Form 3CD along with the annexure thereto gives a true and correct view of the facts mentioned therein. We acknowledge our responsibility to keep and maintain such books of account and other documents as may enable the tax auditor to complete tax audit u/s 44AB, in accordance with the provisions of the Income Tax Act, 1961.');
    lines.push('');
    lines.push('We confirm the following representations to the best of our knowledge and belief:');
    lines.push('');
    lines.push('1. The name of the assessee as per PAN card is ' + d.panName + '. A copy of PAN Card is available / attached.');
    lines.push('2. The assessee has no other business address than communicated to the Income-tax Department for assessment purposes' + (d.businessAddress ? ' (principal place: ' + d.businessAddress + ')' : '') + '.');
    lines.push('3. The Assessee has employed the ' + d.accountingMethod + ' system of accounting during the year.');
    lines.push('4. There has been ' + (d.changeInAccounting === 'Yes' ? 'a change' : 'no change') + ' in the method of accounting employed in the previous year as compared to that employed in the immediately preceding financial year.');
    lines.push('5. The assessee is ' + (d.indirectTax === 'Yes' ? 'liable' : 'not liable') + ' to pay indirect taxes. GSTIN (if any): ' + d.gstin + '.');
    lines.push('6. The Assessee has ' + (d.opted115 === 'Yes' ? 'opted' : 'not opted') + ' to be assessed under any of sections 115BA / 115BAA / 115BAB / 115BAC / 115BAD.');
    lines.push('7. We confirm that the profit and loss account does not include any profits and gains assessable on a presumptive basis under sections 44AD, 44AE, 44AF, 44B, 44BB, 44BBA, 44BBB or any other relevant section, except as disclosed in Form 3CD.');
    lines.push('8. The Assessee is engaged in the business as reported in clause 10(a) of Form 3CD: ' + d.natureOfBusiness + '.');
    lines.push('9. The Assessee has disclosed the nature of every business carried on by it and there is no undisclosed change in the nature of business as compared to earlier years, except as reported in Form 3CD.');
    lines.push('10. Books of account maintained: ' + d.booksList + '. Location of books: as stated in clause 11(b) of Form 3CD.');
    lines.push('11. Members / partners and profit-sharing ratio (if applicable): ' + d.partners + '.');
    lines.push('12. There are no items of the following nature which are not credited to the profit and loss account where applicable: items under section 28; drawbacks / refunds of duty or tax; escalation claims accepted; any other item of income; capital receipts — except as disclosed in Form 3CD.');
    lines.push('13. During the previous year, the assessee has not transferred any land or building for a consideration less than the value adopted or assessed or assessable under section 43CA or 50C, except as disclosed in Form 3CD.');
    lines.push('14. ICDS disclosures and any adjustments required under section 145(2) have been correctly reflected in clause 13 of Form 3CD.');
    lines.push('15. Closing stock of raw material, WIP and finished goods is valued at cost or NRV, whichever is lower. Policy change (if any) and effect on profit are disclosed in Form 3CD.');
    lines.push('16. Particulars of depreciation allowable under the Income Tax Act as required under clause 18 of Form 3CD are correct.');
    lines.push('17. Amounts admissible under sections 32AC, 32AD, 33AB, 33ABA, 35 and similar provisions debited / not debited to P&L are correctly reported in Form 3CD.');
    lines.push('18. No sum has been paid to an employee as bonus or commission for services rendered where such sum was otherwise payable as profits or dividend, except as disclosed.');
    lines.push('19. Employee contributions u/s 2(24)(x) and payments u/s 36(1)(va) as disclosed against clause 20(b) of Form 3CD are correct.');
    lines.push('20. No capital expenditure or personal expenditure has been debited to the Profit and Loss Account, except as disclosed in Form 3CD.');
    lines.push('21. No capital asset has been converted into stock-in-trade except as disclosed.');
    lines.push('22. No advertisement has been released in any souvenir / brochure published by a political party.');
    lines.push('23. No club entrance fees / subscriptions / facilities have been paid except as disclosed.');
    lines.push('24. No expenditure by way of penalty or fine for violation of law, or for any purpose which is an offence or prohibited by law, has been incurred except interest on late deposit of TDS / TCS as reported in Form 3CD (if any).');
    lines.push('25. Amounts inadmissible u/s 40(a) are only as disclosed in Form 3CD.');
    lines.push('26. In relation to expenditure covered u/s 40A(3), payments exceeding the prescribed limit have been made by account payee cheque / draft / electronic clearing, except as disclosed.');
    lines.push('27. No sums disallowed u/s 40A(9) have been paid.');
    lines.push('28. No contingent liability has been debited to the profit and loss account.');
    lines.push('29. Deduction u/s 14A (if any) is correctly computed and disclosed.');
    lines.push('30. Interest inadmissible under the proviso to section 36(1)(iii), if any, is correctly disclosed.');
    lines.push('31. Payments to persons specified u/s 40A(2)(b) as mentioned in clause 23 of Form 3CD are correct.');
    lines.push('32. There is no profit chargeable to tax u/s 41 except as disclosed.');
    lines.push('33. Amounts under section 43B (pre-existing and current year) are correctly reported in clause 26 of Form 3CD.');
    lines.push('34. CENVAT / ITC availed or utilised and treatment in accounts are correctly reported in clause 27 of Form 3CD.');
    lines.push('35. Loans / deposits accepted or repaid in excess of the prescribed limit have been by account payee cheque / draft / ECS only, except as disclosed.');
    lines.push('36. Chapter XVII-B / XVII-BB compliance (TDS/TCS) is as reported in clause 34 of Form 3CD; interest u/s 201(1A) / 206C(7) disclosed is correct.');
    lines.push('37. Quantitative details, ratios (clause 40), demands/refunds under other tax laws (clause 41), and GST expenditure reporting (clause 44) are correct as per Form 3CD.');
    lines.push('38. Statements in Form 61 / 61A / 61B and statements under section 286 (if applicable) have been complied with as required.');
    lines.push('');
    lines.push('For and on behalf of');
    lines.push(d.clientName);
    lines.push('');
    lines.push('');
    lines.push(d.signatoryName);
    lines.push(d.signatoryDesignation);
    lines.push('');
    lines.push('— Generated by CA FirmHub MRL Maker | Designed & Built by Harsh Pala —');
    lines.push('Illustrative structure for tax audit u/s 44AB; tailor clauses to facts of the engagement and Form 3CD.');
    return lines.join('\n');
  }

  function statutoryLetter(d) {
    var lines = [];
    lines.push('ON THE LETTERHEAD OF THE CLIENT');
    lines.push('');
    lines.push('MANAGEMENT REPRESENTATION LETTER IN CONNECTION WITH THE STATUTORY AUDIT OF');
    lines.push(d.clientName.toUpperCase());
    lines.push('FOR THE YEAR ENDED ' + d.yearEnd.toUpperCase());
    lines.push('');
    lines.push('To');
    lines.push(d.auditorName);
    lines.push('Chartered Accountants');
    if (d.auditorAddress) lines.push(d.auditorAddress);
    lines.push('');
    lines.push('Date: ' + d.letterDate);
    lines.push('');
    lines.push('1. This representation letter is provided in connection with your audit of the financial statements of ' + d.clientName + ' for the year ended ' + d.yearEnd + ' for the purpose of expressing an opinion as to whether the financial statements are presented fairly, in all material respects, (or give a true and fair view) in accordance with the applicable accounting standards in India. We confirm that, to the best of our knowledge and belief, having made such inquiries as we considered necessary for the purpose of appropriately informing ourselves:');
    lines.push('');
    lines.push('Representations concerning the financial statements');
    lines.push('2. We have fulfilled our responsibilities, as set out in the terms of the audit engagement dated ' + d.engagementDate + ', for the preparation of the financial statements in accordance with the applicable accounting standards in India; in particular the financial statements are fairly presented (or give a true and fair view) in accordance with the applicable accounting standards in India.');
    lines.push('3. We have provided you with: (a) access to all information of which we are aware that is relevant to the preparation of the financial statements such as records, documentation and other matters; (b) all additional information that you have requested from us for the purpose of the audit; and (c) unrestricted access to persons within the entity from whom you determined it necessary to obtain audit evidence.');
    lines.push('4. All transactions have been recorded in the accounting records and are reflected in the financial statements.');
    lines.push('5. The company has maintained proper books of account as required by law.');
    lines.push('6. The Balance Sheet, Statement of Profit and Loss, Statement of Changes in Equity (where applicable) and Cash Flow Statement (where applicable) dealt with by your audit report are in agreement with the books of account.');
    lines.push('7. In our opinion, the financial statements comply with the applicable accounting standards referred to in section 133 of the Companies Act, 2013, read with the relevant rules (to the extent applicable to the entity).');
    lines.push('8. ' + (d.hasBranches === 'Yes'
      ? 'Proper returns adequate for the purposes of your audit have been received from branches not visited by you (if any), and the accounts of those branches have been appropriately dealt with in preparing the financial statements.'
      : 'The company has no branches.'));
    lines.push('9. On the basis of written representations received from the directors as on ' + d.yearEnd + ', and taken on record by the Board of Directors (if applicable), none of the directors is disqualified as on that date from being appointed as a director in terms of Section 164(2) of the Companies Act, 2013 (to the extent applicable).');
    lines.push('10. The significant accounting policies adopted in the preparation of the financial statements are appropriately described. We believe that the selection and application of accounting policies are appropriate. The financial statements are prepared on accrual basis.');
    lines.push('');
    lines.push('Property, Plant & Equipment / Intangibles');
    lines.push('11. PPE and intangible assets (if any) are stated after accounting for additions, disposals and depreciation / amortisation in accordance with applicable AS / Ind AS and Schedule II / III requirements. Management has physically verified PPE during the year where required by policy.');
    lines.push('');
    lines.push('Inventories');
    lines.push('12. Inventories as on ' + d.yearEnd + ' have been determined under our supervision, are the property of the entity (except as disclosed), do not include goods sold pending delivery, and are valued at cost or NRV whichever is lower. Adequate provision has been considered for slow-moving / damaged / obsolete stock.');
    lines.push('');
    lines.push('Trade receivables, loans, advances and other assets');
    lines.push('13. Trade receivables, loans, advances and other current / non-current assets, except to the extent provided for, are considered good and recoverable and are appropriately disclosed as per AS / Ind AS and Schedule III (as applicable).');
    lines.push('');
    lines.push('Cash and bank balances');
    lines.push('14. Bank accounts operated by the entity are as disclosed in the financial statements. Physical cash balance as on ' + d.yearEnd + ' has been certified by management' + (d.cashBalance ? ' at Rs. ' + d.cashBalance : '') + '.');
    lines.push('');
    lines.push('Liabilities, borrowings and contingencies');
    lines.push('15. We have recorded all known liabilities. All borrowings and contractual covenants that could have a material effect on the financial statements have been disclosed. Contingent liabilities and capital commitments are completely disclosed in the notes; no contingency requiring adjustment has been omitted.');
    lines.push('');
    lines.push('Related parties');
    lines.push('16. We confirm completeness of the list of related parties and related party transactions. All related party transactions of which we are aware have been disclosed and, where required, are at arm\'s length and in the ordinary course of business, and comply with applicable provisions of the Companies Act, 2013 / AS 18 / Ind AS 24.');
    lines.push('');
    lines.push('Other matters');
    lines.push('17. No personal expenses have been charged to the revenue accounts of the entity.');
    lines.push('18. MSME suppliers list has been obtained and statutory requirements under the MSMED Act, 2006 (as applicable) have been addressed; no material claims under delayed payment provisions are outstanding except as disclosed.');
    lines.push('19. The company has not had any transaction with struck-off companies except as disclosed.');
    lines.push('20. The company has not had any crypto currency transactions during the year except as disclosed.');
    lines.push('21. Minutes of meetings of shareholders / directors / committees and statutory registers required to be maintained are complete and authentic to the best of our knowledge.');
    lines.push('22. We have disclosed the results of our assessment of the risk that the financial statements may be materially misstated as a result of fraud. We have no knowledge of fraud or suspected fraud affecting the entity involving management, employees with significant roles in internal control, or others where the fraud could have a material effect on the financial statements, except as communicated to you.');
    lines.push('23. We have disclosed all known actual or possible non-compliance with laws and regulations whose effects should be considered when preparing financial statements.');
    lines.push('24. All events subsequent to the date of the financial statements and for which applicable accounting standards require adjustment or disclosure have been adjusted or disclosed.');
    lines.push('25. The entity has disclosed all guarantees, comfort letters and similar obligations as required.');
    if (d.includeIFC === 'Yes') {
      lines.push('');
      lines.push('Internal Financial Controls (Section 143(3)(i) — where applicable)');
      lines.push('26. We are responsible for establishing and maintaining adequate and effective internal financial controls. Based on our assessment, the company had an adequate internal financial controls system over financial reporting that was operating effectively as at ' + d.yearEnd + ', except for deficiencies (if any) separately disclosed to you.');
    }
    lines.push('');
    lines.push('For and on behalf of');
    lines.push(d.clientName);
    lines.push('');
    lines.push('');
    lines.push(d.signatoryName);
    lines.push(d.signatoryDesignation);
    lines.push('');
    lines.push('— Generated by CA FirmHub MRL Maker | Designed & Built by Harsh Pala —');
    lines.push('Illustrative structure based on SA 580 and ICAI FAQs on Management Representation Letter; adapt to engagement facts.');
    return lines.join('\n');
  }

  function collect() {
    var fy = getFY();
    return {
      type: (document.getElementById('mrl-type') || {}).value || 'tax',
      clientName: val('mrl-client', 'M/s ________________'),
      panName: val('mrl-pan-name', val('mrl-client', '________________')),
      pan: val('mrl-pan', '____________'),
      gstin: val('mrl-gstin', 'Not applicable / ________'),
      businessAddress: val('mrl-addr', ''),
      auditorName: val('mrl-auditor', '________________, Chartered Accountants'),
      auditorAddress: val('mrl-auditor-addr', ''),
      letterDate: val('mrl-date', todayISO()),
      yearEnd: val('mrl-year-end', fyEndFromLabel(fy)),
      engagementDate: val('mrl-eng-date', '____________'),
      accountingMethod: (document.getElementById('mrl-acct') || {}).value || 'mercantile',
      changeInAccounting: (document.getElementById('mrl-change-acct') || {}).value || 'No',
      indirectTax: (document.getElementById('mrl-idt') || {}).value || 'Yes',
      opted115: (document.getElementById('mrl-115') || {}).value || 'No',
      natureOfBusiness: val('mrl-nob', 'as disclosed in Form 3CD'),
      booksList: val('mrl-books', 'Cash Book, Bank Book, Ledger, Journal'),
      partners: val('mrl-partners', 'Not applicable / as per deed'),
      hasBranches: (document.getElementById('mrl-branches') || {}).value || 'No',
      cashBalance: val('mrl-cash', ''),
      includeIFC: (document.getElementById('mrl-ifc') || {}).value || 'No',
      signatoryName: val('mrl-sign-name', '________________'),
      signatoryDesignation: val('mrl-sign-desig', 'Director / Partner / Proprietor')
    };
  }

  function generate() {
    var d = collect();
    var text = d.type === 'statutory' ? statutoryLetter(d) : taxAuditLetter(d);
    var pre = document.getElementById('mrl-preview');
    if (pre) pre.value = text;
    return text;
  }

  function downloadTxt() {
    var text = generate();
    var blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'MRL_' + (collect().type === 'statutory' ? 'Statutory' : 'TaxAudit') + '_' + (collect().clientName || 'Client').replace(/[^\w]+/g, '_').slice(0, 40) + '.txt';
    a.click();
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
    if (typeof toast === 'function') toast('Downloaded', 'ok');
  }

  function copyText() {
    var text = generate();
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        if (typeof toast === 'function') toast('Copied to clipboard', 'ok');
      }).catch(function () { fallbackCopy(text); });
    } else fallbackCopy(text);
  }

  function fallbackCopy(text) {
    var pre = document.getElementById('mrl-preview');
    if (pre) { pre.select(); document.execCommand('copy'); }
    if (typeof toast === 'function') toast('Copied', 'ok');
  }

  function printLetter() {
    generate();
    var text = (document.getElementById('mrl-preview') || {}).value || '';
    var w = window.open('', '_blank');
    if (!w) { if (typeof toast === 'function') toast('Allow pop-ups to print', 'err'); return; }
    w.document.write('<pre style="font-family:Georgia,serif;font-size:12pt;line-height:1.45;white-space:pre-wrap;padding:24px">' +
      esc(text).replace(/\n/g, '<br>') + '</pre>');
    w.document.close();
    w.focus();
    w.print();
  }

  window.cafhMrlGenerate = generate;
  window.cafhMrlDownload = downloadTxt;
  window.cafhMrlCopy = copyText;
  window.cafhMrlPrint = printLetter;

  window.lMrlMaker = function () {
    var fy = getFY();
    document.getElementById('pt').textContent = 'MRL Maker — Management Representation Letter';
    document.getElementById('pa').innerHTML = '';
    var clients = [];
    try { clients = (window.S && S.clients) || []; } catch (e) {}
    var clientOpts = '<option value="">— Select client (optional) —</option>' +
      clients.map(function (c) {
        return '<option value="' + esc(c.name) + '" data-pan="' + esc(c.pan || '') + '" data-gstin="' + esc(c.gstin || '') + '" data-addr="' + esc(c.address || '') + '">' + esc(c.name) + '</option>';
      }).join('');

    document.getElementById('pb').innerHTML =
      '<div style="display:grid;grid-template-columns:minmax(280px,380px) 1fr;gap:16px;align-items:start">' +
      '<div class="card"><div class="card-h">Letter particulars</div><div class="card-b" style="font-size:13px">' +
      '<div class="fg"><label>Type of MRL</label><select id="mrl-type" onchange="cafhMrlToggleType()">' +
      '<option value="tax">Tax Audit (u/s 44AB)</option>' +
      '<option value="statutory">Statutory Audit (SA 580 / ICAI FAQ)</option></select></div>' +
      '<div class="fg"><label>Client (from register)</label><select id="mrl-client-sel" onchange="cafhMrlFillClient()">' + clientOpts + '</select></div>' +
      '<div class="fg"><label>Client / Assessee name *</label><input id="mrl-client" placeholder="M/s ABC Pvt Ltd"></div>' +
      '<div class="fg"><label>Name as per PAN</label><input id="mrl-pan-name" placeholder="Same as client if blank"></div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' +
      '<div class="fg"><label>PAN</label><input id="mrl-pan" placeholder="ABCDE1234F"></div>' +
      '<div class="fg"><label>GSTIN</label><input id="mrl-gstin" placeholder="Optional"></div></div>' +
      '<div class="fg"><label>Business address</label><input id="mrl-addr" placeholder="As communicated to ITD / registered office"></div>' +
      '<div class="fg"><label>Auditor firm name *</label><input id="mrl-auditor" placeholder="XYZ & Co., Chartered Accountants"></div>' +
      '<div class="fg"><label>Auditor address</label><input id="mrl-auditor-addr" placeholder="Optional"></div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px">' +
      '<div class="fg"><label>Letter date</label><input type="date" id="mrl-date" value="' + todayISO() + '"></div>' +
      '<div class="fg"><label>Year ended</label><input id="mrl-year-end" value="' + fyEndFromLabel(fy) + '"></div></div>' +
      '<div class="fg mrl-stat"><label>Audit engagement date</label><input id="mrl-eng-date" placeholder="DD/MM/YYYY"></div>' +
      '<div class="fg mrl-tax"><label>Accounting method</label><select id="mrl-acct"><option>mercantile</option><option>cash</option></select></div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px" class="mrl-tax">' +
      '<div class="fg"><label>Change in method?</label><select id="mrl-change-acct"><option>No</option><option>Yes</option></select></div>' +
      '<div class="fg"><label>Liable to indirect tax?</label><select id="mrl-idt"><option>Yes</option><option>No</option></select></div></div>' +
      '<div class="fg mrl-tax"><label>Opted 115BA/BAA/etc.?</label><select id="mrl-115"><option>No</option><option>Yes</option></select></div>' +
      '<div class="fg mrl-tax"><label>Nature of business</label><input id="mrl-nob" placeholder="Trading / Manufacturing / …"></div>' +
      '<div class="fg mrl-tax"><label>Books maintained</label><input id="mrl-books" value="Cash Book, Bank Book, Ledger, Journal"></div>' +
      '<div class="fg mrl-tax"><label>Partners / members (if any)</label><input id="mrl-partners" placeholder="Not applicable"></div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px" class="mrl-stat">' +
      '<div class="fg"><label>Has branches?</label><select id="mrl-branches"><option>No</option><option>Yes</option></select></div>' +
      '<div class="fg"><label>Include IFC para?</label><select id="mrl-ifc"><option>No</option><option>Yes</option></select></div></div>' +
      '<div class="fg mrl-stat"><label>Cash balance (optional)</label><input id="mrl-cash" placeholder="Rs."></div>' +
      '<div class="fg"><label>Signatory name *</label><input id="mrl-sign-name" placeholder="Full name"></div>' +
      '<div class="fg"><label>Designation</label><input id="mrl-sign-desig" value="Director / Partner / Proprietor"></div>' +
      '<div style="display:flex;flex-wrap:wrap;gap:8px;margin-top:12px">' +
      '<button class="btn btn-p" type="button" onclick="cafhMrlGenerate()">Generate preview</button>' +
      '<button class="btn btn-o" type="button" onclick="cafhMrlCopy()">Copy</button>' +
      '<button class="btn btn-o" type="button" onclick="cafhMrlDownload()">Download .txt</button>' +
      '<button class="btn btn-o" type="button" onclick="cafhMrlPrint()">Print</button>' +
      '</div>' +
      '<p style="font-size:11px;color:var(--text2);margin-top:10px;line-height:1.4">Tax Audit: illustrative MRL for s.44AB / Form 3CD. Statutory: SA 580 structure per ICAI FAQs on MRL. Tailor to engagement facts. Designed & Built by Harsh Pala.</p>' +
      '</div></div>' +
      '<div class="card"><div class="card-h">Preview</div><div class="card-b" style="padding:0">' +
      '<textarea id="mrl-preview" readonly style="width:100%;min-height:70vh;border:0;padding:16px;font-family:Georgia,serif;font-size:13px;line-height:1.5;resize:vertical;box-sizing:border-box" placeholder="Click Generate preview…"></textarea>' +
      '</div></div></div>';

    window.cafhMrlToggleType = function () {
      var t = (document.getElementById('mrl-type') || {}).value;
      document.querySelectorAll('.mrl-tax').forEach(function (el) { el.style.display = t === 'tax' ? '' : 'none'; });
      document.querySelectorAll('.mrl-stat').forEach(function (el) { el.style.display = t === 'statutory' ? '' : 'none'; });
    };
    window.cafhMrlFillClient = function () {
      var sel = document.getElementById('mrl-client-sel');
      if (!sel || !sel.value) return;
      var opt = sel.options[sel.selectedIndex];
      document.getElementById('mrl-client').value = sel.value;
      document.getElementById('mrl-pan-name').value = sel.value;
      if (opt) {
        if (opt.getAttribute('data-pan')) document.getElementById('mrl-pan').value = opt.getAttribute('data-pan');
        if (opt.getAttribute('data-gstin')) document.getElementById('mrl-gstin').value = opt.getAttribute('data-gstin');
        if (opt.getAttribute('data-addr')) document.getElementById('mrl-addr').value = opt.getAttribute('data-addr');
      }
    };
    cafhMrlToggleType();
  };

  function injectNav() {
    try {
      var nav = document.querySelector('.side-nav');
      if (!nav || document.querySelector('[data-p="mrlmaker"]')) return;
      var wp = document.querySelector('[data-p="workpapers"]');
      var el = document.createElement('div');
      el.className = 'ni';
      el.setAttribute('data-p', 'mrlmaker');
      el.setAttribute('onclick', "nav('mrlmaker')");
      el.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><line x1="10" y1="9" x2="8" y2="9"/></svg>MRL Maker';
      if (wp && wp.parentNode) wp.parentNode.insertBefore(el, wp.nextSibling);
      else nav.appendChild(el);
    } catch (e) { console.warn('[mrl]', e); }
  }

  function patchNav() {
    if (window.__cafhMrlNavPatched) return;
    if (typeof window.nav !== 'function') return;
    window.__cafhMrlNavPatched = true;
    var _nav = window.nav;
    window.nav = function (p) {
      if (p === 'mrlmaker') {
        try {
          document.querySelectorAll('.ni').forEach(function (n) { n.classList.toggle('on', n.getAttribute('data-p') === p); });
        } catch (e) {}
        if (typeof window.lMrlMaker === 'function') window.lMrlMaker();
        return;
      }
      return _nav.apply(this, arguments);
    };
  }

  var obs = new MutationObserver(function () {
    injectNav();
    patchNav();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  injectNav();
  patchNav();
})();
