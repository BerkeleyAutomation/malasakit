/* ServiceWorker script.
   Inspired by
   https://developers.google.com/web/fundamentals/getting-started/primers/service-workers
*/

var CACHE_NAME = 'malasakit-cache';
var urlsToCache = [
    '/pcari/landing',
    '/pcari/static/img/landing1.jpg', // TODO: Fix hardcoded url issue
    '/pcari/sw.js',
    '/pcari/quantitative_questions',
    '/pcari/rate_suggestions',
    '/pcari/end'
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
    // Upon receiving an event
    // We first attempt to fetch desired resource from server.
    // fetch(event.request) returns a Promise that may or may not be
    // fulfilled (i.e., do we get a resource?)
    event.respondWith(
        fetch(event.request)
            .catch(function (err) {
                // If fetch fails (i.e. no internet connection or server issue)
                // then attempt to pull resource from cache.
                console.log("=== FETCH FAILED, LOOKING IN CACHE ===");
                console.log(err);
                console.log("======================================");
                return caches.match(event.request)
                    .then(function (response) {
                        if (response) {
                            console.log('found response in cache');
                            return response;
                        }
                        console.log('NO RESPONSE FOUND, SOMETHING IS WRONG!!!');
                        return response; // edge case...shouldn't happen
                    })
            })
    );
}


self.addEventListener("install", function(event) {
    installEvent(event);
});

self.addEventListener("fetch", function(event) {
    fetchEvent(event);
});
