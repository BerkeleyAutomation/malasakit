# Include this line at the beginning of every script.
import environment

from math import sqrt
from pcari.models import QuantitativeQuestion, Rating, Comment, CommentRating


questions = QuantitativeQuestion.objects.all()

for q in questions:
    q.average_score = 0
    q.number_rated = 0
    q.save()

ratings = Rating.objects.all()

for r in ratings:
    r.accounted = False
    r.save()

crs = CommentRating.objects.all()

for cr in crs:
    cr.accounted = False
    cr.save()

comments = Comment.objects.all()

for c in comments:
    c.average_score = 0
    c.number_rated = 0
    c.save()

comments = Comment.objects.all()
for comment in comments:
    ratings = CommentRating.objects.all().filter(cid=comment.id, accounted=False)
    current_ave = comment.average_score * comment.number_rated
    for rating in ratings:
        if rating.score == -1 or rating.score == -2:
            continue
        if rating.accounted:
            continue
        current_ave += rating.score
        rating.accounted = True
        rating.save()
    comment.number_rated += len(ratings)
    if comment.number_rated == 0:
        continue
    comment.average_score = (current_ave+0.0)/(comment.number_rated+0.0)
    comment.save()

comments = Comment.objects.all()
for comment in comments:
    if comment.number_rated == 0:
        continue
    ratings = CommentRating.objects.all().filter(cid=comment.id)
    var = 0
    ave = comment.average_score
    for rating in ratings:
        if rating.score == -1 or rating.score == -2:
            continue
        var += (rating.score - ave + 0.0)**2 / (comment.number_rated + 0.0)
    comment.se = (sqrt(var) + 0.0) / (sqrt(comment.number_rated) + 0.0)
    comment.save()
