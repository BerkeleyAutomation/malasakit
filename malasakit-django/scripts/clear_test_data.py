# Include this line at the beginning of every script.
import environment

from pcari.models import  QuantitativeQuestion, QualitativeQuestion, Rating, UserProgression, Comment, CommentRating, GeneralSetting, UserData
from django.contrib.auth.models import User

# 431
# 500


# count = 0
users = User.objects.all()

# user = User.objects.all().filter(username = "431")
# user.delete()

# user = User.objects.all().filter(username = "500")
# user.delete()

for u in users:
    try:
        userdata = UserData.objects.all().filter(user=u)[0]
        barangay = userdata.barangay
        if "XXX" in barangay or "Xxx" in barangay or "xxx" in barangay or "Test" in barangay or "TEST" in barangay:
            # count += 1
            u.delete()
    except IndexError:
        # print "HI"
        if "data" in u.username:
            pass
        else:
			# count += 1
            u.delete()

users = User.objects.all()

for u in users:
    try:
        comment = Comment.objects.all().filter(user=u)[0]
        if "XXX" in comment.comment or "XXX" in comment.filipino_comment:
            # count += 1
            u.delete()
        if comment.comment == "" and comment.filipino_comment == "":
            # count += 1
            u.delete()
    except IndexError:
        # count += 1
        u.delete()

# print count
