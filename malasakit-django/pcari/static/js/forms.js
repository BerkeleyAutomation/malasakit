/* forms.js */

var DEFAULT_MIN_SCORE = 1;
var DEFAULT_MAX_SCORE = 6;

function addLinebreaks(text) {
    return text.replace(/\n/g, '<br>');
}

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

function renderSlider(id, question) {
    var currentResponse = storage.get(['current']);
    var ratings = storage.get([currentResponse, 'question-ratings']);
    var qid = question.id.toString();
    return makeElement('<input>', {
        id: id,
        type: 'range',
        min: min,
        max: max,
        value: (qid in ratings) ? ratings[qid] : randomInt(min, max)
    });
}

function renderNumericTextField(id, question) {
    var currentResponse = storage.get(['current']);
    return makeElement('<input>', {
        id: id,
        type: 'number',
        min: min,
        max: max,
        // value:
    });
    // TODO
}

function renderButtonGroup(minScore, maxScore, callback) {
    var buttonContainer = $('<div>').addClass('scale-container');
    var buttonGroup = $('<ul>').addClass('button-group scale-center');
    for (var score = minScore; score <= maxScore; score++) {
        buttonGroup.append($('<li>').append(
            $('<div>')
                .addClass('nav-button')
                .text(score)
                .on('click', function() {
                    callback(parseInt($(this).text()));
                })
        ));
    }
    buttonContainer.append(buttonGroup);
    buttonContainer.append($('<span>').addClass('left-anchor').append(
        $('<img>').attr('src', urljoin([STATIC_URL_ROOT, 'img/red-emoticon.png'])).attr('width', 48)
    ));
    buttonContainer.append($('<span>').addClass('right-anchor').append(
        $('<img>').attr('src', urljoin([STATIC_URL_ROOT, 'img/green-emoticon.png'])).attr('width', 48)
    ));
    return buttonContainer;
}

function ProfileQuestionRenderer(previousURL, nextURL) {
    'use strict';
    var questions = storage.get(['quantitative-questions']).concat(
                    storage.get(['option-questions']));
    questions.sort(function(question1, question2) {
        if (question1.order === null || question1.order === undefined) {
            return 1;
        } else if (question2.order === null || question2.order === undefined) {
            return -1;
        } else {
            return question1.order - question2.order;
        }
    });
    $('#num-questions').text(questions.length);
    var index = 0;  // TODO: set to last question

    this.next = function() {
        if (index >= questions.length) {
            redirect(nextURL);
        } else {
            index++;
            this.render();
        }
    };

    this.previous = function() {
        if (index === 0) {
            redirect(previousURL);
        } else {
            index--;
            this.render();
        }
    };

    this.render = function() {
        $('#question-num').text(Math.min(index + 1, questions.length));
        $('#answer').empty();
        $('#notice').empty();
        $('#button-group').empty();
        var question = questions[index];
        var prompt = question.prompts[getCurrentLanguage()]
        $('#prompt').html(addLinebreaks(prompt));

        var question = questions[index];
        var minScore = question['min-score'] || DEFAULT_MIN_SCORE;
        var maxScore = question['max-score'] || DEFAULT_MAX_SCORE;
        switch (question['input-type']) {
            case 'range':
            //    break;
            case 'number':
            //    break;
            case 'buttons':
                // FIXME
                $('#answer').append(
                    renderButtonGroup(minScore, maxScore, function(value) {console.log(value);})
                );
                break;
            case 'select':
                break;
            case 'radio':
                break;
            default:
                redirect(nextURL);
        }
    };
}
