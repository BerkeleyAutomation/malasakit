/** bloom.js
 */

/*

// The Base64 representation of a PNG of `fa-comment` from Font Awesome
// Can be easily configured
const ICON_IMAGE = 'iVBORw0KGgoAAAANSUhEUgAAABgAAAAYCAYAAADgdz34AAABDklEQVR4nNXVzyqEURzG8c+8+Z/i'
                 + 'DmwkKymRspNbsLBxA27AzkLZyF7Kn4XsJEulRsMVuAHJhiZRUzKpGYuZt6bXyzDOSZ56luf7PefX'
                 + 'qR9/mDGs4QxPqGf6jEusY+In4DmUcoDteoX5r8Dd2OkAnO0e+rLwXpwHgKctob9VsB0QnvYohc9G'
                 + 'gKdd0DTFEhzDTUTBfQFV9IiTtwTlSHB4SFCMKCjCNGrCz7+GqdS0EUGw2fqUAvYDwg+R5M1sBS+/'
                 + 'AL9itXnhT7PbAbiKA4xmYVnTIO4wnCMuY6h5poJbXOMCpxo7o222cm5XweJ3DrfLko/f9QQjIeDj'
                 + 'GnOs41FjaUyGAKcZwDJm0BUS/P/zDqZIDzgtIDS2AAAAAElFTkSuQmCC';

const NO_TAG = '(?)';

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
            tag: (tag !== null && tag.trim()) ? tag : NO_TAG,
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

function startCommentRating(commentID) {
    console.log('User selected ' + commentID + ' to rate');
    $('.modal').css('display', 'block');
    var qualitativeQuestions = JSON.parse(localStorage.getItem(QUALITATIVE_QUESTIONS_KEY));
    var comments = JSON.parse(localStorage.getItem(COMMENTS_KEY));
    if (qualitativeQuestions !== null && comments !== null) {
        var prompt = qualitativeQuestions[comments[commentID]['qid']];
        $('#comment-rating').val(0);
        $('#question-prompt').text(prompt);
        $('#comment-message').text(comments[commentID].msg);
        var path = ['comment-ratings', commentID];
        if (getResponseValue(path) === null) {
            setResponseValue(path, [parseInt($('#comment-rating').val())]);
        }
        $('#comment-rating').unbind('change');
        bindHistoryStoreListener($('#comment-rating'), path, parseInt);
        $('#submit').on('click', function() {
            $('.modal').css('display', 'none');
            renderComments();
            setNextButtonStatus();
        });
        $('#skip').unbind('click');
        $('#skip').on('click', function() {
            var history = getResponseValue(path);
            history.push(-1);
            setResponseValue(path, history);
            $('.modal').css('display', 'none');
            renderComments();
            setNextButtonStatus();
        });
    }
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

    var selectedComments = JSON.parse(localStorage.getItem(SELECTED_COMMENTS_KEY)) || {};
    bounds = calculateBounds(selectedComments);
    for (var commentID in selectedComments) {
        if (commentID in getResponseValue(['comment-ratings'])) {
            delete selectedComments[commentID];
        }
    }
    var nodeData = makeNodeData(selectedComments, width, height);

    var drag = d3.drag().on('start', startDrag).on('drag', continueDrag).on('end', endDrag);
    var nodes = bloom.selectAll('g').data(nodeData).enter().append('g');

    nodes.call(drag).on('click', function(node) {
        startCommentRating(node.commentID);
    });
    nodes.append('image')
         .attr('xlink:href', 'data:image/png;base64,' + ICON_IMAGE);
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
    var disabled = Object.keys(getResponseValue(['comment-ratings'])).length < 2;
    if (disabled) {
        $('#next > a').click(function(event) {
            event.preventDefault();
        });
        // $('#next').prop('disabled', true);
    } else {
        $('#next > a').unbind('click');
    }
}

$(document).ready(function() {
    selectComments(selectCommentFromStandardError);
    renderComments();
    setNextButtonStatus();
    $(window).resize(renderComments);
});

*/
