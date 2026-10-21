// Echo Books Service Worker — v2：页面走网络（保证更新），静态库走缓存（保证离线）
const CACHE = 'echo-books-v2';
const STATIC_ASSETS = [
  'manifest.json',
  'libs/jszip.min.js',
  'libs/epub.min.js',
  'libs/pdf.min.js',
  'libs/pdf.worker.min.js',
  'libs/icon-192.png',
  'libs/icon-512.png',
  'libs/apple-touch-icon.png'
];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(STATIC_ASSETS)).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  if(e.request.method !== 'GET') return;

  // 页面导航：网络优先，失败才用缓存（保证永远拿到最新 HTML）
  if(e.request.mode === 'navigate'){
    e.respondWith(
      fetch(e.request).then(resp => {
        const copy = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
        return resp;
      }).catch(() => caches.match(e.request))
    );
    return;
  }

  // 静态资源：缓存优先
  e.respondWith(
    caches.match(e.request).then(cached => {
      if(cached) return cached;
      return fetch(e.request).then(resp => {
        if(resp.ok && e.request.url.startsWith(self.location.origin)){
          const copy = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy));
        }
        return resp;
      }).catch(() => cached);
    })
  );
});