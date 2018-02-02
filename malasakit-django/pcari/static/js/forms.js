/* forms.js */

var SKIPPED = null;
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

function renderControlButton(id, color, label, callback) {
    return $('<button>').attr('id', id).addClass(color).text(label).on('click', callback);
}

function renderPreviousButton(renderer) {
    return renderControlButton('previous', 'blue', gettext('Previous'), function() {
        renderer.previous();
    });
}

function renderNextButton(renderer) {
    return renderControlButton('next', 'blue', gettext('Next'), function() {
        renderer.next();
    });
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

function renderButtonGroup(renderer, minScore, maxScore, saveCallback) {
    var buttonContainer = $('<div>').addClass('scale-container');
    var buttonGroup = $('<ul>').addClass('button-group scale-center');
    for (var score = minScore; score <= maxScore; score++) {
        buttonGroup.append($('<li>').append(
            $('<div>')
                .addClass('nav-button')
                .text(score)
                .on('click', function() {
                    saveCallback(parseInt($(this).text()));
                    renderer.next();
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
    var skip = renderControlButton('skip', 'red', gettext('Skip'), function() {
        saveCallback(SKIPPED);
        renderer.next();
    });
    return $('<div>').append(buttonContainer).append(
        $('<ul>').addClass('button-group')
            .append($('<li>').append(renderPreviousButton(renderer)))
            .append($('<li>').append(skip))
    );
}

function isQuantitativeQuestion(question) {
    var inputType = question['input-type'];
    return inputType === 'range' || inputType === 'number' || inputType === 'buttons';
}

function isOptionQuestion(question) {
    var inputType = question['input-type'];
    return inputType === 'select' || inputType === 'radio';
}

function findFirstUnansweredQuestion(questions) {
    var currentResponse = storage.get(['current']);
    var ratings = storage.get([currentResponse, 'question-ratings']);
    var choices = storage.get([currentResponse, 'question-choices']);
    for (var index in questions) {
        var question = questions[index];
        var qid = question.id.toString();
        if (isQuantitativeQuestion(question) && !(qid in ratings)
                || isOptionQuestion(question) && !(qid in choices)) {
            return index;
        }
    }
    return questions.length - 1;  /* Default to last question. */
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
    var index = findFirstUnansweredQuestion(questions);  // FIXME

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
        var prompt = question.prompts[getCurrentLanguage()];
        $('#prompt').html(addLinebreaks(prompt));

        var question = questions[index];
        var minScore = question['min-score'] || DEFAULT_MIN_SCORE;
        var maxScore = question['max-score'] || DEFAULT_MAX_SCORE;

        function ratingSaveCallback(rating) {
            var currentResponse = storage.get(['current']);
            console.log(question.id);
            storage.set([currentResponse, 'question-ratings', question.id.toString()], rating);
        }

        switch (question['input-type']) {
            case 'range':
            //    break;
            case 'number':
            //    break;
            case 'buttons':
                $('#answer').append(
                    renderButtonGroup(this, minScore, maxScore, ratingSaveCallback)
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
