import environment

from pcari.models import QuantitativeQuestion, Rating

def generate():
	ratings = Rating.objects.all()

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


		with open("pcari/static/data/q%d.tsv" % q.qid, "w") as datafile:
			datafile.write("score	count\n")
			for j in range(len(r_count)):
				if j == len(r_count)-1:
					datafile.write("skip"+"	"+str(r_count[j])+"\n")
				else:
					datafile.write(str(j)+"	"+str(r_count[j])+"\n")

generate()