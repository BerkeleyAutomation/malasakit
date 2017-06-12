# Include this line at the beginning of every script.
from pcari.models import QuantitativeQuestion, Rating


questions = QuantitativeQuestion.objects.all()

ratings = Rating.objects.all().filter(accounted=False)

averages = []
r_count = []

for q in questions:
    averages.append(q.average_score * q.number_rated)
    r_count.append(q.number_rated)

for r in ratings:
    if r.score == -2 or r.score == -1:
        continue
    averages[r.qid-1] += r.score
    r_count[r.qid-1] += 1
    r.accounted = True
    r.save()

for i in range(len(questions)):
    try:
        questions[i].average_score = averages[i]/r_count[i]
        questions[i].number_rated = r_count[i]
        questions[i].save()
    except:
        pass
