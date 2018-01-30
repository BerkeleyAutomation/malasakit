/*
 *  storage.js -- A high-level persistent object storage library
 */

/*global localStorage: false, console: false */

function hasAttr(obj, name) {
    'use strict';
    return obj[name] !== undefined;
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

    this.loadObject = function(name) {
        if (name in cache) {
            return cache[name];
        }

        var key = this.addPrefixToName(name);
        var obj = cache[name] = localStorage.getItem(key);
        if (obj !== null) {
            return JSON.parse(obj);
        }

        obj = cache[name] = this.createObject(name);
        this.storeObject(name, obj);
        return obj;
    };

    this.storeObject = function(name, obj) {
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

/*
 *  Prefix an object's name with the `Storage` object's name to form a key.
 *  Reduces the likelihood of namespace collisions in the `localStorage` object.
 */
Storage.prototype.addPrefixToName = function(name) {
    'use strict';
    return this.name + '-' + name;
};

Storage.prototype.createObject = function(name) {
    'use strict';
    return {
        name: name,
        timestamp: Date.now(),
        data: {}
    };
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
    this.validateObject(obj);
    obj = obj.data;

    for (var index = 1; index < properties.length; index++) {
        property = properties[index];
        if (!(property in obj)) {
            throw 'Object ' + JSON.stringify(obj) +
                  ' is missing property "' + property + '"';
        }
        obj = obj[property];
    }

    return obj;
};

Storage.prototype.set = function(properties, value) {
    'use strict';
    if (properties.length < 1) {
        throw 'List of properties must be non-empty';
    }
    var obj = this.loadObject(properties[0]);
    obj.timestamp = Date.now();
    if (properties.length === 1) {
        obj.data = value;
    } else {
        var data = obj.data;
        for (var index = 1; index < properties.length - 1; index++) {
            var property = properties[index];
            if (!(property in data)) {
                data[property] = {};
            }
            data = data[property];
        }

        var last = properties[properties.length - 1];
        data[last] = value;
    }
    this.storeObject(properties[0], obj);
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
        obj.timestamp = Date.now();
        var data = obj.data;
        for (var index = 1; index < properties.length - 1; index++) {
            var property = properties[index];
            if (!(property in data)) {
                if (Object.keys(data).length === 0) {
                    this.delete(properties.slice(0, index - 1));
                }
                return;
            }
            data = data[property];
        }

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
    var obj = this.loadObject(name);
    return obj.timestamp;
};

var storage = new Storage('malasakit');
