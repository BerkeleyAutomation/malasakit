/** bloom.js
 */

// The Base64 representation of a PNG of `fa-comment` from Font Awesome
var ICON_IMAGE = "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iaXNvLTg4NTktMSI/Pgo8"
               + "IS0tIEdlbmVyYXRvcjogQWRvYmUgSWxsdXN0cmF0b3IgMTYuMC4wLCBTVkcg"
               + "RXhwb3J0IFBsdWctSW4gLiBTVkcgVmVyc2lvbjogNi4wMCBCdWlsZCAwKSAg"
               + "LS0+CjwhRE9DVFlQRSBzdmcgUFVCTElDICItLy9XM0MvL0RURCBTVkcgMS4x"
               + "Ly9FTiIgImh0dHA6Ly93d3cudzMub3JnL0dyYXBoaWNzL1NWRy8xLjEvRFRE"
               + "L3N2ZzExLmR0ZCI+CjxzdmcgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIw"
               + "MDAvc3ZnIiB4bWxuczp4bGluaz0iaHR0cDovL3d3dy53My5vcmcvMTk5OS94"
               + "bGluayIgdmVyc2lvbj0iMS4xIiBpZD0iQ2FwYV8xIiB4PSIwcHgiIHk9IjBw"
               + "eCIgd2lkdGg9IjMycHgiIGhlaWdodD0iMzJweCIgdmlld0JveD0iMCAwIDUx"
               + "MS42MjYgNTExLjYyNiIgc3R5bGU9ImVuYWJsZS1iYWNrZ3JvdW5kOm5ldyAw"
               + "IDAgNTExLjYyNiA1MTEuNjI2OyIgeG1sOnNwYWNlPSJwcmVzZXJ2ZSI+Cjxn"
               + "PgoJPHBhdGggZD0iTTQ3Ny4zNzEsMTI3LjQ0Yy0yMi44NDMtMjguMDc0LTUz"
               + "Ljg3MS01MC4yNDktOTMuMDc2LTY2LjUyM2MtMzkuMjA0LTE2LjI3Mi04Mi4w"
               + "MzUtMjQuNDEtMTI4LjQ3OC0yNC40MSAgIGMtMzQuNjQzLDAtNjcuNzYyLDQu"
               + "ODA1LTk5LjM1NywxNC40MTdjLTMxLjU5NSw5LjYxMS01OC44MTIsMjIuNjAy"
               + "LTgxLjY1MywzOC45N2MtMjIuODQ1LDE2LjM3LTQxLjAxOCwzNS44MzItNTQu"
               + "NTM0LDU4LjM4NSAgIEM2Ljc1NywxNzAuODMzLDAsMTk0LjQ4NCwwLDIxOS4y"
               + "MjhjMCwyOC41NDksOC42MSw1NS4zLDI1LjgzNyw4MC4yMzRjMTcuMjI3LDI0"
               + "LjkzMSw0MC43NzgsNDUuODcxLDcwLjY2NCw2Mi44MTEgICBjLTIuMDk2LDcu"
               + "NjExLTQuNTcsMTQuODQ2LTcuNDI2LDIxLjY5M2MtMi44NTUsNi44NTItNS40"
               + "MjQsMTIuNDc0LTcuNzA4LDE2Ljg1MWMtMi4yODYsNC4zNzctNS4zNzYsOS4y"
               + "MzMtOS4yODEsMTQuNTYyICAgYy0zLjg5OSw1LjMyOC02Ljg0OSw5LjA4OS04"
               + "Ljg0OCwxMS4yNzVjLTEuOTk3LDIuMTktNS4yOCw1LjgxMi05Ljg1MSwxMC44"
               + "NDljLTQuNTY1LDUuMDQ4LTcuNTE3LDguMzI5LTguODQ4LDkuODU1ICAgYy0w"
               + "LjE5MywwLjA4OS0wLjk1MywwLjk1Mi0yLjI4NSwyLjU2N2MtMS4zMzEsMS42"
               + "MTUtMS45OTksMi40MjMtMS45OTksMi40MjNsLTEuNzEzLDIuNTY2Yy0wLjk1"
               + "MywxLjQzMS0xLjM4MSwyLjMzNC0xLjI4NywyLjcwNyAgIGMwLjA5NiwwLjM3"
               + "My0wLjA5NCwxLjMzMS0wLjU3LDIuODUxYy0wLjQ3NywxLjUyNi0wLjQyOCwy"
               + "LjY2OSwwLjE0MiwzLjQzM3YwLjI4NGMwLjc2NSwzLjQyOSwyLjQzLDYuMTg3"
               + "LDQuOTk4LDguMjc3ICAgYzIuNTY4LDIuMDkyLDUuNDc0LDIuOTUsOC43MDgs"
               + "Mi41NjNjMTIuMzc1LTEuNTIyLDIzLjIyMy0zLjYwNiwzMi41NDgtNi4yNzZj"
               + "NDkuODctMTIuNzU4LDkzLjY0OS0zNS43ODIsMTMxLjMzNC02OS4wOTcgICBj"
               + "MTQuMjcyLDEuNTIyLDI4LjA3MiwyLjI4Niw0MS4zOTYsMi4yODZjNDYuNDQy"
               + "LDAsODkuMjcxLTguMTM4LDEyOC40NzktMjQuNDE3YzM5LjIwOC0xNi4yNzIs"
               + "NzAuMjMzLTM4LjQ0OCw5My4wNzItNjYuNTE3ICAgYzIyLjg0My0yOC4wNjIs"
               + "MzQuMjYzLTU4LjY2MywzNC4yNjMtOTEuNzgxQzUxMS42MjYsMTg2LjEwOCw1"
               + "MDAuMjA3LDE1NS41MDksNDc3LjM3MSwxMjcuNDR6IiBmaWxsPSIjZGFhNTIw"
               + "Ii8+CjwvZz4KPGc+CjwvZz4KPGc+CjwvZz4KPGc+CjwvZz4KPGc+CjwvZz4K"
               + "PGc+CjwvZz4KPGc+CjwvZz4KPGc+CjwvZz4KPGc+CjwvZz4KPGc+CjwvZz4K"
               + "PGc+CjwvZz4KPGc+CjwvZz4KPGc+CjwvZz4KPGc+CjwvZz4KPGc+CjwvZz4K"
               + "PGc+CjwvZz4KPC9zdmc+Cg=="

var CONTENT_TYPE = 'image/png';

if (Resource.exists('bloom-icon')) {
    var resource = Resource.load('bloom-icon');
    if (resource.data !== null) {
        ICON_IMAGE = resource.data['encoded-image'];
        CONTENT_TYPE = resource.data['content-type'];
    }
}

const NO_TAG_PLACEHOLDER = '(?)';
const MIN_REQUIRED_COMMENT_RATINGS = 2;

function calculateBounds(comments) {
    var bounds = {
        top: -Infinity, bottom: Infinity, left: Infinity, right: -Infinity
    };

    for (var commentID in comments) {
      var comment = comments[commentID];
        var x = comment['pos'][0], y = comment['pos'][1];
        bounds.top = Math.max(bounds.top, y);
        bounds.bottom = Math.min(bounds.bottom, y);
        bounds.left = Math.min(bounds.left, x);
        bounds.right = Math.max(bounds.right, x);
    }

    return bounds;
}

var bounds;

function makeNodeData(comments, width, height) {
    var nodeData = [];
    for (var commentID in comments) {
        var comment = comments[commentID];
        var x = comment['pos'][0], y = comment['pos'][1], tag = comment['tag'];

        // Normalized coordinates
        nodeData.push({
            x: (x - bounds.left)/(bounds.right - bounds.left)*width,
            y: (y - bounds.bottom)/(bounds.top - bounds.bottom)*height,
            tag: (tag !== null && tag.trim()) ? tag : NO_TAG_PLACEHOLDER,
            commentID: commentID,
        });
    }
    return nodeData;
}

function startDrag(node) {
    if (!d3.event.active) {
        simulation.alphaTarget(0.3).restart();
    }
    node.fx = node.x;
    node.fy = node.y;
}

function continueDrag(node) {
    node.fx = d3.event.x;
    node.fy = d3.event.y;
}

function endDrag(node) {
    if (!d3.event.active) {
        simulation.alphaTarget(0);
    }
    node.fx = null;
    node.fy = null;
}

function resetBloom() {
    $('.modal').css('display', 'none');
    renderComments();
    setNextButtonStatus();
}

function startCommentRating(commentID) {
    var qualitativeQuestions = Resource.load('qualitative-questions').data;
    var comments = Resource.load('comments').data;

    var promptTranslations = qualitativeQuestions[comments[commentID].qid];
    var preferredLanguage = getResponseValue(['respondent-data', 'language']);
    var translatedPrompt = promptTranslations[preferredLanguage];

    var inputElement = $('input.quantitative-input[target-id=comment-rating]');

    $('.modal').css('display', 'block');
    $('#question-prompt').text(translatedPrompt);
    $('#comment-message').text(comments[commentID].msg);

    inputElement.val(0);
    var path = ['comment-ratings', commentID];
    if (getResponseValue(path) === null) {
        setResponseValue(path, parseInt(inputElement.val()));
    }

    function updateOutputReading() {
        $('#quantitative-output').text(inputElement.val().toString() + '/9');
    };

    inputElement.unbind('input');
    inputElement.on('input', function() {
        updateOutputReading();
        setResponseValue(path, parseInt(inputElement.val()));
    });
    updateOutputReading();

    $('#submit').on('click', resetBloom);

    $('#skip').unbind('click');
    $('#skip').on('click', function() {
        setResponseValue(path, -1);
        resetBloom();
    });
}

var simulation;

function renderComments() {
    var bloom = d3.select('#bloom'),
        width = bloom.node().getBoundingClientRect().width,
        height = width * 0.6;  // Constant aspect ratio
    bloom.attr('height', height);

    console.log('Rendering ' + width + 'x' + height + ' bloom');
    simulation = d3.forceSimulation().force('charge', d3.forceManyBody());
    bloom.selectAll('*').remove();

    var selectedComments = Resource.load('selected-comments').data || {};
    bounds = calculateBounds(selectedComments);
    for (var commentID in selectedComments) {
        if (commentID in getResponseValue(['comment-ratings'])) {
            delete selectedComments[commentID];
        }
    }
    var nodeData = makeNodeData(selectedComments, width, height);
    if (nodeData.length == 0) {
        $('#no-more-comments-notice').css('display', 'block');
        return;
    }

    var drag = d3.drag().on('start', startDrag).on('drag', continueDrag).on('end', endDrag);
    var nodes = bloom.selectAll('g').data(nodeData).enter().append('g');

    nodes.call(drag).on('click', function(node) {
        startCommentRating(node.commentID);
    });
    nodes.append('image')
         .attr('xlink:href', 'data:' + CONTENT_TYPE + ';base64,' + ICON_IMAGE);
    nodes.append('text').text(node => node.tag).attr('x', 30).attr('y', 15)
         .attr('fill', '#1371ad');

    function tick() {
        nodes.attr('transform', function(node) {
            var x = Math.max(0, Math.min(node.x, width - 50));
            var y = Math.max(20, Math.min(node.y, height - 20));
            return 'translate(' + x + ', ' + y + ')';
        });
    }

    simulation.nodes(nodeData).on('tick', tick);
}

function setNextButtonStatus() {
    var comments = Resource.load('comments');
    var numComments = Object.keys(comments.data).length;
    var commentRatings = getResponseValue(['comment-ratings']);
    var requiredRatings = Math.min(MIN_REQUIRED_COMMENT_RATINGS, numComments);
    var disabled = Object.keys(commentRatings).length < requiredRatings;

    if (disabled) {
        $('#next > a').click(function(event) {
            event.preventDefault();
        });
        $('#next').addClass('blocked');
    } else {
        $('#next > a').unbind('click');
        $('#next').removeClass('blocked');
    }
}

$(document).ready(function() {
    displayNoCurrentRespondentError();
    selectComments(selectCommentFromStandardError);
    resetBloom();
    $(window).resize(renderComments);
});
