# Include this line at the beginning of every script.
import environment

from pcari.models import QuantitativeQuestion, Rating, Comment, CommentRating
from django.contrib.auth.models import User

def reset():
    comment_ratings = CommentRating.objects.all()
    ratings = Rating.objects.all()
    questions = QuantitativeQuestion.objects.all()
    comments = Comment.objects.all()

    for c in comment_ratings:
        c.accounted = False
        c.save()


    for q in questions:
        q.average_score = 0
        q.number_rated = 0
        q.save()

    for c in comments:
        c.number_rated = 0
        c.average_score = 0
        c.save()

    for r in ratings:
        q = questions[r.qid-1]
        if r.score == -1 or r.score == -2:
            continue
        ave = (q.average_score * q.number_rated + r.score + 0.0) / (q.number_rated + 1)
        q.average_score = ave
        q.number_rated += 1
        q.save()

    for comment in comments:
        ratings = CommentRating.objects.all().filter(cid=comment.id, accounted=False)
        current_ave = comment.average_score * comment.number_rated
        for rating in ratings:
            if rating.score == -1 or rating.score == -2:
                continue
            if rating.accounted == True:
                continue
            current_ave += rating.score
            rating.accounted = True
            rating.save()
        comment.number_rated += len(ratings)
        if comment.number_rated == 0:
            continue
        comment.average_score = (current_ave+0.0)/(comment.number_rated+0.0)
        comment.save()
reset()
