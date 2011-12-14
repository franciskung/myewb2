"""myEWB conference scheduling

This file is part of myEWB
Copyright 2009-2010 Engineers Without Borders Canada

@author: Francis Kung
"""

import datetime, settings
from datetime import date

from account.models import PasswordReset
from django.contrib import auth
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib.auth.views import logout as pinaxlogout
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils.hashcompat import sha_constructor
from pinax.apps.account.forms import ResetPasswordKeyForm, ResetPasswordForm

from account_extra.forms import EmailLoginForm
from base_groups.models import BaseGroup
from conference.forms import ConferenceSessionForm
from conference.models import ConferenceRegistration, ConferenceSession, STREAMS, STREAMS_SHORT
from mailer.sendmail import send_mail
from siteutils import online_middleware
from siteutils.shortcuts import get_object_or_none
from siteutils.helpers import fix_encoding

CONFERENCE_DAYS = (('thurs', 'Thursday', 13),
                   ('fri', 'Friday', 14),
                   ('sat', 'Saturday', 15))

def build_recommended(user, timeslot):
    registration = get_object_or_404(ConferenceRegistration, user=user)
    
    sessions = ConferenceSession.objects.filter(timeslot=timeslot)
    recommendations = set()
    
    for s in sessions:
        criteria = ConferenceSessionCriteria.objects.filter(session=s)
        
        for c in criteria:
            if c.first_conference:
                if c.first_conference == 'yes' and registration.conferenceselectorinfo.first_conference:
                    recommendations.add(s)
                    
                if c.first_conference == 'no' and not registration.conferenceselectorinfo.first_conference:
                    recommendations.add(s)

            if c.roles and registration.conferenceselectorinfo.roles.count(c.roles):
                recommendations.add(s)
                    
            if c.leadership_years and c.leadership_years == registration.conferenceselectorinfo.leadership_years:
                recommendations.add(s)
                
            if c.leadership_day:
                if c.leadership_day == 'yes' and registration.conferenceselectorinfo.leadership_day:
                    recommendations.add(s)
                    
                if c.leadership_day == 'no' and not registration.conferenceselectorinfo.leadership_day:
                    recommendations.add(s)
            
            if c.prep and c.prep == registration.conferenceselectorinfo.prep:
                recommendations.add(s)
                
            if c.past_session and ConferenceSession.objects.filter(id=past_session, attendees=user).count():
                recommendations.add(s)

    return recommendations
                        
                   
@login_required
def questionnaire(request, user=None):
    if not user:
        user= request.user
        
    if request.method == 'POST':
        form = False
        if form.is_valid():
            form.save()
            
            return HttpResponseRedirect('')
        
    else:
        form = False
        
    common_sessions = ConferenceSession.objects.filter(common=True)
    for session in common_sessions:
        session.attendees.add(user)
        
    return render_to_response('conference/schedule2/questionnaire.html',
                              {"form": form},
                              context_instance = RequestContext(request))
                              
@login_required
def session_pick(request, timeslot=None):
    user = request.user

    if not timeslot:
        timeslots = ConferenceTimeslot.objects.all()
        for t in timeslots:
            if t.common or ConferenceSession.objects.filter(timeslot=t, attendees=user).count():
                pass
            else:
                timeslot = t
                break
        
    if not timeslot:
        return HttpResponseRedirect('schedule_for_user')
        
        
    day = timeslot.day
    schedule = ConferenceSession.objects.filter(attendees=user).order_by(timeslot__day, timeslot__time)
    
    recommended = build_recommended(user, timeslot)
    sessions = ConferenceSession.objects.filter(timeslot=timeslot).exclude(id__in=recommended)
    
    return render_to_response('conference/schedule2/pick_session.html',
                              {"day": day,
                               "schedule": schedule,
                               "recommended": recommended,
                               "sessions": sessions,
                               "timeslot": timeslot},
                              context_instance=RequestContext(request))

@login_required
def session_pick_save(request):
    if request.method == 'POST':
        timeslot = request.POST.get('timeslot', None)
        session = request.POST.get('session', None)
        user = request.user

        if timeslot and session:
            timeslot = get_object_or_404(ConferenceTimeslot, id=timeslot)
            session = get_object_or_404(ConferenceSession, id=session, timeslot=timeslot)
            
            current_sessions = ConferenceSession.objects.filter(timeslot=timeslot, attendees=user)
            for s in current_sessions:
                s.attendees.remove(user)
                
            session.attendees.add(user)
    
    return HttpResponseRedirect('session_pick')
    

@login_required
def schedule_for_user(request, user=None, day=None, time=None):
    if not user:
        user = request.user
        
    sessions = ConferenceSession.objects.filter(attendees=user).order_by('timeslot__day, timeslot__time')
        
    timelist = []
    for t in range(8, 22):
        timelist.append(t)

    return render_to_response("conference/schedule2/user.html",
                              {"sessions": sessions,
                               "timelist": timelist,
                               "printable": request.GET.get('printable', None)},
                              context_instance = RequestContext(request))


@login_required
def print_schedule(request):
    return HttpResponse("not implemented")

        
def session_detail(request, session):
    s = get_object_or_404(ConferenceSession, id=session)
    
    attendees = s.attendees.order_by('?')
    numattendees = attendees.count()

    if request.is_mobile or not request.user.has_module_perms("conference"):
        if  numattendees < 10:
            attendees = attendees[0:numattendees]
        else:
            attendees = attendees[0:10]
    
    return render_to_response("conference/schedule2/session_detail.html",
                              {"session": s,
                               "attendees": attendees,
                               "numattendees": numattendees},
                              context_instance = RequestContext(request))


@login_required
def session_new(request):
    if not request.user.has_module_perms("conference"):
        return HttpResponseRedirect(reverse('conference_schedule'))

    if request.method == 'POST':
        form = ConferenceSessionForm(request.POST)

        if form.is_valid():
            session = form.save()
            return HttpResponseRedirect(reverse('conference_session', kwargs={'session': session.id}))
    else:
        form = ConferenceSessionForm()
        
    return render_to_response("conference/schedule/session_edit.html",
                              {"form": form,
                               "new": True},
                              context_instance = RequestContext(request))

@login_required
def session_edit(request, session):
    if not request.user.has_module_perms("conference"):
        return HttpResponseRedirect(reverse('conference_schedule'))

    s = get_object_or_404(ConferenceSession, id=session)
    
    if request.method == 'POST':
        form = ConferenceSessionForm(request.POST, instance=s)

        if form.is_valid():
            session = form.save()
            return HttpResponseRedirect(reverse('conference_session', kwargs={'session': session.id}))
    else:
        form = ConferenceSessionForm(instance=s)
        
    return render_to_response("conference/schedule/session_edit.html",
                              {"form": form},
                              context_instance = RequestContext(request))

@login_required
def session_delete(request, session):
    if not request.user.has_module_perms("conference"):
        return HttpResponseRedirect(reverse('conference_schedule'))

    s = get_object_or_404(ConferenceSession, id=session)
    
    if request.method == 'POST' and request.POST.get('delete', None):
        redirect_day = 'fri'
        if s.day.day == 13:
            redirect_day = 'thurs'
        elif s.day.day == 15:
            redirect_day = 'sat'
            
        s.delete()
        return HttpResponseRedirect(reverse('conference_by_day', kwargs={'day': redirect_day, 'stream': 'all'}))
        
    return render_to_response("conference/schedule/session_delete.html",
                              {"session": s},
                              context_instance = RequestContext(request))

@login_required
def session_attend(request, session):
    s = get_object_or_404(ConferenceSession, id=session)
    s.maybes.remove(request.user)
    s.attendees.add(request.user)
    
    return HttpResponseRedirect(reverse('conference_session', kwargs={'session': s.id}))
    
@login_required
def session_tentative(request, session):
    s = get_object_or_404(ConferenceSession, id=session)
    s.attendees.remove(request.user)
    s.maybes.add(request.user)
    
    return HttpResponseRedirect(reverse('conference_session', kwargs={'session': s.id}))
    
    
@login_required
def session_skip(request, session):
    s = get_object_or_404(ConferenceSession, id=session)
    s.attendees.remove(request.user)
    s.maybes.remove(request.user)
    
    return HttpResponseRedirect(reverse('conference_session', kwargs={'session': s.id}))
    
@login_required
def private_detail(request, session):
    s = get_object_or_404(ConferencePrivateEvent, id=session)
    
    if s.creator != request.user:
        return render_to_response("conference/schedule/denied.html",
                                  {}, context_instance = RequestContext(request))
    
    return render_to_response("conference/schedule/session_private_detail.html",
                              {"session": s,
                               "attendees": [],
                               "private": True},
                              context_instance = RequestContext(request))

@login_required
def private_new(request):
    if request.method == 'POST':
        form = ConferencePrivateEventForm(request.POST)

        if form.is_valid():
            session = form.save(commit=False)
            session.creator = request.user
            session.save()
            return HttpResponseRedirect(reverse('conference_private', kwargs={'session': session.id}))
    else:
        form = ConferencePrivateEventForm()
        
    return render_to_response("conference/schedule/session_edit.html",
                              {"form": form,
                               "new": True,
                               "private": True},
                              context_instance = RequestContext(request))

@login_required
def private_edit(request, session):
    s = get_object_or_404(ConferencePrivateEvent, id=session)
    
    if s.creator != request.user:
        return render_to_response("conference/schedule/denied.html",
                                  {}, context_instance = RequestContext(request))
    
    if request.method == 'POST':
        form = ConferencePrivateEventForm(request.POST, instance=s)

        if form.is_valid():
            session = form.save()
            return HttpResponseRedirect(reverse('conference_private', kwargs={'session': session.id}))
    else:
        form = ConferencePrivateEventForm(instance=s)
        
    return render_to_response("conference/schedule/session_edit.html",
                              {"form": form,
                               "private": True},
                              context_instance = RequestContext(request))

@login_required
def private_delete(request, session):
    s = get_object_or_404(ConferencePrivateEvent, id=session)
    
    if s.creator != request.user:
        return render_to_response("conference/schedule/denied.html",
                                  {}, context_instance = RequestContext(request))
    
    if request.method == 'POST' and request.POST.get('delete', None):
        redirect_day = 14
        if s.day.day == 13:
            redirect_day = 13
        elif s.day.day == 15:
            redirect_day = 15
            
        s.delete()
        return HttpResponseRedirect(reverse('conference_for_user'))
        
    return render_to_response("conference/schedule/session_delete.html",
                              {"session": s,
                               "private": True},
                              context_instance = RequestContext(request))

def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('conference_schedule'))

    signin_form = EmailLoginForm(initial={'remember': 'on'})
    
    if request.method == "POST":
        signin_form = EmailLoginForm(request.POST)
        if signin_form.is_valid():
            user = signin_form.user
            auth.login(request, user)
            return HttpResponseRedirect(reverse('conference_schedule'))

    return render_to_response("conference/schedule/login.html",
                              {'form': signin_form},
                              context_instance = RequestContext(request))

def logout(request):
    online_middleware.remove_user(request)
    return pinaxlogout(request, next_page=reverse('conference_schedule'))

def reset_password(request, key=None):
    context = {}
    
    if request.method == 'POST' and request.POST.get('email', None):
        if request.user.is_authenticated():
            return HttpResponseRedirect(reverse('conference_schedule'))
            
        email = request.POST.get('email', None)
        if User.objects.filter(email__iexact=email).count():
            context['email'] = email
        else:
            context['email_error'] = email

        for user in User.objects.filter(email__iexact=email):
            temp_key = sha_constructor("%s%s%s" % (
                settings.SECRET_KEY,
                user.email,
                settings.SECRET_KEY,
            )).hexdigest()

            # save it to the password reset model
            password_reset = PasswordReset(user=user, temp_key=temp_key)
            password_reset.save()

            current_site = Site.objects.get_current()
            domain = unicode(current_site.domain)

            #send the password reset email
            subject = "myEWB password reset"
            message = render_to_string("conference/schedule/password_reset_message.txt", {
                "user": user,
                "temp_key": temp_key,
                "domain": domain,
            })
            send_mail(subject=subject, txtMessage=message,
                      fromemail=settings.DEFAULT_FROM_EMAIL,
                      recipients=[user.email], priority="high")
        
    elif key:
        if PasswordReset.objects.filter(temp_key__exact=key, reset=False).count():
            if request.method == 'POST':
                form = ResetPasswordKeyForm(request.POST)
                
                if form.is_valid():
                    # get the password_reset object
                    temp_key = form.cleaned_data.get("temp_key")
                    password_reset = PasswordReset.objects.filter(temp_key__exact=temp_key, reset=False)
                    password_reset = password_reset[0]  # should always be safe, as form_clean checks this

                    # now set the new user password
                    user = User.objects.get(passwordreset__exact=password_reset)
                    result = user.set_password(form.cleaned_data['password1'])

                    if not result:
                        # unsuccessful
                        form._errors[forms.forms.NON_FIELD_ERRORS] = ["Error (password is too simple maybe?)"]
                    else:
                        user.save()

                        # change all the password reset records to this person to be true.
                        for password_reset in PasswordReset.objects.filter(user=user):
                            password_reset.reset = True
                            password_reset.save()

                        user = auth.authenticate(username=user.username, password=form.cleaned_data['password1'])
                        auth.login(request, user)
                        return HttpResponseRedirect(reverse('conference_schedule'))
            else:
                form = ResetPasswordKeyForm(initial={'temp_key': key})
            
            context['keyvalid'] = True
            context['form'] = form
        else:
            context['keyerror'] = True
    
    else:
        return HttpResponseRedirect(reverse('conference_schedule_login'))

    return render_to_response("conference/schedule/reset.html",
                              context,
                              context_instance = RequestContext(request))

