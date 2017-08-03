/** client.js
 *
 *  This script is based on ECMAScript 6, which may not be supported by all
 *  browsers at the time of this writing. The optimal way to use this script is
 *  to transpile it to ECMAScript 5 using something like `babel`, the NPM
 *  package.
 */

const DEFAULT_LANGUAGE = 'tl';
const DEFAULT_TIMEOUT = 5000;

const APP_URL_ROOT = '';  // TODO: Change to `/pcari` in production
const API_URL_ROOT = APP_URL_ROOT + '/api';
const STATIC_URL_ROOT = APP_URL_ROOT + '/static';
const RESPONSE_SAVE_ENDPOINT = API_URL_ROOT + '/save-response/';

const RESPONSE_KEY_PREFIX = 'response-';
const EMPTY_RESPONSE = {
    'question-ratings': {},
    'comments': {},
    'comment-ratings': {},
    'respondent-data': {},
};

function displayError(message) {
    var bannerMarkup = '<p class="error banner">' + message + '</p>';
    $('header > .container').append(bannerMarkup);
}

function displayNoCurrentRespondentError() {
    var current = Resource.load('current');
    if (!isResponseName(current.data)) {
        var language = $('html').attr('lang') || DEFAULT_LANGUAGE;
        var landingURL = APP_URL_ROOT + '/' + language + '/landing/';
        displayError('Your answers are not being saved. '
                   + 'You should start a <a href="' + landingURL + '">new response</a>.');
    }
}

function redirect(url) {
    $(location).attr('href', url);
}

function getCurrentTimestamp() {
    return new Date().getTime();
}

class Resource {
    constructor(name, timestamp=null, lifetime=0, endpoint=null,
                timeout=DEFAULT_TIMEOUT, data=null) {
        this.name = name;
        this.timestamp = timestamp;
        // JSON cannot represent `Infinity`, so this is the sentinel value
        // for the lifetime of a resource that does not expire
        this.lifetime = lifetime === Infinity ? null : lifetime;
        this.endpoint = endpoint;
        this.timeout = timeout;
        this.data = data;
    }

    static make(obj) {
        // Wrap a raw JavaScript object with the `Resource` class
        var resource = new Resource(obj.name, obj.timestamp, obj.lifetime,
                                    obj.endpoint, obj.timeout, obj.data);
        for (var name in obj) {
            if (resource[name] === undefined) {
                resource[name] = obj[name];
            }
        }
        return resource;
    }

    static load(name) {
        var rawResource = Resource.get(name);
        return Resource.make(rawResource);
    }

    static loadNames() {
        var names = [];
        for (var index = 0; index < localStorage.length; index++) {
            names.push(localStorage.key(index));
        }
        return names;
    }

    static exists(name) {
        return localStorage.getItem(name) !== null;
    }

    static get(name) {
        return JSON.parse(localStorage.getItem(name));
    }

    static put(name, resource) {
        localStorage.setItem(name, JSON.stringify(resource));
    }

    static delete(name) {
        localStorage.removeItem(name);
    }

    exists() {
        return localStorage.getItem(this.name) !== null;
    }

    get() {
        return Resource.load(this.name);
    }

    put() {
        localStorage.setItem(this.name, JSON.stringify(this));
    }

    delete() {
        localStorage.removeItem(this.name);
    }

    updateTimestamp() {
        this.timestamp = getCurrentTimestamp();
    }

    get stale() {
        if (this.timestamp === undefined) {
            return true;
        } else if (this.lifetime === null || !isFinite(this.lifetime)) {
            return false;
        }
        var now = getCurrentTimestamp();
        var timedelta = now - this.timestamp;
        return timedelta > this.lifetime;
    }

    fetch() {
        var resource = this;  // Alias to avoid conflicts in callbacks
        if (resource.endpoint !== undefined) {
            $.ajax(resource.endpoint, {
                timeout: resource.timeout || DEFAULT_TIMEOUT,
                success: function(data) {
                    resource.data = data;
                    resource.updateTimestamp();
                    resource.put();
                    console.log('Successfully fetched ' + resource.name);
                },
                failure: function() {
                    console.log('Failed to fetch data for ' + resource.name);
                },
            });
        }
    }

    push(deleteOnSuccess=true) {
        var resource = this;  // Alias for the callback
        if (resource.endpoint !== undefined) {
            $.ajax(resource.endpoint, {
                method: 'POST',
                data: JSON.stringify(this.data),
                timeout: resource.timeout || DEFAULT_TIMEOUT,
                success: function() {
                    console.log('Successfully pushed ' + resource.name);
                    if (deleteOnSuccess) {
                        resource.delete();
                    }
                },
                failure: function() {
                    console.log('Failed to push data for ' + resource.name);
                },
            })
        }
    }
}

function initializeResources() {
    var comments = new Resource('comments', null, 12*60*60*1000,
                                API_URL_ROOT + '/fetch/comments/');
    var qualitativeQuestions = new Resource('qualitative-questions', null, 0,
                                            API_URL_ROOT + '/fetch/qualitative-questions/');
    var quantitativeQuestions = new Resource('quantitative-questions', null, 0,
                                             API_URL_ROOT + '/fetch/quantitative-questions/');
    var current = new Resource('current', null, 12*60*60*1000);
    var locationData = new Resource('location-data', null, 12*60*60*1000,
                                    STATIC_URL_ROOT + '/data/location-data.json');
    var bloomIcon = new Resource('bloom-icon', null, 0, STATIC_URL_ROOT + '/data/bloom-icon.json');
    var initialResources = [comments, qualitativeQuestions,
                            quantitativeQuestions, current, locationData,
                            bloomIcon];

    comments.default_sample_size = 8;
    current.updateTimestamp();

    for (var index in initialResources) {
        var resource = initialResources[index];
        if (!resource.exists()) {
            resource.put();
        } else {
            initialResources[index] = Resource.load(resource.name);
        }
    }

    return initialResources;
}

function isResponseName(resourceName) {
    return resourceName !== null && resourceName.startsWith(RESPONSE_KEY_PREFIX);
}

function initializeNewResponse() {
    var now = getCurrentTimestamp();
    var responseKey = RESPONSE_KEY_PREFIX + now.toString();
    var response = new Resource(responseKey, now, Infinity,
                                API_URL_ROOT + '/save-response/',
                                DEFAULT_TIMEOUT, EMPTY_RESPONSE);
    response.put();

    var current = Resource.load('current');
    current.data = responseKey;
    current.updateTimestamp();
    current.put();
}

function recordCurrentLanguage() {
    var language = $('html').attr('lang') || DEFAULT_LANGUAGE;
    var current = Resource.load('current');
    if (current.data !== null) {
        var response = Resource.load(current.data);
        response.data['respondent-data'].language = language;
        response.put();
    }
}

function refreshResources() {
    var resourceNames = Resource.loadNames();
    for (var index in resourceNames) {
        var name = resourceNames[index];
        if (!isResponseName(name)) {
            var resource = Resource.load(name);
            if (resource.stale && resource.endpoint !== undefined) {
                resource.fetch();
            }
        }
    }

    var current = Resource.load('current');
    if (current.stale) {
        current.data = null;
        current.put();
    }
}

function postprocess(responseData) {
    var province = responseData['respondent-data']['province'] || '(No province)';
    var cityOrMunicipality = responseData['respondent-data']['city-or-municipality'] || '(No city or municipality)';
    var barangay = responseData['respondent-data']['barangay'] || '(No barangay)';
    responseData['respondent-data'].location = province + ', ' + cityOrMunicipality + ', ' + barangay;
}

function pushCompletedResponses() {
    var resourceNames = Resource.loadNames();
    var currentResponseName = Resource.load('current').data;
    for (var index in resourceNames) {
        var name = resourceNames[index];
        if (isResponseName(name) && name !== currentResponseName) {
            var response = Resource.load(name);
            postprocess(response.data);
            response.push();
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

function selectCommentFromStandardError(comments) {
    var cumulativeErrors = [0], commentIDs = [null];
    for (var id in comments) {
        var comment = comments[id];
        var indexOfLast = cumulativeErrors.length - 1;
        cumulativeErrors.push(cumulativeErrors[indexOfLast] + comment.sem);
        commentIDs.push(id);
    }

    var totalError = cumulativeErrors[cumulativeErrors.length - 1];
    var selectedPoint = totalError * Math.random();

    for (var index = 1; index < cumulativeErrors.length; index++) {
        if (cumulativeErrors[index - 1] <= selectedPoint
                && selectedPoint < cumulativeErrors[index]) {
            return commentIDs[index];
        }
    }
}

function selectComments(method) {
    var selectedComments = new Resource('selected-comments');
    if (!selectedComments.exists() && Resource.exists('comments')) {
        selectedComments.data = {};
        var comments = Resource.load('comments');
        var numToSelect = Math.min(comments.default_sample_size,
                                   Object.keys(comments.data).length);

        for (var index = 0; index < numToSelect; index++) {
            var commentID = method(comments.data);
            selectedComments.data[commentID] = comments.data[commentID];
            delete comments.data[commentID];
        }

        selectedComments.put();
    }
}

function getNestedValue(obj, path) {
    if (path.length === 0) {
        return obj;
    }
    var first = path[0], rest = path.slice(1);
    return first in obj ? getNestedValue(obj[first], rest) : null;
}

function setNestedValue(obj, path, value) {
    if (path.length === 0) {
        return value;
    }
    var first = path[0], rest = path.slice(1);
    obj[first] = setNestedValue(obj[first] || {}, rest, value);
    return obj;
}

function getResponseValue(path) {
    var currentResponseName = Resource.load('current').data;
    var response = Resource.load(currentResponseName);
    return getNestedValue(response.data, path);
}

function setResponseValue(path, value) {
    var currentResponseName = Resource.load('current').data;
    var response = Resource.load(currentResponseName);
    setNestedValue(response.data, path, value);
    response.put();
}

function main() {
    csrfSetup();
    initializeResources();
    recordCurrentLanguage();
    refreshResources();
    pushCompletedResponses();
}

$(document).ready(main);
