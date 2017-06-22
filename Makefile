# malasakit-v1/Makefile

DJANGO_PROJECT_ROOT=malasakit-django
LINT_CMD=pylint
LINT_OPTIONS=--output-format=colorized --rcfile=.pylintrc
LINT_TARGETS=pcari/models.py pcari/urls.py cafe/urls.py cafe/settings.py pcari/admin.py
CLEANED_TEXT_TARGETS=Comment.message Respondent.location
DB_TRANS_TARGETS=QuantitativeQuestion.prompt QuantitativeQuestion.left_text QuantitativeQuestion.right_text QualitativeQuestion.prompt
LOCALES=tl

all: lint test

test:
	cd $(DJANGO_PROJECT_ROOT) && python2 manage.py test

lint: $(LINT_TARGETS:%.py=$(DJANGO_PROJECT_ROOT)/%.py)
	$(LINT_CMD) $(LINT_OPTIONS) $^

cleandb:
	cd $(DJANGO_PROJECT_ROOT) && python2 manage.py cleantext $(CLEANED_TEXT_TARGETS)

# Prepare translations
preparetrans:
	cd $(DJANGO_PROJECT_ROOT) && python2 manage.py makedbtrans -o locale/db.pot $(DB_TRANS_TARGETS)
	cd $(DJANGO_PROJECT_ROOT) && python2 manage.py makemessages --locale=$(LOCALES)
	rm $(DJANGO_PROJECT_ROOT)/locale/db.pot
