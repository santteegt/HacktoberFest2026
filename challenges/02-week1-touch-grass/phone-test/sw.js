// Caches the test page so it still opens with no signal (needs a secure context to register).
const CACHE = 'leash-walktest-v1';
self.addEventListener('install', e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(['./', './index.html']))); self.skipWaiting(); });
self.addEventListener('activate', e => { e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', e => {
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).catch(() => caches.match('./index.html'))));
});
