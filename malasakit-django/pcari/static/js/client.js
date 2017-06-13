/** storage.js
 */

const CURRENT_RESPONSE_KEY = 'current';
const RESPONSE_KEY_PREFIX = 'user-';
const RESPONSE_LIFETIME = 24*60*60*1000;
const RESPONSE_PUSH_ENDPOINT = '/pcari/save-response/';
const RESPONSE_PUSH_TIMEOUT = 5000;

const COMMENT_KEY = 'comments';
const COMMENT_TIMESTAMP_KEY = 'comments-timestamp';
const COMMENT_LIFETIME = 12*60*60*1000;
const COMMENT_FETCH_ENDPOINT = '/pcari/fetch-comments/';
const COMMENT_FETCH_TIMEOUT = 5000;

const EMPTY_RESPONSE = {
    'question-ratings': {},
    'comments': {},
    'comment-ratings': {},
    'respondent-data': {},
};

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

function getCurrentTimestamp() {
    return new Date().getTime();
}

function editLocalStorageJSON(key, callback) {
    var unserializedObject = JSON.parse(localStorage.getItem(key));
    unserializedObject = callback(unserializedObject);
    localStorage.setItem(key, JSON.stringify(unserializedObject));
}

function initializeNewResponse() {
    var timestamp = getCurrentTimestamp();
    var key = RESPONSE_KEY_PREFIX + timestamp.toString();
    localStorage.setItem(CURRENT_RESPONSE_KEY, key);
    localStorage.setItem(key, JSON.stringify(EMPTY_RESPONSE));
}

function pushCompletedResponses() {
    var currentResponseKey = localStorage.getItem(CURRENT_RESPONSE_KEY);
    for (var key in localStorage) {
        if (key.startsWith(RESPONSE_KEY_PREFIX) && key !== currentResponseKey) {
            $.ajax(RESPONSE_PUSH_ENDPOINT, {
                method: 'POST',
                timeout: RESPONSE_PUSH_TIMEOUT,
                data: localStorage.getItem(key),
                success: function() {
                    console.log('Successfully pushed data for ' + key);
                    localStorage.removeItem(key);
                },
                error: function() {
                    console.log('Could not push data for ' + key);
                },
            });
        }
    }
}

function setLanguage() {
    var currentResponseKey = localStorage.getItem(CURRENT_RESPONSE_KEY);
    editLocalStorageJSON(currentResponseKey, function(response) {
        if (response !== null) {
        }
    });
}

$(document).ready(function() {
    var currentResponseKey = localStorage.getItem(CURRENT_RESPONSE_KEY);
    if (current)
});
