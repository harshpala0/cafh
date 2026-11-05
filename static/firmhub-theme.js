/* CA FirmHub theme polish | Designed & Built by Harsh Pala */
(function () {
  if (window.__cafhTheme) return;
  window.__cafhTheme = true;

  function polishLoginBrand() {
    var brand = document.querySelector('.login-brand');
    if (!brand || brand.getAttribute('data-theme') === '1') return;
    brand.setAttribute('data-theme', '1');
    var h1 = brand.querySelector('h1');
    var p = brand.querySelector('p');
    if (h1 && /CA FirmHub/i.test(h1.textContent || '')) {
      h1.textContent = 'Every client, deadline and invoice — in one ledger.';
      h1.style.fontSize = '22px';
      h1.style.lineHeight = '1.3';
    }
    if (p) {
      p.textContent = 'Client records, compliance calendar, office registers and billing — with a portal your clients can actually use.';
    }
  }

  function polishSubBox() {
    var h2 = document.querySelector('.sub-box h2');
    if (h2 && !h2.getAttribute('data-theme')) {
      h2.setAttribute('data-theme', '1');
      if (/subscription|activate|firm/i.test(h2.textContent || '')) {
        h2.textContent = 'Activate your firm';
      }
    }
  }

  var obs = new MutationObserver(function () {
    polishLoginBrand();
    polishSubBox();
  });
  obs.observe(document.documentElement, { childList: true, subtree: true });
  setTimeout(polishLoginBrand, 80);
  setTimeout(polishSubBox, 80);
  setTimeout(polishLoginBrand, 500);
})();
