from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseNotFound, HttpResponsePermanentRedirect
import urllib, urllib2, json

class TIGSessionMiddleware(object):
    def process_request(self, request):

        if request.user.is_authenticated():
            return None

        if not request.COOKIES.get('TIGUser', None):
            return None
            
        if not request.COOKIES.get('TIGUserInfo', None):
            return None

        userinfo = request.COOKIES['TIGUserInfo']
        print userinfo
        
        return None

        url = "https://www.tigweb.org/partners/ewb/api/login.php"

        values = {'email': request.POST.get('login_name', None),
                  'password': request.POST.get('password', None),
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
