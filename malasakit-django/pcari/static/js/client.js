/** client.js
 *
 *  This script is based on ECMAScript 6, which may not be supported by all
 *  browsers at the time of this writing. The optimal way to use this script is
 *  to transpile it to ECMAScript 5 using something like `babel`, the NPM
 *  package.
 */

const DEFAULT_LANGUAGE = 'tl';

const API_URL_ROOT = '/api';
const RESPONSE_SAVE_ENDPOINT = API_URL_ROOT + '/save-response/';

const DEFAULT_TIMEOUT = 5000;

const EMPTY_RESPONSE = {
    'question-ratings': {},
    'comments': {},
    'comment-ratings': {},
    'respondent-data': {},
};

function getCurrentTimestamp() {
    return new Date().getTime();
}

class Resource {
    constructor(name, lifetime=0, other={}) {
        this.name = name;
        // JSON cannot represent `Infinity`, so this is the sentinel value
        // for the lifetime of a resource that does not expire
        this.lifetime = lifetime === Infinity ? null : lifetime;

        for (var key in other) {
            if (!(key in this)) {
                this[key] = other[key];
            }
        }
    }

    get stale() {
        if (this.timestamp !== undefined && this.lifetime !== null) {
            var now = getCurrentTimestamp();
            var timedelta = now - this.timestamp;
            return timedelta > this.lifetime;
        }
        return false;
    }

    exists() {
        return localStorage.getItem(this.name) !== null;
    }

    get() {
        return JSON.parse(localStorage.getItem(this.name));
    }

    put(value) {
        localStorage.setItem(this.name, JSON.stringify(value));
    }

    delete() {
        localStorage.removeItem(this.name);
    }

    updateTimestamp() {
        this.timestamp = getCurrentTimestamp();
    }

    fetch() {
        var resource = this;  // Alias to avoid conflicts in callbacks
        if (resource.endpoint !== undefined) {
            $.ajax(resource.endpoint, {
                timeout: resource.timeout || DEFAULT_TIMEOUT,
                success: function(data) {
                    resource.put(data);
                    resource.updateTimestamp();
                    console.log('Successfully fetched ' + resource.name);
                },
                failure: function() {
                    console.log('Failed to fetch data for ' + resource.name);
                },
            });
        }
    }
}

class ResourceMap extends Resource {
    constructor(name, lifetime=Infinity) {
        super(name, lifetime);
        this.resources = this.get() || {};
        for (var name in this.resources) {
            var skeleton = this.resources[name];
            this.resources[name] = new Resource(skeleton.name,
                                                skeleton.lifetime, skeleton);
        }
    }

    register(resource, initialOnly=false) {
        if (!initialOnly || !(resource.name in this.resources)) {
            this.resources[resource.name] = resource;
        }
    }

    putAll() {
        this.put(this.resources);
    }
}

const ASSETS_MAP = new ResourceMap('assets-map');
const RESPONSE_STORAGE_MAP = new ResourceMap('response-storage-map');

function initializeResourceMaps() {
    ASSETS_MAP.register(new Resource('comments', 12*60*60*1000, {
        endpoint: API_URL_ROOT + '/fetch-comments/',
        timeout: 5000,
        default_num_to_sample: 8,
    }), true);
    ASSETS_MAP.register(new Resource('qualitative-questions', 0, {
        endpoint: API_URL_ROOT + '/fetch-qualitative-questions/',
        timeout: 5000,
    }), true);
    ASSETS_MAP.register(new Resource('current', 12*60*60*1000), true);
    ASSETS_MAP.putAll();
    RESPONSE_STORAGE_MAP.putAll();
}

function refreshAssets() {
    for (var name in ASSETS_MAP.resources) {
        var resource = ASSETS_MAP.resources[name];
        if (resource.stale || !resource.exists()) {
            if (resource.endpoint !== undefined) {
                resource.fetch();
            }
        }
    }
    ASSETS_MAP.putAll();
}

function initializeNewResponse() {
    var id = getCurrentTimestamp().toString();
    ASSETS_MAP.resources.current.put(id);

    var response = new Resource(id, Infinity);
    response.put(EMPTY_RESPONSE);
    RESPONSE_STORAGE_MAP.register(response);
    RESPONSE_STORAGE_MAP.putAll();
}

function pushCompletedResponses() {
    var currentID = ASSETS_MAP.resources.current.get();
    for (var id in RESPONSE_STORAGE_MAP.resources) {
        if (id !== currentID) {
            var responseResource = RESPONSE_STORAGE_MAP.resources[id];
            $.ajax(RESPONSE_SAVE_ENDPOINT, {
                method: 'POST',
                data: responseResource.get(),
                timeout: DEFAULT_TIMEOUT,
                success: function() {
                    console.log(':: Successfully pushed data for ' + id);
                    responseResource.delete();
                },
                failure: function() {
                    console.log(':: Failed to push data for ' + id);
                },
            });
        }
    }
}

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

function csrfSetup() {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                var csrftoken = getCookie('csrftoken');
                xhr.setRequestHeader('X-CSRFToken', csrftoken);
            }
        }
    });
    console.log('AJAX with CSRF token usage initialized');
}

function displayLocalStorageUsage(precision=3) {
    var total = 0;
    for (var index = 0; index < localStorage.length; index++) {
        var key = localStorage.key(index);
        var data = localStorage.getItem(key);
        var usage = 2 * data.length / 1000;  // 2 bytes per char, in kB
        total += usage;
        console.log(key + ': ' + usage.toFixed(precision) + ' kB');
    }
    console.log('Total: ' + total.toFixed(precision) + ' kB');
}

function main() {
    csrfSetup();
    initializeResourceMaps();
    refreshAssets();
}

$(document).ready(main);
