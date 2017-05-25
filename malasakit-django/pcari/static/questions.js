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

function loadNextQuestion(qid) {
  $.getJSON('/pcari/get-question/' + qid + '/', function(data) {
    $('#question').text(data['question']);
    $('#answer').val(3);
  });
}

var qids;
var index = 0;
$.getJSON('/pcari/get-question-ids/', function(data) {
  qids = data['qids'];
  loadNextQuestion(qids[index]);
});

function submitAnswer(choice) {
  if (index < qids.length) {
    $.post('/pcari/save-answer/', {
      qid: qids[index],
      choice: choice
    });
    // TODO: check that the response code is 200
  }
  
  index++;
  if (index >= qids.length) {
    $('#question').text('All questions answered.');
  } else {
    loadNextQuestion(qids[index]);
  }
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

  $('#submit').click(function(event) {
    var choice = parseInt($('#answer').val());
    submitAnswer(choice);
  });

  $('#skip').click(function(event) {
    submitAnswer(-1);
  });
});
