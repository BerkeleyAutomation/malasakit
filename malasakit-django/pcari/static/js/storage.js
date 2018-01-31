/*
 *  storage.js -- A high-level persistent object storage library
 */

/*global localStorage: false, console: false */

function hasAttr(obj, name) {
    'use strict';
    return obj[name] !== undefined;
}

function walk(obj, properties) {
    'use strict';
    for (var property in properties) {
        if (!(property in obj)) {
            throw 'Could not find property "' + property + '" in: '
                  + JSON.stringify(obj);
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
            cache[name] = obj;
        } else {
            obj = JSON.parse(cache[name]);
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
        timestamp: Date.now(),
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
    return walk(obj.data, properties.slice(1));
};

Storage.prototype.set = function(properties, value) {
    'use strict';
    if (properties.length < 1) {
        throw 'List of properties must be non-empty';
    }
    var obj = this.loadObject(properties[0]);
    if (properties.length === 1) {
        obj.data = value;
    } else {
        var data = walk(obj, properties.slice(1, -1));
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
    } else {
        var obj = this.loadObject(properties[0]);
        var data = walk(obj, properties.slice(1, -1));
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
