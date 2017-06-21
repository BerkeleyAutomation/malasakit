/** client.js -- Response and comment storage and transmission
 *
 *  Uses the `localStorage` API and AJAX calls to store comments and responses
 *  locally.
 */

// TODO: refactor the API with less redundancy

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
const SELECTED_COMMENTS_KEY = 'selected-comments';
const DEFAULT_NUM_COMMENTS_TO_SELECT = 8;

const QUALITATIVE_QUESTIONS_KEY = 'qualitative-questions';
const QUALITATIVE_QUESTIONS_FETCH_ENDPOINT = '/pcari/fetch-qualitative-questions/';
const QUALITATIVE_QUESTIONS_FETCH_TIMEOUT = 5000;

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
            editLocalStorageJSON(key, function(response) {
                console.assert(response !== null);
                postprocess();
                return response;
            });
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
    delete localStorage[CURRENT_RESPONSE_KEY];
    delete localStorage[SELECTED_COMMENTS_KEY];
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

function fetchQualitativeQuestions() {
    $.ajax(QUALITATIVE_QUESTIONS_FETCH_ENDPOINT, {
        timeout: QUALITATIVE_QUESTIONS_FETCH_TIMEOUT,
        success: function(qualitativeQuestions) {
            localStorage.setItem(QUALITATIVE_QUESTIONS_KEY,
                                 JSON.stringify(qualitativeQuestions));
            console.log('Successfully fetched qualitative questions');
        },
        failure: function(qualitativeQuestions) {
            console.log('Failed to fetch qualitative questions');
        }
    });
}

/** Mid-level API */

function followPath(response, path) {
    for (var index in path) {
        var component = path[index];
        if (component in response) {
            response = response[component];
        } else {
            return null;
        }
    }
    return response;
}

function getPathRepr(path, separator = ' -> ') {
    return '[' + path.join(separator) + ']'
}

function getResponseValue(path) {
    var value = null;
    editCurrentResponse(function(response) {
        value = followPath(response, path);
    });
    return value;
}

function setResponseValue(path, value, verbose = true) {
    editCurrentResponse(function(response) {
        var last = path[path.length - 1];
        var parent = followPath(response, path.slice(0, -1));
        parent[last] = value;

        if (verbose) {
            console.log(getPathRepr(path) + ' of current response set to ' + value);
        }
    });
}

function deleteResponseValue(path, verbose = true) {
    editCurrentResponse(function(response) {
        var last = path[path.length - 1];
        var parent = followPath(response, path.slice(0, -1));
        delete parent[last];

        if (verbose) {
            console.log('Deleted ' + getPathRepr(path));
        }
    });
}

/** High-level API */

function bindListener(element, eventName, callback) {
    element.on(eventName, function() {
        var value = $(this).val();
        callback(value);
    });
}

function makeValueStoreCallback(path, preprocess, verbose) {
    console.assert(path.length > 1);
    return function(value) {
        value = value.trim();
        if (value) {
            setResponseValue(path, preprocess(value), verbose);
        } else {
            deleteResponseValue(path, verbose);
        }
    };
}

function makeHistoryStoreCallback(path, preprocess, verbose) {
    console.assert(path.length > 1);
    return function(value) {
        value = value.trim();
        var history = getResponseValue(path);
        if (value) {
            history.push(preprocess(value));
        } else {
            history.push(null);
        }
        setResponseValue(path, history);
    }
}

function refillElementFromValue(element, path) {
    var value = getResponseValue(path);
    if (value !== null) {
        element.val(value);
    }
}

function refillElementFromHistory(element, path) {
    var history = getResponseValue(path);
    if (history !== null && history.length > 0) {
        var last = history[history.length - 1];
        if (last !== null) {
            if (last !== -1) {
                element.val(last);
            } else {
                var id = element.attr('id');
                if (id.startsWith('rating-')) {
                    var skipID = 'button#' + id.substring('rating-'.length);
                    $(skipID).text('Answer Question');
                    $(skipID).css('background-color', '#1dc752');
                    element.prop('disabled', true);
                    element.val(history[history.length - 2]);
                }
            }
        }
    }
}

function bindValueStoreListener(element, path, preprocess = x => x, verbose = true) {
    bindListener(element, 'input', makeValueStoreCallback(path, preprocess, verbose));
    refillElementFromValue(element, path);
}

function bindHistoryStoreListener(element, path, preprocess = x => x, verbose = true) {
    bindListener(element, 'change', makeHistoryStoreCallback(path, preprocess, verbose));
    refillElementFromHistory(element, path);
}

function postprocess() {
    var barangay = getResponseValue(['respondent-data', 'barangay']);
    var province = getResponseValue(['respondent-data', 'province']);

    var respondentLocation = null;
    if (barangay !== null && province !== null) {
        respondentLocation = province + ', ' + barangay;
    } else if (barangay !== null) {
        respondentLocation = barangay;
    } else if (province !== null) {
        respondentLocation = province;
    }

    if (respondentLocation !== null) {
        setResponseValue(['respondent-data', 'location'], respondentLocation);
    }
}

function selectCommentFromStandardError(comments) {
    var cumulativeErrors = [0], commentIDs = [null];
    for (var id in comments) {
        var comment = comments[id];
        var indexOfLast = cumulativeErrors.length - 1;
        cumulativeErrors.push(cumulativeErrors[indexOfLast] + comment['sem']);
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
    if (!(SELECTED_COMMENTS_KEY in localStorage) && COMMENTS_KEY in localStorage) {
        var comments = JSON.parse(localStorage.getItem(COMMENTS_KEY));

        var selectedComments = {};
        var numToSelect = Math.min(DEFAULT_NUM_COMMENTS_TO_SELECT,
                                   Object.keys(comments).length);
        for (var index = 0; index < numToSelect; index++) {
            var commentID = method(comments);
            selectedComments[commentID] = comments[commentID];
            delete comments[commentID];
        }

        localStorage.setItem(SELECTED_COMMENTS_KEY, JSON.stringify(selectedComments));
    }
}

$(document).ready(function() {
    csrfSetup();
    recordCurrentLanguage();
    invalidateOldCurrentResponseKey();
    pushCompletedResponses();
    fetchComments();
    fetchQualitativeQuestions();
});
