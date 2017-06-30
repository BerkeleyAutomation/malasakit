# malasakit-v1/Makefile -- A collection of rules for testing and deploying the project

DJANGO_PROJECT_ROOT=malasakit-django

LINT_CMD=pylint
LINT_OPTIONS=--output-format=colorized --rcfile=.pylintrc
# List of Python source files to inspect for PEP8 compliance
LINT_TARGETS=cafe/settings.py cafe/urls.py cafe/wsgi.py pcari/management/commands/__init__.py pcari/management/commands/cleantext.py pcari/management/commands/makedbtrans.py pcari/management/commands/makemessages.py pcari/templatetags/localize_url.py pcari/admin.py pcari/apps.py pcari/signals.py pcari/urls.py pcari/views.py

CLEANTEXT_TARGETS=Comment.message Respondent.location
DB_TRANS_TARGETS=QuantitativeQuestion.prompt QuantitativeQuestion.left_text QuantitativeQuestion.right_text QualitativeQuestion.prompt
LOCALES=tl

all: preparetrans compiletrans lint test

test:
	cd $(DJANGO_PROJECT_ROOT) && python2 manage.py test

lint: $(LINT_TARGETS:%.py=$(DJANGO_PROJECT_ROOT)/%.py)
	$(LINT_CMD) $(LINT_OPTIONS) $^

# Clean database
cleandb:
	cd $(DJANGO_PROJECT_ROOT) && python2 manage.py cleantext $(CLEANTEXT_TARGETS)

# Prepare translations
preparetrans:
	cd $(DJANGO_PROJECT_ROOT) && python2 manage.py makedbtrans -o locale/db.pot $(DB_TRANS_TARGETS)
	cd $(DJANGO_PROJECT_ROOT) && python2 manage.py makemessages --locale=$(LOCALES)
	rm $(DJANGO_PROJECT_ROOT)/locale/db.pot

# Compile translations
compiletrans:
	cd $(DJANGO_PROJECT_ROOT) && python2 manage.py compilemessages
