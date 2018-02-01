/*
 *  storage.js -- A high-level persistent object storage library
 */

/*global localStorage: false, console: false */

function hasAttr(obj, name) {
    'use strict';
    return obj[name] !== undefined;
}

function walk(obj, properties, create) {
    'use strict';
    for (var index in properties) {
        var property = properties[index];
        if (!(property in obj)) {
            if (create) {
                obj[property] = {};
            } else {
                throw 'Could not find property "' + property + '" in: ' +
                      JSON.stringify(obj);
            }
        }
        obj = obj[property];
    }
    return obj;
}

/*
 *  A namespace of persistent objects.
 *  @constructor
 *  @param {string} name - A unique identifier for this namespace.
 */
function Storage(name) {
    'use strict';
    this.name = name;
    var cache = {};  /* Hidden cache of objects */

    this.hasObject = function(name) {
        return name in cache || localStorage.getItem(this.addPrefixToName(name)) !== null;
    };

    this.loadObject = function(name) {
        var obj;
        if (!(name in cache)) {
            obj = localStorage.getItem(this.addPrefixToName(name));
            if (obj === null) {
                throw 'No object with name "' + name + '"';
            }
            cache[name] = JSON.parse(obj);
        } else {
            obj = cache[name];
        }
        this.validateObject(obj);
        return obj;
    };

    this.storeObject = function(name, obj) {
        obj.timestamp = Date.now();
        this.validateObject(obj);
        localStorage.setItem(this.addPrefixToName(name), JSON.stringify(obj));
        cache[name] = obj;
    };

    this.deleteObject = function(name) {
        localStorage.removeItem(this.addPrefixToName(name));
        delete cache[name];
    };

    this.emptyCache = function() {
        cache = {};
    };
}

Storage.prototype.createObject = function(name) {
    'use strict';
    var obj = {
        name: name,
        timestamp: null,
        data: {}
    };
    this.storeObject(name, obj);
    return obj;
};

/*
 *  Prefix an object's name with the `Storage` object's name to form a key.
 *  Reduces the likelihood of namespace collisions in the `localStorage` object.
 */
Storage.prototype.addPrefixToName = function(name) {
    'use strict';
    return this.name + '-' + name;
};

Storage.prototype.validateObject = function(obj) {
    'use strict';
    if (!hasAttr(obj, 'name') || !hasAttr(obj, 'timestamp') || !hasAttr(obj, 'data')) {
        throw 'Object ' + JSON.stringify(obj) + ' has missing attributes';
    }
};

Storage.prototype.get = function(properties) {
    'use strict';
    if (properties.length < 1) {
        throw 'List of properties must be non-empty';
    }
    var obj = this.loadObject(properties[0]);
    return walk(obj.data, properties.slice(1), false);
};

Storage.prototype.set = function(properties, value) {
    'use strict';
    if (properties.length < 1) {
        throw 'List of properties must be non-empty';
    }

    var obj;
    if (!this.hasObject(properties[0])) {
        obj = this.createObject(properties[0]);
    } else {
        obj = this.loadObject(properties[0]);
    }

    if (properties.length === 1) {
        obj.data = value;
    } else {
        var data = walk(obj.data, properties.slice(1, -1), true);
        var last = properties[properties.length - 1];
        data[last] = value;
    }
    this.storeObject(obj.name, obj);
};

Storage.prototype.delete = function(properties) {
    'use strict';
    if (properties.length < 1) {
        throw 'List of properties must be non-empty';
    }

    if (properties.length === 1) {
        this.deleteObject(properties[0]);
    } else if (this.hasObject(properties[0])) {
        var obj = this.loadObject(properties[0]);
        var data = walk(obj.data, properties.slice(1, -1), true);
        var last = properties[properties.length - 1];
        delete data[last];
        this.storeObject(obj.name, obj);
        if (Object.keys(data).length === 0) {
            this.delete(properties.slice(0, -1));
        }
    }
};

Storage.prototype.lastModified = function(name) {
    'use strict';
    return this.loadObject(name).timestamp;
};

Storage.prototype.isStale = function(name, lifetime) {
    'use strict';
    return Date.now() - this.lastModified(name) > lifetime;
};
