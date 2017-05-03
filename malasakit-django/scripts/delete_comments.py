# Include this line at the beginning of every script.
import environment

from pcari.models import Comment, User

u = User.objects.all().filter(username="14")[0]

for c in Comment.objects.all():
	if c.user == u:
		c.delete()