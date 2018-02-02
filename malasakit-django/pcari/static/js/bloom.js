/** bloom.js
 */

// The Base64 representation of an SVG of `fa-comment` from Font Awesome
// colored using `goldenrod`
var ICON_IMAGE = "PD94bWwgdmVyc2lvbj0iMS4wIiBlbmNvZGluZz0iaXNvLTg4NTktMSI/"
               + "PjwhRE9DVFlQRSBzdmcgUFVCTElDICItLy9XM0MvL0RURCBTVkcgMS4x"
               + "Ly9FTiIgImh0dHA6Ly93d3cudzMub3JnL0dyYXBoaWNzL1NWRy8xLjEv"
               + "RFREL3N2ZzExLmR0ZCI+PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5v"
               + "cmcvMjAwMC9zdmciIHhtbG5zOnhsaW5rPSJodHRwOi8vd3d3LnczLm9y"
               + "Zy8xOTk5L3hsaW5rIiB2ZXJzaW9uPSIxLjEiIGlkPSJDYXBhXzEiIHg9"
               + "IjBweCIgeT0iMHB4IiB3aWR0aD0iMzJweCIgaGVpZ2h0PSIzMnB4IiB2"
               + "aWV3Qm94PSIwIDAgNTExLjYyNiA1MTEuNjI2IiBzdHlsZT0iZW5hYmxl"
               + "LWJhY2tncm91bmQ6bmV3IDAgMCA1MTEuNjI2IDUxMS42MjY7IiB4bWw6"
               + "c3BhY2U9InByZXNlcnZlIj48Zz48cGF0aCBkPSJNNDc3LjM3MSwxMjcu"
               + "NDRjLTIyLjg0My0yOC4wNzQtNTMuODcxLTUwLjI0OS05My4wNzYtNjYu"
               + "NTIzYy0zOS4yMDQtMTYuMjcyLTgyLjAzNS0yNC40MS0xMjguNDc4LTI0"
               + "LjQxICAgYy0zNC42NDMsMC02Ny43NjIsNC44MDUtOTkuMzU3LDE0LjQx"
               + "N2MtMzEuNTk1LDkuNjExLTU4LjgxMiwyMi42MDItODEuNjUzLDM4Ljk3"
               + "Yy0yMi44NDUsMTYuMzctNDEuMDE4LDM1LjgzMi01NC41MzQsNTguMzg1"
               + "ICAgQzYuNzU3LDE3MC44MzMsMCwxOTQuNDg0LDAsMjE5LjIyOGMwLDI4"
               + "LjU0OSw4LjYxLDU1LjMsMjUuODM3LDgwLjIzNGMxNy4yMjcsMjQuOTMx"
               + "LDQwLjc3OCw0NS44NzEsNzAuNjY0LDYyLjgxMSAgIGMtMi4wOTYsNy42"
               + "MTEtNC41NywxNC44NDYtNy40MjYsMjEuNjkzYy0yLjg1NSw2Ljg1Mi01"
               + "LjQyNCwxMi40NzQtNy43MDgsMTYuODUxYy0yLjI4Niw0LjM3Ny01LjM3"
               + "Niw5LjIzMy05LjI4MSwxNC41NjIgICBjLTMuODk5LDUuMzI4LTYuODQ5"
               + "LDkuMDg5LTguODQ4LDExLjI3NWMtMS45OTcsMi4xOS01LjI4LDUuODEy"
               + "LTkuODUxLDEwLjg0OWMtNC41NjUsNS4wNDgtNy41MTcsOC4zMjktOC44"
               + "NDgsOS44NTUgICBjLTAuMTkzLDAuMDg5LTAuOTUzLDAuOTUyLTIuMjg1"
               + "LDIuNTY3Yy0xLjMzMSwxLjYxNS0xLjk5OSwyLjQyMy0xLjk5OSwyLjQy"
               + "M2wtMS43MTMsMi41NjZjLTAuOTUzLDEuNDMxLTEuMzgxLDIuMzM0LTEu"
               + "Mjg3LDIuNzA3ICAgYzAuMDk2LDAuMzczLTAuMDk0LDEuMzMxLTAuNTcs"
               + "Mi44NTFjLTAuNDc3LDEuNTI2LTAuNDI4LDIuNjY5LDAuMTQyLDMuNDMz"
               + "djAuMjg0YzAuNzY1LDMuNDI5LDIuNDMsNi4xODcsNC45OTgsOC4yNzcg"
               + "ICBjMi41NjgsMi4wOTIsNS40NzQsMi45NSw4LjcwOCwyLjU2M2MxMi4z"
               + "NzUtMS41MjIsMjMuMjIzLTMuNjA2LDMyLjU0OC02LjI3NmM0OS44Ny0x"
               + "Mi43NTgsOTMuNjQ5LTM1Ljc4MiwxMzEuMzM0LTY5LjA5NyAgIGMxNC4y"
               + "NzIsMS41MjIsMjguMDcyLDIuMjg2LDQxLjM5NiwyLjI4NmM0Ni40NDIs"
               + "MCw4OS4yNzEtOC4xMzgsMTI4LjQ3OS0yNC40MTdjMzkuMjA4LTE2LjI3"
               + "Miw3MC4yMzMtMzguNDQ4LDkzLjA3Mi02Ni41MTcgICBjMjIuODQzLTI4"
               + "LjA2MiwzNC4yNjMtNTguNjYzLDM0LjI2My05MS43ODFDNTExLjYyNiwx"
               + "ODYuMTA4LDUwMC4yMDcsMTU1LjUwOSw0NzcuMzcxLDEyNy40NHoiIGZp"
               + "bGw9IiNkYWE1MjAiLz48L2c+PC9zdmc+Cg==";

var CONTENT_TYPE = 'image/svg+xml';

if (Resource.exists('bloom-icon')) {
    var resource = Resource.load('bloom-icon');
    if (resource.data !== null) {
        ICON_IMAGE = resource.data['encoded-image'] || ICON_IMAGE;
        CONTENT_TYPE = resource.data['content-type'] || CONTENT_TYPE;
    }
}

const NO_TAG_PLACEHOLDER = '';
const MIN_REQUIRED_COMMENT_RATINGS = 2;

function calculateBounds(comments) {
    var bounds = {
        top: -Infinity, bottom: Infinity, left: Infinity, right: -Infinity
    };

    for (var commentID in comments) {
      var comment = comments[commentID];
        var x = comment.pos[0], y = comment.pos[1];
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
        var x = comment.pos[0], y = comment.pos[1], tag = comment.tag;

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

    var inputElement = $('input#quantitative-input');

    $('.modal').css('display', 'block');
    $('#question-prompt').html(translatedPrompt.replace(/\n/g, '<br>'));
    $('#comment-message').html(comments[commentID].msg.replace(/\n/g, '<br>'));

    inputElement.val(0);
    var path = ['comment-ratings', commentID];
    if (getResponseValue(path) === undefined) {
        setResponseValue(path, parseInt(inputElement.val()));
    }

    function updateOutputReading() {
        $('output#quantitative-output').text(inputElement.val().toString() + '/6');
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
        setResponseValue(path, null);
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
    simulation = d3.forceSimulation().force('charge', d3.forceManyBody().strength(-120));
    bloom.selectAll('*').remove();

    var selectedComments = Resource.load('selected-comments').data || {};
    bounds = calculateBounds(selectedComments);
    for (var commentID in selectedComments) {
        if (commentID in getResponseValue(['comment-ratings'])) {
            delete selectedComments[commentID];
        }
    }
    var nodeData = makeNodeData(selectedComments, width, height);
    if (nodeData.length === 0) {
        $('#notice').empty();
        $('#notice').append($('<p>').addClass('error banner').text(gettext('There are no more comments to rate.')));
        return;
    }

    var drag = d3.drag().on('start', startDrag).on('drag', continueDrag).on('end', endDrag);
    var nodes = bloom.selectAll('g').data(nodeData).enter().append('g').attr('cid', node => node.commentID);

    nodes.call(drag).on('click', function(node) {
        startCommentRating(node.commentID);
    });
    var iconSize = Math.max(0.1*width, 32);
    nodes.append('image')
         .attr('xlink:href', 'data:' + CONTENT_TYPE + ';base64,' + ICON_IMAGE)
         .attr('width', iconSize)
         .attr('height', iconSize);
    nodes.append('text').text(node => node.tag).attr('x', iconSize + 3).attr('y', 15)
         .attr('fill', '#1371ad');

    function tick() {
        var iconHeight = nodes.node().getBoundingClientRect().height;
        nodes.attr('transform', function(node) {
            var x = Math.max(0, Math.min(node.x, width - 2*iconSize));
            var y = Math.max(0.05*iconHeight, Math.min(node.y, height - iconHeight));
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
