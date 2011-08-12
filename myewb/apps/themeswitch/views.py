from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.template import RequestContext, Context, loader

from themeswitch.models import RequestLog

def dashboard(request):
    return render_to_response("themeswitch/dashboard.html",
                              {},
                              context_instance=RequestContext(request))

def switch(request, theme):
    request.session['theme'] = theme
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('home')))

def vote_up(request, theme):
    pass

def vote_down(request, theme):
    pass
