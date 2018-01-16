DJANGO_PROJECT_ROOT=malasakit-django
DOCS_BUILD_PATH=docs-build
DOCS_PATH=docs

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
	pcari/views.py\
	feature_phone/admin.py\
	feature_phone/apps.py\
	feature_phone/models.py\
	feature_phone/urls.py\
	feature_phone/views.py

DB_TRANS_TARGETS=\
	QuantitativeQuestion.prompt\
	QuantitativeQuestion.left_anchor\
	QuantitativeQuestion.right_anchor\
	QualitativeQuestion.prompt

EXCLUDED_MODULES=\
	$(DJANGO_PROJECT_ROOT)/pcari/migrations\
	$(DJANGO_PROJECT_ROOT)/pcari/test*\
	$(DJANGO_PROJECT_ROOT)/pcari/urls.py

CLEANTEXT_TARGETS=\
	Comment.message\
	Comment.tag\
	Respondent.location

STATIC_ROOT_CMD=./manage.py shell -c 'from django.conf import settings; print(settings.STATIC_ROOT)'

CREATE_PROD_DB_QUERY=\
	CREATE DATABASE IF NOT EXISTS pcari CHARACTER SET utf8;\
	GRANT ALL PRIVILEGES ON pcari.* TO root@localhost;\
	FLUSH PRIVILEGES;

install:
	pip2 install -r requirements.txt
	npm install --only=production

all: deploy lint test

lint: $(LINT_TARGETS:%.py=$(DJANGO_PROJECT_ROOT)/%.py)
	pylint --output-format=colorized --rcfile=.pylintrc $^

test:
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py test --exclude-tag=slow

testclient:
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py test --tag=slow --failfast

preparedocs:
	mkdir -p $(DOCS_BUILD_PATH)
	sphinx-apidoc -f -e -o $(DOCS_BUILD_PATH)/source $(DJANGO_PROJECT_ROOT)/pcari $(EXCLUDED_MODULES)

compiledocs:
	rm -rf $(DOCS_PATH)
	cd $(DOCS_BUILD_PATH) && make clean && make html
	mv $(DOCS_BUILD_PATH)/build/html $(DOCS_PATH)

preparetrans:
	mkdir -p $(DJANGO_PROJECT_ROOT)/locale
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py makedbtrans -o locale/db.pot $(DB_TRANS_TARGETS)
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py makemessages -a -d django
	rm -f $(DJANGO_PROJECT_ROOT)/locale/db.pot
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py makemessages -a -d djangojs

compiletrans:
	cd $(DJANGO_PROJECT_ROOT) && django-admin compilemessages

createproddb:
	mysql -e '$(CREATE_PROD_DB_QUERY)' -u root --password="$(shell printenv mysql_pass)"
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py migrate --run-syncdb

deleteproddb:
	mysql -e 'DROP DATABASE pcari;' -u root --password="$(shell printenv mysql_pass)"

cleandb:
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py clearsessions
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py cleantext $(CLEANTEXT_TARGETS)

compilestatic: install
	cd $(DJANGO_PROJECT_ROOT)/pcari/static/css && export PATH=$$PATH:$(shell npm bin) && lessc -x main.less main.min.css

disabledebug:
	sed -i -e 's/DEBUG\s*=\s*True/DEBUG = False/g' $(DJANGO_PROJECT_ROOT)/cafe/settings.py

collectstatic: compilestatic
	cd $(DJANGO_PROJECT_ROOT) && ./manage.py collectstatic --no-input

deploy: disabledebug collectstatic compiletrans
	$(eval STATIC_ROOT=$(shell cd $(DJANGO_PROJECT_ROOT) && $(STATIC_ROOT_CMD)))
	cd $(STATIC_ROOT)/css && rm *.less
