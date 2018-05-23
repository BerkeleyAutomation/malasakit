/** sw.js -- Service worker script that serves cached pages when offline
 *
 *  References:
 *      https://developers.google.com/web/fundamentals/getting-started/primers/service-workers
 */

const CACHE_NAME = 'malasakit-cache';

const APP_ROOT = '/';  // TODO: change to `/pcari/` in production
const STATIC_ROOT = APP_ROOT + 'static/';

const LANGUAGE_CODES = ['en', 'tl', 'ceb', 'ilo'];
const VIEWS = [
    'landing/',
    'quantitative-questions/',
    'rate-comments/',
    'qualitative-questions/',
    'personal-information/',
    'peer-responses/',
    'end/'
];

const STATIC_RESOURCES = [
    'css/main.min.css',
    'data/bloom-icon.json',
    'js/jquery-3.2.1.min.js',
    'js/d3.v4.min.js',
    'js/client.js',
    'js/bloom.js',
    'js/sw-bootstrap.js',
    'js/uuid4.js',
    'img/landing',
    'img/green-emoticon.png',
    'img/yellow-emoticon.jpg',
    'img/red-emoticon.png'
];

function makeURLsToCache() {
    var urls = [];

    LANGUAGE_CODES.forEach(function(languageCode) {
        var languageCodeURLFragment = languageCode + '/';
        VIEWS.forEach(function(viewURLFragment) {
            urls.push(APP_ROOT + languageCodeURLFragment + viewURLFragment);
        });
    });

    STATIC_RESOURCES.forEach(function(urlFragment) {
        urls.push(STATIC_ROOT + urlFragment);
    });

    urls.push(APP_ROOT + 'jsi18n/');
    return urls;
}

var urlsToCache = makeURLsToCache();

function installEvent(event) {
    console.log("Installing. Resources to prefetch:", urlsToCache);
    event.waitUntil(
        caches.delete(CACHE_NAME).then(function (res) {
            caches.open(CACHE_NAME)
                .then(function(cache) {
                    console.log('Cache opened!');
                    return cache.addAll(urlsToCache);
                })
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
            .then(function (response) {
                return caches.open(CACHE_NAME).then(function (cache) {
                    cache.put(event.request, response.clone());
                    return response;
                });
            }, function (err) {
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
                        else if (event.request.url.includes("/landing")) {
                            // PER JONATHAN: DO NOT RESPOND TO THIS URL

                            // Special case: if resource isn't found in cache
                            // because we navigated to /pcari/landing without
                            // a language code, return /en/pcari/landing
                            console.log("/landing with no language code!");
                            // go to our keys, go and find the key that maps to
                            // the landing page with language code, and
                            // make a new request for it
                            // return caches.open(CACHE_NAME).then(function(cache) {
                            //     // open our cache
                            //     return cache.keys().then(function (keys) {
                            //         // look at each of our keys
                            //         console.log(keys);
                            //         console.log(keys.length);
                            //         for (var i = 0; i < keys.length; i++) {
                            //             console.log(keys[i].url, i, keys.length, keys[i].url.includes("/landing"));
                            //             if (keys[i].url.includes("/landing")) {
                            //                 // if the key has /landing/
                            //                 return cache.match(new Request(keys[i].url));
                            //             }
                            //         }
                            //     })
                            // });
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
    if (event.request.method === 'GET') {
        fetchEvent(event);
    } else {
        console.log(event.request);
    }
});
