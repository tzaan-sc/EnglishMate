/* EnglishMate UX layer: theming (dark mode), keyboard shortcuts, onboarding tour, support widget. */
(function () {
  'use strict';

  var root = document.documentElement;
  var meta = document.getElementById('ux-config');
  var cfg = meta ? meta.dataset : {};
  var csrf = (document.querySelector('meta[name="csrf-token"]') || {}).content || cfg.csrf || '';

  function postJSON(url, body) {
    if (cfg.auth !== '1') return Promise.resolve();
    return fetch(url, {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf },
      body: JSON.stringify(body || {})
    }).catch(function () {});
  }

  function isTyping(el) {
    if (!el) return false;
    var tag = el.tagName;
    return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || el.isContentEditable;
  }

  /* ---------------------------------------------------------------- Theme */
  function currentTheme() { return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light'; }

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    root.setAttribute('data-bs-theme', theme);
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      var dark = theme === 'dark';
      btn.setAttribute('aria-pressed', dark ? 'true' : 'false');
      btn.setAttribute('aria-label', dark ? 'Chuyển sang giao diện sáng' : 'Chuyển sang giao diện tối');
      btn.title = dark ? 'Chuyển sang giao diện sáng (T)' : 'Chuyển sang giao diện tối (T)';
      var icon = btn.querySelector('i');
      if (icon) icon.className = dark ? 'ph-bold ph-sun' : 'ph-bold ph-moon';
    });
  }

  function setTheme(theme, persist) {
    applyTheme(theme);
    try { localStorage.setItem('em_theme', theme); } catch (e) {}
    if (persist !== false) postJSON(cfg.themeUrl, { theme: theme });
  }

  function toggleTheme() { setTheme(currentTheme() === 'dark' ? 'light' : 'dark'); }

  /* ------------------------------------------------------------ Shortcuts */
  var NAV_KEYS = {
    d: ['dashUrl', 'Bảng điều khiển'],
    l: ['lessonsUrl', 'Bài học'],
    v: ['vocabUrl', 'Từ vựng'],
    q: ['quizUrl', 'Trắc nghiệm'],
    e: ['examsUrl', 'Đề thi']
  };
  var gPending = false, gTimer = null;

  function showModal(id) {
    var el = document.getElementById(id);
    if (el && window.bootstrap) window.bootstrap.Modal.getOrCreateInstance(el).show();
  }

  function onKeydown(e) {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    if (isTyping(e.target)) return;
    if (document.querySelector('.modal.show') && e.key !== '?') return;
    var key = e.key;

    // Page-specific: quiz answers & navigation
    if (/^[1-9]$/.test(key)) {
      var opt = document.querySelector('[data-shortcut-option="' + key + '"]');
      if (opt) { e.preventDefault(); opt.click(); return; }
    }
    if (key === 'ArrowLeft' || key === 'ArrowRight') {
      var nav = document.querySelector('[data-shortcut="' + (key === 'ArrowLeft' ? 'prev' : 'next') + '"]');
      if (nav && !nav.classList.contains('disabled')) { e.preventDefault(); nav.click(); return; }
    }

    if (key === '?') { e.preventDefault(); showModal('shortcutsModal'); return; }
    if (key === '/') {
      if (document.getElementById('commandPaletteModal')) { e.preventDefault(); showModal('commandPaletteModal'); }
      return;
    }
    if (key === 't' || key === 'T') { toggleTheme(); return; }

    if (gPending) {
      gPending = false; clearTimeout(gTimer);
      var target = NAV_KEYS[key.toLowerCase()];
      if (target && cfg[target[0]]) { e.preventDefault(); window.location.href = cfg[target[0]]; }
      return;
    }
    if (key === 'g' && cfg.auth === '1') {
      gPending = true;
      gTimer = setTimeout(function () { gPending = false; }, 1200);
    }
  }

  /* ------------------------------------------------------------- Onboarding */
  var STEPS = [
    { sel: null, title: 'Chào mừng đến với EnglishMate! 👋', text: 'Hãy dành 30 giây để làm quen với các tính năng chính của hệ thống.' },
    { sel: '.app-sidebar:not(.d-none), #mobileSidebar', fallbackSel: '[data-bs-target="#mobileSidebar"]', title: 'Thanh điều hướng', text: 'Truy cập nhanh Bài học, Từ vựng, Ngữ pháp, Trắc nghiệm, Đề thi và Hồ sơ của bạn tại đây.' },
    { sel: '[data-bs-target="#commandPaletteModal"]', title: 'Tìm kiếm nhanh', text: 'Nhấn Ctrl + K (hoặc phím /) để tìm bài học, từ vựng ngay lập tức.' },
    { sel: '#notifDropdown', title: 'Thông báo học tập', text: 'Nhận nhắc nhở ôn tập từ vựng, mục tiêu ngày và chuỗi streak của bạn.' },
    { sel: '[data-theme-toggle]', title: 'Giao diện Sáng / Tối', text: 'Chuyển chế độ tối để học ban đêm đỡ mỏi mắt. Phím tắt: T.' },
    { sel: '#supportFab', title: 'Trợ giúp & Hỗ trợ', text: 'Cần giúp đỡ? Xem phím tắt, mở lại hướng dẫn này hoặc liên hệ đội ngũ hỗ trợ.' }
  ];

  var tour = { idx: 0, nodes: null, steps: [] };

  function visible(el) {
    if (!el) return false;
    var r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  }

  function findTarget(step) {
    if (!step.sel) return null;
    var el = document.querySelector(step.sel);
    if (visible(el)) return el;
    if (step.fallbackSel) {
      el = document.querySelector(step.fallbackSel);
      if (visible(el)) return el;
    }
    return undefined; // not available -> skip
  }

  function buildTour() {
    var overlay = document.createElement('div');
    overlay.className = 'em-tour-overlay';
    overlay.innerHTML =
      '<div class="em-tour-spot"></div>' +
      '<div class="em-tour-card" role="dialog" aria-modal="true" aria-labelledby="emTourTitle" tabindex="-1">' +
      '<div class="em-tour-step"></div><h2 class="em-tour-title" id="emTourTitle"></h2><p class="em-tour-text"></p>' +
      '<div class="em-tour-actions"><button type="button" class="btn btn-link text-muted p-0" data-tour="skip">Bỏ qua</button>' +
      '<div class="d-flex gap-2"><button type="button" class="btn btn-light border" data-tour="prev">Quay lại</button>' +
      '<button type="button" class="btn btn-primary fw-bold" data-tour="next">Tiếp theo</button></div></div></div>';
    document.body.appendChild(overlay);
    tour.nodes = {
      overlay: overlay,
      spot: overlay.querySelector('.em-tour-spot'),
      card: overlay.querySelector('.em-tour-card'),
      step: overlay.querySelector('.em-tour-step'),
      title: overlay.querySelector('.em-tour-title'),
      text: overlay.querySelector('.em-tour-text'),
      prev: overlay.querySelector('[data-tour="prev"]'),
      next: overlay.querySelector('[data-tour="next"]')
    };
    overlay.addEventListener('click', function (e) {
      var action = e.target.getAttribute && e.target.getAttribute('data-tour');
      if (action === 'next') go(1);
      else if (action === 'prev') go(-1);
      else if (action === 'skip') endTour();
    });
    overlay.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') endTour();
      else if (e.key === 'ArrowRight') go(1);
      else if (e.key === 'ArrowLeft') go(-1);
    });
  }

  function renderStep() {
    var n = tour.nodes, s = tour.steps[tour.idx];
    n.step.textContent = 'Bước ' + (tour.idx + 1) + '/' + tour.steps.length;
    n.title.textContent = s.title;
    n.text.textContent = s.text;
    n.prev.style.visibility = tour.idx === 0 ? 'hidden' : 'visible';
    n.next.textContent = tour.idx === tour.steps.length - 1 ? 'Hoàn tất 🎉' : 'Tiếp theo';

    var pad = 8, card = n.card;
    if (s.el) {
      s.el.scrollIntoView({ block: 'center', inline: 'nearest' });
      var r = s.el.getBoundingClientRect();
      n.spot.style.cssText = 'display:block;top:' + (r.top - pad) + 'px;left:' + (r.left - pad) +
        'px;width:' + (r.width + pad * 2) + 'px;height:' + (r.height + pad * 2) + 'px;';
      card.style.transform = 'none';
      var cw = Math.min(340, window.innerWidth - 24);
      var below = r.bottom + pad + 12 + 190 < window.innerHeight;
      var top = below ? r.bottom + pad + 12 : Math.max(12, r.top - pad - 12 - 190);
      var left = Math.min(Math.max(12, r.left), window.innerWidth - cw - 12);
      card.style.top = top + 'px'; card.style.left = left + 'px';
    } else {
      n.spot.style.display = 'none';
      card.style.top = '50%'; card.style.left = '50%';
      card.style.transform = 'translate(-50%, -50%)';
    }
    n.next.focus();
  }

  function go(delta) {
    var next = tour.idx + delta;
    if (next >= tour.steps.length) return endTour();
    if (next < 0) return;
    tour.idx = next;
    renderStep();
  }

  function endTour() {
    if (tour.nodes) { tour.nodes.overlay.remove(); tour.nodes = null; }
    window.removeEventListener('resize', onTourResize);
    try { localStorage.setItem('em_onboarding_done', '1'); } catch (e) {}
    postJSON(cfg.onboardDoneUrl, {});
  }

  function onTourResize() { if (tour.nodes) renderStep(); }

  function startTour() {
    if (tour.nodes) return;
    tour.steps = [];
    STEPS.forEach(function (s) {
      var el = findTarget(s);
      if (el === undefined) return;
      tour.steps.push({ sel: s.sel, title: s.title, text: s.text, el: el });
    });
    tour.idx = 0;
    buildTour();
    window.addEventListener('resize', onTourResize);
    renderStep();
  }

  /* ----------------------------------------------------------------- Init */
  document.addEventListener('DOMContentLoaded', function () {
    applyTheme(currentTheme());

    document.addEventListener('click', function (e) {
      var themeBtn = e.target.closest('[data-theme-toggle]');
      if (themeBtn) { e.preventDefault(); toggleTheme(); return; }
      var startBtn = e.target.closest('[data-start-tour]');
      if (startBtn) {
        e.preventDefault();
        var modalEl = startBtn.closest('.modal');
        if (modalEl && window.bootstrap) window.bootstrap.Modal.getOrCreateInstance(modalEl).hide();
        setTimeout(startTour, modalEl ? 350 : 0);
        return;
      }
      var copyBtn = e.target.closest('[data-copy-text]');
      if (copyBtn && navigator.clipboard) {
        navigator.clipboard.writeText(copyBtn.getAttribute('data-copy-text')).then(function () {
          var old = copyBtn.innerHTML;
          copyBtn.innerHTML = '<i class="ph-bold ph-check"></i> Đã sao chép';
          setTimeout(function () { copyBtn.innerHTML = old; }, 1800);
        });
      }
    });

    document.addEventListener('keydown', onKeydown);

    var fresh = cfg.auth === '1' && cfg.admin !== '1' && cfg.onboarding === '0';
    var doneLocally = false;
    try { doneLocally = localStorage.getItem('em_onboarding_done') === '1'; } catch (e) {}
    if (fresh && !doneLocally) setTimeout(startTour, 900);
  });

  window.EnglishMateUX = { setTheme: setTheme, toggleTheme: toggleTheme, startTour: startTour };
})();
