/* ServiceWorker script.
   Inspired by
   https://developers.google.com/web/fundamentals/getting-started/primers/service-workers
*/

var CACHE_NAME = 'malasakit-cache';
var langCodes = ['en', 'tl'];
var views = [
    '/pcari/landing/',
    '/pcari/personal-information/',
    '/pcari/quantitative-questions/',
    '/pcari/response-histograms/',
    '/pcari/rate-comments/',
    '/pcari/qualitative-questions/',
    '/pcari/end/'
];

var urlsToCache = [];

for (var i = 0; i < views.length; i++) {
    for (var j = 0; j < langCodes.length; j++) {
        urlsToCache.push(views[i] + "?lang=" + langCodes[j]);
    }
}

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
    console.log("Requesting resource: ", event.request.url);
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
