/* Service Worker для Kanji Study
   Стратегия:
   - HTML: network-first (чтобы обновления подхватывались)
   - Всё остальное: cache-first + фоновая догрузка
*/

const CACHE = 'kanji-study-v6';

const PRECACHE = [
  './',
  './index.html',
  './kanji_data.js',
  './bkb_data.js',
  './kanji_ru.js',
  './warodai_mini.js',
  './manifest.webmanifest',
  './icon.svg',
  './icon-192.png',
  './icon-512.png',
  './apple-touch-icon.png'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE)
      .then(cache => cache.addAll(PRECACHE).catch(err => {
        // Если какого-то файла нет — не падаем, просто логируем
        console.warn('Precache partial fail:', err);
      }))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(
        keys.filter(k => k !== CACHE).map(k => caches.delete(k))
      ))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', event => {
  const req = event.request;

  // Только GET и только наш origin
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  const isHTML = req.headers.get('accept')?.includes('text/html')
    || url.pathname.endsWith('/')
    || url.pathname.endsWith('.html');

  if (isHTML) {
    // Network-first для HTML
    event.respondWith(
      fetch(req)
        .then(res => {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req).then(hit => hit || caches.match('./index.html')))
    );
    return;
  }

  // Cache-first для всего остального
  event.respondWith(
    caches.match(req).then(cached => {
      if (cached) {
        // Обновляем в фоне, но отдаём из кэша сразу
        fetch(req).then(res => {
          if (res && res.ok) caches.open(CACHE).then(c => c.put(req, res.clone()));
        }).catch(() => {});
        return cached;
      }
      return fetch(req).then(res => {
        if (!res || !res.ok || res.type === 'opaque') return res;
        const copy = res.clone();
        caches.open(CACHE).then(c => c.put(req, copy));
        return res;
      });
    })
  );
});

// Позволяет странице попросить SW активироваться немедленно
self.addEventListener('message', event => {
  if (event.data === 'SKIP_WAITING') self.skipWaiting();
});
