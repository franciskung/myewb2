from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import login as auth_login
from django.core.urlresolvers import reverse
from django.http import HttpResponseNotFound, HttpResponsePermanentRedirect

import urllib, urllib2, json, phpserialize

class TIGSessionMiddleware(object):
    def process_request(self, request):
#        return None

        if request.user.is_authenticated():
            return None

        if not request.COOKIES.get('TIGUser', None):
            return None
            
        if not request.COOKIES.get('TIGUserInfo', None):
            return None

        #sessioninfo = phpserialize.loads(request.COOKIES['TIGUserInfo'])
        sessioninfo = phpserialize.loads(urllib.unquote(request.COOKIES['TIGUserInfo']))


        url = "https://www.tigweb.org/partners/ewb/api/login.php"

        values = {'email': sessioninfo['Email'],
                  'password': sessioninfo['SessionID'],
                  'key': settings.EWB_TIG_API_KEY}

        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)

        try:
            req2 = urllib2.urlopen(req)
            response = req2.read()

            auth = json.loads(response)
        except:
            auth = {}
            auth['success'] = False
	
        if auth['success']:
            userinfo = auth['userinfo']

            if sessioninfo['UserID'] != request.COOKIES['TIGUser']:
                return None
            if sessioninfo['UserID'] != userinfo['id']:
                return None

            try:        
                user = User.objects.get(tigid=userinfo['id'])
            except:
                user = None
            
            if not user and userinfo.get('ewbid', None):
                user = User.objects.get(id=userinfo['ewbid'])
                user.tigid = userinfo['id']
                user.save()

            if not user:
                user = User.extras.create_silent_user(userinfo['email'])
                user.tigid = userinfo['id']

                profile = user.get_profile()
                if not profile.first_name:
                    profile.first_name=userinfo['fname']
                if not profile.last_name:
                    profile.last_name=userinfo['lname']

                user.save()
                profile.save()
            
            user.backend = "django.contrib.auth.backends.ModelBackend"
            auth_login(request, user)
            
        return None
