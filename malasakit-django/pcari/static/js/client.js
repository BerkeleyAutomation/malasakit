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
        return this.get() !== null;
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

    register(resource) {
        this.resources[resource.name] = resource;
    }

    registerNew(resource) {
        if (!(resource.name in this.resources)) {
            this.register(resource);
        }
    }

    save() {
        this.put(this.resources);
    }
}

const ASSETS_MAP = new ResourceMap('assets-map');
const RESPONSE_STORAGE_MAP = new ResourceMap('response-storage-map');

function initializeResourceMaps() {
    ASSETS_MAP.registerNew(new Resource('comments', 12*60*60*1000, {
        endpoint: API_URL_ROOT + '/fetch-comments/'
    }));
    ASSETS_MAP.registerNew(new Resource('qualitative-questions', 0, {
        endpoint: API_URL_ROOT + '/fetch-qualitative-questions/'
    }));
    ASSETS_MAP.registerNew(new Resource('current', 12*60*60*1000));
    ASSETS_MAP.save();
    RESPONSE_STORAGE_MAP.save();
}

function initializeNewResponse() {
    ASSETS_MAP.resources.current.put(getCurrentTimestamp());
}

function pushCompletedResponses() {
    var currentID = ASSETS_MAP.resources.current.get();
    for (var id in RESPONSE_STORAGE_MAP.resources) {
        if (id !== currentID) {
            var responseResource = RESPONSE_STORAGE_MAP.resources[id];
            $.ajax(ASSETS_MAP.resources['response-endpoint'].get(), {
                data: responseResource.get(),
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
