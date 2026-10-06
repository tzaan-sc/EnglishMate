/* EnglishMate accessibility helpers: screen reader labels (ARIA) + skip link focus handling. */
(function () {
  'use strict';

  var ICON_SELECTOR = 'i.ph, i.ph-bold, i.ph-fill, i.ph-light, i.ph-duotone, i[class*="ph-"], i.bi, i[class^="bi-"]';

  function hasAccessibleName(el) {
    if (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')) return true;
    var clone = el.cloneNode(true);
    clone.querySelectorAll(ICON_SELECTOR).forEach(function (i) { i.remove(); });
    return (clone.textContent || '').trim().length > 0;
  }

  function enhance(root) {
    root = root || document;

    // Decorative icons are hidden from assistive technology.
    root.querySelectorAll(ICON_SELECTOR).forEach(function (icon) {
      if (!icon.hasAttribute('aria-hidden')) icon.setAttribute('aria-hidden', 'true');
    });

    // Icon-only buttons/links: fall back to the title attribute as accessible name.
    root.querySelectorAll('button, a[href], [role="button"]').forEach(function (el) {
      if (hasAccessibleName(el)) return;
      var title = el.getAttribute('title');
      if (title) el.setAttribute('aria-label', title);
    });

    // Landmarks without a label.
    root.querySelectorAll('nav:not([aria-label]):not([aria-labelledby])').forEach(function (nav) {
      nav.setAttribute('aria-label', nav.classList.contains('app-navbar') ? 'Điều hướng chính' : 'Điều hướng');
    });
    root.querySelectorAll('aside.app-sidebar:not([aria-label])').forEach(function (aside) {
      aside.setAttribute('aria-label', 'Thanh bên');
    });

    // Modals / offcanvas: announce as dialogs.
    root.querySelectorAll('.modal:not([role])').forEach(function (m) {
      m.setAttribute('role', 'dialog');
      m.setAttribute('aria-modal', 'true');
      var heading = m.querySelector('.modal-title, h1, h2, h3, h4, h5');
      if (heading && !m.hasAttribute('aria-labelledby') && !m.hasAttribute('aria-label')) {
        if (!heading.id) heading.id = (m.id || 'modal') + '-title';
        m.setAttribute('aria-labelledby', heading.id);
      }
    });

    // Progress bars.
    root.querySelectorAll('.progress-bar:not([role])').forEach(function (bar) {
      bar.setAttribute('role', 'progressbar');
      bar.setAttribute('aria-valuemin', '0');
      bar.setAttribute('aria-valuemax', '100');
      var w = parseFloat(bar.style.width);
      if (!isNaN(w)) bar.setAttribute('aria-valuenow', String(Math.round(w)));
    });

    // Form controls without any label: use placeholder/title.
    root.querySelectorAll('input:not([type="hidden"]):not([aria-label]), select:not([aria-label]), textarea:not([aria-label])').forEach(function (f) {
      if (f.id && document.querySelector('label[for="' + f.id + '"]')) return;
      if (f.closest('label')) return;
      var name = f.getAttribute('placeholder') || f.getAttribute('title');
      if (name) f.setAttribute('aria-label', name);
    });
  }

  function setupSkipLink() {
    var link = document.querySelector('.skip-link');
    var main = document.getElementById('main-content');
    if (!link || !main) return;
    link.addEventListener('click', function (e) {
      e.preventDefault();
      main.focus({ preventScroll: false });
      main.scrollIntoView();
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    enhance(document);
    setupSkipLink();
    if ('MutationObserver' in window) {
      var pending = false;
      new MutationObserver(function () {
        if (pending) return;
        pending = true;
        setTimeout(function () { pending = false; enhance(document); }, 150);
      }).observe(document.body, { childList: true, subtree: true });
    }
  });

  window.EnglishMateA11y = { enhance: enhance };
})();
