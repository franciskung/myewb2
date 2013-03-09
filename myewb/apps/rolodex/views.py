from django.core.urlresolvers import reverse
from django.db.models import Q
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext, Context, loader
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test

import pickle

from account_extra.forms import EmailLoginForm
from account.views import login as pinaxlogin

from datetime import datetime
from siteutils.shortcuts import get_object_or_none

from rolodex.models import TrackingProfile, Email, ProfileHistory, Interaction, ProfileFlag, ProfileBadge, Flag, Badge, ProfileView
from rolodex.forms import TrackingProfileForm, NoteForm, FlagForm, BadgeForm

def perm(request):
    if request.user.is_authenticated() and request.user.has_module_perms("rolodex"):
        return True
    else:
        return False

def home(request):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))
        
    badges = Badge.objects.all()
    flags = Flag.objects.all()
    recent = ProfileView.objects.filter(user=request.user).order_by('-date')[:20]
        
    return render_to_response("rolodex/home.html",
                              {'flags': flags,
                               'badges': badges,
                               'recent': recent},
                              context_instance=RequestContext(request))

def login(request, form_class=EmailLoginForm, 
        template_name="rolodex/login.html", success_url=None,
        associate_openid=False, openid_success_url=None, url_required=False):
    
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
    if not perm(request):
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

def profile_edit(request, profile_id=None):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))
        
    profile = None
    if profile_id:
        profile = get_object_or_404(TrackingProfile, id=profile_id)
        
    if request.method == 'POST':
        profile_pickle = None
        if profile:
            form = TrackingProfileForm(request.POST, instance=profile)
            profile_pickle = pickle.dumps(profile.to_dict())
        else:
            form = TrackingProfileForm(request.POST)
        
        if form.is_valid():
            profile = form.save(commit=False)
            profile.updated_by = request.user
            profile.save()
            
            # create email and set as primary, if needed
            email = form.cleaned_data['email']
            if email:
                email_obj = get_object_or_none(Email, email=email, profile=profile)
                if not email_obj:
                    email_obj = Email.objects.create(email=email,
                                                     profile=profile,
                                                     updated=datetime.now())
                if not email_obj.primary:
                    other_emails = Email.objects.filter(profile=profile)
                    for e in other_emails:
                        e.primary = False
                        e.save()
                    email_obj.primary = True
                    email_obj.save()
                    
            # save revision history
            if profile_pickle:
                history = ProfileHistory.objects.create(profile=profile,
                                                        editor=request.user,
                                                        revision=profile_pickle)
                

            # display success message            
            if profile:
                request.user.message_set.create(message='Record updated')
            else:
                request.user.message_set.create(message='New record created')
            return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': profile.id}))
            
    else:
        if profile:
            form = TrackingProfileForm(instance=profile)
        else:
            form = TrackingProfileForm()
        
    return render_to_response("rolodex/profile_edit.html",
                              {'form': form,
                               'profile': profile},
                              context_instance=RequestContext(request))

def profile_view(request, profile_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))
    
    profile = get_object_or_404(TrackingProfile, id=profile_id)
    activities = profile.get_activities(user=request.user)
    
    ProfileView.objects.create(profile=profile, user=request.user, ip=request.META['REMOTE_ADDR'])

    return render_to_response("rolodex/profile_view.html",
                              {'profile': profile,
                               'activities': activities},
                              context_instance=RequestContext(request))

def note_new(request, profile_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    profile = get_object_or_404(TrackingProfile, id=profile_id)

    if request.method == 'POST':
        form = NoteForm(request.POST)
        
        if form.is_valid():
            note = form.save(commit=False)
            
            note.profile = profile
            note.activity_type = 'interaction'
            note.date = datetime.now()
            note.added_by = request.user
            note.save()
            
            request.user.message_set.create(message='New interaction saved')
            return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': profile.id}))
            
    else:
        form = NoteForm()
        
    return render_to_response("rolodex/note_new.html",
                              {'form': form,
                               'profile': profile},
                              context_instance=RequestContext(request))

def note_view_ajax(request, note_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    note = get_object_or_none(Interaction, id=note_id)
    
    return render_to_response("rolodex/note_view_ajax.html",
                              {'note': note},
                              context_instance=RequestContext(request))

def note_pin(request, note_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    note = get_object_or_none(Interaction, id=note_id)
    
    if not note.pinned:
        note.pinned = True
        note.save()
        
    request.user.message_set.create(message='Pinned')
    return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': note.profile.id}))

def note_unpin(request, note_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    note = get_object_or_none(Interaction, id=note_id)
    
    if note.pinned:
        note.pinned = False
        note.save()
        
    request.user.message_set.create(message='Un-pinned')
    return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': note.profile.id}))

def flag(request, profile_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    profile = get_object_or_404(TrackingProfile, id=profile_id)
    
    if request.method == 'POST':
        form = FlagForm(request.POST)
        
        if form.is_valid():
            flag = form.save(commit=False)
            
            flag.profile = profile
            flag.flagged_by = request.user
            flag.save()
            
            return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': profile.id}))
            
    else:
        form = FlagForm()
        
    return render_to_response("rolodex/flag.html",
                              {'form': form,
                               'profile': profile},
                              context_instance=RequestContext(request))

def unflag(request, badge_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    flag = get_object_or_404(ProfileFlag, id=flag_id)
    
    flag.unflagged_by = request.user
    flag.unflagged_date = datetime.now()
    flag.active = False
    flag.save()
            
    return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': badge.profile.id}))


def badge(request, profile_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    profile = get_object_or_404(TrackingProfile, id=profile_id)
    
    if request.method == 'POST':
        form = BadgeForm(request.POST)
        
        if form.is_valid():
            badge = form.save(commit=False)
            
            badge.profile = profile
            badge.added_by = request.user
            badge.save()
            
            return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': profile.id}))
            
    else:
        form = BadgeForm()
        
    return render_to_response("rolodex/badge.html",
                              {'form': form,
                               'profile': profile},
                              context_instance=RequestContext(request))

def unbadge(request, badge_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    badge = get_object_or_404(ProfileBadge, id=badge_id)
    
    badge.removed_by = request.user
    badge.removed_date = datetime.now()
    badge.active = False
    badge.save()
            
    return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': badge.profile.id}))

def browse_flags(request, flag_id):
    return HttpResponseRedirect(reverse('rolodex_home'))
    
def browse_badges(request, badge_id):
    return HttpResponseRedirect(reverse('rolodex_home'))
    
