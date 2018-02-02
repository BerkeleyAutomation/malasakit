/* forms.js */

function displayError(message, linkURL, linkMessage) {
    var banner = $('<p>').addClass('error banner').text(message);
    var link = $('<a>').attr('href', linkURL).text(linkMessage);
    banner.append(link);
    $('header > .container').append(banner);
}

function makeClipFunction(lower, upper) {
    return function(n) {
        return Math.max(lower, Math.min(upper, n));
    };
}

function validateResponseState() {
}

function renderSlider() {
    //
}
