import environment

from math import sqrt
from pcari.models import QuantitativeQuestion, Rating, CommentRating, Comment

def comment_update():
	comments = Comment.objects.all()

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
			comment.number_rated += 1
		if comment.number_rated == 0:
			continue
		comment.average_score = (current_ave+0.0)/(comment.number_rated+0.0)
		comment.save()

def se_update():
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

def generate():
	# init_text_cookie(request)

	ratings = Rating.objects.all()

	# url = request.META.get('HTTP_REFERER').split("/")

	r_count = []
	for _ in range(11):
		r_count.append(0)

	for q in QuantitativeQuestion.objects.all():
		r = ratings.filter(qid=q.qid)

		for k in range(len(r_count)):
			r_count[k]=0

		for rating in r:
			if r >= 0:
				r_count[rating.score] += 1
			elif r == -1:
				r_count[10] += 1

		# if "pcari" in url:
		with open("/var/www/opinion/opinion.berkeley.edu/pcari/pcari/static/data/q%d.tsv" % q.qid, "w") as datafile:
			datafile.write("score	count\n")
			for j in range(len(r_count)):
				if j == len(r_count)-1:
					datafile.write("skip"+"	"+str(r_count[j])+"\n")
				else:
					datafile.write(str(j)+"	"+str(r_count[j])+"\n")
		# else:
		# 	with open("pcari/static/data/q%d.tsv" % q.qid, "w") as datafile:
		# 		datafile.write("score	count\n")
		# 		for j in range(len(r_count)):
		# 			if j == len(r_count)-1:
		# 				datafile.write("skip"+"	"+str(r_count[j])+"\n")
		# 			else:
		# 				datafile.write(str(j)+"	"+str(r_count[j])+"\n")

comment_update()
se_update()
generate()