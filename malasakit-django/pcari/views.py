import random

from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.template import loader
from pcari.models import *
from django.views import generic
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

from django.utils.datastructures import MultiValueDictKeyError

# !IMPORTANT! YOU MUST COMMENT OUT THE FOLLOWING GLOBAL VARIABLES
# IF YOU MAKE CHANGES TO models.py
# QUAN_QUESTIONS = list(QuantitativeQuestion.objects.all())
# QUAL_QUESTIONS = list(QualitativeQuestion.objects.all())
# QUAN_COUNT = QuantitativeQuestion.objects.all().count()
# QUAL_COUNT = QualitativeQuestion.objects.all().count()

# Q_COUNT = QUAN_COUNT

# random.shuffle(QUAN_QUESTIONS)
# random.shuffle(QUAL_QUESTIONS)

#TEXT = GeneralSetting.objects.all()[0].get_text()

def translate(language):
    return {"English":"Filipino", "Filipino":"English"}[language]


def switch_language(request):
    url = request.META.get('HTTP_REFERER').split("/")

    user = request.user
    TEXT = request.session['TEXT']
    if user.is_authenticated():
        user_data = UserData.objects.all().filter(user=user)[0]
        user_data.language = translate(user_data.language)
        user_data.save()
        request.session['language'] = user_data.language
        request.session['TEXT'] = GeneralSetting.objects.all()[0].get_text(translate(user_data.language))
    else:
        request.session['TEXT'] = GeneralSetting.objects.all()[0].get_text(TEXT['translate'])
        request.session['language'] = TEXT['translate']

    if "questions" in url:
        return HttpResponseRedirect(reverse('pcari:create_user', args=(0,)))
    elif "comparison" in url:
        return HttpResponseRedirect(reverse('pcari:rate', args=(url[-2],)))
    elif "personal" in url:
        return HttpResponseRedirect(reverse('pcari:personal', args=(url[-2],)))
    elif "review" in url:
        return HttpResponseRedirect(reverse('pcari:review'))
    elif "rate" in url:
        return HttpResponseRedirect(reverse('pcari:get_comment', args=(url[-2],)))
    elif "peerevaluation" in url or "bloom" in url:
        return HttpResponseRedirect(reverse('pcari:bloom'))
    elif "comment" in url:
        return HttpResponseRedirect(reverse('pcari:comment'))
    elif "help" in url:
        return HttpResponseRedirect(reverse('pcari:help'))
    elif "about" in url:
        return HttpResponseRedirect(reverse('pcari:about'))
    elif "logout" in url:
        return HttpResponseRedirect(reverse('pcari:logout'))
    return HttpResponseRedirect(reverse('pcari:landing'))

    # return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

def init_text_cookie(request):
    if 'TEXT' not in request.session:
        request.session['language'] = 'Filipino'
        general_settings = GeneralSetting.objects.first()
        request.session['TEXT'] = general_settings.get_text(request.session['language'])


def landing(request):
    user = request.user
    if user.is_authenticated():
        logout(request)

    init_text_cookie(request)
    TEXT = request.session['TEXT']

    description = TEXT['landing_description'] % len(User.objects.all())
    context = {
        'translate': TEXT['translate'],
        'landing_description': description,
        'more_info': TEXT['more_info'],
        'short_description': TEXT['short_description'],
        'begin': TEXT['begin_button']
    }
    return render(request, 'landing.html', context)


def create_user(request, is_new=True):
    init_text_cookie(request)

    if is_new:
        uid = int(User.objects.last().username) + 1
        username, email, password = str(uid), str(uid) + '@example.com', str(uid)

        # TODO: come up with a better scheme for handling errors (e.g. redirect)
        message = 'Username `{0}` already exists'.format(username)
        assert not User.objects.filter(username__iexact=username).exists(), message

        new_user = User.objects.create_user(username, email, password)
        new_user.save()

        user = authenticate(username=username, password=password)
        login(request, user)

        progression = UserProgression(user=user, landing=True)
        progression.save()

        TEXT = request.session['TEXT']
        user_data = UserData(user=user, language=translate(TEXT['translate']))
        user_data.save()

    return redirect(reverse('pcari:questions'))


def questions(request):
    init_text_cookie(request)
    user = request.user
    if not user.is_authenticated():
        return redirect(reverse('pcari:create_user'))

    return render(request, 'questions.html')


def get_question_ids(request):
    question_data = QuantitativeQuestion.objects.values('id')
    return JsonResponse({'qids': [question['id'] for question in question_data]})


def get_question(request, qid):
    try:
        question = QuantitativeQuestion.objects.get(id=qid)
        response = {'qid': question.id, 'question': question.prompt}
    except QuantitativeQuestion.DoesNotExist:
        raise Http404("No such question exists.")
    return JsonResponse(response)



def save_answer(request):
    init_text_cookie(request)
    user = request.user
    if not user.is_authenticated():
        pass  # TODO: send back an error

    try:
        qid, choice = request.POST['qid'], request.POST['choice']
        rating = Rating(user=user, qid=qid)
        rating.save()
    except IntegrityError:
        rating = Rating.objects.get(user=user, qid=qid)
    except KeyError:
        return HttpResponseBadRequest()

    rating.score = int(choice)
    rating.save()

    # TODO: remove this debug code
    question = QuantitativeQuestion.objects.get(qid=qid).get_question(request.session['language'])
    print(u'User {0} assigned the rating {1} to the statement "{2}"'.format(user.username, rating.score, question['question']))

    progression = UserProgression.objects.get(user=user)
    progression.rating = True
    progression.num_rated = Rating.objects.filter(user=user).count()
    progression.save()

    return HttpResponse()

    if 'TEXT' not in request.session:
        request.session['TEXT'] = GeneralSetting.objects.all()[0].get_text('Filipino')
        request.session['language'] = 'Filipino'

def init_question_cookie(request, language):
    l = []
    Q = QuantitativeQuestion.objects.all()
    for q in Q:
        l.append(q.get_question(language))
    request.session['QUESTION'] = l
    request.session['Q_COUNT'] = Q.count()

def landing(request):
    user = request.user
    if user.is_authenticated():
        logout(request)

    init_text_cookie(request)
    TEXT = request.session['TEXT']

    description = TEXT['landing_description'] % len(User.objects.all())
    context = {
        'translate':TEXT['translate'],
        'landing_description':description,
        'more_info':TEXT['more_info'],
        'short_description':TEXT['short_description'],
        'begin':TEXT['begin_button']
    }
    return render(request, 'landing.html', context)

def create_user(request, is_new=1):
    init_text_cookie(request)
    #User Authentication


    if is_new == 1:
        uid = int(list(User.objects.all())[-1].username) + 1
        new_user = User.objects.create_user('%d' % uid, '%d@example.com' % uid, '%d' % uid)
        new_user.save()

        user = authenticate(username=new_user.username, password=new_user.username)

        login(request, user)

        #Data Initialization
        progression = UserProgression(user=user)
        progression.landing = True
        progression.save()

        init_text_cookie(request)
        TEXT = request.session['TEXT']
        user_data = UserData(user=user, language=translate(TEXT['translate']))
        user_data.save()
    else:
        user = request.user
        user_data = UserData.objects.all().filter(user=user)[0]

    # data = {
 #        'is_taken': User.objects.filter(username__iexact=username).exists()
 #    }
    # print JsonResponse(context
    user_data = UserData.objects.all().filter(user=request.user)[0]
    request.session['TEXT'] = GeneralSetting.objects.all()[0].get_text(user_data.language)
    TEXT = GeneralSetting.objects.all()[0].get_text(user_data.language)

    init_question_cookie(request, user_data.language)
    QUAN_QUESTIONS = request.session['QUESTION']
    Q_COUNT = request.session['Q_COUNT']

    q = QUAN_QUESTIONS[0]

    question_of = TEXT['question_of'] % (QUAN_QUESTIONS.index(q)+1, Q_COUNT)

    if q["qid"] == 5:
        scale_description = "0 (less than one day) to 9 (or more)" if TEXT['translate'] == "Filipino" else "Mula 0 (mas mababa sa isang araw) hanggang 9 (o mas mataas pa)"
    elif q["qid"] == 8:
        scale_description = "0 (less than one week) to 9 (or more)" if TEXT['translate'] == "Filipino" else "Mula 0 (mas mababa sa isang linggo) hanggang 9 (o mas mataas pa)"
    else:
        scale_description = TEXT['scale_description']

    context = {
        'translate':TEXT['translate'],
        'question_description':TEXT['question_description'],
        'feedback_description':TEXT['feedback_description'],
        'skip':TEXT['skip_button'],
        'question_of':question_of,
        'question': q["question"],# if TEXT['translate'] == "Filipino" else q.filipino_question,
        'scale_description':TEXT['scale_description'],
        'qid': q["qid"],
        'rating':True
    }

    return render(request, 'rating.html', context)


def rate(request, qid):
    init_text_cookie(request)
    user = request.user
    if not user.is_authenticated():
        return landing(request)

    user_data = UserData.objects.all().filter(user=user)[0]

    # print request.POST

    init_question_cookie(request, user_data.language)

    try:
        rating = Rating(user=user, qid=qid)
        rating.save()
    except:
        rating = Rating.objects.all().filter(user=user, qid=qid)[0]
        # print "correct"


    try:
        rating.score = request.POST['choice']
        rating.save()
    except:
        pass

    # print rating.score

    if rating.score == "Skip" or rating.score == "Laktawan":
        rating.score = -1
        rating.save()

    # if rating.score == "Submit" or rating.score == "Ipasa":
    #     rating.response = request.POST['comment']

    r = Rating.objects.all().filter(user=user)
    rating_list = map(lambda x: x.qid, r)

    progression = UserProgression.objects.all().filter(user=user)[0]
    progression.rating = True
    progression.num_rated = len(rating_list)
    progression.save()

    # try:
    # 	q = QUAN_QUESTIONS[QUAN_QUESTIONS.index([x for x in QUAN_QUESTIONS if x.qid == int(qid)][0])+1]
    # except:
    # 	return personal(request)

    # if progression.num_rated < Q_COUNT:

    QUAN_QUESTIONS = request.session['QUESTION']
    Q_COUNT = request.session['Q_COUNT']
    user = request.user
    try:
        q = QUAN_QUESTIONS[QUAN_QUESTIONS.index([x for x in QUAN_QUESTIONS if x["qid"] == int(qid)][0])+1]
    except:
        return personal(request)
    # if progression.num_rated < QUAN_COUNT:
    # 	q = QUAN_QUESTIONS[progression.num_rated]
    # 	qualitative = False
    # else:
    # 	q = QUAL_QUESTIONS[progression.num_rated-QUAN_COUNT]
    # 	qualitative = True
    if user.is_authenticated():
        user_data = UserData.objects.all().filter(user=user)[0]
        TEXT = GeneralSetting.objects.all()[0].get_text(user_data.language)
    else:
        TEXT = GeneralSetting.objects.all()[0].get_text(request.session['language'])

    question_of = TEXT['question_of'] % (QUAN_QUESTIONS.index(q)+1, Q_COUNT)




    if q["qid"] == 5:
        scale_description = "0 (less than one day) to 9 (or more)" if TEXT['translate'] == "Filipino" else "Mula 0 (mas mababa sa isang araw) hanggang 9 (o mas mataas pa)"
    elif q["qid"] == 8:
        scale_description = "0 (less than one week) to 9 (or more)" if TEXT['translate'] == "Filipino" else "Mula 0 (mas mababa sa isang linggo) hanggang 9 (o mas mataas pa)"
    else:
        scale_description = TEXT['scale_description']

    context = {
        'translate':TEXT['translate'],
        'question_description':TEXT['question_description'],
        'feedback_description':TEXT['feedback_description'],
        'skip':TEXT['skip_button'],
        'question_of':question_of,
        'question': q["question"],
        'scale_description':scale_description,
        'qid': q["qid"],
        'rating':True
    }

    return render(request, 'rating.html', context)


def personal(request):
    init_text_cookie(request)

    user = request.user
    if not user.is_authenticated():
        return landing(request)
    progression = UserProgression.objects.all().filter(user=user)[0]
    progression.personal_data = True
    progression.save()
    user_data = UserData.objects.all().filter(user=user)[0]
    TEXT = GeneralSetting.objects.all()[0].get_text(user_data.language)
    context = {
        'about':TEXT['about'],
        'rate_more':TEXT['rate_more'],
        'suggest_own':TEXT['suggest_own'],
        'next':TEXT['next_button'],
        'age':TEXT['age'],
        'gender':TEXT['gender'],
        'male':TEXT['male'],
        'female':TEXT['female'],
        'select':TEXT['select'],
        'personal':TEXT['personal'],
        'translate':TEXT['translate']
    }
    return render(request, 'personal_data.html', context)

    # return personal(request)

def review(request):
    init_text_cookie(request)

    user = request.user
    if not user.is_authenticated():
        return landing(request)

    # print request.GET

    try:
        age = request.POST['age']
        if age == "":
            age = -1
        age = int(age)
        barangay = request.POST['barangay']
        gender = request.POST['gender']
        if UserData.objects.all().filter(user=user).count() > 0:
            userdata = UserData.objects.all().filter(user=user)[0]
            userdata.age = age
            userdata.barangay = barangay
            userdata.gender = gender
            userdata.save()
        else:
            userdata = UserData(user=user, age=age, barangay=barangay, gender=gender)
            userdata.save()
    except MultiValueDictKeyError:
        pass


    progression = UserProgression.objects.all().filter(user=user)[0]
    progression.review = True
    progression.save()


    user_data = UserData.objects.all().filter(user=user)[0]
    TEXT = GeneralSetting.objects.all()[0].get_text(user_data.language)

    user = request.user

    q = QuantitativeQuestion.objects.all()
    r = Rating.objects.all().filter(user=user)
    user_ratings = map(lambda x: (x.qid, x.score), r)
    rating_list = map(lambda x: x.qid, r)
    user_ratings.sort(key=lambda x: x[0])
    # print user_ratings

    if TEXT['translate'] == "Filipino":
        tag = map(lambda x: (x.tag, x.qid, user_ratings[x.qid-1][1]) if x.qid in rating_list else (x.tag, x.qid,-2), q)
    else:
        tag = map(lambda x: (x.filipino_tag, x.qid,user_ratings[x.qid-1][1]) if x.qid in rating_list else (x.filipino_tag, x.qid,-2), q)

	# print tag

    context = {
        'translate':TEXT['translate'],
        'language':True if TEXT['translate'] == "English" else False,
        'graph_description':TEXT['graph_description'],
        'next':TEXT['next_button'],
        'more_info':TEXT['more_info'],
        'tags':tag,
        'n':q.count()
    }

    return render(request, 'review.html', context)

def help(request):
    init_text_cookie(request)
    TEXT = request.session['TEXT']

    started = request.user.is_authenticated()
    if started:
        up = UserProgression.objects.filter(user=request.user)[0]
        started = up.bloom

    context = {
        'logged_in': started,
        'about':TEXT['about'],
        'rate_more':TEXT['rate_more'],
        'suggest_own':TEXT['suggest_own'],
        'exit':TEXT['exit'],
        'translate':TEXT['translate']
    }
    return render(request, 'help.html', context)

def bloom(request, done = False):
    init_text_cookie(request)

    user = request.user
    if not user.is_authenticated():
        return landing(request)
	# try:
    progression = UserProgression.objects.all().filter(user=user)[0]
    progression.bloom = True
    progression.save()
    # except:
    # 	return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    if progression.num_peer_rated >= 2:
        done = True

    # comments = map(lambda x: x.id, Comment.objects.all())
    comments = list(Comment.objects.all())
    comments_reverse = list(Comment.objects.all())
    random.seed(random.randint(1, 500))
    # random.shuffle(comments)
    comments.sort(key=lambda c: c.se, reverse=True)
    comments_reverse.sort(key=lambda c: c.se)
    if done:
        data = [{"cid":0, "x_seed":0, "y_seed":0, "shift":0, "n":0}]
    else:
        data = []

	# List of Data
    already_seen = map(lambda x: x.cid, CommentRating.objects.all().filter(user=user))
    n = 1
    for c in comments:
        r = random.random()
        if c.se < r:
            continue
        if n > 4:
            break
        if c.id in already_seen:
            continue
        if c.comment == "" and c.filipino_comment == "":
            continue
        # if c.number_rated>30:
        # 	continue
        data.append({"cid":c.id, "x_seed":random.random(), "y_seed":random.random(), "shift":random.random() * (1 + 1) - 1, "n":n })
        # print c.se
        n += 1

    for c in comments_reverse:
        if n > 8:
            break
        if c.id in already_seen:
            continue
        if c.comment == "" and c.filipino_comment == "":
            continue
        # if c.number_rated>30:
        # 	continue
        data.append({"cid":c.id, "x_seed":random.random(), "y_seed":random.random(), "shift":random.random() * (1 + 1) - 1, "n":n })
        # print c.se
        n += 1

    # print data
    user_data = UserData.objects.all().filter(user=user)[0]
    TEXT = GeneralSetting.objects.all()[0].get_text(user_data.language)
    context = {
        'translate':TEXT['translate'],
        'bloom_description':TEXT['bloom_description'],
        'language':True if TEXT['translate'] == "English" else False,
        'comment_data':data,
        'done':done
    }
    return render(request, 'bloom.html', context)

def comment(request):
    init_text_cookie(request)

    user = request.user
    if not user.is_authenticated():
        return landing(request)
    try:
        progression = UserProgression.objects.all().filter(user=user)[0]
        progression.comment = True
        progression.save()
    except:
        return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

    user_data = UserData.objects.all().filter(user=user)[0]
    TEXT = GeneralSetting.objects.all()[0].get_text(user_data.language)
    context = {
        'translate':TEXT['translate'],
        'comment_description':TEXT['comment_description'],
        'post':TEXT['post_button']
	}
    return render(request, 'comment.html', context)

def logout_view(request):
    init_text_cookie(request)

    user = request.user
    if not user.is_authenticated():
        return landing(request)
    try:
        progression = UserProgression.objects.all().filter(user=user)[0]
        progression.logout = True
        progression.save()
        user_data = UserData.objects.all().filter(user=user)[0]
        request.session['TEXT'] = GeneralSetting.objects.all()[0].get_text(user_data.language)
    except:
        pass

    TEXT = request.session['TEXT']


    try:
        c = Comment(user=user)

        if TEXT['translate'] == "Filipino":
            c.original_language = "English"
            c.comment = request.POST['comment']
        else:
            c.original_language = "Filipino"
            c.filipino_comment = request.POST['comment']
        c.save()
    except:
        pass


    context = {
        'translate':TEXT['translate'],
        'share_description':TEXT['share_description'],
        'learn_more':TEXT['learn_more'],
        'exit':TEXT['exit']
    }
    # reset()
    return render(request, 'logout.html', context)

def get_comment(request, cid):
    init_text_cookie(request)

    user = request.user
    if not user.is_authenticated():
        return landing(request)
    cid = cid
    c = Comment.objects.all().filter(id=cid)[0]
    user_data = UserData.objects.all().filter(user=user)[0]
    TEXT = GeneralSetting.objects.all()[0].get_text(user_data.language)
    comment = c.comment if TEXT['translate'] == "Filipino" else c.filipino_comment
    if comment == "":
        comment = c.comment if TEXT['translate'] == "English" else c.filipino_comment
    context = {
        'translate':TEXT['translate'],
        'peer_evaluation_description':TEXT['peer_evaluation_description'],
        'skip':TEXT['skip_button'],
        'scale_description':TEXT['scale_description'],
        'cid':cid,
        'comment': comment
    }
    return render(request, 'rating.html', context)

def rate_comment(request, cid):
    init_text_cookie(request)

    user = request.user
    if not user.is_authenticated():
        return landing(request)
    progression = UserProgression.objects.all().filter(user=user)[0]
    progression.peer_rating = True
    progression.num_peer_rated += 1
    progression.save()
    cid = cid

    rating = CommentRating(user=user)
    rating.cid = cid
    try:
        score = request.POST['choice']
    except:
        score = -2

    if score == "Skip" or score == "Laktawan":
        score = -1

    rating.score = score

    rating.save()

    if progression.num_peer_rated >= 2:
        return bloom(request, done=True)

    return bloom(request)

def about(request):
    init_text_cookie(request)

    return render(request, 'about.html', {})

def update_ratings(user):
    init_text_cookie(request)

    questions = QuantitativeQuestion.objects.all()
    ratings = Rating.objects.all().filter(user=user)
    for r in ratings:
        q = questions[r.qid-1]
        if r.score == -1 or r.score == -2:
            continue
        ave = (q.average_score * q.number_rated + r.score + 0.0) / (q.number_rated + 1.0)
        q.average_score = ave
        q.number_rated += 1
        q.save()

    # for q in questions:

def generate(request):
    init_text_cookie(request)

    ratings = Rating.objects.all()

    url = request.META.get('HTTP_REFERER').split("/")

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

        if "pcari" in url:
            with open("/var/www/opinion/opinion.berkeley.edu/pcari/pcari/static/data/q%d.tsv" % q.qid, "w") as datafile:
                datafile.write("score	count\n")
                for j in range(len(r_count)):
                    if j == len(r_count)-1:
                        datafile.write("skip"+"	"+str(r_count[j])+"\n")
                    else:
                        datafile.write(str(j)+"	"+str(r_count[j])+"\n")
        else:
            with open("pcari/static/data/q%d.tsv" % q.qid, "w") as datafile:
                datafile.write("score	count\n")
                for j in range(len(r_count)):
                    if j == len(r_count)-1:
                        datafile.write("skip"+"	"+str(r_count[j])+"\n")
                    else:
                        datafile.write(str(j)+"	"+str(r_count[j])+"\n")

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

def clean_empty():
    users = User.objects.all()

    for u in users:
        ratings = Rating.objects.all().filter(user=u)
        if len(ratings) == 0:
            u.delete()
    comments = Comment.objects.all()

    for c in comments:
        if c == "":
            c.delete()
