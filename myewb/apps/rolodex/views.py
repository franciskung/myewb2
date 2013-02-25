from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext, Context, loader
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test

from account_extra.forms import EmailLoginForm
from account.views import login as pinaxlogin

from datetime import datetime

from rolodex.models import TrackingProfile
from rolodex.forms import TrackingProfileForm

def home(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('rolodex_login'))
        
    return render_to_response("rolodex/home.html",
                              {},
                              context_instance=RequestContext(request))

def login(request, form_class=EmailLoginForm, 
        template_name="rolodex/login.html", success_url=None,
        associate_openid=False, openid_success_url=None, url_required=False):
        
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('rolodex_home'))
    
    if not success_url:
        success_url = request.GET.get("url", None)
    if not success_url:
        success_url = reverse('rolodex_home')
        
    next = request.GET.get("next", None)
    
    return pinaxlogin(request, form_class, template_name, success_url, 
            associate_openid, openid_success_url, url_required)

def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect(reverse('rolodex_login'))

def search(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('rolodex_login'))
        
    search = request.POST.get('search', None)
    if not search:
        request.user.message_set.create(message='Please enter a search term')
        return HttpResponseRedirect(reverse('rolodex_home'))
            
    # match on first name
    qry = Q(first_name__icontains=search.split()[0])
    for term in search.split()[1:]:     # support space-deliminated search terms
        qry = qry & Q(first_name__icontains=term)

    # match on last name
    qry2 = Q(last_name__icontains=search.split()[0])
    for term in search.split()[1:]:     # support space-deliminated search terms
        qry2 = qry2 & Q(last_name__icontains=term)
    qry = qry | qry2
        
    # match on email
    qry2 = Q(email__email__icontains=search.split()[0])
    for term in search.split()[1:]:     # support space-deliminated search terms
        qry2 = qry2 & Q(email__email__icontains=term)
    qry = qry | qry2
    
    results = TrackingProfile.objects.filter(qry)
    results = results.distinct().order_by("last_name")

    return render_to_response("rolodex/search.html",
                              {'results': results,
                               'search': search},
                              context_instance=RequestContext(request))

def new(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('rolodex_login'))
        
    if request.method == 'POST':
        form = TrackingProfileForm(request.POST)
        
        if form.is_valid():
            profile = form.save()
            request.user.message_set.create(message='New record created')
            return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': profile.id}))
            
    else:
        form = TrackingProfileForm()
        
    return render_to_response("rolodex/new.html",
                              {'form': form},
                              context_instance=RequestContext(request))

