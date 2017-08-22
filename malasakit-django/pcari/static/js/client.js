/** client.js */

const APP_NAME = 'malasakit';

const DEFAULT_LANGUAGE = 'tl';
const DEFAULT_TIMEOUT = 5000;

const APP_URL_ROOT = '';  // TODO: Change to `/pcari` in production
const API_URL_ROOT = APP_URL_ROOT + '/api';
const STATIC_URL_ROOT = APP_URL_ROOT + '/static';
const RESPONSE_SAVE_ENDPOINT = API_URL_ROOT + '/save-response/';

const RESPONSE_LIFETIME = 12*60*60*1000;
const DEFAULT_COMMENT_SAMPLE_SIZE = 8;
const STATIC_RESOURCES = [
    {
        name: 'quantitative-questions',
        endpoint: API_URL_ROOT + '/fetch/quantitative-questions/',
        lifetime: 0
    },
    {
        name: 'option-questions',
        endpoint: API_URL_ROOT + '/fetch/option-questions/',
        lifetime: 0
    },
    {
        name: 'qualitative-questions',
        endpoint: API_URL_ROOT + '/fetch/qualitative-questions/',
        lifetime: 0
    },
    {
        name: 'comments',
        endpoint: API_URL_ROOT + '/fetch/comments/',
        lifetime: 12*60*60*1000
    },
    {
        name: 'location-data',
        endpoint: STATIC_URL_ROOT + '/data/location-data.json',
        lifetime: 12*60*60*1000
    },
    {
        name: 'bloom-icon',
        endpoint: STATIC_URL_ROOT + '/data/bloom-icon.json',
        lifetime: 0
    }
];

const RESPONSE_KEY_PREFIX = 'response-';
const EMPTY_RESPONSE = {
    'question-ratings': {},
    'question-choices': {},
    'comments': {},
    'comment-ratings': {},
    'respondent-data': {},
};

const SKIPPED = null;

function redirect(url) {
    $(location).attr('href', url);
}

function getCurrentTimestamp() {
    return new Date().getTime();
}

function getCurrentLanguage() {
    return $('html').attr('lang') || DEFAULT_LANGUAGE;
}

function displayError(message) {
    var banner = $('<p>').addClass('error banner').html(message);
    $('header > .container').append(banner);
}

function displayNoCurrentRespondentError() {
    var current = Resource.load('current');
    if (current === undefined || current.data === null || !isResponseName(current.data)) {
        var landingURL = APP_URL_ROOT + '/' + getCurrentLanguage() + '/landing/';
        var landingLink = $('<a>').attr('href', landingURL).text('new response');
        console.log(landingLink[0].outerHTML);
        displayError('Your answers are not being saved. '
                   + 'You should start a ' + landingLink[0].outerHTML + '.');
    }
}

class Resource {
    constructor(name, timestamp, data) {
        this.name = name;
        this.timestamp = timestamp;
        this.data = data;
    }

    static _key(name) {
        return APP_NAME + '-' + name;
    }

    static exists(name) {
        return localStorage.getItem(Resource._key(name)) !== null;
    }

    static load(name) {
        var obj = JSON.parse(localStorage.getItem(Resource._key(name)));
        if (obj !== null) {
            var resource = new Resource(obj.name, obj.timestamp, obj.data);
            for (var name in obj) {
                if (resource[name] === undefined) {
                    resource[name] = obj[name];
                }
            }
            return resource;
        }
    }

    static names() {
        var prefix = APP_NAME + '-';
        var names = [];
        for (var index = 0; index < localStorage.length; index++) {
            var key = localStorage.key(index);
            if (key.startsWith(prefix)) {
                names.push(key.substring(prefix.length));
            }
        }
        return names;
    }

    put() {
        localStorage.setItem(Resource._key(this.name), JSON.stringify(this));
    }

    delete() {
        localStorage.removeItem(Resource._key(this.name));
    }

    updateTimestamp() {
        this.timestamp = getCurrentTimestamp();
    }

    stale(lifetime) {
        return getCurrentTimestamp() - this.timestamp > lifetime;
    }
}

function isResponseName(resourceName) {
    return resourceName !== null && resourceName.startsWith(RESPONSE_KEY_PREFIX);
}

function startResponse() {
    var now = getCurrentTimestamp();
    var responseName = RESPONSE_KEY_PREFIX + now.toString();
    var response = new Resource(responseName, now, EMPTY_RESPONSE);
    response.put();

    response = Resource.load(responseName);
    response.data['respondent-data'].uuid = uuidv4();
    response.put();

    var current = Resource.load('current');
    current.data = responseName;
    current.updateTimestamp();
    current.put();
}

function recordCurrentLanguage() {
    var current = Resource.load('current');
    if (current !== undefined && current.data !== null) {
        var response = Resource.load(current.data);
        response.data['respondent-data'].language = getCurrentLanguage();
        response.put();
    }
}

function refreshResources() {
    STATIC_RESOURCES.forEach(function(metadata) {
        var resource = Resource.load(metadata.name);
        if (resource === undefined || resource.stale(metadata.lifetime)) {
            if (resource === undefined) {
                resource = new Resource(metadata.name, null, null);
            }
            $.ajax(metadata.endpoint, {
                timeout: metadata.timeout || DEFAULT_TIMEOUT,
                success: function(data) {
                    resource.data = data;
                    resource.updateTimestamp();
                    resource.put();

                    var message = gettext('Successfully fetched %s');
                    console.log(interpolate(message, [metadata.name]));
                },
                failure: function() {
                    var message = gettext('Failed to fetch %s');
                    console.log(interpolate(message, [metadata.name]));
                }
            });
        }
    });

    var current = Resource.load('current');
    if (current === undefined) {
        current = new Resource('current', getCurrentTimestamp(), null);
        current.put();
    } else if (current.stale(RESPONSE_LIFETIME)) {
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

function pushResponse(response, deleteOnSuccess=true) {
    postprocess(response.data);
    $.ajax(RESPONSE_SAVE_ENDPOINT, {
        method: 'POST',
        data: JSON.stringify(response.data),
        timeout: DEFAULT_TIMEOUT,
        success: function() {
            var message = 'Successfully pushed %s';
            console.log(interpolate(message, [response.name]));
            if (deleteOnSuccess) {
                response.delete();
            }
        },
        failure: function() {
            var message = 'Failed to push %s';
            console.log(interpolate(message, [response.name]));
        }
    });
}

function pushCompletedResponses() {
    var current = Resource.load('current');
    Resource.names().filter(isResponseName).forEach(function(name) {
        var response = Resource.load(name);
        if (current === undefined || response.name !== current.data) {
            pushResponse(response);
        }
    });
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
    console.log(gettext('AJAX with CSRF token usage initialized'));
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
    if (!Resource.exists('selected-comments') && Resource.exists('comments')) {
        var selectedComments = new Resource('selected-comments', getCurrentTimestamp(), {});
        var comments = Resource.load('comments');
        var numToSelect = Math.min(DEFAULT_COMMENT_SAMPLE_SIZE,
                                   Object.keys(comments.data).length);

        for (var index = 0; index < numToSelect; index++) {
            var id = method(comments.data);
            selectedComments.data[id] = comments.data[id];
            delete comments.data[id];
        }

        selectedComments.put();
    }
}

function getNestedValue(obj, path) {
    if (path.length === 0) {
        return obj;
    }
    var first = path[0], rest = path.slice(1);
    return first in obj ? getNestedValue(obj[first], rest) : undefined;
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

function deleteResponseValue(path) {
    if (path.length > 0) {
        var rest = path.slice(0, -1);
        var obj = getResponseValue(rest);
        delete obj[path[path.length - 1]];
        setResponseValue(rest, obj);
    }
}

function main() {
    csrfSetup();
    refreshResources();
    recordCurrentLanguage();
    pushCompletedResponses();
}

$(document).ready(main);
