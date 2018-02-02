/* forms.js */

var DEFAULT_MIN_SCORE = 1;
var DEFAULT_MAX_SCORE = 6;

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

function makeElement(tag, attrs) {
    var element = $(tag);
    for (var name in attrs) {
        element.attr(name, attrs[name]);
    }
    return element;
}

function renderSlider(id, question) {
    var min = question.min_score || DEFAULT_MIN_SCORE;
    var max = question.max_score || DEFAULT_MAX_SCORE;
    var currentResponse = storage.get(['current']);
    var ratings = storage.get([currentResponse, 'question-ratings']);
    var qid = question.id.toString();
    var slider = makeElement('<input>', {
        id: id,
        type: 'range',
        min: min,
        max: max,
        value: (qid in ratings) ? ratings[qid] : randomInt(min, max)
    });
    // TODO
}

function renderNumericTextField(id, question) {
    var min = question.min_score || DEFAULT_MIN_SCORE;
    var max = question.max_score || DEFAULT_MAX_SCORE;
    var currentResponse = storage.get(['current']);
    var number = makeElement('<input>', {
        id: id,
        type: 'number',
        min: min,
        max: max,
        value:
    });
    // TODO
}

function renderButtonRow(id, question) {
    //
}

function makeProfileQuestionRenderer(previousURL, nextURL) {
    var questions = storage.get(['quantitative-questions']) +
                    storage.get(['option-questions']);
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

    var index = 0;
    return {
        next: function() {
            if (index >= questions.length) {
                redirect(nextURL);
            } else {
                index++;
                this.render();
            }
        },
        previous: function() {
            if (index === 0) {
                redirect(previousURL);
            } else {
                index--;
                this.render();
            }
        },
        render() {
            $('#question-num').text(Math.max(index + 1, questions.length));
            $('#prompt').empty();
            $('#answer').empty();
            $('#notice').empty();
            $('#button-group').empty();

            var question = questions[index];
            switch (question.input_type) {
                case 'range':
                    break;
                case 'number':
                    break;
                case 'buttons':
                    break;
                case 'select':
                    break;
                case 'radio':
                    break;
                default:
                    redirect(nextURL);
            }
        }
    };
}
