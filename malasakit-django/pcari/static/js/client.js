/** client.js -- Response and comment storage and transmission
 *
 *  Uses the `localStorage` API and AJAX calls to store comments and responses
 *  locally.
 */

const CURRENT_RESPONSE_KEY = 'current';
const RESPONSE_KEY_PREFIX = 'user-';
const CURRENT_RESPONSE_LIFETIME = 24*60*60*1000;
const RESPONSE_PUSH_ENDPOINT = '/pcari/save-response/';
const RESPONSE_PUSH_TIMEOUT = 5000;

const COMMENTS_KEY = 'comments';
const COMMENTS_TIMESTAMP_KEY = 'comments-timestamp';
const COMMENTS_LIFETIME = 12*60*60*1000;
const COMMENTS_FETCH_ENDPOINT = '/pcari/fetch-comments/';
const COMMENTS_FETCH_TIMEOUT = 5000;

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
    console.log('AJAX with CSRF token usage initialized');
 }

function getCurrentTimestamp() {
    return new Date().getTime();
}

function editLocalStorageJSON(key, callback) {
    var unserializedObject = JSON.parse(localStorage.getItem(key));
    unserializedObject = callback(unserializedObject);
    if (unserializedObject !== null) {
        localStorage.setItem(key, JSON.stringify(unserializedObject));
    }
}

function initializeNewResponse() {
    var now = getCurrentTimestamp();
    var key = RESPONSE_KEY_PREFIX + now.toString();
    localStorage.setItem(CURRENT_RESPONSE_KEY, key);
    localStorage.setItem(key, JSON.stringify(EMPTY_RESPONSE));
}

function pushResponse(responseKey) {
    var response = localStorage.getItem(responseKey);
    if (response !== null) {
        $.ajax(RESPONSE_PUSH_ENDPOINT, {
            method: 'POST',
            timeout: RESPONSE_PUSH_TIMEOUT,
            data: response,
            success: function() {
                console.log('Successfully pushed data for ' + responseKey);
                localStorage.removeItem(responseKey);
            },
            error: function() {
                console.log('Could not push data for ' + responseKey);
            },
        });
    }
}

function pushCompletedResponses() {
    var currentResponseKey = localStorage.getItem(CURRENT_RESPONSE_KEY);
    for (var key in localStorage) {
        if (key.startsWith(RESPONSE_KEY_PREFIX) && key !== currentResponseKey) {
            pushResponse(key);
        }
    }
}

function editCurrentResponse(callback) {
    var currentResponseKey = localStorage.getItem(CURRENT_RESPONSE_KEY);
    editLocalStorageJSON(currentResponseKey, function(response) {
        if (response === null) {
            return null;
        }
        callback(response);
        return response;
    });
}

function recordCurrentLanguage() {
    editCurrentResponse(function(response) {
        var language = $('html').attr('lang');
        response['respondent-data']['language'] = language;
        console.log('Set respondent language to "' + language + '"');
    });
}

function getTimestampFromResponseKey(key) {
    console.assert(key.startsWith(RESPONSE_KEY_PREFIX));
    return new Date(parseInt(key.substring(RESPONSE_KEY_PREFIX.length)));
}

function invalidateCurrentResponseKey() {
    if (CURRENT_RESPONSE_KEY in localStorage) {
        delete localStorage[CURRENT_RESPONSE_KEY];
    }
}

function invalidateOldCurrentResponseKey() {
    if (CURRENT_RESPONSE_KEY in localStorage) {
        var currentResponseKey = localStorage.getItem(CURRENT_RESPONSE_KEY);
        var now = getCurrentTimestamp();
        var currentResponseTimestamp = getTimestampFromResponseKey(currentResponseKey);
        if (now - currentResponseTimestamp > CURRENT_RESPONSE_LIFETIME) {
            invalidateCurrentResponseKey();
            console.log('Invalidated old current response key');
        } else {
            console.log('Current response key is still alive');
        }
    }
}

function commentsExpired() {
    var now = getCurrentTimestamp();
    var commentsTimestamp = parseInt(localStorage.getItem(COMMENTS_TIMESTAMP_KEY));
    return now - commentsTimestamp > COMMENTS_LIFETIME;
}

function fetchComments() {
    if (!(COMMENTS_KEY in localStorage) || commentsExpired()) {
        $.ajax(COMMENTS_FETCH_ENDPOINT, {
            timeout: COMMENTS_FETCH_TIMEOUT,
            success: function(comments) {
                var now = getCurrentTimestamp();
                localStorage.setItem(COMMENTS_KEY, JSON.stringify(comments));
                localStorage.setItem(COMMENTS_TIMESTAMP_KEY, now.toString());
                console.log('Successfully fetched comments');
            },
            failure: function(comments) {
                console.log('Failed to fetch comments');
            }
        });
    } else {
        console.log('Using cached comments');
    }
}

function bindListener(element, callback) {
    element.on('input', function() {
        var value = $(this).val();
        callback(value);
    });
}

function makeValueStoreCallback(path, preprocess = x => x, verbose = true) {
    console.assert(path.length > 1);
    var pathRepr = '[' + path.join(' -> ') + ']';

    return function(value) {
        value = value.trim();
        editCurrentResponse(function(response) {
            var pathFront = path.slice(0, -1), pathLast = path[path.length - 1];
            var parentObject = response;
            pathFront.forEach(function(key) {
                parentObject = parentObject[key];
            });

            if (value) {
                parentObject[pathLast] = preprocess(value);
                if (verbose) {
                    console.log(pathRepr + ' of current response set to ' + value);
                }
            } else {
                delete parentObject[pathLast];
                if (verbose) {
                    console.log('Removed ' + pathRepr + ' of current response');
                }
            }
        });
    };
}

$(document).ready(function() {
    csrfSetup();
    recordCurrentLanguage();
    invalidateOldCurrentResponseKey();
    pushCompletedResponses();
    fetchComments();
});
