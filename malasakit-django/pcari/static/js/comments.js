/** comments.js
 */

const COMMENTS_KEY = 'comments';
const COMMENTS_TIMESTAMP_KEY = 'comments-timestamp';
const COMMENTS_LIFETIME = 24 * 60 * 60 * 1000;  // in ms

const COMMENTS_ENDPOINT = '/pcari/fetch-comments';

function commentsExpired() {
    if (!(COMMENTS_TIMESTAMP_KEY in localStorage)) {
        return true;
    }

    var millsecondsSinceEpoch = parseInt(localStorage.getItem(COMMENTS_TIMESTAMP_KEY));
    var timestamp = new Date(millsecondsSinceEpoch);
    var now = new Date();
    return now - timestamp > COMMENTS_LIFETIME;
}

function fetchComments() {
    if (!(COMMENTS_KEY in localStorage) || commentsExpired()) {
        $.ajax(COMMENTS_ENDPOINT, {
            timeout: 5000,  // TODO: integrate with `responses.js` with common constants
            success: function(data) {
                var timestamp = new Date().getTime();
                localStorage.setItem(COMMENTS_KEY, JSON.stringify(data));
                localStorage.setItem(COMMENTS_TIMESTAMP_KEY, timestamp.toString());
                console.log('Successfully fetched and stored comments');
            },
            error: function(data) {
                console.log('Failed to fetch comments');
            }
        })
    }
}

$(document).ready(function() {
    fetchComments();
});
