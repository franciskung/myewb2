# thanks http://code.google.com/p/django-httpbl-middleware/

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseNotFound, HttpResponsePermanentRedirect
import socket

from httpbl.models import Whitelist

class HttpBLMiddleware(object):
   """
   "HttpBL" Middleware by iamtgc@gmail.com 
   """
   def __init__(self, age=None, threat=None, classification=None):
      if age is None:
         self.age = getattr(settings, 'HTTPBLAGE', 14)
      else:
         self.age = age
      if threat is None:
         self.threat = getattr(settings, 'HTTPBLTHREAT', 30)
      else:
         self.threat = threat
      if classification is None:
         self.classification = getattr(settings, 'HTTPBLCLASS', 7)
      else:
         self.classification = classification

   def process_request(self, request):
      # skip check if already displaying the blacklist page
      if request.META.get('PATH_INFO', '') == reverse('httpbl_blacklist') or \
        request.META.get('PATH_INFO', '') == reverse('httpbl_validate'):
         return None

      if settings.HTTPBLKEY:
         ip = request.META.get('REMOTE_ADDR')
         
         if ip == '127.0.0.1':
           return None

         iplist = ip.split('.')
         iplist.reverse()

         domain = 'dnsbl.httpbl.org'

         query = settings.HTTPBLKEY + "." + ".".join(iplist) + "." + domain
            
         try:
            result = socket.gethostbyname(query)
         except socket.gaierror:
            return None

         resultlist = result.split('.')

         if (int(resultlist[1]) <= self.age and int(resultlist[2]) >= self.threat and int(resultlist[3]) & self.classification > 0):
           if Whitelist.objects.filter(ip=ip).count() == 0:
              return HttpResponsePermanentRedirect(reverse('httpbl_blacklist'))

      return None
