from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

# IMPORTANT: Create only one instance
class GeneralSetting(models.Model):
    LANGUAGE_CHOICES = (
        ('English', 'English'),
        ('Filipino', 'Filipino'),
    )

    default_language = models.CharField(max_length=15, choices=LANGUAGE_CHOICES, default="English")

    english_landing_description = models.CharField(max_length=500, default="How prepared are you in times of disaster? %d barangay citizens have responded. Join them! It only takes a minute.")
    filipino_landing_description = models.CharField(max_length=500, default="Gaano ka kahanda sa panahon ng kalamidad? %d na ang nag MALASAKIT. Sali na! Isang minuto lamang ang kailangan.")

    english_question_description = models.CharField(max_length=500, default="Please select how strongly you agree with the following statement")
    filipino_question_description = models.CharField(max_length=500, default="Paki pili kung gaano kayo sumasang-ayon sa mga sumusunod na pangungusap")

    english_graph_description = models.CharField(max_length=500, default="The plots below show the average trend of the ratings.")
    filipino_graph_description = models.CharField(max_length=500, default="Ang talaguhitan sa ibaba ay nagpapakita ng madalas na sagot ng ibang tao.")

    english_peer_evaluation_description = models.CharField(max_length=500, default="How helpful is this suggestion? ")
    filipino_peer_evaluation_description = models.CharField(max_length=500, default="Gaano ka halaga ang mungkahing ito?")

    english_comment_description = models.CharField(max_length=500, default="How could your Barangay help you better prepare for a disaster?")
    filipino_comment_description = models.CharField(max_length=500, default="Sa papaanong pamamaraan makakatulong ang inyong barangay upang higit na maging handa ka para sa isang kalamidad")

    english_feedback_description = models.CharField(max_length=500, default="At the end you'll have a chance to give us more feedback")
    filipino_feedback_description = models.CharField(max_length=500, default="Sa dulo, mabibigyan ka ng pagkakataon na magbigay ng iyong mungkahing ideya")

    english_bloom_description = models.CharField(max_length=500, default="Each sphere below represents an idea proposed by another user. Click on the sphere to rate an idea.")
    filipino_bloom_description = models.CharField(max_length=500, default="Kumakatawan sa mungkahing ideya ng ibang tao ang bawat bilog sa ibaba. Pindutin ang isang bilog sa ibaba para magsimula.")

    english_begin_button = "Begin"
    english_skip_button = "Skip"
    english_next_button = "Next"
    english_post_button = "Post"
    english_submit_button = "Submit"

    filipino_begin_button = models.CharField(max_length=20, default="Simulan")
    filipino_skip_button = models.CharField(max_length=20, default="Laktawan")
    filipino_next_button = models.CharField(max_length=20, default="Susunod")
    filipino_post_button = models.CharField(max_length=20, default="Ipasa")
    filipino_submit_button = models.CharField(max_length=20, default="Isumite")

    english_question_of = "Question %d of %d"
    filipino_question_of = "Ika-%d ng %d katanungan"

    english_about_pcari = models.CharField(max_length=30, default="About PCARI")
    filipino_about_pcari = models.CharField(max_length=30, default="Tungkol sa PCARI")

    english_rate_more_ideas = models.CharField(max_length=50, default="Rate More Ideas")
    filipino_rate_more_ideas = models.CharField(max_length=50, default="Bigyan ng grado ang iba pang ideya")

    english_exit = models.CharField(max_length=30, default="Exit")
    filipino_exit = models.CharField(max_length=30, default="Lumabas")

    english_more_info = models.CharField(max_length=30, default="More Information")
    filipino_more_info = models.CharField(max_length=30, default="Iba pang impormasyon")

    english_suggest_own = models.CharField(max_length=50, default="Suggest Your Own Idea")
    filipino_suggest_own = models.CharField(max_length=50, default="Magmungkahi ng iyong sariling ideya")

    english_share_description = models.CharField(max_length=300, default="Thank you for participating. Please share Malasakit with your friends and family")
    filipino_share_description = models.CharField(max_length=300, default="Maraming salamat. Paki bahagi ang Malasakit sa inyong mga kaibigan at pamilya")

    english_learn_more = models.CharField(max_length=300, default="Learn more about how to be prepared for a disaster")
    filipino_learn_more = models.CharField(max_length=300, default="Alamin ang iba pang impormasyon kung paano magiging handa sa isang sakuna")

    english_short_description = models.CharField(max_length=300, default="A project by the CITRIS Connected Communities Initiative at UC Berkeley and the Philippine Commission on Higher Education through the Philippine-California Advanced Research Institutes Project.")
    filipino_short_description = models.CharField(max_length=300, default="Isang proyekto ng CITRIS Connected Communities Initiative ng UC Berkeley, at ng Commission on Higher Education ng Pilipinas sa pamamagitan ng Philippine-California Advanced Research Institutes Project")

    english_scale_description = models.CharField(max_length=300, default="0 (strongly disagree) to 9 (strongly agree)")
    filipino_scale_description = models.CharField(max_length=300, default="Mula 0 (hinding-hindi ako sumasang-ayon) hanggang 9 (lubos akong sumasang-ayon)")

    english_age = models.CharField(max_length=30, default="Age")
    filipino_age = models.CharField(max_length=30, default="Edad")

    english_gender = models.CharField(max_length=30, default="Gender")
    filipino_gender = models.CharField(max_length=30, default="Kasarian")

    english_select = models.CharField(max_length=30, default="Select")
    filipino_select = models.CharField(max_length=30, default="Pili ng kasarian")

    english_male = models.CharField(max_length=30, default="Male")
    filipino_male = models.CharField(max_length=30, default="Lalaki")

    english_female = models.CharField(max_length=30, default="Female")
    filipino_female = models.CharField(max_length=30, default="Babae")

    english_error = models.CharField(max_length=300, default="Please enter the following fields")
    filipino_error = models.CharField(max_length=300, default="Paki sagutan ang mga sumusunod para maikumpara ang iyong sagot sa iba")

    english_personal = models.CharField(max_length=300, default="Please enter the following to see how you compare with others")
    filipino_personal = models.CharField(max_length=300, default="Paki sagutan ang mga sumusunod para maikumpara ang iyong sagot sa iba")


    def get_text(self, language=None):
        if language is None:
            language = "Filipino"

        translate = {"English":"Filipino", "Filipino":"English"}[language]

        if language == "English":
            return {
                'translate' : translate,
                'landing_description' : self.english_landing_description,
                'question_description' : self.english_question_description,
                'graph_description' : self.english_graph_description,
                'peer_evaluation_description' : self.english_peer_evaluation_description,
                'comment_description' : self.english_comment_description,
                'feedback_description' : self.english_feedback_description,
                'bloom_description' : self.english_bloom_description,
                'begin_button' : self.english_begin_button,
                'skip_button' : self.english_skip_button,
                'next_button' : self.english_next_button,
                'post_button' : self.english_post_button,
                'submit_button' : self.english_submit_button,
                'about': self.english_about_pcari,
                'more_info': self.english_more_info,
                'short_description': self.english_short_description,
                'scale_description': self.english_scale_description,
                'suggest_own': self.english_suggest_own,
                'exit': self.english_exit,
                'rate_more': self.english_rate_more_ideas,
                'share_description': self.english_share_description,
                'learn_more': self.english_learn_more,
                "age": self.english_age,
                "gender": self.english_gender,
                "select": self.english_select,
                "male": self.english_male,
                "female": self.english_female,
                "error": self.english_error,
                "personal": self.english_personal,
                'question_of' : self.english_question_of
            }

        return {
            'translate':translate,
            'landing_description' : self.filipino_landing_description,
            'question_description' : self.filipino_question_description,
            'graph_description' : self.filipino_graph_description,
            'peer_evaluation_description' : self.filipino_peer_evaluation_description,
            'comment_description' : self.filipino_comment_description,
            'feedback_description' : self.filipino_feedback_description,
            'bloom_description' : self.filipino_bloom_description,
            'begin_button' : self.filipino_begin_button,
            'skip_button' : self.filipino_skip_button,
            'next_button' : self.filipino_next_button,
            'post_button' : self.filipino_post_button,
            'submit_button' : self.filipino_submit_button,
            'about': self.filipino_about_pcari,
            'more_info': self.filipino_more_info,
            'short_description': self.filipino_short_description,
            'scale_description': self.filipino_scale_description,
            'suggest_own': self.filipino_suggest_own,
            'exit': self.filipino_exit,
            'rate_more': self.filipino_rate_more_ideas,
            'share_description': self.filipino_share_description,
            'learn_more': self.filipino_learn_more,
            "age": self.filipino_age,
            "gender": self.filipino_gender,
            "select": self.filipino_select,
            "male": self.filipino_male,
            "female": self.filipino_female,
            "error": self.filipino_error,
            "personal": self.filipino_personal,
            'question_of' : self.filipino_question_of
        }

class QuantitativeQuestion(models.Model):
    qid = models.AutoField(primary_key=True)
    question = models.CharField(max_length=500, default="")
    average_score = models.FloatField(default=0)
    number_rated = models.IntegerField(default=0)
    tag = models.CharField(max_length=50, default="")
    filipino_tag = models.CharField(max_length=50, default="")
    filipino_question = models.CharField(max_length=500, default="walang filipino pagsasalin")
    def get_question(self, language=None):
        # print "what comes into get Q " + language 
        if language == "English":
            q = self.question
        else:
            # print "in model filipno"
            q = self.filipino_question
        return {'qid':self.qid, 'question':q}

class QualitativeQuestion(models.Model):
    qid = models.AutoField(primary_key=True)
    question = models.CharField(max_length=500, default="")
    filipino_question = models.CharField(max_length=500, default="walang filipino pagsasalin")

class UserData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,)
    age = models.IntegerField(default=0, null=True, blank=True)
    barangay = models.CharField(max_length=500, default="", null=True, blank=True)
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    LANGUAGE_CHOICES = (
    ('English', 'English'),
    ('Filipino', 'Filipino'),
    )
    language = models.CharField(max_length=15, choices=LANGUAGE_CHOICES, default="Filipino")

# If a user does not rate a question, the score will be -2.
# If they choose to skip a question, the score will be -1.
# For qualitative questions, the score will remain -2.
class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    qid = models.IntegerField(default=-1)
    date = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=-2)
    response = models.CharField(max_length=1000, default="")
    accounted = models.BooleanField(default=False)

    class Meta:
        unique_together = (('user', 'qid'),)

class Comment(models.Model):
    LANGUAGE_CHOICES = (
        ('English', 'English'),
        ('Filipino', 'Filipino'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    comment = models.CharField(max_length=1000, default="", null=True, blank=True)
    filipino_comment = models.CharField(max_length=1000, default="", null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    average_score = models.FloatField(default=0)
    number_rated = models.IntegerField(default=0)
    tag = models.CharField(max_length=200, default="", null=True)
    original_language = models.CharField(max_length=15, choices=LANGUAGE_CHOICES, null=True, blank=True)
    se = models.FloatField(default=0, null=True, blank=True)

class CommentRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    cid = models.IntegerField(default=-1)
    score = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True)
    accounted = models.BooleanField(default=False)

class UserProgression(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,)
    date = models.DateTimeField(auto_now_add=True)
    landing = models.BooleanField(default=False)
    rating = models.BooleanField(default=False)
    num_rated = models.IntegerField(default=0)
    review = models.BooleanField(default=False)
    bloom = models.BooleanField(default=False)
    peer_rating = models.BooleanField(default=False)
    num_peer_rated = models.IntegerField(default=0)
    personal_data = models.NullBooleanField(default=False, null=True)
    comment = models.BooleanField(default=False)
    logout = models.BooleanField(default=False)
    completion_rate = models.IntegerField(default=0)

class Progression(models.Model):
    landing = models.FloatField(default=0)
    rating = models.FloatField(default=0)
    review = models.FloatField(default=0)
    bloom = models.FloatField(default=0)
    peer_rating = models.FloatField(default=0)
    comment = models.FloatField(default=0)
    logout = models.FloatField(default=0)

class FlaggedComment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    comment = models.CharField(max_length=1000, default="", null=True)
    filipino_comment = models.CharField(max_length=1000, default="", null=True)
    date = models.DateTimeField(auto_now_add=False)
    average_score = models.FloatField(default=0)
    number_rated = models.IntegerField(default=0)
    tag = models.CharField(max_length=200, default="", null=True)
