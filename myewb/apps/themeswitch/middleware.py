import os.path

from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from datetime import datetime


class ThemeSwitchMiddleware(object):
    def process_request(self, request):
        theme = request.session.get("theme", "myewb1")
        
        dirs = list(settings.TEMPLATE_DIRS)
        dirs.insert(0, os.path.join(settings.THEMESWITCH_BASE_DIR, theme))
        settings.TEMPLATE_DIRS = tuple(dirs)
        
        return None
