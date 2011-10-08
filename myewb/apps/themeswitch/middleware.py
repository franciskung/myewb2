import os.path

from django.conf import settings
from django.contrib.sessions.models import Session
from django.contrib.auth.models import User
from datetime import datetime

from themeswitch.models import RequestLog

class ThemeSwitchMiddleware(object):
    def process_request(self, request):
        theme = request.session.get("theme", settings.THEMESWITCH_DEFAULT_THEME)
        
        if not hasattr(settings, 'TEMPLATE_DIRS_ORIGINAL'):
            settings.TEMPLATE_DIRS_ORIGINAL = settings.TEMPLATE_DIRS
        
        dirs = list(settings.TEMPLATE_DIRS_ORIGINAL)
        print "inserting", theme
        dirs.insert(0, os.path.join(settings.THEMESWITCH_BASE_DIR, theme))
        settings.TEMPLATE_DIRS = tuple(dirs)
        
        request.theme = theme
        
        return None

class ThemeSwitchTrackingMiddleware(object):
    def process_request(self, request):
        theme = request.session.get("theme", "myewb2b")
        
        if request.user.is_authenticated():
            user = request.user
        else:
            user = None
        
        log = RequestLog.objects.create(user=user,
                                        page=request.path,
                                        theme=theme)
        
        return None
