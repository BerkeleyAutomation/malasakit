/** comments.js
 */

const COMMENTS_ENDPOINT = '/pcari/fetch-comments';

function readComments() {
    $.getJSON(COMMENTS_ENDPOINT, function(data) {
        console.log(data);
    });
}

$(document).ready(function() {
    readComments();
});
