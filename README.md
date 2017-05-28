# malasakit-v1

[![Build Status](https://travis-ci.org/BerkeleyAutomation/malasakit-v1.svg?branch=master)](https://travis-ci.org/BerkeleyAutomation/malasakit-v1)

Malasakit is a customizable participatory assessment platform that collects and integrates quantitative assessment, qualitative feedback, and peer-to-peer collaborative filtering on ways local communities can become better prepared for typhoons and floods. 


## Setup (if using pip):
- python 2.7
  - comes by default on most systems, otherwise use 
  - check installed version with `python -V` on terminal
- pip: package manager for python
  - install with instructions from the [`pip` website](https://pip.pypa.io/en/stable/installing/)
- django, numpy, openpyxl
  - install with `sudo pip install requirements.txt`
- run migrations using 'python manage.py migrate'

## Setup (if using conda):
- If you don't have Anaconda installed, follow the instructions [in this tutorial on virtual environments.](http://justinmi.me/blog/2017/04/15/python-virtual-env) to set up `conda`
- create new virtual environment using `conda create --name pcari python=2 django=1.10.5 openpyxl=2.4.7 numpy=1.12.1`
- activate virtual environment using `source activate pcari`
- run migrations using 'python manage.py migrate'
- to deactivate virtual environment, enter `source deactivate`



## To run the system:
- run `python manage.py runserver`
- open up a webbrowser of your choice
- go to `localhost:8000/pcari`
- play around with the system


Permission is granted to copy and distribute this material, provided that the complete bibliographic citation and following credit line is included: "Copyright (C) 2016 UCB." Permission is granted to alter and distribute this material provided that the following credit line is included: "Adapted from (complete bibliographic 
citation). Copyright (C) 2016 UCB. This material may not be copied or distributed for commercial purposes without express written permission of the copyright holder.
