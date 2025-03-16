const CACHE_NAME = "pocketour-cache-v1";
const urlsToCache = [
    "/",
    "/static/css/styles.css",
    "/static/js/main.js",
    "/logos/favicon/icon-192x192.png",
    "/logos/favicon/icon-512x512.png"
];

// Install Service Worker & Cache Files
self.addEventListener("install", event => {
    event.waitUntil(
        caches.open(CACHE_NAME).then(cache => {
            return cache.addAll(urlsToCache);
        })
    );
});

// Fetch Requests & Serve from Cache
self.addEventListener("fetch", event => {
    event.respondWith(
        caches.match(event.request).then(response => {
            return response || fetch(event.request);
        })
    );
});

// Update Cache When New Version Available
self.addEventListener("activate", event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.filter(cache => cache !== CACHE_NAME).map(cache => caches.delete(cache))
            );
        })
    );
});
