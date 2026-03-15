const CACHE_NAME = 'wuthering-waves-dps-v2';
const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/robots.txt',
  '/manifest.json',
  '/picture.webp'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((cacheName) => {
            return cacheName !== CACHE_NAME;
          })
          .map((cacheName) => {
            return caches.delete(cacheName);
          })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  
  if (request.method !== 'GET') {
    return;
  }
  
  if (request.url.includes('/api/')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          if (!response || response.status !== 200) {
            return response;
          }
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseToCache);
          });
          return response;
        })
        .catch(() => {
          return caches.match(request);
        })
    );
    return;
  }
  
  event.respondWith(
    caches.match(request).then((response) => {
      if (response) {
        fetch(request).then((newResponse) => {
          if (newResponse && newResponse.status === 200) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, newResponse);
            });
          }
        });
        return response;
      }
      return fetch(request).then((newResponse) => {
        if (!newResponse || newResponse.status !== 200) {
          return newResponse;
        }
        const responseToCache = newResponse.clone();
        caches.open(CACHE_NAME).then((cache) => {
          cache.put(request, responseToCache);
        });
        return newResponse;
      });
    })
  );
});
