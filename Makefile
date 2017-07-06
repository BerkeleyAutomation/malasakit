# malasakit-v1/Makefile -- A collection of rules for testing and deploying the project

DJANGO_PROJECT_ROOT=malasakit-django

LINT_TARGETS=\
	cafe/settings.py\
	cafe/urls.py\
	cafe/wsgi.py\
	pcari/management/commands/__init__.py\
	pcari/management/commands/cleantext.py\
	pcari/management/commands/makedbtrans.py\
	pcari/management/commands/makemessages.py\
	pcari/templatetags/localize_url.py\
	pcari/admin.py\
	pcari/apps.py\
	pcari/signals.py\
	pcari/urls.py\
	pcari/views.py

CLEANTEXT_TARGETS=\
	Comment.message\
	Comment.tag\
	Respondent.location

install:
	pip2 install -r requirements.txt
	npm install --only=production

lint: $(LINT_TARGETS:%.py=$(DJANGO_PROJECT_ROOT)/%.py)
	pylint --output-format=colorized --rcfile=.pylintrc $^

test:
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py test

cleandb:
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py clearsessions
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py cleantext $(CLEANTEXT_TARGETS)

compilestatic: install
	cd $(DJANGO_PROJECT_ROOT)/pcari/static/css && lessc -x main.less main.min.css

disabledebug:
	sed -i -e 's/DEBUG\s*=\s*True/DEBUG = False/g' $(DJANGO_PROJECT_ROOT)/cafe/settings.py

collectstatic: compilestatic
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py collectstatic --no-input

deploy: disabledebug compilestatic
	$(eval STATIC_ROOT=$(shell cd $(DJANGO_PROJECT_ROOT) && ./manage.py shell -c 'from django.conf import settings; print settings.STATIC_ROOT'))
	cd $(STATIC_ROOT)/css && rm *.less
