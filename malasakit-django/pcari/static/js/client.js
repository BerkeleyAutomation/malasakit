/* client.js */

var storage = new Storage('malasakit');
var DEFAULT_TIMEOUT = 5000;
var DEFAULT_LANGUAGE = 'tl';

function redirect(url) {
    window.location.replace(url);
}

function urljoin(components) {
    var url = '/';
    for (var index = 0; index < components.length; index++) {
        url += components[index] + '/';
    }
    return url.replace(/\/+/g, '/');  // Remove duplicate forward slashes
}

function randomInt(a, b) {
    return Math.floor((b - a + 1)*Math.random()) + a;
}

function getCurrentLanguage() {
    return $('html').attr('lang') || DEFAULT_LANGUAGE;
}

function recordCurrentLanguage() {
    if (storage.hasObject('current-response')) {
        var current = storage.get(['current-response']);
        if (current !== null) {
            storage.set([current, 'personal-data', 'language'], getCurrentLanguage());
        }
    }
}

var URL_ROOT = '';  // TODO: change to `/pcariv2` on `opinion.berkeley.edu`
var API_URL_ROOT = urljoin([URL_ROOT, '/api/']);
var STATIC_URL_ROOT = urljoin([URL_ROOT, '/static/']);
var SAVE_ENDPOINT = urljoin([API_URL_ROOT, '/save-response/']);

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
}

function fetch(url, properties) {
    $.ajax(url, {
        timeout: DEFAULT_TIMEOUT,
        success: function(data) {
            storage.set(properties, data);
        }
    });
}

function push(url, data) {
    var success = false;
    $.ajax(url, {
        method: 'POST',
        data: JSON.stringify(data),
        timeout: DEFAULT_TIMEOUT,
        success: function() {
            success = true;
        }
    });
    return success;
}

function initializeStorageState() {
    if (!storage.hasObject('current-response') ||
            storage.isStale('current-response', 24*60*60*1000)) {
        storage.set(['current-response'], null);
    }
    if (!storage.hasObject('completed-responses')) {
        storage.set(['completed-responses'], []);
    }
}

function fetchAPIData() {
    fetch(urljoin([API_URL_ROOT, '/fetch/quantitative-questions/']), ['quantitative-questions']);
    fetch(urljoin([API_URL_ROOT, '/fetch/option-questions/']), ['option-questions']);
    fetch(urljoin([API_URL_ROOT, '/fetch/qualitative-questions/']), ['qualitative-questions']);
    fetch(urljoin([API_URL_ROOT, '/fetch/locations/']), ['locations']);
    fetch(urljoin([STATIC_URL_ROOT, '/data/bloom-icon.json']), ['bloom-icon']);
    if (!storage.hasObject('comments') || storage.isStale('comments', 12*60*60*1000)) {
        fetch(urljoin([API_URL_ROOT, '/fetch/comments/']), ['comments']);
    }
}

function pushCompletedResponses() {
    if (storage.hasObject('completed-responses')) {
        var completedResponses = storage.get(['completed-responses']);
        completedResponses = completedResponses.filter(function(responseName) {
            var response = storage.get([responseName]);
            if (push(SAVE_ENDPOINT, response)) {
                storage.delete([responseName]);
                return false;
            }
            return true;
        });
        storage.set(['completed-responses'], completedResponses);
    }
}

function startResponse() {
    if (storage.hasObject('current')) {
        var currentResponse = storage.get(['current']);
        if (currentResponse !== null) {
            var completedResponses = storage.get(['completed-responses']);
            completedResponses.push(currentResponse);
            storage.set(['completed-responses'], completedResponses)
        }
    }

    var responseName = 'response-' + Date.now();
    storage.set([responseName], {
        'question-ratings': {},
        'question-choices': {},
        'comments': {},
        'comment-ratings': {},
        'personal-data': {
            'uuid': uuidv4(),
        },
    });
    storage.set(['current'], responseName);
}

function displayLocalStorageUsage() {
    var total = 0;
    for (var index = 0; index < localStorage.length; index++) {
        var key = localStorage.key(index);
        var data = localStorage.getItem(key);
        var usage = (2*key.length + 2*data.length)/1024;  // In KiB = 2^10 B
        total += usage;
        console.log(key + ': ' + usage.toFixed(3) + ' KiB');
    }
    console.log('Total: ' + total.toFixed(3) + ' KiB');
}

$(document).ready(function() {
    csrfSetup();
    initializeStorageState();
    fetchAPIData();
    recordCurrentLanguage();
    pushCompletedResponses();
});



/*
const DEFAULT_COMMENT_SAMPLE_SIZE = 8;

const SKIPPED = null;

function displayNoCurrentRespondentError() {
    var current = Resource.load('current');
    if (current === undefined || current.data === null || !isResponseName(current.data)) {
        var landingURL = APP_URL_ROOT + '/' + getCurrentLanguage() + '/landing/';
        var landingLink = $('<a>').attr('href', landingURL).text(gettext('new response'));
        displayError(gettext('Your answers are not being saved.') + ' '
                     + interpolate('You should start a %s.', [landingLink[0].outerHTML]));
    }
}

function validatePositiveInteger(event) {
    return event.ctrlKey || event.altKey || 0x30 <= event.keyCode <= 0x39;
}

function displayLocalStorageUsage(precision=3) {

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
*/
