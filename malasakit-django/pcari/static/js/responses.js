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

const RESPONSE_SAVE_ENDPOINT = '/pcari/save-response/';
const DEFAULT_TIMEOUT = 5000;  // in ms

const EMPTY_RESPONSE = {
    'question-ratings': {},
    'comments': {},
    'comment-ratings': {},
    'respondent-data': {}
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
            console.log('Invalidating current ID');
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

function updateCurrentResponse(callback) {
    var currentID = getCurrentID();
    if (currentID !== null) {
        var response = JSON.parse(localStorage.getItem(currentID));
        callback(response);
        localStorage.setItem(currentID, JSON.stringify(response))
    }
}

function updateRespondentAttribute(name, value) {
    updateCurrentResponse(function(response) {
        response['respondent-data'][name] = value;
    });
}

function deleteRespondentAttribute(name) {
    updateCurrentResponse(function(response) {
        if (name in response['respondent-data']) {
            delete response['respondent-data'][name];
        }
    });
}

function setLanguage() {
    updateCurrentResponse(function(response) {
        if (response !== null) {
            response['respondent-data']['language'] = $('html').attr('lang');
        }
    });
}

$(document).ready(function() {
    csrfSetup();
    setLanguage();
    attemptInvalidateCurrentID();
    attemptDataPush();
});
