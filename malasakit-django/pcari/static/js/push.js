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

function getCurrentIdentifier() {
    return localStorage.getItem("current");
}

function push(identifier) {
    console.log("Attempting to push data for ID " + identifier);
    $.ajax('/pcari/save-response', {
        method: 'POST',
        timeout: 5000,
        data: localStorage.getItem(identifier),
        success: function() {
            console.log("=> Data push succeeded, deleting identifier");
            localStorage.removeItem(identifier);
        },
        error: function() {
            console.log("Could not push data for ID " + identifier);
        }
    });
}

$(document).ready(function() {
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
                var csrftoken = getCookie('csrftoken');
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

    for (var index = 0; index < localStorage.length; index++) {
        var key = localStorage.key(index);
        if (key.startsWith('id-') && key !== getCurrentIdentifier()) {
            push(key);
        }
    }
});
