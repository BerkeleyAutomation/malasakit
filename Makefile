# malasakit-v1/Makefile

DJANGO_PROJECT_ROOT=malasakit-django
LINT_CMD=pylint
LINT_OPTIONS=--output-format=colorized --rcfile=.pylintrc
LINT_TARGETS=pcari/models.py pcari/urls.py cafe/urls.py cafe/settings.py pcari/admin.py

all: lint test

test:
	cd $(DJANGO_PROJECT_ROOT) && python2 manage.py test

lint: $(LINT_TARGETS:%.py=$(DJANGO_PROJECT_ROOT)/%.py)
	$(LINT_CMD) $(LINT_OPTIONS) $^
