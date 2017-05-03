# Include this line at the beginning of every script.
import environment

from pcari.models import QuantitativeQuestion, QualitativeQuestion, User

english_question=[
"I have suffered the consequence of a typhoon or flood",
"I feel prepared to handle a major typhoon right now.",
"The barangay’s typhoon Early Warning System is effective.",
"My family has identified a place to meet and ways to communicate in a disaster.",
"How many days of disaster supplies (e.g., canned food, bottled water, medicine) are immediately available to you in your home?",
"I feel like I could count on my immediate neighbors for support when recovering from a major typhoon.",
"I believe our barangay will help my community repair and rebuild after a major typhoon.",
"How many weeks has it been since you participated in a disaster drill?"
]

filipino_question=[
"Malawak at mabigat ang epekto ng bagyo o pagbabaha sa akin",
"Nararamdaman kong handa akong harapin ang pagdating ng malakas na bagyo",
"Epektibo ang ginagamit na “Early Warning System” ng barangay tuwing may bagyo",
"Tuwing may sakuna, napagkasunduan ng aking pamilya na magkita sa isang lugar at may tinukoy kaming paraan ng komunikasyon",
"Kung may sakuna, hanggang ilang araw tatagal ang naitabing gamit at pagkain (halimbawa delata, inuming tubig, gamot) sa inyong tahanan?",
"Sa pakiramdam ko, maaasahan ko ang tulong ng aking mga karatig-bahay upang makabangon muli pagkatapos ng isang malakas na bagyo",
"Naniniwala akong tutulong ang aking barangay sa pag-aayos at pagtatayo ng aming komunidad pagkatapos ng isang malakas na bagyo",
"Ilang linggo na ang nakalipas mula nang sumali ka sa isang “disaster drill”?"
]

for i in range(len(english_question)):
	new_q = QuantitativeQuestion(question=english_question[i],filipino_question=filipino_question[i])
	new_q.save()


admin = User.objects.all()[0]
for q in QuantitativeQuestion.objects.all():
	for score in range(-1,10):
		r = Rating(user=admin,score=score,qid=q.id)