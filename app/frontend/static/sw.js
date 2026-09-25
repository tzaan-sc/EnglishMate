// EnglishMate Service Worker for Web Push & Offline Vocabulary Notifications
self.addEventListener('install', (event) => {
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(clients.claim());
});

self.addEventListener('push', (event) => {
  let data = {
    title: 'EnglishMate - Nhắc nhở ôn tập từ vựng 📚',
    body: 'Bạn có từ vựng đến hạn ôn tập SRS hôm nay. Hãy dành vài phút ôn luyện nhé!',
    icon: '/static/favicon.ico',
    url: '/vocabulary/review'
  };

  if (event.data) {
    try {
      data = Object.assign(data, event.data.json());
    } catch (e) {
      data.body = event.data.text();
    }
  }

  const options = {
    body: data.body,
    icon: data.icon || '/static/favicon.ico',
    badge: '/static/favicon.ico',
    data: { url: data.url || '/vocabulary/review' },
    actions: [
      { action: 'review', title: 'Ôn tập ngay 🚀' },
      { action: 'close', title: 'Để sau' }
    ]
  };

  event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', (event) => {
  event.notification.close();
  if (event.action === 'close') return;

  const targetUrl = (event.notification.data && event.notification.data.url) ? event.notification.data.url : '/vocabulary/review';
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((windowClients) => {
      for (let client of windowClients) {
        if (client.url.includes('/vocabulary') && 'focus' in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(targetUrl);
      }
    })
  );
});
