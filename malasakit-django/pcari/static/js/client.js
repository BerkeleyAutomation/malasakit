/** client.js
 *
 *  This script is based on ECMAScript 6, which may not be supported by all
 *  browsers at the time of this writing. The optimal way to use this script is
 *  to transpile it to ECMAScript 5 using something like `babel`, the NPM
 *  package.
 */

const API_URL_ROOT = '/api';
const DEFAULT_LANGUAGE = 'tl';

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
            this[key] = other[key];
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
ASSETS_MAP.registerNew(new Resource('comments', 12*60*60*1000, {
    endpoint: API_URL_ROOT + 'fetch-comments/'
}));
ASSETS_MAP.registerNew(new Resource('qualitative-questions', 0, {
    endpoint: API_URL_ROOT + 'fetch-qualitative-questions/'
}));
ASSETS_MAP.save()

const RESPONSE_STORAGE_MAP = new ResourceMap('response-storage-map');
RESPONSE_STORAGE_MAP.save()
