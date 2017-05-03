import environment

from pcari.models import QuantitativeQuestion, Rating
from django.contrib.auth.models import User

def init_bargraph():

	for i in range(-1,10):
		uid = User.objects.all().count()
		new_user = User.objects.create_user('data%d' % uid)
		for q in QuantitativeQuestion.objects.all():
			r = Rating(user=new_user,qid=q.qid,score=i)
			r.save()

			
init_bargraph()