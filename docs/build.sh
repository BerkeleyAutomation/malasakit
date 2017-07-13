#!/bin/bash

sphinx-apidoc -f -e -o source/ ../malasakit-django/pcari/ ../malasakit-django/pcari/migrations/ ../malasakit-django/pcari/test* ../malasakit-django/pcari/urls.py
make html
