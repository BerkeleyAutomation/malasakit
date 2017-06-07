/* ServiceWorker script.
   Inspired by
   https://developers.google.com/web/fundamentals/getting-started/primers/service-workers
*/

var CACHE_NAME = 'malasakit-cache';
var urlsToCache = [
    '/pcari/landing',
    '/pcari/static/img/landing1.jpg' // TODO: Fix hardcoded url issue
];

function installEvent(event) {
    console.log("Installing. Resources to prefetch:", urlsToCache);
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(function(cache) {
                console.log('Cache opened!');
                return cache.addAll(urlsToCache);
            })
    );
}

function fetchEvent(event) {
    console.log("Fetch event!");
    event.respondWith(
        caches.match(event.request)
            .then(function(response) {
                if (response) {
                    console.log('found response in cache');
                    return response;
                }
                console.log('no response found in cache');
                return fetch(event.request);
            })
    );
}


self.addEventListener("install", function(event) {
    installEvent(event);
});

self.addEventListener("fetch", function(event) {
    fetchEvent(event);
});
