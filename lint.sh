#!/bin/sh

cd malasakit-django
pylint --load-plugins pylint_django --docstring-min-length=5 pcari/models.py
