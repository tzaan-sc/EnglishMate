/**
 * EnglishMate - Vocabulary Web Push & Desktop Notifications
 */
(function() {
  'use strict';

  // Register service worker if supported
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/static/sw.js').catch((err) => {
        console.debug('Service Worker registration skipped or failed:', err);
      });
    });
  }

  // Helper to request notification permission
  async function requestNotificationPermission() {
    if (!('Notification' in window)) {
      if (window.showCustomFlashToast) {
        window.showCustomFlashToast('Trình duyệt của bạn không hỗ trợ tính năng Web Notifications.', 'warning', 'Không hỗ trợ');
      }
      return 'unsupported';
    }

    try {
      const permission = await Notification.requestPermission();
      updatePermissionUI(permission);
      if (permission === 'granted') {
        // Send subscription state to backend
        fetch('/api/vocabulary/subscribe-push', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled: true, permission: 'granted' })
        }).catch(() => {});

        if (window.showCustomFlashToast) {
          window.showCustomFlashToast('Đã cấp quyền thông báo đẩy Web Notifications thành công!', 'success', 'Thông báo bật');
        }
      } else if (permission === 'denied') {
        if (window.showCustomFlashToast) {
          window.showCustomFlashToast('Quyền thông báo đã bị chặn trong cài đặt trình duyệt của bạn.', 'danger', 'Đã chặn');
        }
      }
      return permission;
    } catch (e) {
      console.error('Error requesting notification permission:', e);
      return 'denied';
    }
  }

  // Update permission UI indicator if elements exist on settings page
  function updatePermissionUI(permission) {
    const statusEl = document.getElementById('notifPermissionStatus');
    const badgeEl = document.getElementById('notifPermissionBadge');
    if (!statusEl || !badgeEl) return;

    if (permission === 'granted') {
      badgeEl.className = 'badge bg-success-subtle text-success border border-success-subtle rounded-pill px-2.5 py-1';
      badgeEl.innerHTML = '<i class="ph-bold ph-check-circle me-1"></i>Đã cấp quyền (Granted)';
    } else if (permission === 'denied') {
      badgeEl.className = 'badge bg-danger-subtle text-danger border border-danger-subtle rounded-pill px-2.5 py-1';
      badgeEl.innerHTML = '<i class="ph-bold ph-x-circle me-1"></i>Đang bị chặn (Denied)';
    } else {
      badgeEl.className = 'badge bg-warning-subtle text-warning border border-warning-subtle rounded-pill px-2.5 py-1';
      badgeEl.innerHTML = '<i class="ph-bold ph-question me-1"></i>Chưa cấp quyền (Default)';
    }
  }

  // Show desktop notification
  function showDesktopNotification(title, body, url) {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;

    try {
      const notif = new Notification(title, {
        body: body,
        icon: '/static/favicon.ico',
        badge: '/static/favicon.ico',
        tag: 'englishmate-vocab-reminder'
      });
      notif.onclick = function() {
        window.focus();
        if (url) window.location.href = url;
      };
    } catch (e) {
      console.error('Notification constructor error:', e);
    }
  }

  // Test Notification Trigger
  async function triggerTestNotification() {
    if (!('Notification' in window)) {
      alert('Trình duyệt không hỗ trợ Web Notifications.');
      return;
    }

    if (Notification.permission !== 'granted') {
      const perm = await requestNotificationPermission();
      if (perm !== 'granted') return;
    }

    try {
      const res = await fetch('/api/vocabulary/send-test-notification', { method: 'POST' });
      const data = await res.json();
      if (data.success) {
        showDesktopNotification(data.title, data.body, data.review_url);
        if (window.showCustomFlashToast) {
          window.showCustomFlashToast('Đã phát thông báo thử nghiệm tới trình duyệt!', 'info', 'Kiểm tra thông báo');
        }
      }
    } catch (e) {
      showDesktopNotification(
        'EnglishMate - Nhắc nhở ôn tập từ vựng 🔔',
        'Đây là thông báo mẫu! Bạn có từ vựng đến hạn ôn tập SRS.',
        '/vocabulary/review'
      );
    }
  }

  // Check due words for reminder
  async function checkDueVocabularyNotification() {
    if (!('Notification' in window) || Notification.permission !== 'granted') return;

    // Check if already notified in this session
    const lastNotified = sessionStorage.getItem('last_vocab_notified_date');
    const todayStr = new Date().toDateString();
    if (lastNotified === todayStr) return;

    try {
      const res = await fetch('/api/vocabulary/notification-check');
      if (!res.ok) return;
      const data = await res.json();

      if (data.success && data.enabled && data.has_due) {
        sessionStorage.setItem('last_vocab_notified_date', todayStr);
        showDesktopNotification(data.title, data.body, data.review_url);
      }
    } catch (e) {}
  }

  // Expose to window
  window.requestVocabNotificationPermission = requestNotificationPermission;
  window.triggerTestVocabNotification = triggerTestNotification;
  window.checkDueVocabularyNotification = checkDueVocabularyNotification;

  document.addEventListener('DOMContentLoaded', () => {
    if ('Notification' in window) {
      updatePermissionUI(Notification.permission);
    }

    // Attach listeners on settings page
    const btnTest = document.getElementById('btnTestWebPush');
    if (btnTest) {
      btnTest.addEventListener('click', (e) => {
        e.preventDefault();
        triggerTestNotification();
      });
    }

    const pushSwitch = document.getElementById('pushSwitch');
    if (pushSwitch) {
      pushSwitch.addEventListener('change', async function() {
        if (this.checked && 'Notification' in window && Notification.permission !== 'granted') {
          const perm = await requestNotificationPermission();
          if (perm !== 'granted') {
            this.checked = false;
          }
        }
      });
    }

    // Run background check 3 seconds after page load for logged-in users
    setTimeout(checkDueVocabularyNotification, 3000);
  });
})();
