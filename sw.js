// Echo Books Service Worker — 离线缓存
const CACHE = 'echo-books-v1';
const ASSETS = [
  'echo-books.html',
  'manifest.json',
  'libs/jszip.min.js',
  'libs/epub.min.js',
  'libs/pdf.min.js',
  'libs/pdf.worker.min.js',
  'libs/icon-192.png',
  'libs/icon-512.png',
  'libs/apple-touch-icon.png'
];

// 安装：预缓存核心文件
self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting())
  );
});

// 激活：清理旧缓存
self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE).map(k => caches.delete(k))
    )).then(() => self.clients.claim())
  );
});

// 请求拦截：缓存优先
self.addEventListener('fetch', e => {
  if(e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then(cached => {
      if(cached) return cached;
      return fetch(e.request).then(resp => {
        // 成功的 GET 请求缓存一份
        if(resp.ok && e.request.url.startsWith(self.location.origin)){
          const copy = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy));
        }
        return resp;
      }).catch(() => cached);
    })
  );
});