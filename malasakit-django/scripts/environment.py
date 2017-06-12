# Include this line at the beginning of every script.
import environment
import os
import sys
from django.core.wsgi import get_wsgi_application

proj_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["DJANGO_SETTINGS_MODULE"] = "cafe.settings"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cafe.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

application = get_wsgi_application()
