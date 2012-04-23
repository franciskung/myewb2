from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext, Context, loader

from httpbl.models import Whitelist

def blacklist(request):
    return render_to_response("httpbl/blacklist.html",
                              {},
                              context_instance=RequestContext(request))

def validate(request):
    print "got ", request.POST.get('text', '')
    if request.POST.get('text', '') == 'myEWB':
        ip = request.META.get('REMOTE_ADDR')
        Whitelist.objects.get_or_create(ip=ip)
        return HttpResponseRedirect(reverse('home'))    
        
    else:
        return HttpResponseRedirect(reverse('httpbl_blacklist'))
