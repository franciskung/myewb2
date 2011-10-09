# myewb.wsgi is configured to live in projects/myewb/deploy.

import os
import sys

# redirect sys.stdout to sys.stderr for bad libraries like geopy that uses
# print statements for optional import exceptions.
sys.stdout = sys.stderr

from os.path import abspath, dirname, join
from site import addsitedir

sys.path.insert(0, "/home/myewb2/pinax/lib/python2.6/site-packages")
#sys.path.append(abspath(join(dirname(__file__), "../../pinax/lib/python2.6/site-packages")))
#sys.path.insert(0, abspath(join(dirname(__file__), "../../pinax/lib/python2.6/site-packages")))
#sys.path.insert(0, abspath(join(dirname(__file__), "../../pinax/lib/python2.6/site-packages/lxml-2.3-py2.6-linux-i686.egg")))
#sys.path.insert(0, abspath(join(dirname(__file__), "../../pinax/lib/python2.6/site-packages/PIL/PIL")))
#sys.path.insert(0, abspath(join(dirname(__file__), "../../pinax/lib/python2.6/site-packages/python_ldap-2.4.2-py2.6-linux-i686.egg")))
sys.path.insert(0, "/home/myewb2")
sys.path.insert(0, abspath(join(dirname(__file__), "../../")))
sys.path.insert(0, abspath(join(dirname(__file__), "../")))

from django.conf import settings
os.environ["DJANGO_SETTINGS_MODULE"] = "myewb.settings"

sys.path.insert(0, join(settings.PINAX_ROOT, "apps"))
sys.path.insert(0, join(settings.PROJECT_ROOT, "apps"))

from django.core.handlers.wsgi import WSGIHandler
application = WSGIHandler()
