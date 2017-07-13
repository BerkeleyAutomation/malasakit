#!/bin/bash

sphinx-apidoc -f -e -o source/ ../malasakit-django/pcari/ ../malasakit-django/pcari/migrations/
make html
