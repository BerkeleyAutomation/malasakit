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

function loadQuestion(question) {
  $('#question').text(question['prompt']);
  $('#answer').val(3);
}

function submitAnswer(choice) {
  if (index < questions.length) {
    console.log(choice);
    /*$.post('/pcari/save-answer/', {
      qid: qids[index],
      choice: choice
    });*/
    // TODO: check that the response code is 200
  }

  index++;
  if (index >= questions.length) {
    $('#question').text('All questions answered.');
  } else {
    loadQuestion(questions[index]);
  }
}

var questions;
var index = 0;
$(document).ready(function() {
  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
              var csrftoken = getCookie('csrftoken');
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
          }
      }
  });

  $.getJSON('/pcari/get/quantitative-questions/', function(data) {
    questions = data['questions'];
    loadQuestion(questions[index]);
  });

  $('#submit').click(function(event) {
    var choice = parseInt($('#answer').val());
    submitAnswer(choice);
  });

  $('#skip').click(function(event) {
    submitAnswer(-1);
  });
});
