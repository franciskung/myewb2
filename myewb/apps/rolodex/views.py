from django.core.urlresolvers import reverse
from django.db.models import Q, Count, Max
from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect
from django.template import RequestContext, Context, loader
from django.contrib.auth.models import User
from django.contrib.auth.decorators import user_passes_test

import pickle

from account_extra.forms import EmailLoginForm
from account.views import login as pinaxlogin

from datetime import datetime, date
from siteutils.shortcuts import get_object_or_none
from networks.models import Network

from rolodex.models import TrackingProfile, Email, ProfileHistory, Interaction, ProfileFlag, ProfileBadge, Flag, Badge, ProfileView, Activity, CustomField, CustomValue, Event, EventAttendance
from rolodex.forms import TrackingProfileForm, NoteForm, FlagForm, BadgeForm, CustomFieldForm

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

    recent = ProfileView.objects.filter(user=request.user).values('profile').annotate(latest_view=Max('date')).order_by('-latest_view')[:15]
    recent_objs = []
    for r in recent:
        recent_objs.append(TrackingProfile.objects.get(id=r['profile']))
        
    updated = Activity.objects.values('profile').annotate(latest_view=Max('entered')).order_by('-latest_view')[:10]
    updated_objs = []
    for u in updated:
        updated_objs.append(TrackingProfile.objects.get(id=u['profile']))
        
    chapters = Network.objects.filter(chapter_info__isnull=False, is_active=True).order_by('name')
        
    return render_to_response("rolodex/home.html",
                              {'flags': flags,
                               'badges': badges,
                               'recent': recent_objs,
                               'updated': updated_objs,
                               'chapters': chapters},
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
        
    search = request.GET.get('search', None)
    if not search:
        request.user.message_set.create(message='Please enter a search term')
        return HttpResponseRedirect(reverse('rolodex_home'))
            
    # match on first name, lastname, or email
    qry = Q(first_name__icontains=search.split()[0])
    qry = qry | Q(last_name__icontains=search.split()[0])
    qry = qry | Q(email__email__icontains=search.split()[0])

    # support space-deliminated search terms
    for term in search.split()[1:]:     
        qry2 = Q(first_name__icontains=term)
        qry2 = qry2 | Q(last_name__icontains=term)
        qry2 = qry2 | Q(email__email__icontains=term)
        
        qry = qry & qry2
    
    results = TrackingProfile.objects.filter(qry)
    results = results.distinct().order_by("last_name")

    # in case they searched events
    events = Event.objects.filter(name__icontains=search).order_by('-date')
    
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
            
            # create email/phone and set as primary, if needed
            profile.update_email(form.cleaned_data['email'])
            profile.update_phone(form.cleaned_data['phone'])
                    
            # save revision history
            if profile_pickle:
                history = ProfileHistory.objects.create(profile=profile,
                                                        editor=request.user,
                                                        revision=profile_pickle)
                

            # log into interaction history
            log = Activity.objects.create(profile=profile,
                                          activity_type='edit',
                                          date=datetime.now(),
                                          added_by=request.user)

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
    custom = profile.get_custom_fields(user=request.user)
    
    ProfileView.objects.create(profile=profile, user=request.user, ip=request.META['REMOTE_ADDR'])
    
    
    if not profile.city:
        if profile.chapter and hasattr(profile.chapter, 'chapter_info'):
            profile.city = profile.chapter.chapter_info.city
            profile.save()

    return render_to_response("rolodex/profile_view.html",
                              {'profile': profile,
                               'activities': activities,
                               'custom': custom},
                              context_instance=RequestContext(request))

def note_edit(request, profile_id=None, note_id=None):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    if note_id:
        note = get_object_or_none(Interaction, id=note_id)
        profile = note.profile
        editing = True
    else:
        note = None
        profile = get_object_or_404(TrackingProfile, id=profile_id)
        editing = False

    if request.method == 'POST':
        if note:
            form = NoteForm(request.POST, instance=note)
        else:
            form = NoteForm(request.POST)
        
        if form.is_valid():
            note = form.save(commit=False)
            
            note.profile = profile
            note.activity_type = 'interaction'
            if not note.date:
                note.date = datetime.now()
            note.added_by = request.user
            
            if editing:
                note.edited = datetime.now()
                
            note.save()
            
            request.user.message_set.create(message='New interaction saved')
            return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': profile.id}))
            
    else:
        if note:
            form = NoteForm(instance=note)
        else:
            form = NoteForm()
        
    return render_to_response("rolodex/note_edit.html",
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

def flag(request, profile_id=None, flag_id=None):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    if profile_id:
        profile = get_object_or_404(TrackingProfile, id=profile_id)
        flag = None
    else:
        flag = get_object_or_404(ProfileFlag, id=flag_id)
        profile = flag.profile
    
    if request.method == 'POST':
        if flag:
            form = FlagForm(request.POST, instance=flag)
        else:
            form = FlagForm(request.POST)
        
        if form.is_valid():
            flag = form.save(commit=False)
            
            flag.profile = profile
            flag.flagged_by = request.user
            flag.save()
            
            log = Activity.objects.create(profile=profile,
                                          activity_type='flag',
                                          date=datetime.now(),
                                          added_by=request.user,
                                          content_object=flag)
            
            return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': profile.id}))
            
    else:
        if flag:
            form = FlagForm(instance=flag)
        else:
            form = FlagForm()
        
    return render_to_response("rolodex/flag.html",
                              {'form': form,
                               'profile': profile,
                               'flag': flag,
                               'flags': Flag.objects.all()},
                              context_instance=RequestContext(request))

def unflag(request, flag_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    flag = get_object_or_404(ProfileFlag, id=flag_id)
    
    flag.unflagged_by = request.user
    flag.unflagged_date = datetime.now()
    flag.active = False
    flag.save()
            
    log = Activity.objects.create(profile=flag.profile,
                                  activity_type='unflag',
                                  date=datetime.now(),
                                  added_by=request.user,
                                  content_object=flag)
    
    return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': flag.profile.id}))

def flag_view_ajax(request, flag_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    flag = get_object_or_none(ProfileFlag, id=flag_id)
    
    return render_to_response("rolodex/flag_view_ajax.html",
                              {'flag': flag},
                              context_instance=RequestContext(request))

def badge(request, profile_id=None, badge_id=None):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    if profile_id:
        profile = get_object_or_404(TrackingProfile, id=profile_id)
        badge = None
    else:
        badge = get_object_or_404(ProfileBadge, id=badge_id)
        profile = badge.profile
    
    if request.method == 'POST':
        if badge:
            form = BadgeForm(request.POST, instance=badge)
        else:
            form = BadgeForm(request.POST)
        
        if form.is_valid():
            badge = form.save(commit=False)
            
            badge.profile = profile
            badge.added_by = request.user
            badge.save()

            log = Activity.objects.create(profile=profile,
                                          activity_type='badge',
                                          date=datetime.now(),
                                          added_by=request.user,
                                          content_object=badge)
            
            return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': profile.id}))
            
    else:
        if badge:
            form = BadgeForm(instance=badge)
        else:
            form = BadgeForm()
        
    return render_to_response("rolodex/badge.html",
                              {'form': form,
                               'profile': profile,
                               'badge': badge},
                              context_instance=RequestContext(request))

def unbadge(request, badge_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    badge = get_object_or_404(ProfileBadge, id=badge_id)
    
    badge.removed_by = request.user
    badge.removed_date = datetime.now()
    badge.active = False
    badge.save()
            
    log = Activity.objects.create(profile=badge.profile,
                                  activity_type='unbadge',
                                  date=datetime.now(),
                                  added_by=request.user,
                                  content_object=badge)
    
    return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': badge.profile.id}))

def badge_view_ajax(request, badge_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    badge = get_object_or_none(ProfileBadge, id=badge_id)
    
    return render_to_response("rolodex/badge_view_ajax.html",
                              {'badge': badge},
                              context_instance=RequestContext(request))

def browse_flags(request, flag_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    flag = get_object_or_404(Flag, id=flag_id)
    results = ProfileFlag.objects.filter(flag=flag, active=True).order_by('-flagged_date')
    
    return render_to_response("rolodex/browse_flags.html",
                              {'flag': flag,
                               'results': results},
                              context_instance=RequestContext(request))

def browse_badges(request, badge_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    badge = get_object_or_404(Badge, id=badge_id)
    years = ProfileBadge.objects.filter(badge=badge).values('year').annotate(num_hits=Count('id')).order_by('-year')

    results = ProfileBadge.objects.filter(badge=badge, active=True)
    
    current_year = None
    if request.GET.get('year', None):
        results = results.filter(year=request.GET['year'])
        current_year = request.GET['year']
    
    results = results.order_by('-added_date')
    
    return render_to_response("rolodex/browse_badges.html",
                              {'badge': badge,
                               'results': results,
                               'years': years,
                               'current_year': current_year},
                              context_instance=RequestContext(request))

def custom_fields(request):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))

    form = CustomFieldForm()

    if request.method == 'POST':
        if request.POST.get('action', None) == 'add':
            form = CustomFieldForm(request.POST)
            
            if form.is_valid():
                field = form.save(commit=False)
                field.owner = request.user
                field.save()
                
                request.user.message_set.create(message='Field added.')
                return HttpResponseRedirect(reverse('rolodex_custom_fields'))
            
        elif request.POST.get('action', None) == 'update':
            field = get_object_or_none(CustomField, id=request.POST['field_id'])
            
            if field and (field.visibility == 'everyone' or (field.visibility == 'private' and field.owner == request.user)):
                form = CustomFieldForm(request.POST, instance=field)
                
                if form.is_valid():
                    field = form.save()
                    
                    request.user.message_set.create(message='Field updated.')
                    return HttpResponseRedirect(reverse('rolodex_custom_fields'))
            
        elif request.POST.get('action', None) == 'delete' & request.POST.get('field_id', None):
            field = get_object_or_none(CustomField, id=request.POST['field_id'])
            
            if field and (field.visibility == 'everyone' or (field.visibility == 'private' and field.owner == request.user)):
                field.delete()
                request.user.message_set.create(message='Field deleted.')
                return HttpResponseRedirect(reverse('rolodex_custom_fields'))

    qry = Q(visibility='anyone') | (Q(visibility='private') & Q(owner=request.user))
    fields = CustomField.objects.filter(qry).order_by('name')
    
    badges = Badge.objects.all()
    flags = Flag.objects.all()

    return render_to_response("rolodex/custom_fields.html",
                              {'fields': fields,
                               'badges': badges,
                               'flags': flags},
                              context_instance=RequestContext(request))

def profile_edit_custom(request, profile_id):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))
        
    profile = get_object_or_404(TrackingProfile, id=profile_id)
    fields = profile.get_custom_fields(user=request.user, include_blank=True)
    
    if request.method == 'POST':
        profile_pickle = pickle.dumps(profile.to_dict())
        changed = False
        
        for field, value in fields.items():
            newvalue = request.POST.get("custom_field_%d" % field.id, None)
            
            if (newvalue and not value) or (value and not newvalue) or (value.value != newvalue):
                if not value:
                    value, created = CustomValue.objects.get_or_create(field=field, profile=profile)
                
                if newvalue:
                    value.value = newvalue
                    value.save()
                else:
                    value.delete()
                
                changed = True

        if changed:        
            profile.updated_by = request.user
            profile.save()
                
            # save revision history
            history = ProfileHistory.objects.create(profile=profile,
                                                    editor=request.user,
                                                    revision=profile_pickle)
                

            # log into interaction history
            log = Activity.objects.create(profile=profile,
                                          activity_type='edit',
                                          date=datetime.now(),
                                          added_by=request.user)

        # display success message            
        request.user.message_set.create(message='Record updated')
        return HttpResponseRedirect(reverse('rolodex_view', kwargs={'profile_id': profile.id}))

        
    return render_to_response("rolodex/profile_edit_custom.html",
                              {'fields': fields,
                               'profile': profile},
                              context_instance=RequestContext(request))

def import_list(request):
    if not perm(request):
        return HttpResponseRedirect(reverse('rolodex_login'))
        
    if request.method == 'POST':
        action = request.POST.get('conditions', None)
        
        extra_obj = None
        kwargs = {}
        dupe_args = {}
        log_type = None
        
        if action == 'flag' and request.POST.get('flag', None):
            flag = get_object_or_none(Flag, id=request.POST['flag'])
            extra_obj = ProfileFlag
            
            dupe_args['flag'] = flag
            dupe_args['active'] = True
            
            kwargs['flag'] = flag
            kwargs['note'] = request.POST.get('flag_note', None)
            kwargs['flagged_by'] = request.user
            log_type = 'flag'
            
        elif action == 'badge' and request.POST.get('badge', None):
            badge = get_object_or_none(Badge, id=request.POST['badge'])
            extra_obj = ProfileBadge
            
            dupe_args['badge'] = badge
            dupe_args['active'] = True
            dupe_args['current'] = True
            
            kwargs['badge'] = badge
            kwargs['year'] = date.today().year
            kwargs['note'] = request.POST.get('badge_note', None)
            kwargs['added_by'] = request.user
            log_type = 'badge'
            
        elif action == 'badge2' and request.POST.get('badge2', None):
            badge = get_object_or_none(Badge, id=request.POST['badge2'])
            extra_obj = ProfileBadge
            
            dupe_args['badge'] = badge
            dupe_args['active'] = True
            dupe_args['current'] = False
            
            kwargs['badge'] = badge
            kwargs['current'] = False
            kwargs['note'] = request.POST.get('badge_note', None)
            kwargs['added_by'] = request.user
            log_type = 'badge'
            
        elif action == 'note' and request.POST.get('note', None):
            extra_obj = Interaction
            
            kwargs['note'] = request.POST.get('note', None)
            kwargs['activity_type'] = 'interaction'
            kwargs['interaction_type'] = 'note'
            kwargs['date'] = date.today()
            kwargs['added_by'] = request.user
            
            dupe_args = kwargs
            
        elif action == 'event':
            eventid = request.POST.get('event', None)
            if eventid == 'new':
                event = Event.objects.create(name=request.POST.get('new_event', None),
                                             date=request.POST.get('new_event_date', date.today()))
            else:
                event = Event.objects.get(id=eventid)
                
            extra_obj = EventAttendance
            
            dupe_args['event'] = event
            
            kwargs['event'] = event
            kwargs['activity_type'] = 'event'
            kwargs['date'] = date.today()
        
        emails  = request.POST.get('emails', "").split("\n")
        updated = []
        dupe = []
        skipped = []
        for email in emails:
            email = email.strip()
            
            email_obj = Email.objects.filter(email=email)
            if email_obj:
                kwargs['profile'] = email_obj[0].profile
                dupe_args['profile'] = email_obj[0].profile
                
                if extra_obj.objects.filter(**dupe_args).count():
                    dupe.append(email)
                
                else:
                    created = extra_obj.objects.create(**kwargs)

                    if log_type:
                        Activity.objects.create(profile=email_obj[0].profile,
                                                activity_type=log_type,
                                                date=datetime.now(),
                                                added_by=request.user,
                                                content_object=created)

                    updated.append(email)

            else:
                skipped.append(email)
        
        return render_to_response("rolodex/import_complete.html",
                                  {'updated': updated,
                                   'dupe': dupe,
                                   'skipped': skipped},
                                  context_instance=RequestContext(request))

    badges = Badge.objects.all()
    flags = Flag.objects.all()
    events = Event.objects.all()

    return render_to_response("rolodex/import.html",
                              {'badges': badges,
                               'flags': flags,
                               'events': events},
                              context_instance=RequestContext(request))

def browse_chapter(request, chapter=None):
    if request.GET.get('chapter') and not chapter:
        chapter = request.GET['chapter']
        return HttpResponseRedirect(reverse('rolodex_browse_chapter', \
            kwargs={'chapter': chapter}))
            
    chapter = get_object_or_none(Network, slug=chapter)
    if not chapter:
        request.user.message_set.create(message='Chapter not found')
        return HttpResponseRedirect(reverse('rolodex_home'))

    results = TrackingProfile.objects.filter(chapter=chapter)
    
    filters = request.GET.get('filters', '')
    if filters:
        if filters == 'role':
            results = results.filter(profilebadge__current=True, profilebadge__active=True).distinct()
        if filters == 'past':
            results = results.filter(profilebadge__current=False, profilebadge__active=True).distinct()
        if filters == 'flag':
            results = results.filter(profileflag__active=True).distinct()
    
    results = results.order_by('last_name')

    return render_to_response("rolodex/browse_chapter.html",
                              {'chapter': chapter,
                               'results': results,
                               'filters': filters},
                              context_instance=RequestContext(request))

def browse_event(request, event_id=None):
    if not event_id and not request.POST.get('event', None):
        request.user.message_set.create(message='Enter an event into the search')
        return HttpResponseRedirect(reverse('rolodex_home'))

    if not event_id:
        #events = Event.objects.filter(name__icontains=request.POST['event']).order_by('-date')

        # support space-deliminated search terms
        qry = Q(name__icontains=request.POST['event'].split()[0])
        for term in request.POST['event'].split()[1:]:
            qry = qry & Q(name__icontains=term)

        events = Event.objects.filter(qry).order_by('-date')        
        
        if events.count() == 1:
            return HttpResponseRedirect(reverse('rolodex_browse_event', \
                                                kwargs={'event_id': events[0].id}))
            
        return render_to_response("rolodex/browse_event_search.html",
                                  {'events': events},
                                  context_instance=RequestContext(request))

                                  
    event = get_object_or_none(Event, id=event_id)

    results = EventAttendance.objects.filter(event=event)
    results = results.order_by('profile__last_name')
    
    return render_to_response("rolodex/browse_event.html",
                              {'event': event,
                               'results': results},
                              context_instance=RequestContext(request))

