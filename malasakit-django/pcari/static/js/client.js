/** client.js
 *
 *  This script is based on ECMAScript 6, which may not be supported by all
 *  browsers at the time of this writing. The optimal way to use this script is
 *  to transpile it to ECMAScript 5 using something like `babel`, the NPM
 *  package.
 */

function getCurrentTimestamp() {
    return new Date().getTime();
}

class Resource {
    constructor(name, timestamp=null, lifetime=0) {
        this.name = name;
        this.timestamp = timestamp === null ? getCurrentTimestamp() : timestamp;
        this.lifetime = lifetime === null ? Infinity : lifetime;
    }

    get stale() {
        var now = getCurrentTimestamp();
        var timedelta = now - this.timestamp;
        return timedelta > this.lifetime;
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
