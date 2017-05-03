import os,sys

proj_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.environ["DJANGO_SETTINGS_MODULE"] = "cafe.settings"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cafe.settings")
sys.path.append(proj_path)

os.chdir(proj_path)

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()