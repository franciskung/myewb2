from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext, Context, loader

from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

@login_required
def intro(request):

    return render_to_response("profileupdate2013/intro.html",
                              {'profile_user': request.user},
                              context_instance=RequestContext(request))

@login_required
def contact(request):
    return render_to_response("profileupdate2013/contact.html",
                              {'profile_user': request.user},
                              context_instance=RequestContext(request))

@login_required
def workplace(request):
    return render_to_response("profileupdate2013/intro.html",
                              {'profile_user': request.user},
                              context_instance=RequestContext(request))

@login_required
def school(request):
    return render_to_response("profileupdate2013/intro.html",
                              {'profile_user': request.user},
                              context_instance=RequestContext(request))

@login_required
def interests(request):

    return render_to_response("profileupdate2013/intro.html",
                              {'profile_user': request.user},
                              context_instance=RequestContext(request))

@login_required
def complete(request):
    return render_to_response("profileupdate2013/complete.html",
                              {'profile_user': request.user},
                              context_instance=RequestContext(request))

