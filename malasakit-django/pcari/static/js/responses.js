/** responses.js -- Response data storage and transmission
 *
 *  Stores response data as JSON using the local storage API.
 *  Attempts to push response data for inactive users when online.
 *
 *  Full specification:
 *    https://github.com/BerkeleyAutomation/malasakit-v1/wiki/Response-Storage-and-Transmission-Specification
 */

const ID_PREFIX = 'id-';
const CURRENT_ID_KEY = 'current';
const CURRENT_ID_LIFETIME = 24 * 60 * 60 * 1000;  // in ms
const NO_CURRENT_ID = 'none';

const RESPONSE_SAVE_ENDPOINT = '/pcari/save-response';
const DEFAULT_TIMEOUT = 5000;  // in ms

const EMPTY_RESPONSE = {
    'question-ratings': [],
    'comments': [],
    'comment-ratings': [],
    'respondent-data': {}
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
}

function getTimestampFromID(id) {
    var millsecondsSinceEpoch = parseInt(id.substring(ID_PREFIX.length));
    return new Date(millsecondsSinceEpoch);
}

function getCurrentID() {
    return localStorage.getItem(CURRENT_ID_KEY);
}

function invalidateCurrentID() {
    localStorage.removeItem(CURRENT_ID_KEY);
}

function attemptInvalidateCurrentID() {
    var currentID = getCurrentID();
    if (currentID !== null) {
        var dateStarted = getTimestampFromID(currentID);
        var now = new Date();
        if (now - dateStarted > CURRENT_ID_LIFETIME) {
            invalidateCurrentID();
        }
    }
}

function pushResponse(id, timeout) {
    var surveyResponse = localStorage.getItem(id);
    $.ajax(RESPONSE_SAVE_ENDPOINT, {
        method: 'POST',
        timeout: timeout,
        data: surveyResponse,
        success: function() {
            console.log('Data push succeeded for ID ' + id);
            localStorage.removeItem(id);
        },
        error: function() {
            console.log('Could not push data for ID ' + id);
        }
    });
}

function attemptDataPush() {
    var currentID = getCurrentID();
    for (var key in localStorage) {
        if (key.startsWith(ID_PREFIX) && key !== currentID) {
            pushResponse(key, DEFAULT_TIMEOUT);
        }
    }
}

function createNewCurrentID() {
    var timestamp = new Date().getTime();
    var id = ID_PREFIX + timestamp;
    localStorage.setItem(CURRENT_ID_KEY, id);
    localStorage.setItem(id, JSON.stringify(EMPTY_RESPONSE));
}

function editCurrentResponse(callback) {
    var currentID = getCurrentID();
    var response = JSON.parse(localStorage.getItem(currentID));
    callback(response);
    localStorage.setItem(currentID, JSON.stringify(response))
}

function updateRespondentAttribute(name, value) {
    editCurrentResponse(function(response) {
        response['respondent-data'][name] = value;
    });
}

function deleteRespondentAttribute(name) {
    editCurrentResponse(function(response) {
        if (name in response['respondent-data']) {
            delete response['respondent-data'][name];
        }
    });
}

$(document).ready(function() {
    csrfSetup();
    attemptInvalidateCurrentID();
    attemptDataPush();
});
